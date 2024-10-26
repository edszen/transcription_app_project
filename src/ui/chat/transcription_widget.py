from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTextEdit, 
                             QProgressBar, QHBoxLayout,QFileDialog, QMessageBox, QComboBox)
from PyQt5.QtCore import pyqtSlot, QSettings, QTimer, pyqtSignal
from src.core.transcribe import Transcriber
from src.utils.file_operations import FileOperations
from src.ui.styles.theme_manager import ThemeManager

class TranscriptionWidget(QWidget):
    audio_loaded = pyqtSignal(str)
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.theme_manager = ThemeManager()
        self.transcriber = None
        self.file_ops = FileOperations()
        self.init_ui()
        self.dot_count = 0
        self.transcribing_timer = QTimer()
        self.transcribing_timer.timeout.connect(self.update_transcribing_message)

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create horizontal layout for buttons
        button_layout = QHBoxLayout()
        
        # Upload button - Add this new section
        self.upload_button = QPushButton('Upload and Transcribe Audio')
        self.upload_button.clicked.connect(self.upload_and_transcribe)
        button_layout.addWidget(self.upload_button)
        
        # Cancel button
        self.cancel_button = QPushButton('Cancel Transcription')
        self.cancel_button.clicked.connect(self.cancel_transcription)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        
        # Add button layout to main layout
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Transcription text area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)
        
        # Save button and format selection
        save_layout = QHBoxLayout()
        self.save_button = QPushButton('Save Transcription')
        self.save_button.clicked.connect(self.save_transcript)
        save_layout.addWidget(self.save_button)
        layout.addLayout(save_layout)
        
        self.setLayout(layout)
        
    def update_theme(self, theme):
        colors = self.theme_manager.get_colors(theme)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
            }}
            
            QTextEdit {{
                background-color: {colors['input_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border_primary']};
                border-radius: 6px;
                padding: 8px;
                selection-background-color: {colors['accent_primary']};
                selection-color: #ffffff;
            }}
            
            QPushButton {{
                background-color: {colors['button_bg']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['button_active']};
            }}
            
            QPushButton:disabled {{
                background-color: {colors['border_primary']};
                color: {colors['text_muted']};
            }}
            
            QProgressBar {{
                border: 1px solid {colors['border_primary']};
                border-radius: 4px;
                text-align: center;
                padding: 1px;
                background-color: {colors['background']};
            }}
            
            QProgressBar::chunk {{
                background-color: {colors['accent_secondary']};
                border-radius: 3px;
            }}
        """)

    def upload_and_transcribe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Upload Audio', '', 'Audio Files (*.mp3 *.wav *.m4a *.ogg *.mp4);;All Files (*)')
        if file_path:
            self.audio_loaded.emit(file_path)
            self.start_transcription(file_path)

    def start_transcription(self, file_path):
        self.text_area.setText("Initializing transcription...")
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
        self.progress_bar.setVisible(False)

    @pyqtSlot(str)
    def update_transcription(self, text):
        formatted_text = self.format_transcript(text)
        self.text_area.setHtml(formatted_text)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)

    def format_transcript(self, text):
        colors = self.theme_manager.get_colors(
            self.settings.value("app_theme", "default").lower()
        )
        
        lines = text.split('\n')
        formatted_lines = []
        for line in lines:
            parts = line.split('|', 1)
            if len(parts) == 2:
                timestamp, content = parts
                speaker, speech = content.split(':', 1)
                formatted_lines.append(
                    f'<span style="color: {colors["accent_primary"]}">{timestamp}</span> | '
                    f'<span style="color: {colors["accent_secondary"]}"><b>{speaker}</b></span>:'
                    f'<span style="color: {colors["text_primary"]}">{speech}</span>'
                )
            else:
                formatted_lines.append(line)
        return '<br>'.join(formatted_lines)

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(str)
    def update_status(self, status):
        self.text_area.setText(status)
        
    def update_transcribing_message(self):
        self.dot_count = (self.dot_count + 1) % 4
        dots = "." * self.dot_count
        self.text_area.setText(f"Transcribing{dots}")
        
    def save_transcript(self):
        transcript = self.text_area.toPlainText()
        self.file_ops.save_transcript(transcript, self)
        
    @pyqtSlot(str)
    def show_error(self, error_message):
        QMessageBox.critical(self, 'Error', error_message)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.text_area.setText("Transcription failed. Please try again.")

    def get_transcript(self):
        return self.text_area.toPlainText()
    
    def clear(self):
        """Clear the transcription widget state"""
        self.text_area.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.cancel_button.setEnabled(False)
        if self.transcribing_timer.isActive():
            self.transcribing_timer.stop()
        self.dot_count = 0

    def set_transcript(self, transcript):
        """Set the transcript text and format it"""
        if transcript:
            formatted_text = self.format_transcript(transcript)
            self.text_area.setHtml(formatted_text)
        else:
            self.text_area.clear()