import os
import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
import datetime

class FileOperations:
    def __init__(self, main_window=None):
        self.main_window = main_window
        self.documents_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'GatherScribe')
        
        # Dedicated directories for different types of files
        self.sessions_dir = os.path.join(self.documents_dir, 'Sessions')
        self.transcripts_dir = os.path.join(self.documents_dir, 'Transcripts')
        self.chats_dir = os.path.join(self.documents_dir, 'Chats')
        
        self._ensure_directories()
        self.current_session_path = None
        self.last_saved_state = None

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
            
    def save_transcript(self, transcript, parent_widget):
        """Save transcript to external file (separate from session saving)"""
        default_dir = os.path.join(self.documents_dir, 'Transcripts')
        os.makedirs(default_dir, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            'Export Transcript',
            default_dir,
            'Text Files (*.txt);;JSON Files (*.json);;All Files (*)'
        )
    
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if file_path.endswith('.json'):
                        json.dump({'transcript': transcript}, f, indent=2, ensure_ascii=False)
                    else:
                        f.write(transcript)
                return True
            except Exception as e:
                QMessageBox.critical(parent_widget, "Export Error", 
                                   f"Failed to export transcript: {str(e)}")
                return False
        return False

    def save_session(self, transcript, chat_history, auto_save=False):
        """Save current session state"""
        if auto_save and not self.current_session_path:
            # For auto-save after transcription, create a default filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"Session_{timestamp}.gss"
            self.current_session_path = os.path.join(self.sessions_dir, default_filename)
        
        if not auto_save and not self.current_session_path:
            # For manual save, let user choose location
            file_path, _ = QFileDialog.getSaveFileName(
                self.main_window,
                'Save Session',
                self.sessions_dir,
                'GatherScribe Session (*.gss)'
            )
            if not file_path:
                return False
            if not file_path.endswith('.gss'):
                file_path += '.gss'
            self.current_session_path = file_path

        session_data = {
            'transcript': transcript,
            'chat_history': chat_history,
            'date_modified': datetime.datetime.now().isoformat(),
            'version': '1.0'  # For future compatibility
        }

        try:
            with open(self.current_session_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            self.last_saved_state = self._calculate_state_hash(session_data)
            return True
        except Exception as e:
            if not auto_save:  # Only show error for manual saves
                QMessageBox.critical(self.main_window, "Save Error", 
                                   f"Failed to save session: {str(e)}")
            return False

    def load_session(self):
        """Load a session file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            'Load Session',
            self.sessions_dir,
            'GatherScribe Session (*.gss)'
        )
        if not file_path:
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            self.current_session_path = file_path
            self.last_saved_state = self._calculate_state_hash(session_data)
            return session_data
        except Exception as e:
            QMessageBox.critical(self.main_window, "Load Error", 
                               f"Failed to load session: {str(e)}")
            return None
        
    def has_unsaved_changes(self, transcript, chat_history):
        """Check if there are unsaved changes in the current session"""
        if not self.last_saved_state:
            return bool(transcript.strip() or chat_history)
        
        current_state = self._calculate_state_hash({
            'transcript': transcript,
            'chat_history': chat_history
        })
        return current_state != self.last_saved_state

    def _calculate_state_hash(self, state_data):
        """Calculate a hash of the current state for change detection"""
        # Convert to string and get hash for comparison
        state_str = json.dumps(state_data, sort_keys=True)
        return hash(state_str)

    def _get_file_filter(self, format):
        filters = {
            'json': 'JSON Files (*.json)',
            'txt': 'Text Files (*.txt)',
            'pdf': 'PDF Files (*.pdf)'
        }
        return filters.get(format, 'All Files (*)')

    def _save_as_pdf(self, file_path, content):
        doc = QTextDocument()
        doc.setPlainText(content)
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        doc.print_(printer)