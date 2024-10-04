import numpy as np
import scipy.io.wavfile as wavfile
import os

# Get the current working directory
current_dir = os.getcwd()
print(f"Current working directory: {current_dir}")

# Create a directory for test files if it doesn't exist
test_files_dir = os.path.join(current_dir, 'tests', 'test_files')
os.makedirs(test_files_dir, exist_ok=True)
print(f"Created directory: {test_files_dir}")

# Generate a simple sine wave
sample_rate = 44100
duration = 3  # 3 seconds
t = np.linspace(0, duration, sample_rate * duration, False)
audio = np.sin(440 * 2 * np.pi * t)  # 440 Hz sine wave

# Normalize the audio
audio = (audio * 32767).astype(np.int16)

# Save the audio file
file_path = os.path.join(test_files_dir, 'sample.wav')
wavfile.write(file_path, sample_rate, audio)

print(f"Sample audio file created at: {file_path}")
print(f"File exists: {os.path.exists(file_path)}")