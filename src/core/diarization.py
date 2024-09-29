import logging
import torch
import numpy as np
import whisperx
from pyannote.audio import Pipeline
from pyannote.core import Segment
from src.api.whisperx_api import load_whisperx_audio


logger = logging.getLogger(__name__)

def apply_diarization(audio_path, transcript, api_key):
    try:
        device = _get_device()
        logger.info(f"Initializing WhisperX diarization with device: {device}")
        
        # Load audio
        audio = load_whisperx_audio(audio_path)
        
        # First pass: Create speaker embeddings
        speaker_embeddings = _create_speaker_embeddings(audio, api_key)
        
        # Perform speaker diarization
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=api_key, device=device)
        diarize_segments = diarize_model(audio)
        logger.info("Initial diarization completed")
        
        # Refine diarization using speaker embeddings
        refined_segments = _refine_diarization(diarize_segments, speaker_embeddings, audio, api_key)
        
        # Assign speaker labels
        result = whisperx.assign_word_speakers(refined_segments, transcript)
        logger.info("Speaker labels assigned to words")
        
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
    
def _create_speaker_embeddings(audio, api_key):
    embedding_model = Pipeline.from_pretrained("pyannote/speaker-embedding", use_auth_token=api_key)
    embeddings = {}
    window_duration = 5.0  # 5 seconds window
    step = 2.5  # 2.5 seconds step
    for start in range(0, len(audio), int(step * 16000)):
        end = start + int(window_duration * 16000)
        segment = audio[start:end]
        if len(segment) < 16000:  # Skip segments shorter than 1 second
            continue
        embedding = embedding_model(segment)
        embeddings[start/16000] = embedding
    return embeddings

def _refine_diarization(diarize_segments, speaker_embeddings, audio, api_key):
    embedding_model = Pipeline.from_pretrained("pyannote/speaker-embedding", use_auth_token=api_key)
    refined_segments = []
    for segment, _, speaker in diarize_segments.itertracks(yield_label=True):
        segment_audio = audio[int(segment.start * 16000):int(segment.end * 16000)]
        segment_embedding = embedding_model(segment_audio)
        closest_speaker = min(speaker_embeddings.items(), key=lambda x: torch.cdist(segment_embedding, x[1]))
        refined_segments.append((segment.start, segment.end, f"SPEAKER_{closest_speaker[0]}"))
    return refined_segments

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