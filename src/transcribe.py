import whisper

def transcribe_audio(file_path):
    model = whisper.load_model("base")
    try:
        result = model.transcribe(file_path)
        return result['text']
    except Exception as e:
        return f"Error during transcription: {e}"