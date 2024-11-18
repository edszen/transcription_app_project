from PyQt5.QtWidgets import (QMainWindow, QAction, QHBoxLayout, QVBoxLayout, QWidget,
                            QPushButton, QStackedWidget, QLabel, QFrame, QToolButton, QMessageBox)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QSettings
from src.utils.file_operations import FileOperations
from src.ui.main_ui import TranscriptionApp
from src.ui.settings import SettingsDialog
from src.ui.help_dialog import HelpDialog
from src.ui.sidebar.sidebar_menu import SidebarMenu
from src.ui.styles.theme_manager import ThemeManager
import datetime
from src.core.managers.session_manager import SessionManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize theme manager and utilities
        self.theme_manager = ThemeManager()
        self.settings = QSettings("SZ Apps", "GatherScribe")        
        self.file_ops = FileOperations()
        
        # Initialize SessionManager
        self.session_manager = SessionManager(self.file_ops)
        
        # Initialize TranscriptionApp with SessionManager
        self.transcription_app = TranscriptionApp(session_manager=self.session_manager)
        
        self.init_ui()
        self.setup_connections()
        
        # Apply initial theme
        current_theme = self.settings.value("app_theme", "default").lower()
        self.theme_manager.apply_theme(self, current_theme)
        
    def init_ui(self):
        """Initialize the main window UI"""
        self.setWindowTitle('GatherScribe')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main layout
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
        
    def setup_connections(self):
        """Setup signal connections"""
        # Connect session manager signals
        self.session_manager.session_loaded.connect(self.on_session_loaded)
        self.session_manager.session_error.connect(self.on_session_error)
        self.session_manager._state.session_modified.connect(self.on_session_modified)    
        
    def connect_sidebar_signals(self):
        """Connect sidebar button signals"""
        self.sidebar.new_session_triggered.connect(self.new_session)
        self.sidebar.load_session_triggered.connect(self.load_session)
        self.sidebar.save_session_triggered.connect(self.save_session)
        self.sidebar.edit_speaker_names_triggered.connect(self.edit_speaker_names)
        self.sidebar.edit_speaker_colors_triggered.connect(self.edit_speaker_colors)
        self.sidebar.toggle_timestamps_triggered.connect(self.toggle_timestamps)
        self.sidebar.toggle_speaker_names_triggered.connect(self.toggle_speaker_names)
        self.sidebar.help_triggered.connect(self.show_help)
        self.sidebar.settings_triggered.connect(self.open_settings)
        self.sidebar.close_app_triggered.connect(self.close)
        
    def new_session(self):
        """Create new session"""
        if self.check_unsaved_changes():
            self.session_manager.new_session()
    
    def load_session(self):
        """Load a session file"""
        if self.check_unsaved_changes():
            self.session_manager.load_session()

    def save_session(self):
        """Save current session"""
        transcript = self.transcription_app.transcription_widget.get_transcript()
        chat_history = self.transcription_app.chat_widget.get_chat_history()
        return self.session_manager.save_session(transcript, chat_history)
    
    def on_session_loaded(self, session):
        """Handle loaded session data"""
        self.transcription_app.transcription_widget.set_transcript(session.transcript)
        self.transcription_app.chat_widget.load_chat(session.chat_history)

    def on_session_error(self, error_message):
        """Handle session errors"""
        QMessageBox.critical(self, "Session Error", error_message)

    def on_session_modified(self, modified: bool):
        """Handle session modification state"""
        title = 'GatherScribe'
        if modified:
            title += ' *'
        self.setWindowTitle(title)
        
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
        """Show help dialog"""
        dialog = HelpDialog(self)
        dialog.exec_()

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec_():
            self.apply_theme()

    def check_unsaved_changes(self):
        """Check for unsaved changes before proceeding"""
        if self.session_manager.has_unsaved_changes():
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
        self.sidebar.update_theme(theme)
        self.transcription_app.update_theme(theme)

    def closeEvent(self, event):
        """Handle application close"""
        if self.check_unsaved_changes():
            self.session_manager.cleanup()
            event.accept()
        else:
            event.ignore()