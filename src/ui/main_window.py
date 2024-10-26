from PyQt5.QtWidgets import (QMainWindow, QAction, QHBoxLayout, QVBoxLayout, QWidget,
                            QPushButton, QStackedWidget, QLabel, QFrame, QToolButton, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QSettings
from PyQt5.QtGui import QIcon, QFont
from src.ui.chat.transcription_widget import TranscriptionWidget
from src.ui.chat.chat_widget import ChatWidget
from src.utils.file_operations import FileOperations
from src.ui.main_ui import TranscriptionApp
from src.ui.settings import SettingsDialog
from src.ui.help_dialog import HelpDialog
from src.ui.sidebar.sidebar_menu import SidebarMenu
from src.ui.styles.theme_manager import ThemeManager
import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        # Initialize QSettings
        self.settings = QSettings("SZ Apps", "GatherScribe")
        self.transcription_app = TranscriptionApp()
        self.file_ops = FileOperations(self)
        self.init_ui()
        
        # Apply initial theme
        current_theme = self.settings.value("app_theme", "default").lower()
        self.theme_manager.apply_theme(self, current_theme)
        
    def init_ui(self):
        self.setWindowTitle('GatherScribe')
        self.setGeometry(100, 100, 1200, 800)
        main_layout = QHBoxLayout()
        
        # Create and add SidebarMenu
        self.sidebar = SidebarMenu()
        self.connect_sidebar_signals()
        main_layout.addWidget(self.sidebar)

        # Add transcription app to main layout
        main_layout.addWidget(self.transcription_app, 4)

        # Create central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)       
        
    def connect_sidebar_signals(self):
        self.sidebar.new_session_triggered.connect(self.new_session)
        self.sidebar.load_session_triggered.connect(self.load_session)
        self.sidebar.open_session_triggered.connect(self.open_session)
        self.sidebar.save_session_triggered.connect(self.save_session)
        self.sidebar.edit_speaker_names_triggered.connect(self.edit_speaker_names)
        self.sidebar.edit_speaker_colors_triggered.connect(self.edit_speaker_colors)
        self.sidebar.toggle_timestamps_triggered.connect(self.toggle_timestamps)
        self.sidebar.toggle_speaker_names_triggered.connect(self.toggle_speaker_names)
        self.sidebar.help_triggered.connect(self.show_help)
        self.sidebar.settings_triggered.connect(self.open_settings)
        self.sidebar.close_app_triggered.connect(self.close)
        
    def new_session(self):
        if self.check_unsaved_changes():
            self.transcription_app.transcription_widget.clear()
            self.transcription_app.chat_widget.clear()
            self.file_ops.current_session_path = None
            self.file_ops.last_saved_state = None
    
    def load_session(self):
        """Load a session file"""
        if self.check_unsaved_changes():
            session_data = self.file_ops.load_session()
            if session_data:
                # Load transcript
                self.transcription_app.transcription_widget.set_transcript(session_data.get('transcript', ''))
                
                # Load chat history
                chat_history = session_data.get('chat_history', [])
                if chat_history:
                    # Create a new chat for this session
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    chat_name = f"Loaded Session {timestamp}"
                    
                    # Reset chat widget state and load the chat history
                    self.transcription_app.chat_widget.load_session_chat(chat_name, chat_history)
                    
                return True
        return False

    def open_session(self):
        session_data = self.file_ops.load_session()
        if session_data:
            self.transcription_app.transcription_widget.text_area.setPlainText(session_data['transcript'])
            self.transcription_app.chat_widget.load_chat(session_data['chat_history'])

    def save_session(self):
        transcript = self.transcription_app.transcription_widget.get_transcript()
        chat_history = self.transcription_app.chat_widget.get_chat_history()
        return self.file_ops.save_session(transcript, chat_history)
        
    def edit_speaker_names(self):
        # Implement speaker name editing
        pass

    def edit_speaker_colors(self):
        # Implement speaker color editing
        pass

    def toggle_timestamps(self, state):
        # Implement timestamp toggling
        pass

    def toggle_speaker_names(self, state):
        # Implement speaker name toggling
        pass

    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.apply_theme()
            
    def closeEvent(self, event):
        if self.check_unsaved_changes():
            event.accept()
        else:
            event.ignore()

    def check_unsaved_changes(self):
        transcript = self.transcription_app.transcription_widget.get_transcript()
        chat_history = self.transcription_app.chat_widget.get_chat_history()
        
        if self.file_ops.has_unsaved_changes(transcript, chat_history):
            reply = QMessageBox.question(
                self,
                'Unsaved Changes',
                "You have unsaved changes. Do you want to save before continuing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                return self.save_session()
            elif reply == QMessageBox.Cancel:
                return False
        return True

    def apply_theme(self):
        """Apply theme throughout the application"""
        theme = self.settings.value("app_theme", "default").lower()
        self.theme_manager.apply_theme(self, theme)
        
        # Update child components
        self.sidebar.update_theme(theme)
        self.transcription_app.update_theme(theme)