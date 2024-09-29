import pytest
from unittest.mock import patch, MagicMock
import torch
from src.core.diarization import apply_diarization, match_to_speaker, _post_process_diarization

@pytest.fixture
def mock_whisperx():
    with patch('src.core.diarization.whisperx') as mock:
        yield mock

@pytest.fixture
def mock_vad():
    with patch('src.core.diarization.apply_pyannote_vad') as mock:
        yield mock

def test_apply_diarization(mock_whisperx, mock_vad):
    mock_vad.return_value = ([], {})
    mock_whisperx.DiarizationPipeline.return_value.return_value = MagicMock()
    
    audio_path = "test.wav"
    transcript = {"segments": [{"start": 0, "end": 1, "text": "Hello"}]}
    api_key = "test_key"
    
    result = apply_diarization(audio_path, transcript, api_key)
    
    assert isinstance(result, str)
    assert "Hello" in result

def test_match_to_speaker():
    transcription_segments = [
        {"start": 0, "end": 1, "text": "Hello", "embedding": torch.tensor([1.0, 2.0, 3.0])}
    ]
    speaker_embeddings = {0.5: torch.tensor([1.0, 2.0, 3.0])}
    
    result = match_to_speaker(transcription_segments, speaker_embeddings)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert "speaker" in result[0]
    assert result[0]["speaker"] == "Speaker_0.5"

def test_post_process_diarization():
    diarized_transcription = [
        {"start": 0, "end": 1, "speaker": "SPEAKER_1", "text": "Hello"},
        {"start": 1, "end": 2, "speaker": "SPEAKER_2", "text": "Hi"},
    ]
    
    result = _post_process_diarization(diarized_transcription)
    
    assert isinstance(result, str)
    assert "SPEAKER_1" in result
    assert "SPEAKER_2" in result
    assert "Hello" in result
    assert "Hi" in result

if __name__ == "__main__":
    pytest.main([__file__])