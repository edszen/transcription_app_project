import unittest
from unittest.mock import MagicMock, patch
from src.core.transcribe import Transcriber

class TestTranscriber(unittest.TestCase):
    
    @patch('src.core.transcribe.WhisperModel') # Patch the WhisperModel class
    def test_transcribe(self, mock_whisper):
        # Mock WhisperModel and its transcribe method
        mock_whisper.return_value.transcribe.return_value = (
            [MagicMock(start=0, end=1, text="Hello")],
            {}
        )
        
        transcriber = Transcriber()
        audio = MagicMock() # Mock audio data
        result = transcriber._transcribe_audio(audio)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], 'Hello')
        
    def test_cancel_transcription(self):
        transcriber = Transcriber()
        transcriber.cancel_transcription()
        self.assertTrue(transcriber.cancel_flag)

if __name__ == '__main__':
    unittest.main()     