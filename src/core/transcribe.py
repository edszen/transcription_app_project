import logging
from faster_whisper import WhisperModel
from PyQt5.QtCore import QObject, pyqtSignal
import torch
from src.utils.encryption import EncryptionUtils
from src.core.diarization import apply_diarization
from src.utils.audio_processing import load_audio, chunk_audio
import tempfile
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Transcriber(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    chunk_progress = pyqtSignal(int, int, int) # current_chunk, total_chunks, chunk_progress

    def __init__(self):
        super().__init__()
        self.cancel_flag = False
        self.logger = logging.getLogger(__name__)
        self.model = self._initialize_model()
        self.encryption = EncryptionUtils()

    def _initialize_model(self):
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        compute_type = "float16" if device in ["cuda", "mps"] else "int8"
        self.logger.info(f"Initializing Whisper model with device: {device} and compute type: {compute_type}")
        return WhisperModel("small", device=device, compute_type=compute_type)
        
    def transcribe(self, file_path, use_diarization=False, encrypted_api_key=None):
        try:
            self.cancel_flag = False
            self.logger.info(f"Starting transcription for file: {file_path}")
            self.status_updated.emit("Loading audio file...")
            
            audio = load_audio(file_path)
            self.logger.info(f"Audio file loaded, duration: {len(audio)/1000:.2f} seconds")
            
            chunk_length_ms = 5 * 60 * 1000  # 5 minutes
            if len(audio) > chunk_length_ms:
                chunks = chunk_audio(audio, chunk_length_ms)
            else:
                chunks = [audio]
            
            transcripts = []
            for i, chunk in enumerate(chunks):
                if self.cancel_flag:
                    break
                self.status_updated.emit(f"Processing chunk {i+1} of {len(chunks)}")
                chunk_transcript = self.process_chunk(chunk, i, len(chunks), use_diarization, encrypted_api_key)
                transcripts.append(chunk_transcript)
            
            if not self.cancel_flag:
                full_transcript = "\n".join(transcripts)
                self.progress.emit(100)
                self.status_updated.emit("Transcription completed!")
                self.finished.emit(full_transcript)
                return full_transcript

        except Exception as e:
            error_message = f"Error during transcription: {str(e)}"
            self.logger.error(error_message, exc_info=True)
            self.error.emit(error_message)
            raise
    
    def process_chunk(self, chunk, chunk_index, total_chunks, use_diarization, encrypted_api_key):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            chunk_path = temp_file.name
            try:
                chunk.export(chunk_path, format="wav")
                
                # Verify the exported audio file
                if os.path.getsize(chunk_path) == 0:
                    raise ValueError("Exported audio file is empty")
                
                # Transcribe with Whisper
                segments, _ = self.model.transcribe(chunk_path)
                transcript = [{"start": segment.start, "end": segment.end, "text": segment.text} for segment in segments]
                
                if use_diarization:
                    try:
                        api_key = self.encryption.decrypt(encrypted_api_key) if encrypted_api_key else ""
                        transcript = apply_diarization(chunk_path, transcript, api_key)
                    except ValueError as ve:
                        self.logger.error(f"Diarization failed for chunk {chunk_index}: {str(ve)}")
                        # Continue with undiarized transcript
                        transcript = [{"start": 0, "end": 0, "text": f"[Diarization failed: {str(ve)}] " + " ".join(seg['text'] for seg in transcript)}]
                    except Exception as e:
                        self.logger.error(f"Unexpected error in diarization for chunk {chunk_index}: {str(e)}")
                        transcript = [{"start": 0, "end": 0, "text": f"[Diarization error] " + " ".join(seg['text'] for seg in transcript)}]

                formatted_transcript = self.format_transcript(transcript)
                self.chunk_progress.emit(chunk_index + 1, total_chunks, 100)
                return formatted_transcript
            except Exception as e:
                self.logger.error(f"Error processing chunk {chunk_index}: {str(e)}", exc_info=True)
                return f"[Processing failed for chunk {chunk_index}]"
            finally:
                os.unlink(chunk_path)
            
            
    def format_transcript(self, transcript):
        formatted_lines = []
        for segment in transcript:
            start = f"{segment['start']:.2f}"
            end = f"{segment['end']:.2f}"
            speaker = segment.get('speaker', 'Unknown')
            text = segment['text']
            formatted_lines.append(f"{start} - {end} | Speaker {speaker}: {text}")
        return "\n".join(formatted_lines)

    def cancel_transcription(self):
        self.cancel_flag = True
        self.logger.info("Transcription cancelled")

if __name__ == "__main__":
    # This section can be used for testing the Transcriber class directly
    pass