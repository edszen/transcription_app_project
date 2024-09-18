import sys
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, 
                             QFileDialog, QMessageBox, QProgressBar, QHBoxLayout)
from PyQt5.QtCore import pyqtSlot, QTimer, QSettings
from transcribe import Transcriber
from settings import SettingsDialog
from help_dialog import HelpDialog
import re
from encryption_utils import EncryptionUtils
import logging

import warnings
import re

def filter_warnings(message, category, filename, lineno, file=None, line=None):
    if category == UserWarning:
        if re.match(r"The MPEG_LAYER_III subtype is unknown to TorchAudio", str(message)):
            return None  # Suppress the warning
    return True  # Show other warnings

warnings.filterwarnings("always", category=UserWarning)
warnings.showwarning = filter_warnings

class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("YourCompany", "AudioTranscriptionApp")
        self.encryption_utils = EncryptionUtils()
        self.init_ui()
        self.transcribing_timer = QTimer()
        self.transcribing_timer.timeout.connect(self.update_transcribing_message)
        self.dot_count = 0
        self.setup_logging()
        self.transcriber = None
        
    def closeEvent(self, event):
        if self.transcriber:
            self.transcriber.cancel_transcription()
        event.accept()

    def setup_logging(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def init_ui(self):
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        
        self.upload_button = QPushButton('Upload and Transcribe Audio')
        self.upload_button.clicked.connect(self.upload_and_transcribe)
        self.cancel_button = QPushButton('Cancel Transcription')
        self.cancel_button.clicked.connect(self.cancel_transcription)
        self.cancel_button.setEnabled(False)
        
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.cancel_button)
        
        self.settings_button = QPushButton('Settings')
        self.settings_button.clicked.connect(self.open_settings)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.diarization_progress_bar = QProgressBar()
        self.diarization_progress_bar.setVisible(False)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.help_button = QPushButton('Help')
        self.help_button.clicked.connect(self.show_help)
        
        layout.addLayout(button_layout)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.diarization_progress_bar)
        layout.addWidget(self.text_area)
        layout.addWidget(self.help_button)
        
        self.setLayout(layout)
        self.setWindowTitle('Audio Transcription App')
        self.setGeometry(300, 300, 600, 400)

    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.logger.info("Settings updated")

    def upload_and_transcribe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Upload Audio', '', 'Audio Files (*.mp3 *.wav *.m4a)')
        if file_path:
            self.text_area.setText("Initializing transcription...")
            self.start_transcribing_animation()
            self.upload_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.diarization_progress_bar.setVisible(False)
            self.diarization_progress_bar.setValue(0)
            
            use_diarization = self.settings.value("use_diarization", False, type=bool)
            api_key_encrypted = self.settings.value("huggingface_api_key", "")
            api_key = self.encryption_utils.decrypt(api_key_encrypted) if api_key_encrypted else ""
            
            self.transcriber = Transcriber()
            self.transcriber.finished.connect(self.update_transcription)
            self.transcriber.progress.connect(self.update_progress)
            self.transcriber.error.connect(self.show_error)
            self.transcriber.diarization_progress.connect(self.update_diarization_progress)
            
            self.logger.info(f"Starting transcription with diarization: {use_diarization}")
            self.thread = threading.Thread(target=self.transcriber.transcribe, 
                                           args=(file_path, use_diarization, api_key))
            self.thread.start()
        else:
            QMessageBox.warning(self, 'Error', 'No file selected')

    def cancel_transcription(self):
        self.logger.info("Cancellation requested by user")
        if self.transcriber:
            self.transcriber.cancel_transcription()
        self.cancel_button.setEnabled(False)
        self.text_area.setText("Cancelling transcription...")
        self.transcribing_timer.stop()
        self.upload_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.diarization_progress_bar.setVisible(False)

    def start_transcribing_animation(self):
        self.dot_count = 0
        self.transcribing_timer.start(500)  # Update every 500 ms

    def update_transcribing_message(self):
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.text_area.setText(f"Transcribing{dots}")

    @pyqtSlot(str)
    def update_transcription(self, text):
        self.transcribing_timer.stop()
        formatted_text = self.convert_to_html(text)
        self.text_area.setHtml(formatted_text)
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.diarization_progress_bar.setVisible(False)
        self.logger.info("Transcription and processing completed and displayed")
        
        # Add a "Save Transcript" button
        if not hasattr(self, 'save_button'):
            self.save_button = QPushButton("Save Transcript")
            self.save_button.clicked.connect(lambda: self.save_transcript())
            self.layout().addWidget(self.save_button)
        else:
            self.save_button.setVisible(True)
        
    @pyqtSlot(str)    
    def save_transcript(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Transcript", "", "Text Files (*.txt)")
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.text_area.toPlainText())
            QMessageBox.information(self, "Success", "Transcript saved successfully!")

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        if value == 25:
            self.text_area.setText("Transcribing audio...")
        elif value == 50:
            if self.settings.value("use_diarization", False, type=bool):
                self.text_area.setText("Transcription complete. Starting diarization...")
                self.diarization_progress_bar.setVisible(True)
            else:
                self.text_area.setText("Transcription complete. Formatting results...")
        elif value == 75:
            self.text_area.setText("Aligning transcription with speaker segments...")
        elif value == 100:
            self.text_area.setText("Processing complete. Preparing final transcript...")

    @pyqtSlot(float)
    def update_diarization_progress(self, value):
        self.diarization_progress_bar.setValue(int(value))

    @pyqtSlot(str)
    def show_error(self, error_message):
        self.transcribing_timer.stop()
        self.logger.error(f"Transcription error: {error_message}")
        detailed_message = f"An error occurred during transcription:\n\n{error_message}\n\nPlease check the application logs for more details."
        QMessageBox.critical(self, 'Error', detailed_message)
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.diarization_progress_bar.setVisible(False)
        self.text_area.setText("Transcription failed. Please try again.")

    def convert_to_html(self, text):
        css = """
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            p { margin-bottom: 10px; }
            .speaker { font-weight: bold; color: #2c3e50; }
            .timestamp { color: #7f8c8d; font-size: 0.9em; }
            .content { margin-left: 20px; }
        </style>
        """
        
        lines = text.split('\n')
        formatted_lines = []
        pattern = re.compile(r'^([\d.]+)\s*-\s*([\d.]+)\s*\|\s*(Speaker\s*\d+):\s*(.*)')

        for line in lines:
            line = line.strip()
            match = pattern.match(line)
            if match:
                start, end, speaker, content = match.groups()
                formatted_lines.append(f'<p><span class="timestamp">{start} - {end}</span> <span class="speaker">{speaker}:</span><br><span class="content">{content}</span></p>')
            else:
                formatted_lines.append(f'<p>{line}</p>')

        html_content = ''.join(formatted_lines)
        return f"{css}<body>{html_content}</body>"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TranscriptionApp()
    ex.show()
    sys.exit(app.exec_())