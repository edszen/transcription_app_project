import unittest
import numpy as np
from unittest.mock import MagicMock, patch
import os
from src.core.vad import apply_energy_vad, apply_pyannote_vad
from pydub import AudioSegment

class TestVAD(unittest.TestCase):
    def setUp(self):
        self.test_audio_path = os.path.join('tests', 'test_files', 'sample.wav')
        
    def test_energy_vad(self):
        # Test energy-based VAD
        audio = np.random.rand(16000)  # 1 second of random audio
        audio = (audio * 32767).astype(np.int16)  # Convert to 16-bit PCM
        segments = apply_energy_vad(audio)
        self.assertIsInstance(segments, list)
        self.assertTrue(len(segments) > 0, "Energy VAD should detect at least one segment")
        
    def test_energy_vad_silent_audio(self):
        # Test energy-based VAD with silent audio
        silent_audio = np.zeros(16000, dtype=np.int16)  # 1 second of silence
        segments = apply_energy_vad(silent_audio)
        self.assertEqual(len(segments), 0, "Energy VAD should not detect segments in silent audio")
        
    @patch('src.core.vad.Pipeline')
    @patch('src.core.vad.EncryptionUtils')
    def test_pyannote_vad(self, mock_encryption, mock_pipeline):
        mock_pipeline.from_pretrained.return_value.return_value = MagicMock(
            itertracks=lambda yield_label: [
                (MagicMock(start=0, end=1), None, None),
                (MagicMock(start=2, end=3), None, None),
            ]
        )
        mock_encryption.return_value.decrypt.return_value = "decrypted_api_key"
        
        file_path = self.test_audio_path
        encrypted_api_key = 'encrypted_dummy_api_key'
        
        self.assertTrue(os.path.exists(file_path), f"Test audio file not found at {file_path}")
        
        segments = apply_pyannote_vad(file_path, encrypted_api_key)
        self.assertIsInstance(segments, list)
        self.assertEqual(len(segments), 2, "Pyannote VAD should detect 2 segments")
        mock_encryption.return_value.decrypt.assert_called_once_with(encrypted_api_key)

    @patch('src.core.vad.Pipeline')
    @patch('src.core.vad.EncryptionUtils')
    @patch('src.core.vad.AudioSegment.from_file')
    @patch('src.core.vad.apply_energy_vad')
    def test_pyannote_vad_error_handling(self, mock_energy_vad, mock_audio_segment, mock_encryption, mock_pipeline):
        mock_pipeline.from_pretrained.side_effect = Exception("API Error")
        mock_encryption.return_value.decrypt.return_value = "decrypted_api_key"
        mock_audio_segment.return_value = MagicMock()
        mock_energy_vad.return_value = []  # Simulate energy VAD failing and returning an empty list
        
        file_path = self.test_audio_path
        encrypted_api_key = 'encrypted_dummy_api_key'
        
        segments = apply_pyannote_vad(file_path, encrypted_api_key)
        self.assertIsInstance(segments, list)
        self.assertEqual(len(segments), 0, "Should return empty list when both Pyannote and energy VAD fail")
        mock_encryption.return_value.decrypt.assert_called_once_with(encrypted_api_key)
        mock_energy_vad.assert_called_once()

    @patch('src.core.vad.Pipeline')
    @patch('src.core.vad.AudioSegment.from_file')
    @patch('src.core.vad.apply_energy_vad')
    def test_pyannote_vad_fallback(self, mock_energy_vad, mock_audio_segment, mock_pipeline):
        mock_pipeline.from_pretrained.side_effect = Exception("API Error")
        mock_audio_segment.return_value = MagicMock()
        mock_energy_vad.return_value = [MagicMock()]  # Simulate energy VAD returning one segment
        
        file_path = self.test_audio_path
        encrypted_api_key = 'encrypted_dummy_api_key'
        
        segments = apply_pyannote_vad(file_path, encrypted_api_key)
        self.assertIsInstance(segments, list)
        self.assertEqual(len(segments), 1, "Should fallback to energy VAD and return 1 segment")
        mock_energy_vad.assert_called_once()

if __name__ == '__main__':
    unittest.main()