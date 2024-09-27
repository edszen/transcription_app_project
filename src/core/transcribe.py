import logging
from faster_whisper import WhisperModel
from PyQt5.QtCore import QObject, pyqtSignal
import torch
from utils.encryption import EncryptionUtils
from core.diarization import apply_diarization
from utils.audio_processing import load_audio, chunk_audio
from core.vad import apply_energy_vad, apply_pyannote_vad
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
        self.encryption = EncryptionUtils()
        self.whisper_model = self._initialize_whisper_model()

    def _initialize_whisper_model(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        self.logger.info(f"Initializing Whisper model with device: {device} and compute type: {compute_type}")
        return WhisperModel("small", device=device, compute_type=compute_type)
        
    def transcribe(self, file_path, use_diarization=False, encrypted_api_key=None, vad_method="pyannote"):
        try:
            self.cancel_flag = False
            self.logger.info(f"Starting transcription for file: {file_path}")
            self.status_updated.emit("Loading audio file...")
            
            audio = load_audio(file_path)
            self.logger.info(f"Audio file loaded, duration: {len(audio)/1000:.2f} seconds")
            
            # Apply VAD
            self.status_updated.emit("Applying Voice Activity Detection...")
            if vad_method == 'pyannote':
                try:
                    api_key = self.encryption.decrypt(encrypted_api_key) if encrypted_api_key else ""
                    speech_segments = apply_pyannote_vad(file_path, api_key)
                except Exception as e:
                    self.logger.error(f"Pyannote VAD failed: {str(e)}. Falling back to energy-based VAD.")
                    self.status_updated.emit("Pyannote VAD failed. Falling back to energy-based VAD.")
                    speech_segments = apply_energy_vad(audio)
            elif vad_method == 'energy':
                speech_segments = apply_energy_vad(audio)
            else:
                speech_segments = [audio]  # No VAD, use full audio
            
            self.logger.info(f"VAD applied, found {len(speech_segments)} speech segments")
            self.progress.emit(20)

            # Chunk the audio if it's longer than 5 minutes
            chunk_length_ms = 5 * 60 * 1000  # 5 minutes
            transcripts = []
            
            for i, segment in enumerate(speech_segments):
                if self.cancel_flag:
                    break
                
                if len(segment) > chunk_length_ms:
                    chunks = chunk_audio(segment, chunk_length_ms)
                else:
                    chunks = [segment]
                
                for j, chunk in enumerate(chunks):
                    if self.cancel_flag:
                        break
                    self.status_updated.emit(f"Processing segment {i+1}/{len(speech_segments)}, chunk {j+1}/{len(chunks)}")
                    chunk_transcript = self.process_chunk(chunk, i*len(chunks)+j, len(speech_segments)*len(chunks), use_diarization, encrypted_api_key)
                    transcripts.append(chunk_transcript)

            full_transcript = " ".join(transcripts)

            if use_diarization:
                self.status_updated.emit("Applying diarization...")
                try:
                    api_key = self.encryption.decrypt(encrypted_api_key) if encrypted_api_key else ""
                    full_transcript = apply_diarization(file_path, full_transcript, api_key)
                except Exception as e:
                    self.logger.error(f"Diarization failed: {str(e)}")
                    full_transcript = f"[Diarization failed: {str(e)}]\n\n" + full_transcript

            if not self.cancel_flag:
                self.progress.emit(100)
                self.status_updated.emit("Transcription completed!")
                self.finished.emit(full_transcript)

        except Exception as e:
            self.logger.error(f"Error during transcription: {str(e)}", exc_info=True)
            self.error.emit(f"Error during transcription: {str(e)}")

    def process_chunk(self, chunk, chunk_index, total_chunks, use_diarization, encrypted_api_key):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            chunk_path = temp_file.name
            try:
                chunk.export(chunk_path, format="wav")
                
                if os.path.getsize(chunk_path) == 0:
                    raise ValueError("Exported audio file is empty")
                
                segments, _ = self.whisper_model.transcribe(chunk_path)
                transcript = " ".join([seg.text for seg in segments])

                self.chunk_progress.emit(chunk_index + 1, total_chunks, 100)
                return transcript
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