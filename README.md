# Audio Transcription Application

This is an audio transcription application for **MacOS** and **Windows**. It uses **Python**, **PyQt5** for the UI, and **Faster Whisper** for audio transcription. The application allows users to upload audio files, transcribe them, and view transcripts with speaker diarization.

## Features

- **Transcription with Faster Whisper**: The app utilizes the Faster Whisper model for efficient audio transcription.
- **PyQt5-based UI**: Users can upload audio files and view transcripts in a desktop-friendly user interface.
- **Speaker Diarization**: Implements WhisperX for speaker diarization.
- **Voice Activity Detection (VAD)**: Uses Pyannote.audio for VAD, with a fallback to energy-based VAD.
- **Chunked Processing**: Handles long audio files by processing them in chunks.
- **Robust Error Handling**: Gracefully handles errors during the transcription process.

## Current Status
- The user interface is functional and allows file uploads via a button.
- Transcription is performed in chunks for efficient processing of longer files.
- Speaker diarization is integrated using WhisperX.
- VAD is implemented with Pyannote.audio, falling back to energy-based VAD if needed.
- Improved error handling for diarization failures, with informative feedback to the user.
- The application continues to provide a transcript even if diarization fails for some parts of the audio.
- The user interface now features a sleek sidebar for improved navigation and functionality
- Session management allows users to create, open, and save transcription sessions

## Recent Changes
- Refactored the codebase for better modularity:
  - Separated core functionality into `src/core/` directory.
  - Moved utility functions to `src/utils/` directory.
  - Reorganized UI-related code in `src/ui/` directory.
- Improved chunking system for handling longer audio files.
- Enhanced integration of diarization with the chunking system.

## Recent UI Improvements

- Implemented a modern sidebar for easy navigation
- Added session management features (New Session, Open Session, Save Session)
- Improved overall layout and styling for better user experience
- Integrated Settings and Help sections for easier configuration and support

## How to Install Dependencies

1. Ensure you have Python 3.7+ installed.
2. Clone this repository:
git clone https://github.com/edszen/audio-transcription-app.git
cd audio-transcription-app
3. Create a virtual environment:
python -m venv venv
4. Activate the virtual environment:
- On Windows: `venv\Scripts\activate`
- On macOS and Linux: `source venv/bin/activate`
5. Install the required dependencies:
pip install -r requirements.txt
## How to Run
1. Ensure your virtual environment is activated.
2. Run the application:
python src/main.py
## Hugging Face API Key Setup

To use Pyannote VAD, you need to set up a Hugging Face API key:

1. Visit [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) to create an API token.
2. Accept the user conditions for 'pyannote/voice-activity-detection' at [https://huggingface.co/pyannote/voice-activity-detection](https://huggingface.co/pyannote/voice-activity-detection).
3. In the application, go to Settings and enter your API key in the designated field.



## To-Do

1. **Add Timestamps**:
   - Display timestamps alongside the transcribed text indicating when each section was spoken.
   
2. **Improve Speaker Recognition**:
   - Enhance the current speaker differentiation system for more accurate results.
   - Implement a fallback mechanism to handle diarization failures more gracefully.

3. **Summarization**:
   - Provide a concise summary of the entire transcription or specific sections for quick reference.
   
4. **Keyword Detection**:
   - Automatically detect and highlight key phrases or topics in the transcription for easier navigation.
   - Implement user-defined keyword detection.

5. **AI Chat Extension**:
   - Integrate an AI-powered chat system for transcript-based Q&A.
   
6. **Security Measures**:
   - Ensure local processing of audio files for confidentiality.

7. **Improve UI**:
   - Add buttons for accessing timestamps, improved speaker recognition, keyword detection.
   - AI chat interface.
   - Refine the layout for better usability and visual appeal.

8. **Testing and Debugging**:
   - Thoroughly test with various audio formats and scenarios.
   - Debug any issues that arise during testing.

9. **Documentation**:
   - Update the README file to include instructions on how to run the application and any additional information needed.

10. **Ensure long audio files are transcribed**:
    - Implement a mechanism to handle long audio files by breaking them into smaller chunks and transcribing them separately.
    - Maybe use pydub to split the audio file into smaller chunks and then use whisper to transcribe each chunk.

11. **Add a progress bar**:
    - Implement a progress bar to show the progress of the transcription process.
    - Show percentage next to the progress bar.
    - Maybe add the 3 dots to indicate that the transcription is still in progress in the text area. e.g. "Transcribing audio file... Please wait..." with the 3 dots at the end counting up to 3 and then resetting to 0.

13. **Add settings menu**:
    - Implement a settings menu for configuration options (e.g., Whisper model selection, API key setup).
    - Add options to edit speaker names, keywords, and formatting preferences.

14. **Error Handling**:
    - ✓ Implement robust error handling for various scenarios, including file upload errors, transcription errors, and UI errors.
    - ✓ Provide clear error messages to users.
    - Add a button to retry the transcription in case of an error.
    - Add a button to cancel the transcription in case of an error.

15. **Add functionality to let users input and store their own tokens securely in app for speech diarization**:
    - Add a button to open a dialog box to input and store the tokens securely in app.

16. **Add languages recognition**:
    - Add a button to open a dialog box to input and store the languages to be recognized in app.
    - Make the transcript recognize the languages and display them in the transcript.

17. **Deployment**:
    - Package the application for distribution, making it easy for users to install and run.
    - Provide clear instructions for installation and usage.

18. **Privacy Policy**:
    - Include a privacy policy that outlines how user data is handled and stored.
    - Ensure compliance with relevant data protection regulations.

## How to Run

1. Ensure you have Python installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Activate the virtual environment:
   ```bash
   source venv/bin/activate # On Unix or MacOS
   venv\Scripts\activate # On Windows
   ```
4. Run the application:
   ```bash
   python main.py
   ```

### Hugging Face API Key Setup

To use Pyannote VAD, you need to set up a Hugging Face API key:

1. Visit [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) to create an API token.
2. Accept the user conditions for 'pyannote/voice-activity-detection' at [https://huggingface.co/pyannote/voice-activity-detection](https://huggingface.co/pyannote/voice-activity-detection).
3. In the application, go to Settings and enter your API key in the designated field.

## How to Run

Run the application:
```bash
python run.py
```

**Troubleshooting**
If you encounter issues:

Verify you have the latest version of the app.
Check your Hugging Face API key in the settings.
Ensure you've accepted the necessary model licenses on Hugging Face.
Note that if Pyannote VAD fails, the app will use energy-based VAD as a fallback.

For further assistance, please refer to the in-app error messages or contact support.

## Contributing

We welcome contributions! Please see our Contributing Guidelines for more details.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Privacy Policy

GatherScribe prioritizes user privacy. All audio processing is done locally on your machine. We do not collect or store any user data or transcribed content. For more details, please see our full Privacy Policy.