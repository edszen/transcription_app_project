import unittest
from unittest.mock import patch, MagicMock
from PyQt5.QtCore import QObject, pyqtSignal
import torch
import numpy as np
from src.core.transcribe import Transcriber, EncryptionUtils

class TestTranscriber(unittest.TestCase):
    def setUp(self):
        self.transcriber = Transcriber()

    @patch('src.core.transcribe.preprocess_audio')  # Updated patch
    @patch('src.core.transcribe.EncryptionUtils.decrypt')  # Updated patch
    @patch('src.core.transcribe.whisperx.load_model')  # Updated patch
    @patch('src.core.transcribe.whisperx.load_align_model')  # Updated patch
    @patch('src.core.transcribe.whisperx.align')  # Updated patch
    @patch('src.core.transcribe.apply_diarization')  # Updated patch
    @patch('src.core.transcribe.assign_speakers')  # Updated patch
    @patch('src.core.transcribe.align_transcription_with_diarization')  # Updated patch
    @patch('src.core.transcribe.linguistic_post_processing')  # Updated patch
    def test_transcribe(self, mock_linguistic_post_processing, mock_align_transcription, 
                        mock_assign_speakers, mock_apply_diarization, mock_align, 
                        mock_load_align_model, mock_load_model, mock_decrypt, mock_preprocess_audio):
        # Mock return values
        mock_preprocess_audio.return_value = np.array([0.1, 0.2, 0.3])
        mock_decrypt.return_value = "decrypted_api_key"
        mock_load_model.return_value = MagicMock()
        mock_load_model.return_value.transcribe.return_value = {"segments": [{"start": 0, "end": 1, "text": "Hello"}]}
        mock_load_align_model.return_value = (MagicMock(), MagicMock())
        mock_align.return_value = {"segments": [{"start": 0, "end": 1, "text": "Hello"}]}
        mock_apply_diarization.return_value = [{"start": 0, "end": 1, "speaker": "SPEAKER_01"}]
        mock_assign_speakers.return_value = [{"start": 0, "end": 1, "text": "Hello", "speaker": "SPEAKER_01"}]
        mock_align_transcription.return_value = [{"start": 0, "end": 1, "text": "Hello", "speaker": "SPEAKER_01"}]
        mock_linguistic_post_processing.return_value = [{"start": 0, "end": 1, "text": "Hello", "speaker": "SPEAKER_01"}]

        # Call the method
        self.transcriber.transcribe("test.wav", use_diarization=True, encrypted_api_key="encrypted_key")

        # Assertions
        mock_preprocess_audio.assert_called_once_with("test.wav")
        mock_decrypt.assert_called_once_with("encrypted_key")
        mock_load_model.assert_called_once()
        mock_load_align_model.assert_called_once()
        mock_align.assert_called_once()
        mock_apply_diarization.assert_called_once()
        mock_assign_speakers.assert_called_once()
        mock_align_transcription.assert_called_once()
        mock_linguistic_post_processing.assert_called_once()

    @patch('src.core.transcribe.EncryptionUtils.decrypt')  # Updated patch
    def test_cancel_transcription(self, mock_decrypt):
        self.transcriber.cancel_transcription()
        self.assertTrue(self.transcriber.cancel_flag)

    def test_format_transcript(self):
        segments = [
            {"start": 0, "end": 5, "text": "Hello", "speaker": "SPEAKER_01"},
            {"start": 5, "end": 10, "text": "World", "speaker": "SPEAKER_02"}
        ]
        formatted = self.transcriber._format_transcript(segments)
        expected = "00:00 - 00:05 | Speaker 1: Hello\n00:05 - 00:10 | Speaker 2: World\n"
        self.assertEqual(formatted, expected)

if __name__ == '__main__':
    unittest.main()