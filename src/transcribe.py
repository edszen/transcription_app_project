import whisper
from PyQt5.QtCore import QObject, pyqtSignal

class Transcriber(QObject):
    finished = pyqtSignal(str)

    def transcribe(self, file_path):
        try:
            print("Loading Whisper model...")
            model = whisper.load_model("base")
            print("Model loaded successfully!")
            
            print(f"Transcribing {file_path}...")
            result = model.transcribe(file_path)
            print("Transcription completed.")
            
            print(f"Emitting result: {result['text'][:100]}...")  # Debug print
            self.finished.emit(result['text'])
        except Exception as e:
            error_message = f"Error during transcription: {str(e)}"
            print(error_message)
            self.finished.emit(error_message)