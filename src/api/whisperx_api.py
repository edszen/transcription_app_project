import whisperx

def load_whisperx_audio(file_path):
    return whisperx.load_audio(file_path)

def load_audio(file_path):
    return whisperx.load_audio(file_path)

def load_align_model(language_code, device):
    return whisperx.load_align_model(language_code=language_code, device=device)

def align(segments, model, metadata, audio):
    return whisperx.align(segments, model, metadata, audio, device=model.device)

def assign_word_speakers(diarize_segments, transcript):
    return whisperx.assign_word_speakers(diarize_segments, transcript)