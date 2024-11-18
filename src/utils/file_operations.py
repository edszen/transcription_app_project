# Low-level file system operations

import os
import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
import datetime

class FileOperations:
    """Handles basic file system operations and directory management"""
    def __init__(self):
        #self.main_window = main_window
        self.documents_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'GatherScribe')
        
        # Dedicated directories for different types of files
        self.sessions_dir = os.path.join(self.documents_dir, 'Sessions')
        self.transcripts_dir = os.path.join(self.documents_dir, 'Transcripts')
        self.chats_dir = os.path.join(self.documents_dir, 'Chats')
        
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.documents_dir,
            self.sessions_dir,    # For .gss session files only
            self.transcripts_dir, # For exported transcripts and transcripts+chats
            self.chats_dir       # For chat history and chat-related files
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
    def get_open_file_path(self, title: str, directory: str, format_type: str) -> tuple[str, str]:
        """Get file path for opening a file"""
        return QFileDialog.getOpenFileName(
            None, 
            title, 
            directory,
            self.get_file_filters(format_type)
        )

    def get_save_file_path(self, title: str, directory: str, 
                          file_filter: str) -> tuple[str, str]:
        """Get file path for saving a file"""
        return QFileDialog.getSaveFileName(
            None, title, directory, file_filter
        )
            
    def save_transcript(self, transcript: str, parent_widget) -> bool:
        """Save transcript to file"""
        file_path, _ = self.get_save_file_path(
            'Export Transcript',
            self.transcripts_dir,
            'Text Files (*.txt);;JSON Files (*.json);;PDF Files (*.pdf);;All Files (*)'
        )
        
        if not file_path:
            return False

        try:
            if file_path.endswith('.pdf'):
                return self._save_as_pdf(file_path, transcript)
            elif file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({'transcript': transcript}, f, indent=2)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(transcript)
            return True
            
        except Exception as e:
            QMessageBox.critical(parent_widget, "Export Error", 
                               f"Failed to export transcript: {str(e)}")
            return False
        
    def ensure_file_extension(self, path: str, extension: str) -> str:
        """Ensure file has the correct extension"""
        return path if path.endswith(extension) else f"{path}{extension}"
    
    def get_timestamp_filename(self, prefix: str, extension: str) -> str:
        """Generate a filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}{extension}"

    def get_file_filters(self, format_type: str) -> str:
        """Get file dialog filters based on format"""
        filters = {
            'json': 'JSON Files (*.json)',
            'txt': 'Text Files (*.txt)',
            'pdf': 'PDF Files (*.pdf)',
            'session': 'Session Files (*.gss)',
            'all': 'All Files (*)'
        }
        return filters.get(format_type, filters['all'])

    def _save_as_pdf(self, file_path: str, content: str) -> bool:
        """Save content as PDF"""
        try:
            doc = QTextDocument()
            doc.setPlainText(content)
            printer = QPrinter()
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_path)
            doc.print_(printer)
            return True
        except Exception:
            return False
        
    def get_default_directory(self, dir_type: str) -> str:
        """Get default directory path based on type"""
        dirs = {
            'transcripts': self.transcripts_dir,
            'sessions': self.sessions_dir,
            'chats': self.chats_dir
        }
        return dirs.get(dir_type, self.documents_dir)