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
import webrtcvad

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
        
        # Initialize WebRTC VAD
        self.vad = webrtcvad.Vad(1)  # Mode 1 is less aggressive

    def transcribe(self, file_path, use_diarization=False, api_key=None):
        try:
            self.cancel_flag = False
            self.logger.info(f"Starting transcription for file: {file_path}")
            self.status_updated.emit("Loading audio file...")
            
            # Load audio file
            audio = self.load_audio(file_path)
            self.logger.info(f"Audio file loaded, duration: {len(audio)/1000:.2f} seconds")
            
            # Apply VAD
            self.status_updated.emit("Applying Voice Activity Detection...")
            try:
                speech_segments = self.apply_vad(audio)
                self.logger.info(f"VAD applied, found {len(speech_segments)} speech segments")
            except Exception as e:
                self.logger.warning(f"VAD failed, proceeding with full audio: {str(e)}")
                speech_segments = [audio]
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
        
    def apply_vad(self, audio):
        # Ensure audio is mono and at 16000Hz
        audio = audio.set_channels(1).set_frame_rate(16000)
        
        # Convert audio to the format expected by WebRTC VAD
        audio_array = np.array(audio.get_array_of_samples())
        audio_float32 = audio_array.astype(np.float32) / 32768.0
        
        # Set frame duration and process audio
        frame_duration = 30  # ms
        frames = self.frame_generator(audio_float32, frame_duration)
        speech_frames = []
        for frame in frames:
            try:
                if self.vad.is_speech(frame.tobytes(), 16000):
                    speech_frames.append(frame)
            except Exception as e:
                self.logger.warning(f"Error processing VAD frame: {str(e)}")
                continue
        
        # Convert speech frames back to AudioSegment
        speech_segments = [
            AudioSegment(
                frame.tobytes(),
                frame_rate=16000,
                sample_width=2,
                channels=1
            )
            for frame in speech_frames
        ]
        
        return speech_segments

    def frame_generator(self, audio, frame_duration):
        n = int(16000 * (frame_duration / 1000.0))
        offset = 0
        while offset + n < len(audio):
            yield audio[offset:offset + n]
            offset += n

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

# Remove the test_diarization function as it's no longer needed in this file

if __name__ == "__main__":
    # This section can be used for testing the Transcriber class directly
    pass