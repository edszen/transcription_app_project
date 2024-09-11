from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from transcribe import transcribe_audio


class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__() # Call parent class (QWidget) constructor
        self.init_ui() # Initialize the UI
        
    # Set up UI elements
    def init_ui(self):
        # Set up layout for the widgets (buttons, labels)
        layout = QVBoxLayout()
        
        # Create upload audio button and connect it to upload_file method
        self.upload_button = QPushButton('Upload Audio')
        self.upload_button.clicked.connect(self.upload_file)
        
        # Create a label that will display the transcribed text
        self.transcription_label = QLabel('Transcribed Text:')
        
        # Add button and label to layout
        layout.addWidget(self.upload_button)
        layout.addWidget(self.transcription_label)
        
        # Set layout for the window, window title, and show the window
        self.setLayout(layout)
        self.setWindowTitle('Audio Transcription App')
        self.show()
        
    # Function to upload audio file    
    def upload_file(self):
        # Open file dialog to select audio file
        file_path, _ = QFileDialog.getOpenFileName(self, 'Upload Audio', '', 'Audio Files (*.mp3 *.wav *.m4a)')        
        # Check if file path is valid
        if file_path:
            # Transcribe audio file
            transcription = transcribe_audio(file_path)
            # Display transcribed text
            self.transcription_label.setText(f"Transcribed Text: {transcription}")
        else:
            # Display error message if file path is invalid
            QMessageBox.warning(self, 'No File selected', 'Please select a valid audio file.')