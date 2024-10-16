from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTextEdit, 
                             QProgressBar, QHBoxLayout,QFileDialog, QMessageBox)
from PyQt5.QtCore import pyqtSlot, QSettings, QTimer
from src.core.transcribe import Transcriber

class TranscriptionWidget(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.transcriber = None
        self.init_ui()
        self.dot_count = 0
        self.transcribing_timer = QTimer()
        self.transcribing_timer.timeout.connect(self.update_transcribing_message)

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Cancel button
        self.cancel_button = QPushButton('Cancel Transcription')
        self.cancel_button.clicked.connect(self.cancel_transcription)
        self.cancel_button.setEnabled(False)
        layout.addWidget(self.cancel_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Transcription text area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        
        self.setLayout(layout)

    def upload_and_transcribe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Upload Audio', '', 'Audio Files (*.mp3 *.wav *.m4a *.ogg *.mp4);;All Files (*)')
        if file_path:
            self.start_transcription(file_path)

    def start_transcription(self, file_path):
        self.text_area.setText("Initializing transcription...")
        self.cancel_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        use_diarization = self.settings.value("use_diarization", False, type=bool)
        encrypted_api_key = self.settings.value("huggingface_api_key", "")
        
        self.transcriber = Transcriber()
        self.transcriber.finished.connect(self.update_transcription)
        self.transcriber.progress.connect(self.update_progress)
        self.transcriber.error.connect(self.show_error)
        self.transcriber.status_updated.connect(self.update_status)
        
        self.transcriber.transcribe(file_path, use_diarization, encrypted_api_key)

    def cancel_transcription(self):
        if self.transcriber:
            self.transcriber.cancel_transcription()
        self.cancel_button.setEnabled(False)
        self.text_area.setText("Cancelling transcription...")
        self.progress_bar.setVisible(False)

    @pyqtSlot(str)
    def update_transcription(self, text):
        formatted_text = self.format_transcript(text)
        self.text_area.setHtml(formatted_text)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)

    def format_transcript(self, text):
        lines = text.split('\n')
        formatted_lines = []
        for line in lines:
            parts = line.split('|', 1)
            if len(parts) == 2:
                timestamp, content = parts
                speaker, speech = content.split(':', 1)
                formatted_lines.append(f"{timestamp} | <b>{speaker}</b>:{speech}")
            else:
                formatted_lines.append(line)
        return '<br>'.join(formatted_lines)

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(str)
    def update_status(self, status):
        self.text_area.setText(status)
        
    def update_transcribing_message(self):
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.text_area.setText(f"Transcribing{dots}")
        
    @pyqtSlot(str)
    def show_error(self, error_message):
        QMessageBox.critical(self, 'Error', error_message)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.text_area.setText("Transcription failed. Please try again.")

    def get_transcript(self):
        return self.text_area.toPlainText()