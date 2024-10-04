import librosa
import numpy as np
import logging
from pydub import AudioSegment
from src import config

logger = logging.getLogger(__name__)

def load_audio(file_path):
    try:
        audio, sr = librosa.load(file_path, sr=config.SAMPLE_RATE)
        return audio
    except Exception as e:
        logger.error(f"Failed to load audio file: {str(e)}")
        raise ValueError(f"Failed to load audio file: {str(e)}")

def preprocess_audio(file_path):
    try:
        audio = load_audio(file_path)
        
        # Noise reduction (optional, depending on use case)
        # audio = librosa.effects.remove_noise(audio)
        
        # Normalize audio
        audio = librosa.util.normalize(audio)
        
        logger.info(f"Audio loaded and preprocessed successfully: {file_path}")
        return audio
    except Exception as e:
        logger.error(f"Error preprocessing audio: {str(e)}")
        raise
    
def chunk_audio(audio, chunk_length_ms):
    return [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
