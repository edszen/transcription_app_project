import threading
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSlot, QTimer
from transcribe import Transcriber

class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.upload_button = QPushButton('Upload and Transcribe Audio')
        self.upload_button.clicked.connect(self.upload_and_transcribe)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)

        layout.addWidget(self.upload_button)
        layout.addWidget(self.text_area)

        self.setLayout(layout)
        self.setWindowTitle('Audio Transcription App')
        self.setGeometry(300, 300, 400, 300)

    def upload_and_transcribe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Upload Audio', '', 'Audio Files (*.mp3 *.wav *.m4a)')
        if file_path:
            print(f"File selected: {file_path}")  # Debug print
            self.text_area.setText("Transcribing... Please wait.")
            self.upload_button.setEnabled(False)

            self.transcriber = Transcriber()
            self.transcriber.finished.connect(self.update_transcription)
            
            print("Starting transcription thread")  # Debug print
            self.thread = threading.Thread(target=self.transcriber.transcribe, args=(file_path,))
            self.thread.start()
        else:
            QMessageBox.warning(self, 'Error', 'No file selected')

    @pyqtSlot(str)
    def update_transcription(self, text):
        print(f"Received transcription: {text[:100]}...")  # Debug print
        QTimer.singleShot(0, lambda: self.set_text(text))

    def set_text(self, text):
        print("Updating UI")  # Debug print
        self.text_area.setText(text)
        self.upload_button.setEnabled(True)
        print("UI update complete")  # Debug print