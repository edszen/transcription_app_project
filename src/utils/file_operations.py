import os
import json
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
import datetime

class FileOperations:
    def __init__(self, main_window=None):
        self.main_window = main_window
        self.documents_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'GatherScribe')
        if not os.path.exists(self.documents_dir):
            os.makedirs(self.documents_dir)

    def save_transcript(self, transcript, parent_widget):
        default_dir = os.path.join(self.documents_dir, 'Transcripts')
        os.makedirs(default_dir, exist_ok=True)
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            parent_widget,
            'Save Transcript',
            default_dir,
            'Text Files (*.txt);;JSON Files (*.json);;PDF Files (*.pdf);;All Files (*)'
        )
    
        if file_path:
            file_format = os.path.splitext(file_path)[1].lower()
            if file_format == '.json':
                with open(file_path, 'w') as f:
                    json.dump(transcript, f, indent=2)
            elif file_format == '.pdf':
                self._save_as_pdf(file_path, transcript)
            else:  # Default to txt
                with open(file_path, 'w') as f:
                    f.write(transcript)

    def save_session(self, transcript, chat_history):
        session_name, ok = QFileDialog.getSaveFileName(self.main_window, 'Save Session', self.documents_dir, 'GatherScribe Session (*.gss)')
        if ok:
            session_data = {
                'transcript': transcript,
                'chat_history': chat_history,
                'date': datetime.datetime.now().isoformat()
            }
            with open(session_name, 'w') as f:
                json.dump(session_data, f, indent=2)

    def load_session(self):
        file_path, _ = QFileDialog.getOpenFileName(self.main_window, 'Load Session', self.documents_dir, 'GatherScribe Session (*.gss)')
        if file_path:
            with open(file_path, 'r') as f:
                session_data = json.load(f)
            return session_data
        return None

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