import threading
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSlot, QTimer
from transcribe import Transcriber
import re  # Importing re for handling regular expressions

class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """
        Initializes the user interface, including the upload button and text area for displaying the transcription.
        """
        layout = QVBoxLayout()

        # Upload button for selecting audio file
        self.upload_button = QPushButton('Upload and Transcribe Audio')
        self.upload_button.clicked.connect(self.upload_and_transcribe)

        # Text area for showing the transcription
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)  # Read-only to prevent user edits

        # Adding widgets to the layout
        layout.addWidget(self.upload_button)
        layout.addWidget(self.text_area)

        # Set the layout and window properties
        self.setLayout(layout)
        self.setWindowTitle('Audio Transcription App')
        self.setGeometry(300, 300, 400, 300)

    def upload_and_transcribe(self):
        """
        Opens a file dialog to select an audio file, disables the button during transcription,
        and starts the transcription in a separate thread.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, 'Upload Audio', '', 'Audio Files (*.mp3 *.wav *.m4a)')
        if file_path:
            print(f"File selected: {file_path}")  # Debug print
            self.text_area.setText("Transcribing... Please wait.")
            self.upload_button.setEnabled(False)

            # Create Transcriber instance and connect its signal
            self.transcriber = Transcriber()
            self.transcriber.finished.connect(self.update_transcription)
            
            # Start transcription in a separate thread
            print("Starting transcription thread")  # Debug print
            self.thread = threading.Thread(target=self.transcriber.transcribe, args=(file_path,))
            self.thread.start()
        else:
            QMessageBox.warning(self, 'Error', 'No file selected')

    @pyqtSlot(str)
    def update_transcription(self, text):
        """
        Receives the transcription text from the transcriber and updates the UI.
        This method runs in the main thread.
        """
        print(f"Received transcription: {text[:100]}...")  # Debug print
        QTimer.singleShot(0, lambda: self.set_text(text))

    def set_text(self, text):
        """
        Updates the QTextEdit widget with the formatted transcript.
        """
        print("Updating UI")  # Debug print
        
        # Convert plain text to HTML for more control over the formatting
        formatted_text = self.convert_to_html(text)
        
        # Set the formatted HTML text in the QTextEdit widget
        self.text_area.setHtml(formatted_text)
        
        # Re-enable the upload button after transcription
        self.upload_button.setEnabled(True)
        print("UI update complete")  # Debug print

    def convert_to_html(self, text):
        """
        Converts plain transcript text into HTML for display in QTextEdit.
        This handles bold speaker tags, extra line breaks between speakers, and better spacing.
        
        Parameters:
            text (str): The plain text transcript.
        
        Returns:
            (str): The formatted HTML string.
        """
        # Debugging: Print the raw text before formatting
        print(f"Raw transcript: {text[:200]}...")

        # Split the transcript into lines
        lines = text.split('\n')
        
        # Initialize an empty list to hold formatted lines
        formatted_lines = []
        
        # Regular expression to detect speaker lines like "Speaker 1:", "Speaker A:", etc.
        speaker_pattern = re.compile(r'^(Speaker\s\d+|Speaker\s[A-Z]):')

        # Iterate over each line in the transcript
        for line in lines:
            line = line.strip()  # Trim extra spaces
            
            # If the line starts with "Speaker X:" where X is a number or letter
            if speaker_pattern.match(line):
                # Bold the speaker name and add a break for better visual separation
                formatted_lines.append(f'<b>{line}</b><br><br>')
            else:
                # Add regular lines with single line breaks
                formatted_lines.append(f'{line}<br>')
        
        # Join the formatted lines into a single string
        html_text = ''.join(formatted_lines)
        
        # Debugging: Print the HTML to check the formatting
        print(f"Formatted HTML: {html_text[:200]}...")

        return html_text  # Ensure correct indentation here
