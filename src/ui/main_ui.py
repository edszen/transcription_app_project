import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
                             QSplitter)
from PyQt5.QtCore import QSettings
from src.ui.settings import SettingsDialog
from src.ui.help_dialog import HelpDialog
from utils.encryption import EncryptionUtils
import logging
import os
from src.api.openai_chat import ChatGPTIntegration
from src.ui.chat.chat_widget import ChatWidget
from src.ui.chat.transcription_widget import TranscriptionWidget

# Project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.speaker_names = {}
        self.settings = QSettings("SZ Apps", "GatherScribe")
        #self.encryption_utils = EncryptionUtils()
        self.setup_logging()
        self.chatgpt = ChatGPTIntegration()
        self.transcription_widget = TranscriptionWidget(self.settings)
        self.chat_widget = ChatWidget()
        self.init_ui()
        self.setup_connections()
        #self.raw_text = "" 
        #self.total_chunks = 0
        #self.processed_chunks = 0       

    def setup_logging(self):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Menu buttons
        menu_layout = QHBoxLayout()
        self.upload_button = QPushButton('Upload and Transcribe Audio')
        self.settings_button = QPushButton('Settings')
        self.help_button = QPushButton('Help')
        
        for button in [self.upload_button, self.settings_button, self.help_button]:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    color: white;
                    border: none;
                    padding: 8px;
                    margin: 3px;
                    border-radius: 4px;
                    font-size: 12px;
                    max-width: 200px;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
            """)
        
        menu_layout.addWidget(self.upload_button)
        menu_layout.addWidget(self.settings_button)
        menu_layout.addWidget(self.help_button)
        menu_layout.addStretch()
        
        main_layout.addLayout(menu_layout)
        
        # Maybe delete
        #self.chat_widget.new_question.connect(self.ask_chatgpt)
        
        # Create a splitter for resizable panels
        splitter = QSplitter()
        
        # Left side (Transcription)
        #self.transcription_widget = TranscriptionWidget(self.settings)
        splitter.addWidget(self.transcription_widget)
        # Right side (Chat)
        #self.chat_widget = ChatWidget()
        splitter.addWidget(self.chat_widget)
        
        main_layout.addWidget(splitter)
        
        #self.setLayout(main_layout)
        self.setWindowTitle('GatherScribe')
        #self.setGeometry(100, 100, 1200, 800)
        
        self.setLayout(main_layout)
        
        # Connect buttons
        self.upload_button.clicked.connect(self.transcription_widget.upload_and_transcribe)
        self.settings_button.clicked.connect(self.open_settings)
        self.help_button.clicked.connect(self.show_help)
        
    def update_theme(self, theme):
        if theme == "default":
            self.setStyleSheet("""
                QWidget {
                    background-color: #f0f0f0;
                    color: #333333;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #b0b0b0;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QLineEdit, QTextEdit {
                    background-color: white;
                    border: 1px solid #b0b0b0;
                    padding: 3px;
                }
            """)
        elif theme == "dark_midnight":
            self.setStyleSheet("""
                QWidget {
                    background-color: #1e1e2e;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #2d2d44;
                    border: 1px solid #3d3d5c;
                    padding: 5px;
                    border-radius: 3px;
                    color: #ffffff;
                }
                QPushButton:hover {
                    background-color: #3d3d5c;
                }
                QLineEdit, QTextEdit {
                    background-color: #2d2d44;
                    border: 1px solid #3d3d5c;
                    padding: 3px;
                    color: #ffffff;
                }
            """)
        
        # Update theme for child widgets
        self.transcription_widget.update_theme(theme)
        self.chat_widget.update_theme(theme)
        
    def setup_connections(self):
        self.chatgpt.response_received.connect(self.chat_widget.add_response)
        self.chatgpt.error_occurred.connect(self.chat_widget.add_response)
        self.chat_widget.new_question.connect(self.ask_chatgpt)

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.chatgpt.load_settings()

    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()
            
    def ask_chatgpt(self, question):
        transcript = self.transcription_widget.get_transcript()
        self.chatgpt.answer_question(transcript, question)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transcription_app = TranscriptionApp()
    transcription_app.show()
    sys.exit(app.exec_())