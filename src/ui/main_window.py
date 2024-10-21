from PyQt5.QtWidgets import (QMainWindow, QAction, QHBoxLayout, QVBoxLayout, QWidget,
                            QPushButton, QStackedWidget, QLabel, QFrame, QToolButton, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont
from src.ui.chat.transcription_widget import TranscriptionWidget
from src.ui.chat.chat_widget import ChatWidget
from src.utils.file_operations import FileOperations
from src.ui.main_ui import TranscriptionApp
from src.ui.settings import SettingsDialog
from src.ui.help_dialog import HelpDialog
from src.ui.sidebar.sidebar_menu import SidebarMenu

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.transcription_app = TranscriptionApp()
        self.file_ops = FileOperations(self)
        self.init_ui()

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
        self.sidebar.close_app_triggered.connect(self.close_application)
        
    def new_session(self):
        # Implement new session logic
        pass
    
    def load_session(self):
        # This can be the same as open_session if there's no distinction
        self.open_session()

    def open_session(self):
        session_data = self.file_ops.load_session()
        if session_data:
            self.transcription_app.transcription_widget.text_area.setPlainText(session_data['transcript'])
            self.transcription_app.chat_widget.load_chat(session_data['chat_history'])

    def save_session(self):
        transcript = self.transcription_app.transcription_widget.get_transcript()
        chat_history = self.transcription_app.chat_widget.get_chat_history()
        self.file_ops.save_session(transcript, chat_history)
        
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
            # Handle settings update
            # You may need to update the following settings:
            # - Hugging Face API Key
            # - OpenAI API key
            # - Enable diarization
            # - App Theme (Normal/Grey, Dark/Midnight theme)
            pass

    def close_application(self):
        if self.check_unsaved_changes():
            self.close()

    def check_unsaved_changes(self):
        # Check if there are unsaved changes
        unsaved_changes = False  # Replace with actual check
        if unsaved_changes:
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         "You have unsaved changes. Do you want to save before closing?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                         QMessageBox.Save)
            if reply == QMessageBox.Save:
                self.save_session()
                return True
            elif reply == QMessageBox.Cancel:
                return False
        return True