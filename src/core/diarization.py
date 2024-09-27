import logging
import whisperx
import torch
from pydub import AudioSegment
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)

def apply_diarization(audio_path, transcript, api_key):
    try:
        device = _get_device()
        logger.info(f"Initializing DiarizationPipeline with device: {device}")
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=api_key, device=device)
        
        logger.info(f"Running diarization on audio file: {audio_path}")
        diarize_segments = diarize_model(audio_path)
        
        logger.info("Diarization completed. Segments:")
        logger.info(diarize_segments)
        
        logger.info("Preparing transcript segments")
        transcript_segments = _prepare_transcript_segments(transcript)
        
        logger.info("Assigning word speakers")
        result = whisperx.assign_word_speakers(diarize_segments, transcript_segments)
        
        return _post_process_diarization(result)
    except Exception as e:
        logger.error(f"Diarization error: {str(e)}", exc_info=True)
        raise ValueError(f"Diarization failed: {str(e)}")

def _get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")

def _prepare_transcript_segments(transcript):
    words = transcript.split()
    segments = []
    start_time = 0
    for i, word in enumerate(words):
        end_time = start_time + 0.4  # Assume each word takes about 0.4 seconds
        segments.append({"start": start_time, "end": end_time, "text": word})
        start_time = end_time
    return {"segments": segments}

def _post_process_diarization(result):
    formatted_transcript = []
    embeddings = np.array([s['speaker_embedding'] for s in result['segments'] if 'speaker_embedding' in s])
    
    if len(embeddings) > 0:
        # Determine optimal number of clusters
        max_clusters = min(len(embeddings), 10)  # Set a reasonable upper limit
        best_n_clusters = 2  # Default to 2 if we can't find a better option
        best_score = -1
        
        for n_clusters in range(2, max_clusters + 1):
            clustering = AgglomerativeClustering(n_clusters=n_clusters).fit(embeddings)
            score = silhouette_score(embeddings, clustering.labels_)
            if score > best_score:
                best_score = score
                best_n_clusters = n_clusters
        
        clustering = AgglomerativeClustering(n_clusters=best_n_clusters).fit(embeddings)
        labels = clustering.labels_
    else:
        labels = [0] * len(result['segments'])
    
    current_speaker = None
    current_text = []
    start_time = None
    
    for i, segment in enumerate(result['segments']):
        start = f"{segment['start']:.2f}"
        end = f"{segment['end']:.2f}"
        speaker = f"SPEAKER_{labels[i] + 1}"
        text = segment['text']
        
        if speaker != current_speaker:
            if current_speaker:
                formatted_transcript.append(f"{start_time} - {prev_end} | {current_speaker}: {' '.join(current_text)}")
            current_speaker = speaker
            current_text = [text]
            start_time = start
        else:
            current_text.append(text)
        
        prev_end = end
    
    if current_speaker:
        formatted_transcript.append(f"{start_time} - {prev_end} | {current_speaker}: {' '.join(current_text)}")
    
    return "\n".join(formatted_transcript)