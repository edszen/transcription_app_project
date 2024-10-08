import os


# Project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory for storing audio files
AUDIO_FILES_DIR = os.path.join(ROOT_DIR, "audio_files")

# Models directory
MODELS_DIR = os.path.join(ROOT_DIR, "models")

# Audio processing
SAMPLE_RATE = 16000
CHUNK_SIZE = 3600 # seconds

# VAD
VAD_MODEL = "pyannote/voice-activity-detection"
VAD_THRESHOLD = 0.5

# Speaker Embedding
SPEAKER_EMBEDDING_MODEL = "speechbrain/spkrec-ecapa-voxceleb"

# Diarization
MAX_SPEAKERS = 10
CLUSTERING_METHOD = "agglomerative"

# Transcription
WHISPER_MODEL = "medium"
# Device will be determined at runtime in the respective modules

# Logging
LOG_DIR = os.path.join(ROOT_DIR, "logs")
LOG_LEVEL = "INFO"

# Encryption
ENCRYPTION_KEY_FILE = os.path.join(ROOT_DIR, "src", "utils", "encryption.key")

# API
HUGGINGFACE_API_MODEL = "pyannote/voice-activity-detection"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ChatGPT model config
CHATGPT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # Default to gpt-3.5-turbo if not set

AVAILABLE_MODELS = [
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "gpt-4",
    "gpt-4-32k",
    "gpt-4-1106-preview",
    "gpt-4-vision-preview"
]

# API Version constant
OPENAI_API_VERSION = "2024-10-01"

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

# UI
HELP_DIALOG_WIDTH = 400
HELP_DIALOG_HEIGHT = 300

# Do not store the API key directly in this file
# It will be handled securely in the application

def create_directories():
    """Create necessary directories if they don't exist."""
    for directory in [AUDIO_FILES_DIR, MODELS_DIR, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)