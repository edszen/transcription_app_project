import unittest
import numpy as np
from src.core.diarization import apply_diarization

class TestDiarization(unittest.TestCase):
    
    def test_apply_diarization(self):
        # MOck VAD segments and embeddings for multiple speakers
        mock_segments = [(0, 1), (1, 2), (2, 3)] # 3 segments of 1 second each
        mock_embeddings = np.random.rand(3, 128) # 3 segments of 128 dimensions
        
        result = apply_diarization(mock_segments, mock_embeddings)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(mock_segments))
        self.assertTrue(all('speaker' in segment for segment in result))
        
    def test_single_speaker(self):
        # Test with only one segment (should be one speaker)
        mock_segments = [(0, 1)] # 1 segment of 1 second
        mock_embeddings = np.random.rand(1, 128) # 1 segment of 128 dimensions
        
        result = apply_diarization(mock_segments, mock_embeddings)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['speaker'], 'Speaker_0')
        self.assertEqual(result[0]['start'], 0)
        self.assertEqual(result[0]['end'], 1)
        
if __name__ == '__main__':
    unittest.main()