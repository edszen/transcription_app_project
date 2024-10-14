import os
import unittest
from unittest.mock import patch
import numpy as np
import soundfile as sf
from src.core.diarization import apply_diarization

class TestDiarization(unittest.TestCase):
    def setUp(self):
        # Create a dummy WAV file for testing
        self.audio_path = "dummy_audio.wav"
        dummy_audio = np.random.rand(16000)  # 1 second of random noise at 16kHz
        sf.write(self.audio_path, dummy_audio, 16000)

    def tearDown(self):
        # Remove the dummy file after tests
        if os.path.exists(self.audio_path):
            os.remove(self.audio_path)

    @patch('src.utils.encryption.EncryptionUtils.decrypt')
    def test_apply_diarization(self, mock_decrypt):
        mock_decrypt.return_value = "dummy_api_key"
        encrypted_api_key = "encrypted_dummy_key"

        # Check if the file exists
        self.assertTrue(os.path.exists(self.audio_path), f"Test audio file does not exist: {self.audio_path}")

        # Print the absolute path
        print(f"Using audio file: {os.path.abspath(self.audio_path)}")

        try:
            result = apply_diarization(self.audio_path, encrypted_api_key)
            # Add your assertions here
            self.assertIsNotNone(result)
            # Add more specific assertions based on expected output
        except Exception as e:
            self.fail(f"apply_diarization raised an exception: {str(e)}")

    # Add more test methods as needed

if __name__ == '__main__':
    unittest.main()