import logging
from whisperx import DiarizationPipeline, load_audio
import torch
import numpy as np
import whisperx
from utils.encryption import EncryptionUtils
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist


logger = logging.getLogger(__name__)

def apply_diarization(audio_path, transcript, encrypted_api_key, embeddings=None):
    try:
        device = _get_device()
        logger.info(f"Initializing WhisperX diarization with device: {device}")
        
        # Decrypt the API key
        encryption_utils = EncryptionUtils()
        api_key = encryption_utils.decrypt(encrypted_api_key)
        
        # Load audio
        audio = whisperx.load_audio(audio_path)
        
        # Perform speaker diarization
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=api_key, device=device)
        diarize_segments = diarize_model(audio)
        
        logger.info("Diarization completed")
        
        # Assign speaker labels
        result = whisperx.assign_word_speakers(diarize_segments, transcript)
        logger.info("Speaker labels assigned to words")
        
        # If embeddings are provided, use them for speaker clustering
        if embeddings is not None:
            result = _cluster_speakers_with_embeddings(result, embeddings)
            logger.info("Speakers clustered using embeddings")
        
        return _post_process_diarization(result)
    except Exception as e:
        logger.error(f"Diarization error: {str(e)}", exc_info=True)
        return f"[Diarization failed: {str(e)}]\n\n" + "\n".join([seg["text"] for seg in transcript["segments"]])

def _get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")
    
def _cluster_speakers_with_embeddings(diarization_result, embeddings):
    segment_embeddings = []
    for segment in diarization_result["segments"]:
        start_frame = int(segment["start"] * 16000)
        end_frame = int(segment["end"] * 16000)
        segment_embedding = embeddings[:, :, start_frame:end_frame].mean(dim=2).numpy()
        segment_embeddings.append(segment_embedding.flatten())

    segment_embeddings = np.array(segment_embeddings)
    
    # Check for NaN values
    if np.isnan(segment_embeddings).any():
        logger.warning("NaN values found in embeddings. Replacing with 0.")
        segment_embeddings = np.nan_to_num(segment_embeddings, nan=0.0)
    
    # Check if we have enough valid embeddings for clustering
    if len(segment_embeddings) < 2:
        logger.warning("Not enough valid embeddings for clustering. Skipping clustering.")
        return diarization_result

    try:
        # Normalize the embeddings
        scaler = StandardScaler()
        normalized_embeddings = scaler.fit_transform(segment_embeddings)

        # Compute the distance matrix
        distance_matrix = cdist(normalized_embeddings, normalized_embeddings, metric='cosine')

        # Perform clustering
        n_clusters = min(len(segment_embeddings), 10)  # Limit to 10 speakers maximum
        clustering = AgglomerativeClustering(n_clusters=n_clusters, affinity='precomputed', linkage='average')
        labels = clustering.fit_predict(distance_matrix)

        # Assign speaker labels
        for i, segment in enumerate(diarization_result["segments"]):
            segment["speaker"] = f"SPEAKER_{labels[i]}"

    except Exception as e:
        logger.error(f"Clustering failed: {str(e)}. Falling back to original diarization.")
        return diarization_result

    return diarization_result

def _post_process_diarization(result):
    formatted_transcript = []
    current_speaker = None
    current_text = []
    start_time = None
    speaker_change_threshold = 0.8  # Fine-tune this value to switch speakers more appropriately
    
    for segment in result["segments"]:
        start = f"{segment['start']:.2f}"
        end = f"{segment['end']:.2f}"
        speaker = segment.get('speaker', 'UNKNOWN')

        # Fallback to previous speaker if UNKNOWN
        if speaker == 'UNKNOWN':
            speaker = current_speaker if current_speaker else 'SPEAKER_XX'

        text = segment['text']

        # Condition to switch speakers with a more generous threshold
        if speaker != current_speaker or (float(start) - float(prev_end) > speaker_change_threshold if 'prev_end' in locals() else False):
            if current_speaker:
                formatted_transcript.append(f"{start_time} - {prev_end} | {current_speaker}: {' '.join(current_text)}")
            current_speaker = speaker
            current_text = [text]
            start_time = start
        else:
            current_text.append(text)

        prev_end = end

    # Append the final speaker block
    if current_speaker:
        formatted_transcript.append(f"{start_time} - {prev_end} | {current_speaker}: {' '.join(current_text)}")

    return "\n".join(formatted_transcript)