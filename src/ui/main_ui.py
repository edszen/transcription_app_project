## New main_ui.py to work with sidebar_menu and main_window.py

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
                             QSplitter, QStyle, QStyleOption, QTextEdit, QFileDialog, QMessageBox, QComboBox,
                             QDialogButtonBox, QCheckBox, QProgressBar, QLineEdit, QLabel)
from PyQt5.QtCore import QSettings, Qt, pyqtSlot, QObject
from PyQt5.QtGui import QPainter, QStyleOption, QStyle
import logging
import os
from src.api.openai_chat import ChatGPTIntegration
from src.ui.chat.chat_widget import ChatWidget
from src.ui.chat.transcription_widget import TranscriptionWidget
from src.ui.styles.theme_manager import ThemeManager
from src.core.managers.session_manager import SessionManager

# Project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TranscriptionApp(QWidget):
    """Main application widget containing transcription and chat panels"""
    def __init__(self, session_manager=None):
        super().__init__()
        self.setup_logging()
        
        self.speaker_names = {}
        
        # Initialize core components
        self.settings = QSettings("SZ Apps", "GatherScribe")
        self.theme_manager = ThemeManager()
        #self.encryption_utils = EncryptionUtils()
        self.chatgpt = ChatGPTIntegration()
        
        # Initialize widgets with session manager
        self.transcription_widget = TranscriptionWidget(self.settings)
        self.chat_widget = ChatWidget(session_manager=session_manager)
        
        self.init_ui()
        self.setup_connections()
        #self.raw_text = "" 
        #self.total_chunks = 0
        #self.processed_chunks = 0  
        
        # Apply initial theme
        current_theme = self.settings.value("app_theme", "default").lower()
        self.update_theme(current_theme)     

    def setup_logging(self):
        """Setup application logging"""
        logging.basicConfig(level=logging.DEBUG, 
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for better integration
        
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
        # Add widgets to the splitter
        # Left side (Transcription)
        splitter.addWidget(self.transcription_widget)
        # Right side (Chat)
        splitter.addWidget(self.chat_widget)
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        self.setWindowTitle('GatherScribe')
        
    def setup_connections(self):
        """Setup signal connections between components"""
        # ChatGPT connections
        self.chatgpt.response_received.connect(self.chat_widget.add_response)
        self.chatgpt.error_occurred.connect(self.chat_widget.add_response)
        self.chat_widget.new_question.connect(self.ask_chatgpt)
        
        # Audio file loading connection
        self.transcription_widget.audio_loaded.connect(self.chat_widget.set_audio_file)
        
        # Connect transcript changes to trigger session modification
        if hasattr(self.transcription_widget, 'text_changed'):
            self.transcription_widget.text_changed.connect(self.on_content_changed)
        if hasattr(self.chat_widget, 'chat_changed'):
            self.chat_widget.chat_changed.connect(self.on_content_changed)
        
    def update_theme(self, theme):
        """Update application theme"""
        colors = self.theme_manager.get_colors(theme)
        
        # Update main app style
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
            }}
            
            QSplitter::handle {{
                background-color: {colors['border_primary']};
            }}
            
            QSplitter::handle:hover {{
                background-color: {colors['border_secondary']};
            }}
        """)
        
        # Update child widgets
        self.transcription_widget.update_theme(theme)
        self.chat_widget.update_theme(theme)
            
    def ask_chatgpt(self, question):
        """Handle ChatGPT question/answer"""
        transcript = self.transcription_widget.get_transcript()
        self.chatgpt.answer_question(transcript, question)
        
    def on_content_changed(self):
        """Handle content changes in transcript or chat"""
        if hasattr(self, '_session_manager') and self._session_manager:
            transcript = self.transcription_widget.get_transcript()
            chat_history = self.chat_widget.get_chat_history()
            self._session_manager.update_session_state(transcript, chat_history)
        
    def paintEvent(self, event):
        """Enable stylesheet for custom widgets"""
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    transcription_app = TranscriptionApp()
    transcription_app.show()
    sys.exit(app.exec_())