import re
import whisper
import textwrap
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
            
            # Format the transcription
            transcript = result['text']
            formatted_transcript = self.format_transcript(transcript)
            
            # Emit the transcription result
            print(f"Emitting formatted result: {formatted_transcript[:100]}...")  # Debug print
            self.finished.emit(formatted_transcript)
            
        except Exception as e:
            error_message = f"Error during transcription: {str(e)}"
            print(error_message)
            self.finished.emit(error_message)
    
    def format_transcript(self, transcript, wrap_width=80):
        """
        Formats the transcript text by wrapping lines, adding spacing between paragraphs,
        and handling speaker turns and timestamps if included.
        """
        # Split the transcript by lines (in case it is a block of text)
        lines = transcript.split("\n")        
        
        # Initialize formatted output
        formatted_lines = []
        
        # Regex to detect speakers (assuming format like 'Speaker 1: ...')
        speaker_pattern = re.compile(r'^(Speaker\s\d+|Speaker\s[A-Z]):')
        
        # Iterate over each line
        for line in lines:
            line = line.strip()
            
            if not line:
                # Skip empty lines
                continue
            
            # Check if the line is a speaker turn
            if speaker_pattern.match(line):
                # Add a newline before the speaker turn
                formatted_lines.append("\n")
                # Wrap the line and append to formatted lines
                formatted_lines.append(textwrap.fill(line, width=wrap_width))
                formatted_lines.append("\n") # Extra line for clarity
            else:
                # Handle regular lines
                formatted_lines.append(textwrap.fill(line, width=wrap_width))
                
        # Join the formatted lines into a single string
        formatted_text = "\n".join(formatted_lines)
        
        return formatted_text