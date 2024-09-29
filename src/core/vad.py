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


logger = logging.getLogger(__name__)

def apply_pyannote_vad(file_path, encrypted_api_key):
    try:
        encryption_utils = EncryptionUtils()
        decrypted_api_key = encryption_utils.decrypt(encrypted_api_key)
        
        # Initialize Pyannote VAD
        vad_pipeline = Pipeline.from_pretrained("pyannote/voice-activity-detection", use_auth_token=decrypted_api_key)
        vad_results = vad_pipeline(file_path)
        
        # Load audio file
        audio = AudioSegment.from_file(file_path)
        
        # Load speaker embedding model
        embedding_model = Model.from_pretrained("pyannote/embedding", use_auth_token=decrypted_api_key)
        inference = Inference(embedding_model, window="whole")

        speaker_embeddings = []
        speech_segments = []
        
        # Extract speech segments
        for speech_turn, _, _ in vad_results.itertracks(yield_label=True):
            start_ms = int(speech_turn.start * 1000)
            end_ms = int(speech_turn.end * 1000)
            segment = audio[start_ms:end_ms]
            speech_segments.append(segment)
        
        # Extract speaker embeddings
            waveform = torch.tensor(segment.get_array_of_samples()).float()
            waveform = waveform.unsqueeze(0) # add batch dimension
            embedding = embedding_model({"waveform": waveform, "sample_rate": segment.frame_rate})
            speaker_embeddings.append((speech_turn, embedding))
            
        # Return both speech segments and speaker embeddings for diarization refinement
        return speech_segments, speaker_embeddings
    
    except Exception as e:
        logger.error(f"Error during Pyannote VAD: {str(e)}")
        logger.info("Falling back to energy-based VAD")
        return apply_energy_vad(AudioSegment.from_file(file_path))
    
def apply_energy_vad(audio, min_silence_len=300, silence_thresh=-40):
    try:
        # Make sure file is in Mono 
        audio = audio.set_channels(1)
        nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
        speech_segments = [audio[start:end] for start, end in nonsilent_ranges]
        return speech_segments, [] # Return empty list for speaker embeddings
    except Exception as e:
        logger.error(f"Error during energy-based VAD: {str(e)}")
        logger.info("VAD failed. Returning full audio.")
        return [audio], [] # Return full audio and empty list for speaker embeddings
        
        