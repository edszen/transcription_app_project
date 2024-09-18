import whisper
from PyQt5.QtCore import QObject, pyqtSignal
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pyannote.audio import Pipeline
from pyannote.core import Segment
import torch
import time
import warnings
import os

import warnings
import re

os.environ["WHISPER_CACHE_DIR"] = os.path.join(os.path.expanduser("~"), ".cache", "whisper")

def get_whisper_model(model_name="large"):
    cache_dir = os.environ["WHISPER_CACHE_DIR"]
    model_path = os.path.join(cache_dir, f"{model_name}.en.pt")
    
    if not os.path.exists(model_path):
        print(f"Loading {model_name} model from cache")
        return whisper.load_model(model_name)
    
    else:
        print(f"Downloading {model_name} model")
        return whisper.load_model(model_name)
    
def filter_warnings(message, category, filename, lineno, file=None, line=None):
    if category == UserWarning:
        if re.match(r"The MPEG_LAYER_III subtype is unknown to TorchAudio", str(message)):
            return None
    return True

warnings.filterwarnings("always", category=UserWarning)
warnings.showwarning = filter_warnings

class TranscriptionError(Exception):
    pass

class Transcriber(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    diarization_progress = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.cancel_flag = False
        self.logger = logging.getLogger(__name__)

    def transcribe(self, file_path, use_diarization=False, api_key=None):
        try:
            self.cancel_flag = False
            self.logger.info(f"Starting transcription for file: {file_path}")
            
            # Step 1: Transcription
            transcript = self.perform_transcription(file_path)
            if self.cancel_flag:
                raise TranscriptionError("Transcription cancelled by user")
            self.logger.info("Transcription completed successfully")
            self.progress.emit(50)  # 50% progress after transcription
            
            # Step 2: Diarization (if enabled)
            if use_diarization and api_key:
                self.logger.info("Starting speech diarization")
                try:
                    diarization = self.perform_diarization(file_path, api_key)
                    if self.cancel_flag:
                        raise TranscriptionError("Transcription cancelled by user")
                    if diarization is not None:
                        formatted_transcript = self.format_transcript_with_diarization(transcript, diarization)
                        self.logger.info("Diarization and formatting completed successfully")
                    else:
                        raise Exception("Diarization returned None")
                except Exception as e:
                    self.logger.error(f"Diarization failed: {str(e)}", exc_info=True)
                    formatted_transcript = self.format_transcript(transcript)
                    self.logger.info("Falling back to non-diarized formatting")
            else:
                formatted_transcript = self.format_transcript(transcript)
            
            if not self.cancel_flag:
                self.progress.emit(100)
                self.finished.emit(formatted_transcript)
            
        except Exception as e:
            if not self.cancel_flag:
                error_message = f"Error during transcription: {str(e)}"
                self.logger.error(error_message, exc_info=True)
                self.error.emit(error_message)

    def perform_transcription(self, file_path):
        model = whisper.load_model("large")
        self.logger.info("Whisper model loaded successfully")

        result = model.transcribe(file_path, language="en")
        return result["segments"]

    def perform_diarization(self, file_path, api_key):
        try:
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1",
                                                use_auth_token=api_key)
            
            device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
            pipeline = pipeline.to(device)
            self.logger.info(f"Diarization pipeline initialized on device: {device}")

            start_time = time.time()
            diarization = pipeline(file_path, min_speakers=2, max_speakers=10)
            end_time = time.time()

            self.logger.info(f"Diarization completed in {end_time - start_time:.2f} seconds")
            self.logger.info(f"Diarization result type: {type(diarization)}")
            self.logger.info(f"Number of speakers detected: {len(set(diarization.labels()))}")
            
            # Print the first few results (for logging purposes)
            for turn, _, speaker in list(diarization.itertracks(yield_label=True))[:5]:
                self.logger.info(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
            
            return diarization
        except Exception as e:
            self.logger.error(f"Diarization error: {str(e)}", exc_info=True)
            return None

    def format_transcript(self, transcript):
        return "\n\n".join([f"{segment['start']:.2f} - {segment['end']:.2f}: {segment['text']}" for segment in transcript])

    def format_transcript_with_diarization(self, transcript, diarization):
        if diarization is None:
            return self.format_transcript(transcript)
        
        formatted_lines = []
        total_turns = len(list(diarization.itertracks(yield_label=True)))
        for i, (turn, _, speaker) in enumerate(diarization.itertracks(yield_label=True)):
            relevant_segments = [
                segment for segment in transcript
                if segment['start'] <= turn.end and segment['end'] >= turn.start
            ]
            if relevant_segments:
                # Merge overlapping segments
                text = ' '.join([segment['text'].strip() for segment in relevant_segments])
                # Remove duplicate phrases
                text = ' '.join(dict.fromkeys(text.split()))
                formatted_lines.append(f"{turn.start:.2f} - {turn.end:.2f} | Speaker {speaker}: {text}")
                
                # Emit progress (50% to 95%)
                progress = 50 + (i / total_turns) * 45
                self.diarization_progress.emit(progress)
        
        return '\n\n'.join(formatted_lines)

    def cancel_transcription(self):
        self.cancel_flag = True
        self.logger.info("Transcription cancelled")

def test_diarization(audio_file, api_key):
    print(f"Testing diarization on file: {audio_file}")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"MPS available: {torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else 'N/A'}")

    try:
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1",
                                            use_auth_token=api_key)
        
        device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
        pipeline = pipeline.to(device)
        print(f"Using device: {device}")

        start_time = time.time()
        diarization = pipeline(audio_file)
        end_time = time.time()

        print(f"Diarization completed in {end_time - start_time:.2f} seconds")
        
        # Print the first few results
        for turn, _, speaker in list(diarization.itertracks(yield_label=True))[:5]:
            print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
        
        print("Diarization successful!")
        return True
    except Exception as e:
        print(f"An error occurred during diarization: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    from PyQt5.QtCore import QSettings
    from encryption_utils import EncryptionUtils

    if len(sys.argv) < 2:
        print("Usage: python transcribe.py /path/to/audio/file.mp3")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    # Load and decrypt the API key
    settings = QSettings("YourCompany", "AudioTranscriptionApp")
    encryption_utils = EncryptionUtils()
    encrypted_key = settings.value("huggingface_api_key", "")
    if not encrypted_key:
        print("Error: No API key found in settings. Please set up your API key first.")
        sys.exit(1)
    
    api_key = encryption_utils.decrypt(encrypted_key)
    
    success = test_diarization(audio_file, api_key)
    if not success:
        print("Diarization test failed. Please check the error messages above.")