import logging
from faster_whisper import WhisperModel
from PyQt5.QtCore import QObject, pyqtSignal
import torch
from utils.encryption import EncryptionUtils
from core.diarization import apply_diarization
from utils.audio_processing import load_audio
from core.vad import apply_energy_vad, apply_pyannote_vad, embed_speakers
import whisperx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        return WhisperModel("small", device=device, compute_type=compute_type)

    def transcribe(self, file_path, use_diarization=False, encrypted_api_key=None, vad_method="pyannote", use_embedding=True):
        try:
            self.cancel_flag = False
            logger.info(f"Starting transcription for file: {file_path}")
            self.status_updated.emit("Loading audio file...")
            
            audio = whisperx.load_audio(file_path)
            logger.info(f"Audio file loaded, duration: {len(audio)/16000:.2f} seconds")
            
            embeddings = None
            if use_embedding and use_diarization:
                self.status_updated.emit("Computing speaker embeddings...")
                embeddings = embed_speakers(file_path, encrypted_api_key)
                if embeddings is None:
                    logger.warning("Speaker embedding failed. Proceeding without embeddings.")
            
            self.status_updated.emit("Applying Voice Activity Detection...")
            vad_segments = self._apply_vad(file_path, audio, vad_method, encrypted_api_key)
            logger.info(f"VAD applied, found {len(vad_segments)} speech segments")
            self.progress.emit(20)

            self.status_updated.emit("Transcribing audio...")
            segments, info = self.whisper_model.transcribe(audio, beam_size=5)
            
            whisperx_segments = [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                } for segment in segments
            ]
            result = {"segments": whisperx_segments, "language": info.language}
            self.progress.emit(60)

            if use_diarization:
                self.status_updated.emit("Applying diarization...")
                try:
                    full_transcript = apply_diarization(file_path, result, encrypted_api_key, embeddings)
                except Exception as e:
                    logger.error(f"Diarization failed: {str(e)}")
                    full_transcript = f"[Diarization failed: {str(e)}]\n\n" + "\n".join([seg["text"] for seg in result["segments"]])
            else:
                full_transcript = "\n".join([seg["text"] for seg in result["segments"]])

            if not self.cancel_flag:
                self.progress.emit(100)
                self.status_updated.emit("Transcription completed!")
                self.finished.emit(full_transcript)

        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}", exc_info=True)
            self.error.emit(f"Error during transcription: {str(e)}")

    def _apply_vad(self, file_path, audio, vad_method, encrypted_api_key):
        if vad_method == 'pyannote':
            try:
                return apply_pyannote_vad(file_path, encrypted_api_key)
            except Exception as e:
                logger.error(f"Pyannote VAD failed: {str(e)}. Falling back to energy-based VAD.")
                self.status_updated.emit("Pyannote VAD failed. Falling back to energy-based VAD.")
                return apply_energy_vad(audio)
        elif vad_method == 'energy':
            return apply_energy_vad(audio)
        else:
            return [audio]  # No VAD, use full audio

    def cancel_transcription(self):
        self.cancel_flag = True
        logger.info("Transcription cancelled")

if __name__ == "__main__":
    # This section can be used for testing the Transcriber class directly
    pass