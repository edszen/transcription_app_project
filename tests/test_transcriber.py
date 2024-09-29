import pytest
from unittest.mock import patch, MagicMock
from PyQt5.QtCore import QObject
from src.core.transcribe import Transcriber

@pytest.fixture
def transcriber():
    return Transcriber()

@pytest.fixture
def mock_whisper_model():
    with patch('src.core.transcribe.WhisperModel') as mock:
        yield mock

@pytest.fixture
def mock_diarization():
    with patch('src.core.transcribe.apply_diarization') as mock:
        yield mock

def test_initialize_whisper_model(transcriber, mock_whisper_model):
    transcriber._initialize_whisper_model()
    mock_whisper_model.assert_called_once()

def test_transcribe(transcriber, mock_whisper_model, mock_diarization):
    transcriber.whisper_model = MagicMock()
    transcriber.whisper_model.transcribe.return_value = (
        [MagicMock(start=0, end=1, text="Hello")],
        MagicMock(language="en")
    )
    
    mock_diarization.return_value = "SPEAKER_1: Hello"
    
    transcriber.finished = MagicMock()
    transcriber.progress = MagicMock()
    transcriber.status_updated = MagicMock()
    
    transcriber.transcribe("test.wav", use_diarization=True)
    
    transcriber.finished.emit.assert_called_once()
    assert transcriber.progress.emit.call_count > 0
    assert transcriber.status_updated.emit.call_count > 0

def test_process_chunk(transcriber):
    chunk = MagicMock()
    result = transcriber.process_chunk(chunk, 0, 1, False, None)
    assert isinstance(result, str)

def test_apply_diarization(transcriber, mock_diarization):
    mock_diarization.return_value = "SPEAKER_1: Hello"
    result = transcriber.apply_diarization("test.wav", "Hello", "encrypted_key")
    assert "SPEAKER_1: Hello" in result

def test_cancel_transcription(transcriber):
    transcriber.cancel_transcription()
    assert transcriber.cancel_flag == True

if __name__ == "__main__":
    pytest.main([__file__])