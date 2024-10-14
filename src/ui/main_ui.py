import sys
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, 
                             QFileDialog, QMessageBox, QProgressBar, QHBoxLayout, QDialog,
                             QLabel, QLineEdit, QDialogButtonBox, QCheckBox, QComboBox, QSplitter)
from PyQt5.QtCore import pyqtSlot, QTimer, QSettings, QObject
from src.ui.settings import SettingsDialog
from src.ui.help_dialog import HelpDialog
import re
from utils.encryption import EncryptionUtils
import logging
from src.core.transcribe import Transcriber
import os
from src.api.openai_chat import ChatGPTIntegration
from src import config
from src.ui.chat.chat_widget import ChatWidget

# Project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class SecureCodingDelegate(QObject):
    def applicationSupportsSecureRestorableState(self):
        return True

class SpeakerIdentificationDialog(QDialog):
    def __init__(self, speaker_count, parent=None):
        super().__init__(parent)
        self.speaker_count = speaker_count
        self.speaker_names = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        for i in range(self.speaker_count):
            hbox = QHBoxLayout()
            hbox.addWidget(QLabel(f"Speaker {i+1}:"))
            line_edit = QLineEdit()
            hbox.addWidget(line_edit)
            layout.addLayout(hbox)
            self.speaker_names[f"Speaker {i+1}"] = line_edit

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.setWindowTitle("Identify Speakers")

    def get_speaker_names(self):
        return {k: v.text() if v.text() else k for k, v in self.speaker_names.items()}

class SecureCodingDelegate(QObject):
    def applicationSupportsSecureRestorableState(self):
        return True

class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.speaker_names = {}
        self.settings = QSettings("SZ Apps", "GatherScribe")
        self.encryption_utils = EncryptionUtils()
        self.setup_logging()
        self.chatgpt = ChatGPTIntegration()
        self.init_ui()
        self.transcribing_timer = QTimer()
        self.transcribing_timer.timeout.connect(self.update_transcribing_message)
        self.dot_count = 0
        self.transcriber = None
        self.raw_text = "" 
        self.total_chunks = 0
        self.processed_chunks = 0       

    def setup_logging(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Left side (Transcription)
        left_layout = QVBoxLayout()
        
        # Transcription buttons
        transcription_layout = QHBoxLayout()
        self.upload_button = QPushButton('Upload and Transcribe Audio')
        self.upload_button.clicked.connect(self.upload_and_transcribe)
        self.cancel_button = QPushButton('Cancel Transcription')
        self.cancel_button.clicked.connect(self.cancel_transcription)
        self.cancel_button.setEnabled(False)
        transcription_layout.addWidget(self.upload_button)
        transcription_layout.addWidget(self.cancel_button)
        left_layout.addLayout(transcription_layout)
        
        # Settings and Help buttons
        button_layout = QHBoxLayout()
        self.settings_button = QPushButton('Settings')
        self.settings_button.clicked.connect(self.open_settings)
        self.help_button = QPushButton('Help')
        self.help_button.clicked.connect(self.show_help)
        button_layout.addWidget(self.settings_button)
        button_layout.addWidget(self.help_button)
        left_layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)
        
        # Transcription text area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        left_layout.addWidget(self.text_area)
        
        # Right side (Chat)
        self.chat_widget = ChatWidget()
        self.chat_widget.new_question.connect(self.ask_chatgpt)
        
        # Adding both sides to a splitter
        splitter = QSplitter()
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.chat_widget)
        
        main_layout.addWidget(splitter)
        
        self.setLayout(main_layout)
        self.setWindowTitle('GatherScribe')
        self.setGeometry(100, 100, 1200, 800)


    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.logger.info("Settings updated")
            self.chatgpt.load_settings()
            
    def ask_chatgpt(self, question):
        transcript = self.text_area.toPlainText()
        response = self.chatgpt.answer_question(transcript, question)
        self.chat_widget.add_response(response)

    def upload_and_transcribe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Upload Audio', '', 'Audio Files (*.mp3 *.wav *.m4a *.ogg *.mp4);;All Files (*)')
        if file_path:
            self.start_transcription(file_path)

    def start_transcription(self, file_path):
        self.text_area.setText("Initializing transcription...")
        self.upload_button.setEnabled(False)
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
        self.upload_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    @pyqtSlot(str)
    def update_transcription(self, text):
        self.text_area.setText(text)
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(str)
    def update_status(self, status):
        self.text_area.setText(status)

    @pyqtSlot(str)
    def show_error(self, error_message):
        self.transcribing_timer.stop()
        self.logger.error(f"Transcription error: {error_message}")
        detailed_message = f"An error occurred during transcription:\n\n{error_message}\n\nPlease check the application logs for more details."
        QMessageBox.critical(self, 'Error', detailed_message)
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.text_area.setText("Transcription failed. Please try again.")
        
    def update_transcribing_message(self):
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.text_area.setText(f"Transcribing{dots}")

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