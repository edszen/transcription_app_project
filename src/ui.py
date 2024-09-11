import threading
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from PyQt5.QtCore import QMetaObject, Qt, QTimer
from transcribe import transcribe_audio

def update_ui(self, transcription):
    self.transcription_label.setText(f"Transcribed Text: {transcription}")

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
        
        # Create a QTextEdit for displaying the transcription
        self.transcription_text = QTextEdit()
        self.transcription_text.setReadOnly(True)
        
        # Add button, label, and text edit to layout
        layout.addWidget(self.upload_button)
        layout.addWidget(self.transcription_label)
        layout.addWidget(self.transcription_text)
        
        # Set layout for the window, window title, and show the window
        self.setLayout(layout)
        self.setWindowTitle('Audio Transcription App')
        self.show()
        
    # Function to upload audio file    
    def upload_file(self):

def update_ui(self, transcription):
    self.transcription_text.setText(transcription)
        # Open file dialog to select audio file
        file_path, _ = QFileDialog.getOpenFileName(self, 'Upload Audio', '', 'Audio Files (*.mp3 *.wav *.m4a)')        
        # Check if file path is valid
        if file_path:
            # Transcribe audio file
            threading.Thread(target=self.run_transcription, args=(file_path,)).start()
        else:
            # Display error if no file is selected
            QMessageBox.warning(self, 'Error', 'No file selected')
    
    # Function that runs transcription in a separate thread
    def run_transcription(self, file_path):
        try:
            # Transcribe audio file
            transcription = transcribe_audio(file_path)
            
            # Log the transcription result to the console
            print(f"Transcription: {transcription}")
            
            # Use QTimer to update the UI in a separate thread
            QTimer.singleShot(0, lambda: self.update_ui(transcription))
            
            # Update the UI safely on the main thread
            #QMetaObject.invokeMethod(self.transcription_label, 'setText', Qt.QueuedConnection, f"Transcribed Text: {transcription}")
            
        except Exception as e:
            # Display error if issue occurs
            QMessageBox.critical(self, 'Error', f"Error during transcription: {e}")
    def update_ui(self, transcription):
        self.transcription_label.setText(f"Transcribed Text: {transcription}")