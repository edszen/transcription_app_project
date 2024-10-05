import logging
import os
from faster_whisper import WhisperModel
from PyQt5.QtCore import QObject, pyqtSignal
import torch
import numpy as np
from src.utils.encryption import EncryptionUtils
from src.core.diarization import apply_diarization
from src.utils.audio_processing import load_audio, preprocess_audio
from src.core.vad import apply_energy_vad, apply_pyannote_vad
from src.core.speaker_embedding import extract_speaker_embeddings
from src.core.alignment import align_transcription_with_diarization
from src import config

# Create necessary directories
config.create_directories()

log_file = os.path.join(config.LOG_DIR, 'transcription.log')
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler()  # This will also print logs to console
    ]
)
logger = logging.getLogger(__name__)

# Log the configuration
logger.info(f"Logging initialized. Log file: {log_file}")
logger.info(f"Log level: {config.LOG_LEVEL}")

class Transcriber(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    chunk_progress = pyqtSignal(int, int, int)

    def __init__(self):
        super().__init__()
        self.cancel_flag = False
        self.encryption = EncryptionUtils()
        self.whisper_model = self._initialize_whisper_model()

    def _initialize_whisper_model(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        logger.info(f"Initializing Whisper model with device: {device} and compute type: {compute_type}")
        return WhisperModel(config.WHISPER_MODEL, device=device, compute_type=compute_type)

    def transcribe(self, file_path, use_diarization=False, encrypted_api_key=None, vad_method="pyannote"):
        try:
            self.cancel_flag = False
            logger.info(f"Starting transcription for file: {file_path}")
            logger.info(f"Use diarization: {use_diarization}")
            logger.info(f"VAD method: {vad_method}")
            
            # Audio Preprocessing
            self.status_updated.emit("Preprocessing audio file...")
            audio = preprocess_audio(file_path)
            logger.info(f"Audio file preprocessed, duration: {len(audio)/config.SAMPLE_RATE:.2f} seconds")
            self.progress.emit(10)
            
            # Voice Activity Detection
            self.status_updated.emit("Applying voice activity detection...")
            vad_segments = self._apply_vad(file_path, audio, encrypted_api_key, vad_method)
            if not vad_segments:
                logger.error("No speech segments detected in the audio file")
                raise ValueError("No speech segments detected in the audio file")
            
            logger.info(f"VAD applied, found {len(vad_segments)} speech segments")
            self.progress.emit(25)
            
            # Speaker Embedding Extraction
            if use_diarization:
                self.status_updated.emit("Extracting speaker embedding...")
                embedding = extract_speaker_embeddings(vad_segments)
                logger.info("Speaker embedding extracted")
                self.progress.emit(40)
            
            # Speaker Clustering (Diarization)
            if use_diarization:
                self.status_updated.emit("Performing speaker diarization...")
                diarization_result = apply_diarization(vad_segments, embedding)
                logger.info("Speaker diarization completed")
                self.progress.emit(60)
            
            # Transcription
            self.status_updated.emit("Transcribing audio...")
            transcript = self._transcribe_audio(audio)
            logger.info("Transcription completed")
            self.progress.emit(80)
            
            # Alignment and speaker label assignment
            if use_diarization:
                self.status_updated.emit("Aligning transcription with speaker labels...")
                final_transcript = align_transcription_with_diarization(transcript, diarization_result)
                logger.info("Alignment completed")
            else:
                final_transcript = transcript
            self.progress.emit(100)
            
            self.status_updated.emit("Transcription completed")
            self.finished.emit(self._format_transcript(final_transcript))
        
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}", exc_info=True)
            self.error.emit(f"Error during transcription: {str(e)}")
            print(f"Terminal log: Error during transcription: {str(e)}")

    def _apply_vad(self, file_path, audio, encrypted_api_key, vad_method):
        try:
            if vad_method == "pyannote":
                logger.info("Applying Pyannote VAD")
                return apply_pyannote_vad(file_path, encrypted_api_key)
            elif vad_method == "energy":
                logger.info("Applying energy-based VAD")
                return apply_energy_vad(audio)
            else:
                logger.warning(f"Unknown VAD method: {vad_method}. Falling back to energy-based VAD.")
                return apply_energy_vad(audio)
        except ValueError as ve:
            logger.error(f"VAD failed due to configuration error: {str(ve)}. Falling back to energy-based VAD.")
            self.status_updated.emit("VAD failed due to configuration error. Falling back to energy-based VAD.")
            return apply_energy_vad(audio)
        except Exception as e:
            logger.error(f"VAD failed: {str(e)}. Falling back to energy-based VAD.")
            self.status_updated.emit("VAD failed. Falling back to energy-based VAD.")
            return apply_energy_vad(audio)
        
    def _transcribe_audio(self, audio):
        segments, info = self.whisper_model.transcribe(audio, beam_size=5)
        return [{"start": segment.start, "end": segment.end, "text": segment.text} for segment in segments]

    def _format_transcript(self, transcript):
        formatted = ""
        speaker_count = {}
        for segment in transcript:
            start = f"{int(segment['start'] // 60):02d}:{int(segment['start'] % 60):02d}"
            end = f"{int(segment['end'] // 60):02d}:{int(segment['end'] % 60):02d}"
            
            if 'speaker' in segment:
                speaker = segment['speaker']
                if speaker not in speaker_count:
                    speaker_count[speaker] = len(speaker_count) + 1
                speaker_label = f"Speaker {speaker_count[speaker]}"
            else:
                speaker_label = "Speaker Unknown"
            
            logger.debug(f"Formatting segment: {start}-{end}, Original speaker: {segment.get('speaker', 'Unknown')}, Assigned label: {speaker_label}")
            
            formatted += f"{start} - {end} | {speaker_label}: {segment['text']}\n"
        
        logger.info(f"Transcript formatted with {len(speaker_count)} unique speakers")
        logger.debug(f"Speaker count: {speaker_count}")
        return formatted

    def cancel_transcription(self):
        self.cancel_flag = True
        logger.info("Transcription cancelled")

if __name__ == "__main__":
    # This section can be used for testing the Transcriber class directly
    pass