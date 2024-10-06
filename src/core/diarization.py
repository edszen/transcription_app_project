import logging
import torch
import numpy as np
from pyannote.audio import Pipeline
from src import config
from src.utils.encryption import EncryptionUtils
import torchaudio

logger = logging.getLogger(__name__)

def apply_diarization(audio_path, encrypted_api_key):
    try:
        logger.info("Starting speaker diarization with Pyannote")
        
        # Decrypt the API key
        encryption_utils = EncryptionUtils()
        api_key = encryption_utils.decrypt(encrypted_api_key)
        
        # Determine the device
        device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Load Pyannote pipeline
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=api_key)
        pipeline = pipeline.to(torch.device(device))
        
        # Load audio
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Ensure audio is mono and at 16kHz
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if sample_rate != config.SAMPLE_RATE:
            waveform = torchaudio.functional.resample(waveform, sample_rate, config.SAMPLE_RATE)
        
        # Run diarization
        diarization = pipeline({"waveform": waveform, "sample_rate": config.SAMPLE_RATE})
        
        # Process diarization results
        diarization_result = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            diarization_result.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })
        
        logger.info(f"Diarization completed. Found {len(set(segment['speaker'] for segment in diarization_result))} speakers.")
        return diarization_result
    
    except Exception as e:
        logger.error(f"Error during diarization: {str(e)}")
        raise

def count_speakers(segments):
    """
    Count the number of unique speakers in the segments.
    """
    unique_speakers = set(segment['speaker'] for segment in segments)
    speaker_count = len(unique_speakers)
    logger.info(f"Detected {speaker_count} unique speakers")
    return speaker_count

def find_matching_transcription(segment, transcription):
    for trans in transcription:
        if (trans['start'] <= segment['end'] and trans['end'] >= segment['start']):
            return trans['text']
    return ""