import logging
import threading
import numpy as np
from faster_whisper import WhisperModel
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtCore import QObject, pyqtSignal
import whisperx
import torch
from pyannote.audio import Pipeline
from encryption_utils import EncryptionUtils

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Transcriber(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    chunk_progress = pyqtSignal(int, int, int) # current chunk, total chunks

    def __init__(self):
        super().__init__()
        self.cancel_flag = False
        self.logger = logging.getLogger(__name__)
        self.encryption_utils = EncryptionUtils()
        
        # Initialize Faster Whisper model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        self.whisper_model = WhisperModel("small", device=device, compute_type=compute_type)
        
        # Initialize pyannote VAD
        self.vad_pipeline = None  # We'll initialize this later with the API token

    def transcribe(self, file_path, use_diarization=False, encrypted_api_key=None, vad_method='pyannote'):
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
                try:
                    api_key = self.encryption_utils.decrypt(encrypted_api_key) if encrypted_api_key else ""
                except Exception as e:
                    self.logger.error(f"Failed to decrypt API key: {str(e)}")
                    self.status_updated.emit("Failed to decrypt API key. Falling back to energy-based VAD.")
                    vad_method = 'energy'
                    api_key = ""
                
                if api_key:
                    speech_segments = self.apply_pyannote_vad(file_path, api_key)
                else:
                    self.logger.warning("No valid API key for Pyannote VAD. Falling back to energy-based VAD.")
                    self.status_updated.emit("No valid API key. Falling back to energy-based VAD.")
                    speech_segments = self.apply_energy_vad(audio)
            elif vad_method == 'energy':
                speech_segments = self.apply_energy_vad(audio)
            else:
                speech_segments = [audio]  # No VAD, use full audio
            
            self.logger.info(f"VAD applied, found {len(speech_segments)} speech segments")
            self.progress.emit(20)
            
            # Chunk the audio if it's longer than 5 minutes
            chunk_length_ms = 5 * 60 * 1000  # 5 minutes
            if len(audio) > chunk_length_ms:
                chunks = self.chunk_audio(audio, chunk_length_ms)
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

        except Exception as e:
            if not self.cancel_flag:
                error_message = f"Error during transcription: {str(e)}"
                self.logger.error(error_message, exc_info=True)
                self.error.emit(error_message)
            
            # Transcribe speech segments
            transcripts = self.transcribe_segments(speech_segments)
            self.logger.info(f"Transcription completed, {len(transcripts)} segments processed")
            self.progress.emit(80)
            
            # Combine transcripts
            full_transcript = self.combine_transcripts(transcripts)
            self.logger.info(f"Combined transcript length: {len(full_transcript)}")
            
            if use_diarization:
                self.status_updated.emit("Starting transcription with diarization...")
                api_key = self.encryption_utils.decrypt(encrypted_api_key) if encrypted_api_key else ""
                self.api_key = api_key
                transcript = self.transcribe_with_diarization(file_path)
            else:
                transcript = full_transcript  # Use the full transcript when not using diarization

            if not self.cancel_flag:
                self.progress.emit(100)
                self.status_updated.emit("Transcription completed!")
                self.finished.emit(transcript)
            
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

    def apply_energy_vad(self, audio, min_silence_len=300, silence_thresh=-40):
        try:
            # Ensure audio is mono
            audio = audio.set_channels(1)
            
            # Use detect_nonsilent from pydub.silence
            nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
            
            # Create speech segments based on non-silent ranges
            speech_segments = [audio[start:end] for start, end in nonsilent_ranges]
            
            return speech_segments
        except Exception as e:
            self.logger.error(f"Error in energy-based VAD: {str(e)}")
            self.status_updated.emit("Energy-based VAD failed. Transcribing full audio.")
            return [audio]

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
    
    def transcribe_with_diarization(self, file_path):
        try:
            self.status_updated.emit("Loading audio file...")
            
            # Determine the appropriate device
            if torch.backends.mps.is_available():
                device = torch.device('mps')
                compute_type = "float16"
            elif torch.cuda.is_available():
                device = torch.device('cuda')
                compute_type = "float16"
            else:
                device = torch.device('cpu')
                compute_type = "int8"

            self.logger.info(f"Using device: {device} with compute type: {compute_type}")

            # Load the audio file
            audio = AudioSegment.from_file(file_path)
            
            # Ensure the audio is in a format compatible with the diarization model
            if audio.channels > 1:
                audio = audio.set_channels(1)
            if audio.frame_rate != 16000:
                audio = audio.set_frame_rate(16000)
            
            # Split the audio into 30-second chunks
            chunk_length_ms = 30 * 1000  # 30 seconds
            chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

            results = []
            
            with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
                future_to_chunk = {executor.submit(self.process_chunk, chunk, i, len(chunks), True, self.api_key): i for i, chunk in enumerate(chunks)}
                for future in as_completed(future_to_chunk):
                    chunk_index = future_to_chunk[future]
                    try:
                        result = future.result()
                        results.append(result)
                        self.chunk_progress.emit(chunk_index + 1, len(chunks), 100)
                    except Exception as e:
                        self.logger.error(f"Chunk {chunk_index} generated an exception: {e}")

            # Combine results
            combined_result = " ".join(results)
            
            return combined_result
        except Exception as e:
            self.logger.error(f"Error in transcribe_with_diarization: {str(e)}", exc_info=True)
            raise
    
    def chunk_audio(self, audio, chunk_length_ms):
        return [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    
    def process_chunk(self, chunk, chunk_index, total_chunks, use_diarization, encrypted_api_key):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            chunk_path = temp_file.name
            try:
                chunk.export(chunk_path, format="wav")
                
                # Verify the exported audio file
                if os.path.getsize(chunk_path) == 0:
                    raise ValueError("Exported audio file is empty")
                
                # Transcribe with Whisper
                segments, _ = self.whisper_model.transcribe(chunk_path)
                transcript = " ".join([segment.text for segment in segments])

                if use_diarization:
                    try:
                        api_key = self.encryption_utils.decrypt(encrypted_api_key) if encrypted_api_key else ""
                        transcript = self.apply_diarization(chunk_path, transcript, api_key)
                    except ValueError as ve:
                        self.logger.error(f"Diarization failed for chunk {chunk_index}: {str(ve)}")
                        # Continue with undiarized transcript
                        transcript = f"[Diarization failed: {str(ve)}] {transcript}"
                    except Exception as e:
                        self.logger.error(f"Unexpected error in diarization for chunk {chunk_index}: {str(e)}")
                        transcript = f"[Diarization error] {transcript}"

                return transcript
            except Exception as e:
                self.logger.error(f"Error processing chunk {chunk_index}: {str(e)}", exc_info=True)
                return f"[Processing failed for chunk {chunk_index}]"
            finally:
                os.unlink(chunk_path)
                self.chunk_progress.emit(chunk_index + 1, total_chunks, 100)
    
    def apply_diarization(self, audio_path, transcript, api_key):
        try:
            if torch.backends.mps.is_available():
                device = torch.device("mps")
            elif torch.cuda.is_available():
                device = torch.device("cuda")
            else:
                device = torch.device("cpu")
            self.logger.info(f"Initializing DiarizationPipeline with device: {device}")
            diarize_model = whisperx.DiarizationPipeline(use_auth_token=api_key, device=device)
            
            self.logger.info(f"Running diarization on audio file: {audio_path}")
            diarize_segments = diarize_model(audio_path)
            
            self.logger.info("Diarization completed. Segments:")
            self.logger.info(diarize_segments)
            
            self.logger.info("Preparing transcript segments")
            transcript_segments = [{"start": 0, "end": len(transcript) / 10, "text": transcript}]
            
            self.logger.info("Assigning word speakers")
            result = whisperx.assign_word_speakers(diarize_segments, {"segments": transcript_segments})
            
            return self.format_diarized_result(result)
        except KeyError as ke:
            self.logger.error(f"KeyError in diarization: {str(ke)}", exc_info=True)
            raise ValueError(f"Diarization failed due to missing key: {str(ke)}")
        except Exception as e:
            self.logger.error(f"Diarization error: {str(e)}", exc_info=True)
            raise ValueError(f"Diarization failed: {str(e)}")
        
    def combine_chunk_results(self, results):
        combined_segments = []
        time_offset = 0
        
        for result in results:
            for segment in result["segments"]:
                segment["start"] += time_offset
                segment["end"] += time_offset
                combined_segments.append(segment)
            
            time_offset += result["segments"][-1]["end"] if result["segments"] else 0

        return {"segments": combined_segments}
    
    def format_diarized_result(self, result):
        formatted_transcript = []
        for segment in result["segments"]:
            start = f"{segment['start']:.2f}"
            end = f"{segment['end']:.2f}"
            speaker = segment.get('speaker', 'Unknown')
            text = segment['text']
            formatted_transcript.append(f"{start} - {end} | Speaker {speaker}: {text}")
        return "\n".join(formatted_transcript)

    def cancel_transcription(self):
        self.cancel_flag = True
        self.logger.info("Transcription cancelled")

if __name__ == "__main__":
    # This section can be used for testing the Transcriber class directly
    pass