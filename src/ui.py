import sys
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, 
                             QFileDialog, QMessageBox, QProgressBar, QHBoxLayout, QDialog,
                             QLabel, QLineEdit, QDialogButtonBox, QCheckBox, QComboBox)
from PyQt5.QtCore import pyqtSlot, QTimer, QSettings, QObject
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
        self.settings = QSettings("YourCompany", "AudioTranscriptionApp")
        self.encryption_utils = EncryptionUtils()
        self.init_ui()
        self.transcribing_timer = QTimer()
        self.transcribing_timer.timeout.connect(self.update_transcribing_message)
        self.dot_count = 0
        self.setup_logging()
        self.transcriber = None
        self.raw_text = ""        

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
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.help_button = QPushButton('Help')
        self.help_button.clicked.connect(self.show_help)
        
        self.edit_speakers_button = QPushButton('Edit Speakers')
        self.edit_speakers_button.clicked.connect(self.edit_speakers)
        self.edit_speakers_button.setEnabled(False) # Disable the button initially
        layout.addWidget(self.edit_speakers_button)
        
        self.save_button = QPushButton("Save Transcript")
        self.save_button.clicked.connect(self.save_transcript)
        self.save_button.setVisible(False)
        
        layout.addLayout(button_layout)
        layout.addWidget(self.settings_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.text_area)
        layout.addWidget(self.edit_speakers_button)
        layout.addWidget(self.save_button)
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
        file_path, _ = QFileDialog.getOpenFileName(self, 'Upload Audio', '', 'Audio Files (*.mp3 *.wav *.m4a *.ogg *.mp4);;All Files (*)')
        if file_path:
            self.text_area.setText("Initializing transcription...")
            self.start_transcribing_animation()
            self.upload_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            use_diarization = self.settings.value("use_diarization", False, type=bool)
            api_key_encrypted = self.settings.value("huggingface_api_key", "")
            api_key = self.encryption_utils.decrypt(api_key_encrypted) if api_key_encrypted else ""
            vad_method = self.settings.value("vad_method", "pyannote")
            
            self.transcriber = Transcriber()
            self.transcriber.finished.connect(self.update_transcription)
            self.transcriber.progress.connect(self.update_progress)
            self.transcriber.error.connect(self.show_error)
            self.transcriber.status_updated.connect(self.update_status)
            
            self.logger.info(f"Starting transcription with diarization: {use_diarization}, VAD method: {vad_method}")
            self.thread = threading.Thread(target=self.transcriber.transcribe, 
                                        args=(file_path, use_diarization, api_key, vad_method))
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

    def start_transcribing_animation(self):
        self.dot_count = 0
        self.transcribing_timer.start(500)  # Update every 500 ms

    def update_transcribing_message(self):
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.text_area.setText(f"Transcribing{dots}")
        
    def identify_speakers(self):
        speaker_pattern = re.compile(r'Speaker (\d+)')
        speakers = set(speaker_pattern.findall(self.raw_text))
        
        dialog = SpeakerIdentificationDialog(len(speakers), self)
        if dialog.exec_():
            self.speaker_names = dialog.get_speaker_names()
            self.format_and_display_transcript()

    def edit_speakers(self):
        speaker_pattern = re.compile(r'Speaker (\w+)')
        speakers = set(speaker_pattern.findall(self.raw_text))
    
        dialog = SpeakerIdentificationDialog(len(speakers), self)
        if dialog.exec_():
            self.speaker_names = dialog.get_speaker_names()
            self.format_and_display_transcript()
            
    def format_and_display_transcript(self):
        formatted_text = self.raw_text
        for old_name, new_name in self.speaker_names.items():
            formatted_text = re.sub(f"{old_name}:", f"{new_name}:", formatted_text)
        
        formatted_text = self.convert_to_html(formatted_text)
        self.text_area.setHtml(formatted_text)

    @pyqtSlot(str)
    def update_transcription(self, text):
        self.transcribing_timer.stop()
        self.raw_text = text
        self.logger.info(f"Received transcription with length: {len(text)}")
        if not text:
            self.logger.warning("Received empty transcription")
            self.text_area.setText("No transcription available. The audio might be silent or not contain recognizable speech.")
        else:
            self.format_and_display_transcript()
        self.upload_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.edit_speakers_button.setEnabled(True)
        self.logger.info("Transcription and processing completed and displayed")
        
        self.save_button.setVisible(True)
            
    def save_transcript(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Transcript", "", "Text Files (*.txt)")
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.text_area.toPlainText())
            QMessageBox.information(self, "Success", "Transcript saved successfully!")
    
    @pyqtSlot(str)
    def update_status(self, status):
        self.text_area.setText(status)

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        if value == 20:
            self.text_area.setText("Applying Voice Activity Detection...")
        elif value == 40:
            self.text_area.setText("Transcribing speech segments...")
        elif value == 60:
            if self.settings.value("use_diarization", False, type=bool):
                self.text_area.setText("Transcription complete. Starting diarization...")
            else:
                self.text_area.setText("Transcription complete. Formatting results...")
        elif value == 80:
            self.text_area.setText("Aligning transcription with speaker segments...")
        elif value == 100:
            self.text_area.setText("Processing complete. Preparing final transcript...")

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

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("YourCompany", "AudioTranscriptionApp")
        self.encryption_utils = EncryptionUtils()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Diarization checkbox
        self.diarization_checkbox = QCheckBox("Enable Speaker Diarization")
        self.diarization_checkbox.setChecked(
            self.settings.value("use_diarization", False, type=bool)
        )
        layout.addWidget(self.diarization_checkbox)

        # VAD method selection
        vad_layout = QHBoxLayout()
        vad_layout.addWidget(QLabel("VAD Method:"))
        self.vad_combo = QComboBox()
        self.vad_combo.addItems(["No VAD", "Energy-based VAD", "Pyannote VAD"])
        current_vad = self.settings.value("vad_method", "pyannote")
        if current_vad == "none":
            self.vad_combo.setCurrentIndex(0)
        elif current_vad == "energy":
            self.vad_combo.setCurrentIndex(1)
        elif current_vad == "pyannote":
            self.vad_combo.setCurrentIndex(2)
        vad_layout.addWidget(self.vad_combo)
        layout.addLayout(vad_layout)

        # API Key input layout
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("Hugging Face API Key:"))
        self.api_key_input = QLineEdit()
        
        # Load and decrypt the API key if it exists
        encrypted_key = self.settings.value("huggingface_api_key", "")
        if encrypted_key:
            decrypted_key = self.encryption_utils.decrypt(encrypted_key)
            self.api_key_input.setText(decrypted_key)
        
        api_key_layout.addWidget(self.api_key_input)
        layout.addLayout(api_key_layout)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.setWindowTitle("Transcription Settings")

    def save_settings(self):
        # Save the checkbox state
        use_diarization = self.diarization_checkbox.isChecked()
        self.settings.setValue("use_diarization", use_diarization)

        # Save VAD method
        vad_index = self.vad_combo.currentIndex()
        if vad_index == 0:
            self.settings.setValue("vad_method", "none")
        elif vad_index == 1:
            self.settings.setValue("vad_method", "energy")
        elif vad_index == 2:
            self.settings.setValue("vad_method", "pyannote")

        # Encrypt and save the API key
        api_key = self.api_key_input.text()
        encrypted_key = self.encryption_utils.encrypt(api_key)
        self.settings.setValue("huggingface_api_key", encrypted_key)

        self.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    secure_delegate = SecureCodingDelegate()
    app.setProperty("NSApplicationDelegate", secure_delegate)
    ex = TranscriptionApp()
    app.setApplicationName("Audio Transcription App")
    ex.show()
    sys.exit(app.exec_())