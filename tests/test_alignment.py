import unittest
from src.core.alignment import align_transcription_with_diarization

class TestAlignment(unittest.TestCase):
    
    def test_align_transcription_with_diarization(self):
        transcription = [
            {"start": 0, "end": 1, "text": "Hello"},
            {"start": 1, "end": 2, "text": "world"},
        ]
        diarization_result = [
            {"start": 0, "end": 1, "speaker": "Speaker_1"},
            {"start": 1, "end": 2, "speaker": "Speaker_2"},
        ]
        
        result = align_transcription_with_diarization(transcription, diarization_result)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['speaker'], 'Speaker_1')
        self.assertEqual(result[1]['speaker'], 'Speaker_2')
        self.assertEqual(result[0]['text'], 'Hello')
        self.assertEqual(result[1]['text'], 'world')
        
    def test_misaligned_segments(self):
        transcription = [{"start": 0, "end": 2, "text": "Hello world"}]
        diarization_result = [
            {"start": 0, "end": 1, "speaker": "Speaker_1"},
            {"start": 1, "end": 2, "speaker": "Speaker_2"},
        ]
        
        result = align_transcription_with_diarization(transcription, diarization_result)
        
        self.assertEqual(len(result), 1)
        self.assertIn(result[0]['speaker'], ['Speaker_1', 'Speaker_2'])
        
if __name__ == '__main__':
    unittest.main()