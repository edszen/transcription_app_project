import logging
import whisperx
import torch

logger = logging.getLogger(__name__)

def apply_diarization(audio_path, transcript, api_key):
    try:
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Initializing DiarizationPipeline with device: {device}")
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=api_key, device=device)
        
        logger.info(f"Running diarization on audio file: {audio_path}")
        diarize_segments = diarize_model(audio_path)
        
        logger.info("Assigning speakers to transcript")
        result = whisperx.assign_word_speakers(diarize_segments, {"segments": transcript})
        
        return result["segments"]
    except Exception as e:
        logger.error(f"Diarization error: {str(e)}", exc_info=True)
        raise ValueError(f"Diarization failed: {str(e)}")