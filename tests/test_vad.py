import pytest
from unittest.mock import patch, MagicMock
import os
import sys
import torch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.vad import apply_pyannote_vad, apply_energy_vad
from pydub import AudioSegment

@pytest.fixture
def api_key():
    return "test_api_key"

@pytest.fixture
def audio_segment():
    return AudioSegment.silent(duration=2000)

@pytest.fixture
def mock_pipeline():
    with patch('pyannote.audio.Pipeline.from_pretrained') as mock:
        yield mock

@pytest.fixture
def mock_embedding_model():
    with patch('pyannote.audio.Model.from_pretrained') as mock:
        yield mock

def test_apply_pyannote_vad_success(mock_pipeline, mock_embedding_model, tmp_path, api_key):
    test_audio_path = tmp_path / "test_audio.wav"
    AudioSegment.silent(duration=1000).export(test_audio_path, format="wav")

    mock_vad_result = MagicMock()
    mock_vad_result.itertracks.return_value = [
        (MagicMock(start=0.0, end=0.5), None, "SPEECH"),
        (MagicMock(start=0.6, end=1.0), None, "SPEECH"),
    ]
    mock_pipeline.return_value.return_value = mock_vad_result

    mock_embedding_model.return_value.return_value = torch.tensor([0.1, 0.2, 0.3])

    speech_segments, speaker_embeddings = apply_pyannote_vad(str(test_audio_path), api_key)

    assert len(speech_segments) == 2
    assert len(speaker_embeddings) == 2
    assert isinstance(speaker_embeddings[0][1], torch.Tensor)

def test_apply_pyannote_vad_failure(mock_pipeline, tmp_path, api_key):
    test_audio_path = tmp_path / "test_audio.wav"
    AudioSegment.silent(duration=1000).export(test_audio_path, format="wav")

    mock_pipeline.side_effect = Exception("Pyannote VAD failed")

    with patch('core.vad.apply_energy_vad') as mock_energy_vad:
        mock_energy_vad.return_value = ([], [])
        speech_segments, speaker_embeddings = apply_pyannote_vad(str(test_audio_path), api_key)

    assert len(speech_segments) == 0
    assert len(speaker_embeddings) == 0

def test_apply_energy_vad_silent(audio_segment):
    speech_segments, speaker_embeddings = apply_energy_vad(audio_segment)
    assert len(speech_segments) == 0
    assert len(speaker_embeddings) == 0

def test_apply_energy_vad_with_speech(audio_segment):
    # Create a more pronounced speech segment
    speech = AudioSegment.silent(duration=500).overlay(AudioSegment.from_wav("tests/test_files/speech_sample.wav"))
    audio_with_speech = audio_segment.overlay(speech, position=500)
    speech_segments, speaker_embeddings = apply_energy_vad(audio_with_speech)
    assert len(speech_segments) > 0
    assert len(speaker_embeddings) == 0  # Energy VAD doesn't produce embeddings

def test_apply_energy_vad_failure():
    with patch('pydub.AudioSegment.set_channels', side_effect=Exception("Audio processing failed")):
        audio = MagicMock(spec=AudioSegment)
        speech_segments, speaker_embeddings = apply_energy_vad(audio)
        assert len(speech_segments) == 1
        assert isinstance(speech_segments[0], AudioSegment)
        assert len(speaker_embeddings) == 0

if __name__ == "__main__":
    pytest.main([__file__])