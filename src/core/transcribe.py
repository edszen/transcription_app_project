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
import whisperx

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

    def transcribe(self, file_path, use_diarization=True, encrypted_api_key=None, vad_method="pyannote"):
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
            
            # Decrypt the API key
            encryption_utils = EncryptionUtils()
            api_key = encryption_utils.decrypt(encrypted_api_key)
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if torch.cuda.is_available() else "int8"
            logger.info(f"Using device: {device} with compute type: {compute_type}")
            
            # Voice Activity Detection
            self.status_updated.emit("Applying voice activity detection...")
            vad_segments = self._apply_vad(file_path, audio, encrypted_api_key, vad_method)
            if not vad_segments:
                logger.error("No speech segments detected in the audio file")
                raise ValueError("No speech segments detected in the audio file")
            
            logger.info(f"VAD applied, found {len(vad_segments)} speech segments")
            self.progress.emit(25)
            
            # Load WhisperX model
            self.status_updated.emit("Loading WhisperX model...")
            model = whisperx.load_model("large-v2", device, compute_type=compute_type, language="en")
            
            # Transcribe
            self.status_updated.emit("Transcribing audio...")
            result = model.transcribe(audio, batch_size=16)
            self.progress.emit(50)
            
            # Align whisper output
            self.status_updated.emit("Aligning transcription...")
            model_a, metadata = whisperx.load_align_model(language_code="en", device=device)
            result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
            self.progress.emit(70)
            
            if use_diarization:
                self.status_updated.emit("Performing speaker diarization...")
                diarization_result = apply_diarization(file_path, encrypted_api_key)
                self.progress.emit(90)

                # Align diarization with transcription
                aligned_result = self._align_diarization_with_transcription(result["segments"], diarization_result)
            else:
                aligned_result = result["segments"]

            self.status_updated.emit("Formatting transcript...")
            formatted_transcript = self._format_transcript(aligned_result)
            
            self.status_updated.emit("Transcription completed")
            self.finished.emit(formatted_transcript)
        
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

    def _align_diarization_with_transcription(self, transcription, diarization):
        aligned_result = []
        for segment in transcription:
            matching_diar = next((d for d in diarization if d['start'] <= segment['end'] and d['end'] >= segment['start']), None)
            if matching_diar:
                segment['speaker'] = matching_diar['speaker']
            else:
                segment['speaker'] = 'UNKNOWN'
            aligned_result.append(segment)
        return aligned_result

    # Update the _format_transcript method
    def _format_transcript(self, segments):
        formatted = ""
        speaker_count = {}
        for segment in segments:
            start = f"{int(segment['start'] // 60):02d}:{int(segment['start'] % 60):02d}"
            end = f"{int(segment['end'] // 60):02d}:{int(segment['end'] % 60):02d}"
            
            speaker = segment.get('speaker', 'UNKNOWN')
            if speaker not in speaker_count:
                speaker_count[speaker] = len(speaker_count) + 1
            speaker_label = f"Speaker {speaker_count[speaker]}"
            
            formatted += f"{start} - {end} | {speaker_label}: {segment['text']}\n"
        
        logger.info(f"Transcript formatted with {len(speaker_count)} unique speakers")
        return formatted

    def cancel_transcription(self):
        self.cancel_flag = True
        logger.info("Transcription cancelled")

if __name__ == "__main__":
    # This section can be used for testing the Transcriber class directly
    pass