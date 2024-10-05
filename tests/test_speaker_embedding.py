import unittest
import numpy as np
import torch
from unittest.mock import MagicMock, patch
from src.core.speaker_embedding import extract_speaker_embeddings

class TestSpeakerEmbedding(unittest.TestCase):
    
    @patch('src.core.speaker_embedding.EncoderClassifier')
    def test_extract_speaker_embeddings(self, mock_classifier):
        mock_classifier.from_hparams.return_value.encode_batch.return_value = torch.rand(1, 192)
        # Mock VAD segments (list of audio segments)
        mock_segments = [np.random.rand(16000) for _ in range(3)] # 3 segments of 1 second each
        
        embeddings = extract_speaker_embeddings(mock_segments)
        
        self.assertIsInstance(embeddings, np.ndarray)
        self.assertEqual(embeddings.shape[0], len(mock_segments)) # One embedding per segment
        self.assertEqual(embeddings.shape[1], 192) # Embedding dimension
        
    def test_empty_input(self):
        # Test empty input
        with self.assertRaises(ValueError):
            extract_speaker_embeddings([])
    
    def test_single_segment(self):
        # Test with a single segment
        with patch('src.core.speaker_embedding.EncoderClassifier') as mock_classifier:
            mock_classifier.from_hparams.return_value.encode_batch.return_value = torch.rand(1, 192)
            mock_segment = np.random.rand(16000)  # 1 segment of 1 second
            
            embeddings = extract_speaker_embeddings([mock_segment])
            
            self.assertIsInstance(embeddings, np.ndarray)
            self.assertEqual(embeddings.shape[0], 1)  # One embedding
            self.assertEqual(embeddings.shape[1], 192)  # Embedding dimension
            
if __name__ == '__main__':
    unittest.main()