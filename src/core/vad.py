import logging
from pyannote.audio import Pipeline
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import torch
import torchaudio
from src.utils.encryption import EncryptionUtils
from src import config
import numpy as np
import librosa

logger = logging.getLogger(__name__)

def apply_pyannote_vad(file_path, encrypted_api_key):
    try:
        logger.info("Initializing Pyannote VAD pipeline")
        encryption_utils = EncryptionUtils()
        api_key = encryption_utils.decrypt(encrypted_api_key)
        vad_pipeline = Pipeline.from_pretrained(config.VAD_MODEL, use_auth_token=api_key)
        
        logger.info("Running Pyannote VAD")
        vad_results = vad_pipeline(file_path)
        
        audio, sr = librosa.load(file_path, sr=config.SAMPLE_RATE)
        speech_segments = []
        for speech_turn, _, _ in vad_results.itertracks(yield_label=True):
            start_sample = int(speech_turn.start * sr)
            end_sample = int(speech_turn.end * sr)
            segment = audio[start_sample:end_sample]
            speech_segments.append(segment)
        
        if not speech_segments:
            logger.warning("No speech segments detected by Pyannote VAD")
        else:
            logger.info(f"Pyannote VAD completed, found {len(speech_segments)} speech segments")
        
        return speech_segments
    except Exception as e:
        logger.error(f"Error during Pyannote VAD: {str(e)}", exc_info=True)
        logger.info("Falling back to energy-based VAD")
        return apply_energy_vad(audio)

def apply_energy_vad(audio, min_silence_len=300, silence_thresh=-40):
    try:
        logger.info("Applying energy-based VAD")
        if isinstance(audio, np.ndarray):
            audio_array = audio
        else:
            raise ValueError("Unsupported audio type")
        
        # Convert to mono if stereo
        if audio_array.ndim == 2:
            audio_array = audio_array.mean(axis=1)
        
        # Create AudioSegment from numpy array (for using detect_nonsilent)
        audio_segment = AudioSegment(
            audio_array.tobytes(),
            frame_rate=config.SAMPLE_RATE,
            sample_width=audio_array.dtype.itemsize,
            channels=1
        )
        
        nonsilent_ranges = detect_nonsilent(audio_segment, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
        speech_segments = [audio_array[start:end] for start, end in nonsilent_ranges]
        
        if not speech_segments:
            logger.warning("No speech segments detected by energy-based VAD")
        else:
            logger.info(f"Energy-based VAD completed, found {len(speech_segments)} speech segments")
        
        return speech_segments
    except Exception as e:
        logger.error(f"Error during energy-based VAD: {str(e)}", exc_info=True)
        logger.info("VAD failed. Returning empty list.")
        return []  # Return an empty list when energy-based VAD fails