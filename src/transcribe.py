import whisper
from PyQt5.QtCore import QObject, pyqtSignal
from pydub import AudioSegment
import os
import numpy as np

class Transcriber(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.chunk_duration = 10 * 60 * 1000  # 10 minutes in milliseconds

    def transcribe(self, file_path):
        try:
            print("Loading Whisper model...")
            model = whisper.load_model("base")
            print("Model loaded successfully!")

            audio = AudioSegment.from_file(file_path)
            total_duration = len(audio)
            chunks = self.split_audio(audio)
            
            full_transcript = []
            for i, chunk in enumerate(chunks):
                chunk_path = f"temp_chunk_{i}.wav"
                chunk.export(chunk_path, format="wav")
                
                print(f"Transcribing chunk {i+1}/{len(chunks)}...")
                result = model.transcribe(chunk_path)
                full_transcript.extend(result['segments'])
                
                os.remove(chunk_path)
                
                progress = int((i + 1) / len(chunks) * 100)
                self.progress.emit(progress)

            formatted_transcript = self.format_transcript(full_transcript)
            self.finished.emit(formatted_transcript)
            
        except Exception as e:
            error_message = f"Error during transcription: {str(e)}"
            print(error_message)
            self.finished.emit(error_message)

    def split_audio(self, audio):
        chunks = []
        for i in range(0, len(audio), self.chunk_duration):
            chunks.append(audio[i:i+self.chunk_duration])
        return chunks

    def format_transcript(self, transcript_segments):
        formatted_lines = []
        current_speaker = 0
        for segment in transcript_segments:
            if not formatted_lines or self.is_new_speaker(segment, transcript_segments[transcript_segments.index(segment)-1]):
                current_speaker = (current_speaker % 5) + 1  # Cycle through speakers 1-5
            formatted_lines.append(f"Speaker {current_speaker}: {segment['text'].strip()}")
        return '\n\n'.join(formatted_lines)

    def is_new_speaker(self, current_segment, previous_segment):
        # Simple heuristic: if there's a pause of more than 1 second, assume it's a new speaker
        return current_segment['start'] - previous_segment['end'] > 1.0