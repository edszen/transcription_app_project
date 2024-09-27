import logging
import whisperx
import torch
from pydub import AudioSegment

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
        audio = AudioSegment.from_file(audio_path)
        transcript_segments = _prepare_transcript_segments(transcript, len(audio) / 1000)
        
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

def _prepare_transcript_segments(transcript, audio_duration):
    return {"segments": [{"start": 0, "end": audio_duration, "text": transcript}]}

def _post_process_diarization(result):
    formatted_transcript = []
    speaker_map = {}
    current_speaker = None
    current_text = []
    
    for segment in result["segments"]:
        start = f"{segment['start']:.2f}"
        end = f"{segment['end']:.2f}"
        speaker = segment.get('speaker')
        
        if speaker not in speaker_map:
            speaker_map[speaker] = f"SPEAKER_{len(speaker_map) + 1}"
        
        speaker_id = speaker_map[speaker]
        
        if speaker_id != current_speaker:
            if current_speaker:
                formatted_transcript.append(f"{start_time} - {prev_end} | {current_speaker}: {' '.join(current_text)}")
            current_speaker = speaker_id
            current_text = [segment['text']]
            start_time = start
        else:
            current_text.append(segment['text'])
        
        prev_end = end
    
    if current_speaker:
        formatted_transcript.append(f"{start_time} - {prev_end} | {current_speaker}: {' '.join(current_text)}")
    
    return "\n".join(formatted_transcript)