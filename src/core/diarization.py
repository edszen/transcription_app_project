import logging
#from whisperx import DiarizationPipeline, load_audio
import torch
import numpy as np
import whisperx


logger = logging.getLogger(__name__)

def apply_diarization(audio_path, transcript, api_key):
    try:
        device = _get_device()
        logger.info(f"Initializing WhisperX diarization with device: {device}")
        
        # Load audio
        audio = whisperx.load_audio(audio_path)
        
        # Perform speaker diarization
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=api_key, device=device)
        diarize_segments = diarize_model(audio)
        logger.info("Diarization completed")
        
        # Prepare transcript segments
        transcript_segments = _prepare_transcript_segments(transcript)
        
        # Assign speaker labels
        result = whisperx.assign_word_speakers(diarize_segments, transcript_segments)
        logger.info("Speaker labels assigned to words")
        
        return _post_process_diarization(result)
    except Exception as e:
        logger.error(f"Diarization error: {str(e)}", exc_info=True)
        return f"[Diarization failed: {str(e)}]\n\n{transcript}"

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
    for word in words:
        end_time = start_time + 0.4  # Assume each word takes about 0.4 seconds
        segments.append({"start": start_time, "end": end_time, "text": word})
        start_time = end_time
    return {"segments": segments}

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