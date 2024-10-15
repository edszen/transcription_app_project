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
from src.ui.chat.transcription_widget import TranscriptionWidget

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
        self.raw_text = "" 
        self.total_chunks = 0
        self.processed_chunks = 0       

    def setup_logging(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def init_ui(self):
        main_layout = QHBoxLayout()
        
        # Left side (Transcription)
        self.transcription_widget = TranscriptionWidget(self.settings)
        
        # Right side (Chat)
        self.chat_widget = ChatWidget()
        self.chat_widget.new_question.connect(self.ask_chatgpt)
        
        # Create a splitter for resizable panels
        splitter = QSplitter()
        splitter.addWidget(self.transcription_widget)
        splitter.addWidget(self.chat_widget)
        
        main_layout.addWidget(splitter)
        
        self.setLayout(main_layout)
        self.setWindowTitle('GatherScribe')
        self.setGeometry(100, 100, 1200, 800)

            
    def ask_chatgpt(self, question):
        transcript = self.text_area.toPlainText()
        response = self.chatgpt.answer_question(transcript, question)
        self.chat_widget.add_response(response)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TranscriptionApp()
    ex.show()
    sys.exit(app.exec_())