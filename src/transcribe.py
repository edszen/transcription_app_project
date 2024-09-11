import whisper

def transcribe_audio(file_path):
    print("Loading Whisper model...")
    model = whisper.load_model("base")
    print("Model loaded successfully!") 
    
    try:
        print(f"Transcribing {file_path}...") # Log the start of the transcription process
        result = model.transcribe(file_path)
        print(f"Transcription completed.") 
        return result['text'] # Return the transcribed text
    except Exception as e:
        print(f"Error during transcription: {e}") # Log the error
        return f"Error during transcription: {e}"