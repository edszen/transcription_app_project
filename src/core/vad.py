import logging
from pyannote.audio import Pipeline, Model
from pyannote.audio import Inference
from pyannote.core import Segment
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import torch
from utils.encryption import EncryptionUtils
from scipy.spatial.distance import cdist
import numpy as np
import os

logger = logging.getLogger(__name__)

def embed_speakers(file_path, api_key):
    try:
        encryption_utils = EncryptionUtils()
        api_key = encryption_utils.decrypt(api_key)
        
        logger.info("API key decrypted successfully")
        
        embedding_model = Pipeline.from_pretrained("pyannote/embedding", use_auth_token=api_key)
        embeddings = embedding_model(file_path)
        
        logger.info("Embedding model loaded successfully")
        
        # Use GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        model = model.to(device)
        
        logger.info(f"Using device: {device} for embedding")
        
        # Create inference object
        inference = Inference(model, window="sliding", duration=5.0, step=0.5)
        
        logger.info("Inference object created successfully")
        
        # Compute embeddings
        embeddings = inference(file_path)
        
        logger.info(f"Speaker embeddings computed successfully. Shape: {embeddings.data.shape}")
        
        return embeddings
    except Exception as e:
        logger.error(f"Error during embedding: {str(e)}")
        return None

def apply_pyannote_vad(file_path, api_key, use_embedding=False):
    try:
        vad_pipeline = Pipeline.from_pretrained("pyannote/voice-activity-detection", use_auth_token=api_key)
        vad_results = vad_pipeline(file_path)
        
        audio = AudioSegment.from_file(file_path)
        speech_segments = []
        for speech_turn, _, _ in vad_results.itertracks(yield_label=True):
            start_ms = int(speech_turn.start * 1000)
            end_ms = int(speech_turn.end * 1000)
            segment = audio[start_ms:end_ms]
            speech_segments.append(segment)
        
        if use_embedding:
            embeddings = embed_speakers(file_path, api_key)
            return speech_segments, embeddings
        else:
            return speech_segments
    except Exception as e:
        logger.error(f"Error during Pyannote VAD: {str(e)}")
        logger.info("Falling back to energy-based VAD")
        return apply_energy_vad(AudioSegment.from_file(file_path)), None
    
def apply_energy_vad(audio, min_silence_len=300, silence_thresh=-40):
    try:
        if isinstance(audio, np.ndarray):
            # Convert numpy array to AudioSegment
            audio = AudioSegment(
                audio.tobytes(),
                frame_rate=16000,
                sample_width=audio.dtype.itemsize,
                channels=1
            )
        
        # Make sure file is in Mono 
        audio = audio.set_channels(1)
        nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
        speech_segments = [audio[start:end] for start, end in nonsilent_ranges]
        return speech_segments
    except Exception as e:
        logger.error(f"Error during energy-based VAD: {str(e)}")
        logger.info("VAD failed. Returning full audio.")
        return [audio]