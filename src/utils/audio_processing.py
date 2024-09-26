from pydub import AudioSegment
import logging

logger = logging.getLogger(__name__)

def load_audio(file_path):
    try:
        audio = AudioSegment.from_file(file_path)
        return audio
    except Exception as e:
        logger.error(f"Failed to load audio file: {str(e)}")
        raise ValueError(f"Failed to load audio file: {str(e)}")
    
def chunk_audio(audio, chunk_length_ms):
    return [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
