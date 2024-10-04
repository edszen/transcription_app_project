import os

# Project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory for storing audio files
AUDIO_FILES_DIR = os.path.join(ROOT_DIR, "audio_files")

# Models directory
MODELS_DIR = os.path.join(ROOT_DIR, "models")

# Audio processing
SAMPLE_RATE = 16000
CHUNK_SIZE = 30 # seconds

# VAD
VAD_MODEL = "pyannote/voice-activity-detection"
VAD_THRESHOLD = 0.5

# Speaker Embedding
SPEAKER_EMBEDDING_MODEL = "speechbrain/spkrec-ecapa-voxceleb"

# Diarization
MAX_SPEAKERS = 10
CLUSTERING_METHOD = "agglomerative"

# Transcription
WHISPER_MODEL = "small"
# Device will be determined at runtime in the respective modules

# Logging
LOG_DIR = os.path.join(ROOT_DIR, "logs")
LOG_LEVEL = "INFO"

# Encryption
ENCRYPTION_KEY_FILE = os.path.join(ROOT_DIR, "src", "utils", "encryption.key")

# API
HUGGINGFACE_API_MODEL = "pyannote/voice-activity-detection"

# UI
HELP_DIALOG_WIDTH = 400
HELP_DIALOG_HEIGHT = 300

# Do not store the API key directly in this file
# It will be handled securely in the application

def create_directories():
    """Create necessary directories if they don't exist."""
    for directory in [AUDIO_FILES_DIR, MODELS_DIR, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)