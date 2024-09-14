import threading
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTextEdit, 
                             QFileDialog, QMessageBox, QProgressBar)
from PyQt5.QtCore import pyqtSlot, QTimer, QSettings
from transcribe import Transcriber
from settings import SettingsDialog
from help_dialog import HelpDialog
import re

class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("YourCompany", "AudioTranscriptionApp")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.upload_button = QPushButton('Upload and Transcribe Audio')
        self.upload_button.clicked.connect(self.upload_and_transcribe)
        self.settings_button = QPushButton('Settings')
        self.settings_button.clicked.connect(self.open_settings)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.upload_button)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.text_area)
        self.setLayout(layout)
        self.setWindowTitle('Audio Transcription App')
        self.setGeometry(300, 300, 600, 400)
        self.help_button = QPushButton('Help')
        self.help_button.clicked.connect(self.show_help)
        layout.addWidget(self.help_button)

    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def upload_and_transcribe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Upload Audio', '', 'Audio Files (*.mp3 *.wav *.m4a)')
        if file_path:
            self.text_area.setText("Transcribing... Please wait.")
            self.upload_button.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.transcriber = Transcriber()
            self.transcriber.finished.connect(self.update_transcription)
            self.transcriber.progress.connect(self.update_progress)
            
            use_diarization = self.settings.value("use_diarization", False, type=bool)
            api_key = self.settings.value("huggingface_api_key", "")
            
            # Decrypt the API key TESTING
            api_key_encrypted = self.settings.value("huggingface_api_key", "")
            api_key = self.encryption_utils.decrypt(api_key_encrypted)  # Decrypt the token
            
            # Now use the decrypted API key
            use_diarization = self.settings.value("use_diarization", False, type=bool)
            
            self.thread = threading.Thread(target=self.transcriber.transcribe, 
                                           args=(file_path, use_diarization, api_key))
            self.thread.start()
        else:
            QMessageBox.warning(self, 'Error', 'No file selected')

    @pyqtSlot(str)
    def update_transcription(self, text):
        QTimer.singleShot(0, lambda: self.set_text(text))

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def set_text(self, text):
        formatted_text = self.convert_to_html(text)
        self.text_area.setHtml(formatted_text)
        self.upload_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def convert_to_html(self, text):
        css = """
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            p { margin-bottom: 10px; }
            .speaker { font-weight: bold; color: #2c3e50; }
            .content { margin-left: 20px; }
        </style>
        """
        
        lines = text.split('\n')
        formatted_lines = []
        speaker_pattern = re.compile(r'^(Speaker\s\d+):\s*(.*)')

        for line in lines:
            line = line.strip()
            match = speaker_pattern.match(line)
            if match:
                speaker, content = match.groups()
                formatted_lines.append(f'<p><span class="speaker">{speaker}:</span><br><span class="content">{content}</span></p>')
            else:
                formatted_lines.append(f'<p>{line}</p>')

        html_content = ''.join(formatted_lines)
        return f"{css}<body>{html_content}</body>"