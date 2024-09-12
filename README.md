# Audio Transcription Application

This is an audio transcription application for **MacOS** and **Windows**. It uses **Python**, **PyQt5** for the UI, and **Whisper** for audio transcription. The application allows users to upload audio files, transcribe them, and view transcripts.

## Features

- **Transcription with Whisper**: The app utilizes the Whisper model for audio transcription.
- **PyQt5-based UI**: Users can upload audio files and view transcripts in a desktop-friendly user interface.

## Current Status
The user interface is functional and allows file uploads via a button.
The transcription is performed in a separate thread to keep the UI responsive.
Transcript formatting with bold speaker names and proper line breaks is in progress and not yet fully implemented.

## To-Do

1. **Add Timestamps**:
   - Display timestamps alongside the transcribed text indicating when each section was spoken.
   
2. **Speaker Recognition**:
   - Automatically detect and label different speakers in the transcript (e.g., "Speaker 1", "Speaker 2").

3. **Summarization**:
   - Provide a concise summary of the entire transcription or specific sections for quick reference.
   
4. **Keyword Detection**:
   - Automatically detect and highlight key phrases or topics in the transcription for easier navigation.
   - Can be set up to detect specific keywords or phrases that are important and set by the user.

5. **AI Chat Extension**:
   - Integrate an AI-powered chat system that allows users to ask questions and get explanations or clarifications based on the transcription.
   
6. **Security Measures**:
   - Implement security measures to ensure that audio files containing confidential information are processed locally and not exposed to the web.

7. **Improve UI**:
   - Add new features to the UI, including buttons for accessing timestamps, speaker recognition, keyword detection, and an AI chat interface.
   - Refine the layout for better usability and visual appeal.

8. **Testing and Debugging**:
   - Thoroughly test the application to ensure it functions correctly and handles various audio formats and scenarios.
   - Debug any issues that arise during testing.

9. **Documentation**:
   - Update the README file to include instructions on how to run the application and any additional information needed.

10. **Ensure long audio files are transcribed**:
    - Implement a mechanism to handle long audio files by breaking them into smaller chunks and transcribing them separately.
    - Maybe use pydub to split the audio file into smaller chunks and then use whisper to transcribe each chunk.

11. **Add a progress bar**:
    - Implement a progress bar to show the progress of the transcription process.
    - Maybe add the 3 dots to indicate that the transcription is still in progress in the text area. e.g. "Transcribing audio file... Please wait..." with the 3 dots at the end counting up to 3 and then resetting to 0.

12. **Add a button to download the transcript**:
    - Add a button to download the transcript as a text file.

13. **Add settings menu**:
    - Add a settings menu to allow users to configure the application, such as selecting the Whisper model to use.
    - Configure your AI API key in the settings menu.
    - Add a button to open the settings menu.
    - Add section to edit speaker names, keywords, formatting, and more.

14. **Deployment**:
    - Package the application for distribution, making it easy for users to install and run.


## How to Run

1. Ensure you have Python installed.
2. Install the required dependencies:
   ```bash
   pip install PyQt5 whisper pydub

source venv/bin/activate # Activate the virtual environment
python main.py # Run the application
pip freeze > requirements.txt # Save the requirements to a file
To run your application:

Make sure you're in your project directory.
Activate your virtual environment if it's not already activated.
Run your main Python script, which is likely named main.py:
python main.py
This will start your application.