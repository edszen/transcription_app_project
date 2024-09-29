import logging
from faster_whisper import WhisperModel
from PyQt5.QtCore import QObject, pyqtSignal
import torch
from utils.encryption import EncryptionUtils
from core.diarization import apply_diarization
from utils.audio_processing import load_audio, chunk_audio
from core.vad import apply_energy_vad, apply_pyannote_vad, embed_speakers
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

    def transcribe(self, file_path, use_diarization=False, encrypted_api_key=None, vad_method="pyannote", use_embedding=True):
        try:
            self.cancel_flag = False
            logger.info(f"Starting transcription for file: {file_path}")
            self.status_updated.emit("Loading audio file...")
            
            # Load audio file
            audio = whisperx.load_audio(file_path)
            logger.info(f"Audio file loaded, duration: {len(audio)/16000:.2f} seconds")
            
            # Compute speaker embeddings for the entire audio file
            embeddings = None
            if use_embedding and use_diarization:
                self.status_updated.emit("Computing speaker embeddings...")
                embeddings = embed_speakers(file_path, encrypted_api_key)
                if embeddings is None:
                    logger.warning("Speaker embedding failed. Proceeding without embeddings.")
            
            # Apply VAD
            self.status_updated.emit("Applying Voice Activity Detection...")
            if vad_method == 'pyannote':
                try:
                    vad_segments = apply_pyannote_vad(file_path, encrypted_api_key)
                except Exception as e:
                    logger.error(f"Pyannote VAD failed: {str(e)}. Falling back to energy-based VAD.")
                    self.status_updated.emit("Pyannote VAD failed. Falling back to energy-based VAD.")
                    vad_segments = apply_energy_vad(audio)
            elif vad_method == 'energy':
                vad_segments = apply_energy_vad(audio)
            else:
                vad_segments = [audio]  # No VAD, use full audio
            
            logger.info(f"VAD applied, found {len(vad_segments)} speech segments")
            self.progress.emit(20)

            # Transcribe audio using Faster Whisper
            self.status_updated.emit("Transcribing audio...")
            segments, info = self.whisper_model.transcribe(audio, beam_size=5)
            
            # Convert Faster Whisper segments to WhisperX format
            whisperx_segments = [
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                } for segment in segments
            ]
            result = {"segments": whisperx_segments, "language": info.language}
            self.progress.emit(60)

            # Apply diarization if enabled
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

    def process_chunk(self, chunk, chunk_index, total_chunks, use_diarization, encrypted_api_key):
        max_retries = 3  # Retry up to 3 times if processing a chunk fails
        retries = 0
        success = False
        
        while retries < max_retries and not success:
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    chunk_path = temp_file.name
                    chunk.export(chunk_path, format="wav")
                    
                    if os.path.getsize(chunk_path) == 0:
                        raise ValueError("Exported audio file is empty")

                    # Transcription
                    segments, _ = self.whisper_model.transcribe(chunk_path)
                    transcript = " ".join([seg.text for seg in segments])
                    
                    success = True
                    self.chunk_progress.emit(chunk_index + 1, total_chunks, 100)
                    return transcript
            except Exception as e:
                retries += 1
                logger.error(f"Error processing chunk {chunk_index}, retry {retries}/{max_retries}: {str(e)}", exc_info=True)
                if retries == max_retries:
                    return f"[Processing failed for chunk {chunk_index} after {max_retries} retries]"
            finally:
                if os.path.exists(chunk_path):
                    os.unlink(chunk_path)
    
    def apply_diarization(self, audio_path, transcript, encrypted_api_key):
        try:
            api_key = self.encryption.decrypt(encrypted_api_key) if encrypted_api_key else ""
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

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

            # Process results and fallback if needed
            final_transcript = self._post_process_diarization(result)
            return final_transcript

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