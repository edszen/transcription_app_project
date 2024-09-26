import torch
from pyannote.audio import Pipeline
import whisper
from PyQt5.QtCore import QSettings
from utils.encryption import EncryptionUtils
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def perform_transcription(file_path):
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["segments"]

def perform_diarization(file_path, api_key):
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1", use_auth_token=api_key)
    device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
    pipeline = pipeline.to(device)
    return pipeline(file_path)

def format_transcript_with_diarization(transcript, diarization):
    formatted_lines = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        relevant_segments = [
            segment for segment in transcript
            if segment['start'] <= turn.end and segment['end'] >= turn.start
        ]
        if relevant_segments:
            text = ' '.join([segment['text'].strip() for segment in relevant_segments])
            formatted_lines.append(f"{turn.start:.2f} - {turn.end:.2f} | Speaker {speaker}: {text}")
    return '\n\n'.join(formatted_lines)

def test_transcription_and_diarization(audio_file, api_key):
    try:
        transcript = perform_transcription(audio_file)
        logger.info("Transcription successful")

        diarization = perform_diarization(audio_file, api_key)
        logger.info("Diarization successful")

        formatted_transcript = format_transcript_with_diarization(transcript, diarization)
        
        print("\nSample of formatted transcript:")
        print("\n".join(formatted_transcript.split("\n")[:10]))
        return True
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    settings = QSettings("YourCompany", "AudioTranscriptionApp")
    encryption_utils = EncryptionUtils()
    encrypted_key = settings.value("huggingface_api_key", "")
    if not encrypted_key:
        print("Error: No API key found in settings. Please set up your API key first.")
        exit(1)
    
    api_key = encryption_utils.decrypt(encrypted_key)
    
    audio_file = input("Enter the path to your audio file: ")
    
    success = test_transcription_and_diarization(audio_file, api_key)
    if not success:
        print("Test failed. Please check the error messages above.")
    else:
        print("Test completed successfully.")