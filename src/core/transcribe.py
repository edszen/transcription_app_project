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

    def transcribe(self, file_path, use_diarization=False, encrypted_api_key=None, vad_method="pyannote"):
        try:
            self.cancel_flag = False
            logger.info(f"Starting transcription for file: {file_path}")
            self.status_updated.emit("Loading audio file...")
            
            audio = load_audio(file_path)
            logger.info(f"Audio file loaded, duration: {len(audio)/1000:.2f} seconds")
            
            # Apply VAD
            self.status_updated.emit("Applying Voice Activity Detection...")
            if vad_method == 'pyannote':
                try:
                    api_key = self.encryption.decrypt(encrypted_api_key) if encrypted_api_key else ""
                    speech_segments = apply_pyannote_vad(file_path, api_key)
                except Exception as e:
                    logger.error(f"Pyannote VAD failed: {str(e)}. Falling back to energy-based VAD.")
                    self.status_updated.emit("Pyannote VAD failed. Falling back to energy-based VAD.")
                    speech_segments = apply_energy_vad(audio)
            elif vad_method == 'energy':
                speech_segments = apply_energy_vad(audio)
            else:
                speech_segments = [audio]  # No VAD, use full audio
            
            logger.info(f"VAD applied, found {len(speech_segments)} speech segments")
            self.progress.emit(20)

            # Chunk the audio if it's longer than 5 minutes
            chunk_length_ms = 5 * 60 * 1000  # 5 minutes
            chunks = self.chunk_audio(audio, chunk_length_ms)

            transcripts = []
            for i, chunk in enumerate(chunks):
                if self.cancel_flag:
                    break
                self.status_updated.emit(f"Processing chunk {i+1} of {len(chunks)}")
                chunk_transcript = self.process_chunk(chunk, i, len(chunks), use_diarization, encrypted_api_key)
                transcripts.append(chunk_transcript)

            if not self.cancel_flag:
                full_transcript = "\n".join(transcripts)
                if use_diarization:
                    full_transcript = self.apply_diarization(file_path, full_transcript, encrypted_api_key)
                self.progress.emit(100)
                self.status_updated.emit("Transcription completed!")
                self.finished.emit(full_transcript)

        except Exception as e:

            full_transcript = " ".join(transcripts)

            if use_diarization:
                self.status_updated.emit("Applying diarization...")
                try:
                    api_key = self.encryption.decrypt(encrypted_api_key) if encrypted_api_key else ""
                    diarized_transcript = apply_diarization(file_path, full_transcript, api_key)
                    if diarized_transcript.startswith("[Diarization failed:"):
                        logger.warning(diarized_transcript)
                        # Optionally, you can choose to use the non-diarized transcript here
                        # full_transcript = diarized_transcript.split("\n\n", 1)[1]
                    else:
                        full_transcript = diarized_transcript
                except Exception as e:
                    logger.error(f"Diarization failed: {str(e)}")
                    full_transcript = f"[Diarization failed: {str(e)}]\n\n" + full_transcript

            if not self.cancel_flag:
                self.progress.emit(100)
                self.status_updated.emit("Transcription completed!")
                self.finished.emit(full_transcript)

        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}", exc_info=True)
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
    
    def apply_diarization(self, audio_path, transcript, encrypted_api_key):
        try:
            api_key = self.encryption_utils.decrypt(encrypted_api_key) if encrypted_api_key else ""
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Initializing DiarizationPipeline with device: {device}")
            diarize_model = whisperx.DiarizationPipeline(use_auth_token=api_key, device=device)
            
            logger.info(f"Running diarization on audio file: {audio_path}")
            diarize_segments = diarize_model(audio_path)
            
            logger.info("Diarization completed. Segments:")
            logger.info(diarize_segments)
            
            logger.info("Preparing transcript segments")
            transcript_segments = self._prepare_transcript_segments(transcript)
            
            logger.info("Assigning word speakers")
            result = whisperx.assign_word_speakers(diarize_segments, transcript_segments)
            
            return self._post_process_diarization(result)
        except Exception as e:
            logger.error(f"Diarization error: {str(e)}", exc_info=True)
            return f"[Diarization failed: {str(e)}]\n\n{transcript}"

    def _prepare_transcript_segments(self, transcript):
        words = transcript.split()
        segments = []
        start_time = 0
        for word in words:
            end_time = start_time + 0.4  # Assume each word takes about 0.4 seconds
            segments.append({"start": start_time, "end": end_time, "text": word})
            start_time = end_time
        return {"segments": segments}

    def _post_process_diarization(self, result):
        formatted_transcript = []
        current_speaker = None
        current_text = []
        start_time = None
        
        for segment in result["segments"]:
            start = f"{segment['start']:.2f}"
            end = f"{segment['end']:.2f}"
            speaker = f"SPEAKER_{segment.get('speaker', 'UNKNOWN')}"
            text = segment['text']
            
            if speaker != current_speaker or (float(start) - float(prev_end) > 1.0 if 'prev_end' in locals() else False):
                if current_speaker:
                    formatted_transcript.append(f"{start_time} - {prev_end} | {current_speaker}: {' '.join(current_text)}")
                current_speaker = speaker
                current_text = [text]
                start_time = start
            else:
                current_text.append(text)
            
            prev_end = end
        
        if current_speaker:
            formatted_transcript.append(f"{start_time} - {prev_end} | {current_speaker}: {' '.join(current_text)}")
        
        return "\n".join(formatted_transcript)

    def chunk_audio(self, audio, chunk_length_ms):
        return [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

    def cancel_transcription(self):
        self.cancel_flag = True
        logger.info("Transcription cancelled")

if __name__ == "__main__":
    # This section can be used for testing the Transcriber class directly
    pass