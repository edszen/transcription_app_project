import logging
import threading
import numpy as np
from faster_whisper import WhisperModel
from pydub import AudioSegment
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtCore import QObject, pyqtSignal
import torch
from pyannote.audio import Pipeline

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Transcriber(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    status_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.cancel_flag = False
        self.logger = logging.getLogger(__name__)
        
        # Initialize Faster Whisper model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        self.whisper_model = WhisperModel("small", device=device, compute_type=compute_type)
        
        # Initialize pyannote VAD
        self.vad_pipeline = None  # We'll initialize this later with the API token

    def transcribe(self, file_path, use_diarization=False, api_key=None, vad_method='pyannote'):
        try:
            self.cancel_flag = False
            self.logger.info(f"Starting transcription for file: {file_path}")
            self.status_updated.emit("Loading audio file...")
            
            # Load audio file
            audio = self.load_audio(file_path)
            self.logger.info(f"Audio file loaded, duration: {len(audio)/1000:.2f} seconds")
            
            # Apply VAD
            self.status_updated.emit("Applying Voice Activity Detection...")
            if vad_method == 'pyannote':
                speech_segments = self.apply_pyannote_vad(file_path, api_key)
            elif vad_method == 'energy':
                speech_segments = self.apply_energy_vad(audio)
            else:
                speech_segments = [audio]  # No VAD, use full audio
            
            self.logger.info(f"VAD applied, found {len(speech_segments)} speech segments")
            self.progress.emit(20)
            
            # Transcribe speech segments
            transcripts = self.transcribe_segments(speech_segments)
            self.logger.info(f"Transcription completed, {len(transcripts)} segments processed")
            self.progress.emit(80)
            
            # Combine transcripts
            full_transcript = self.combine_transcripts(transcripts)
            self.logger.info(f"Combined transcript length: {len(full_transcript)}")
            
            # TODO: Implement diarization (will be done in next steps)
            if use_diarization:
                self.logger.info("Diarization requested, but not yet implemented")
                # This is where we'll add diarization in the next step

            if not self.cancel_flag:
                self.progress.emit(100)
                self.status_updated.emit("Transcription completed!")
                self.finished.emit(full_transcript)
            
        except Exception as e:
            if not self.cancel_flag:
                error_message = f"Error during transcription: {str(e)}"
                self.logger.error(error_message, exc_info=True)
                self.error.emit(error_message)

    def load_audio(self, file_path):
        try:
            audio = AudioSegment.from_file(file_path)
            return audio
        except Exception as e:
            self.logger.error(f"Failed to load audio file: {str(e)}")
            raise ValueError(f"Failed to load audio file: {str(e)}")
        
    def apply_pyannote_vad(self, file_path, api_key):
        try:
            if self.vad_pipeline is None:
                self.vad_pipeline = Pipeline.from_pretrained("pyannote/voice-activity-detection",
                                                            use_auth_token=api_key)
            
            vad_results = self.vad_pipeline(file_path)
            
            audio = AudioSegment.from_file(file_path)
            speech_segments = []
            for speech_turn, _, _ in vad_results.itertracks(yield_label=True):
                start_ms = int(speech_turn.start * 1000)
                end_ms = int(speech_turn.end * 1000)
                segment = audio[start_ms:end_ms]
                speech_segments.append(segment)
            
            return speech_segments
        except Exception as e:
            self.logger.error(f"Error in pyannote VAD: {str(e)}")
            self.status_updated.emit("Pyannote VAD failed. Falling back to energy-based VAD.")
            return self.apply_energy_vad(AudioSegment.from_file(file_path))

    def apply_energy_vad(self, audio, threshold=-30, min_silence_len=300):
        audio = audio.set_channels(1)
        chunks = audio.split_to_mono()[0].detect_nonsilent(
            min_silence_len=min_silence_len,
            silence_thresh=threshold
        )
        speech_segments = [audio[start:end] for start, end in chunks]
        return speech_segments

    def transcribe_segments(self, segments):
        transcripts = []
        total_segments = len(segments)
        
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_segment = {executor.submit(self.transcribe_segment, segment, i): i for i, segment in enumerate(segments)}
            for future in as_completed(future_to_segment):
                segment_index = future_to_segment[future]
                try:
                    transcript = future.result()
                    if transcript:
                        transcripts.append(transcript)
                    progress = int(20 + (segment_index + 1) / total_segments * 60)  # 20% to 80% progress
                    self.progress.emit(progress)
                    self.status_updated.emit(f"Transcribed segment {segment_index + 1} of {total_segments}")
                except Exception as e:
                    self.logger.error(f"Segment {segment_index} generated an exception: {e}")
        
        return transcripts

    def transcribe_segment(self, segment, segment_index):
        if self.cancel_flag:
            return None
        self.logger.info(f"Starting transcription of segment {segment_index}")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            segment_path = temp_file.name
            segment.export(segment_path, format="wav")
            segments, _ = self.whisper_model.transcribe(segment_path, language="en")
            result = " ".join([segment.text for segment in segments])
        os.unlink(segment_path)  # Clean up temporary file
        self.logger.info(f"Transcription of segment {segment_index} completed")
        return result
    
    def combine_transcripts(self, transcripts):
        return " ".join(transcripts)

    def cancel_transcription(self):
        self.cancel_flag = True
        self.logger.info("Transcription cancelled")

if __name__ == "__main__":
    # This section can be used for testing the Transcriber class directly
    pass