import logging
from pyannote.audio import Pipeline
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import torch
import torchaudio
import config

logger = logging.getLogger(__name__)

def apply_pyannote_vad(file_path, api_key):
    try:
        logger.info("Initializing Pyannote VAD pipeline")
        vad_pipeline = Pipeline.from_pretrained(config.VAD_MODEL, use_auth_token=api_key)
        
        logger.info("Running Pyannote VAD")
        vad_results = vad_pipeline(file_path)
        
        audio = AudioSegment.from_file(file_path)
        speech_segments = []
        for speech_turn, _, _ in vad_results.itertracks(yield_label=True):
            start_ms = int(speech_turn.start * 1000)
            end_ms = int(speech_turn.end * 1000)
            segment = audio[start_ms:end_ms]
            speech_segments.append(segment)
            
        logger.info(f"Pyannote VAD completed, found {len(speech_segments)} speech segments")
        return speech_segments
    except Exception as e:
        logger.error(f"Error during Pyannote VAD: {str(e)}")
        raise

def apply_energy_vad(audio, min_silence_len=300, silence_thresh=-40):
    try:
        logger.info("Applying energy-based VAD")
        if isinstance(audio, AudioSegment):
            audio = audio.set_channels(1)
        else:
            # Convert numpy array to AudioSegment
            audio = AudioSegment(
                audio.tobytes(),
                frame_rate=config.SAMPLE_RATE,
                sample_width=audio.dtype.itemsize,
                channels=1
            )
        
        nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
        speech_segments = [audio[start:end] for start, end in nonsilent_ranges]
        
        logger.info(f"Energy-based VAD completed, found {len(speech_segments)} speech segments")
        return speech_segments
    except Exception as e:
        logger.error(f"Error during energy-based VAD: {str(e)}")
        logger.info("VAD failed. Returning full audio.")
        return [audio]