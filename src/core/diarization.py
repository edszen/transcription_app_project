import logging
import torch
import whisperx
from src.core.vad import apply_pyannote_vad
from src.api.whisperx_api import load_whisperx_audio

logger = logging.getLogger(__name__)

def apply_diarization(audio_path, transcript, api_key):
    try:
        # Initialize WhisperX
        device = _get_device()
        logger.info(f"Initializing WhisperX diarization with device: {device}")
        
        # Load audio
        audio = load_whisperx_audio(audio_path)
        
        # Apply VAD and extract speaker embeddings
        speaker_embeddings, vad_segments = apply_pyannote_vad(audio, api_key)
        
        # Perform speaker diarization
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=api_key, device=device)
        diarize_segments = diarize_model(audio)
        logger.info("Initial diarization completed")
        
        # Match transcriptions to speakers using embeddings from vad.py
        diarized_transcription = match_to_speaker(transcript["segments"], speaker_embeddings, diarize_segments)
        
        return _post_process_diarization(diarized_transcription)
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
    
def match_to_speaker(transcription_segments, speaker_embeddings, diarize_segments):
    diarized_transcription = []
    for transcription in transcription_segments:
        best_speaker = _find_closest_speaker(transcription, speaker_embeddings, diarize_segments)
        diarized_transcription.append({
            "start": transcription["start"],
            "end": transcription["end"],
            "text": transcription["text"],
            "speaker": best_speaker
        })
    return diarized_transcription

def _find_closest_speaker(transcription, speaker_embeddings, diarize_segments):
    best_match = None
    min_distance = float('inf')
    
    for speaker_turn, embedding in speaker_embeddings:
        if overlap(transcription["start"], transcription["end"], speaker_turn.start, speaker_turn.end):
            distance = torch.nn.functional.cosine_similarity(
                transcription["embedding"].unsqueeze(0), embedding.unsqueeze(0)
            ).item()
            if distance < min_distance:
                min_distance = distance
                best_match = f"SPEAKER_{speaker_turn.start:.2f}"
            
    # If no match found, use whisterx diarization result
    if best_match is None:
        for segment in diarize_segments:
            if overlap(transcription["start"], transcription["end"], segment["start"], segment["end"]):
                best_match = f"SPEAKER_{segment["speaker"]}"
                break
    
    return best_match if best_match else "UNKNOWN"

def _post_process_diarization(diarized_transcription):
    formatted_transcript = []
    current_speaker = None
    current_text = []
    start_time = None
    speaker_change_threshold = 0.8
    
    for segment in diarized_transcription:
        start = f"{segment['start']:.2f}"
        end = f"{segment['end']:.2f}"
        speaker = segment.get('speaker', 'UNKNOWN')
        
        if speaker == 'UNKNOWN':
            speaker = current_speaker if current_speaker else 'SPEAKER_XX'

        text = segment['text']

        if speaker != current_speaker or (float(start) - float(prev_end) > speaker_change_threshold if 'prev_end' in locals() else False):
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

def overlap(start1, end1, start2, end2):
    return max(start1, start2) < min(end1, end2)