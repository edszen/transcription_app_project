## New main_ui.py to work with sidebar_menu and main_window.py

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
                             QSplitter, QStyle, QStyleOption, QTextEdit, QFileDialog, QMessageBox, QComboBox,
                             QDialogButtonBox, QCheckBox, QProgressBar, QLineEdit, QLabel)
from PyQt5.QtCore import QSettings, Qt, pyqtSlot, QObject
from PyQt5.QtGui import QPainter
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
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better integration
        
        # Menu buttons
        menu_layout = QHBoxLayout()
        menu_layout.setContentsMargins(10, 10, 10, 10)
        menu_layout.setSpacing(8)
        
        self.upload_button = QPushButton('Upload and Transcribe Audio')
        self.settings_button = QPushButton('Settings')
        self.help_button = QPushButton('Help')
        
        # Use native button styling
        button_style = """
            QPushButton {
                min-height: 24px;
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 13px;
            }
        """
        
        for button in [self.upload_button, self.settings_button, self.help_button]:
            button.setStyleSheet(button_style)
        
        menu_layout.addWidget(self.upload_button)
        menu_layout.addWidget(self.settings_button)
        menu_layout.addWidget(self.help_button)
        menu_layout.addStretch()
        
        main_layout.addLayout(menu_layout)
        
        # Maybe delete
        #self.chat_widget.new_question.connect(self.ask_chatgpt)
        
        # Create a splitter for resizable panels
        splitter = QSplitter()
        splitter.setHandleWidth(1)  # Thinner splitter handle
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e0e0e0;
            }
            QSplitter::handle:hover {
                background-color: #d0d0d0;
            }
        """)
        
        # Left side (Transcription)
        #self.transcription_widget = TranscriptionWidget(self.settings)
        splitter.addWidget(self.transcription_widget)
        # Right side (Chat)
        #self.chat_widget = ChatWidget()
        splitter.addWidget(self.chat_widget)
        
        main_layout.addWidget(splitter)
        
        #self.setLayout(main_layout)
        self.setLayout(main_layout)
        self.setWindowTitle('GatherScribe')
        #self.setGeometry(100, 100, 1200, 800)
        
        # Connect buttons
        self.upload_button.clicked.connect(self.transcription_widget.upload_and_transcribe)
        self.settings_button.clicked.connect(self.open_settings)
        self.help_button.clicked.connect(self.show_help)
        
    def update_theme(self, theme):
        if theme == "default":
            self.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    color: #333333;
                }
                QPushButton {
                    background-color: #f5f5f5;
                    border: 1px solid #e0e0e0;
                    color: #333333;
                }
                QPushButton:hover {
                    background-color: #e9e9e9;
                }
                QPushButton:pressed {
                    background-color: #d9d9d9;
                }
                QLineEdit, QTextEdit {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    padding: 4px;
                }
                QComboBox {
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    padding: 4px;
                    min-height: 24px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: url(:/down-arrow);
                    width: 12px;
                    height: 12px;
                }
            """)
        else:  # dark_midnight
            self.setStyleSheet("""
                QWidget {
                    background-color: #1a1b26;
                    color: #c0caf5;
                }
                QPushButton {
                    background-color: #24283b;
                    border: 1px solid #414868;
                    color: #c0caf5;
                }
                QPushButton:hover {
                    background-color: #2f354d;
                }
                QPushButton:pressed {
                    background-color: #3b4261;
                }
                QLineEdit, QTextEdit {
                    background-color: #1f2335;
                    border: 1px solid #414868;
                    color: #c0caf5;
                    padding: 4px;
                }
                QComboBox {
                    background-color: #1f2335;
                    border: 1px solid #414868;
                    color: #c0caf5;
                    padding: 4px;
                    min-height: 24px;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox::down-arrow {
                    image: url(:/down-arrow-light);
                    width: 12px;
                    height: 12px;
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
        
    def paintEvent(self, event):
        # Enable stylesheet for custom widgets
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transcription_app = TranscriptionApp()
    transcription_app.show()
    sys.exit(app.exec_())