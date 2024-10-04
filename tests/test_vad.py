import unittest
import numpy as np
from unittest.mock import MagicMock, patch
from src.core.vad import apply_energy_vad, apply_pyannote_vad

class TestVAD(unittest.TestCase):
    def test_energy_vad(self):
        # Test energy-based VAD
        audio = np.random.rand(16000) # 1 second of random audio
        segments = apply_energy_vad(audio)
        self.assertIsInstance(segments, list)
        
    @patch('src.core.vad.Pipeline')    
    def test_pyannote_vad(self, mock_pipeline):
        mock_pipeline.from_pretrained.return_value.return_value = MagicMock(
            itertracks =lambda yield_label: [
                (MagicMock(start=0, end=1), None, None),
                (MagicMock(start=2, end=3), None, None),
            ]
        )
        # Test Pyannote VAD (requires API key)

        file_path = 'test_files/sample.wav'
        api_key = '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'
        segments = apply_pyannote_vad(file_path, api_key)
        self.assertIsInstance(segments, list)
        self.assertTrue(len(segments) > 2)
        
if __name__ == '__main__':
    unittest.main()