import unittest
import numpy as np
import os
from src.utils.audio_processing import load_audio, preprocess_audio

class TestAudioProcessing(unittest.TestCase):
    
    def setUp(self):
        self.test_audio_path = os.path.join(os.path.dirname(__file__), 'test_files', 'sample.wav')
    
    def test_load_audio(self):
        # Test loading a valid audio file
        audio = load_audio(self.test_audio_path)
        self.assertIsInstance(audio, np.ndarray)
        self.assertTrue(len(audio) > 0)
        
    def test_load_audio_invalid_file(self):
        # Test loading an invalid audio file
        with self.assertRaises(ValueError):
            load_audio('test_files/invalid.txt')
            
    def test_preprocess_audio(self):
        # Test audio preprocessing
        processed_audio = preprocess_audio(self.test_audio_path)
        self.assertIsInstance(processed_audio, np.ndarray)
        self.assertTrue(np.max(processed_audio) <= 1.0) # check if audio is normalized
        
if __name__ == '__main__':
    unittest.main()