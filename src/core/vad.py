import logging
from pyannote.audio import Pipeline, Model
from pyannote.audio import Inference
from pyannote.core import Segment
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import torch
import torchaudio
from speechbrain.inference.speaker import EncoderClassifier
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
        
        logger.info("Loading SpeechBrain ECAPA-TDNN model for speaker embedding")
        classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
        
        logger.info("Embedding model loaded successfully")
        
        waveform, sample_rate = torchaudio.load(file_path)
        
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
        
        # Process the audio in chunks of 10 seconds
        chunk_size = 10 * 16000  # 10 seconds at 16kHz
        embeddings = []
        
        for i in range(0, waveform.shape[1], chunk_size):
            chunk = waveform[:, i:i+chunk_size]
            if chunk.shape[1] < chunk_size:
                # Pad the last chunk if it's shorter than 10 seconds
                chunk = torch.nn.functional.pad(chunk, (0, chunk_size - chunk.shape[1]))
            
            chunk_embedding = classifier.encode_batch(chunk)
            embeddings.append(chunk_embedding)
        
        embeddings = torch.cat(embeddings, dim=2)
        
        # Replace NaN values with 0
        embeddings = torch.nan_to_num(embeddings, nan=0.0)
        
        logger.info(f"Speaker embeddings computed successfully. Shape: {embeddings.shape}")
        
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