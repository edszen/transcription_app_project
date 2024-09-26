from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        help_text = """
        <h2>Audio Transcription App Help</h2>
        <h3>Transcribing Audio</h3>
        <ol>
            <li>Click "Upload and Transcribe Audio"</li>
            <li>Select an audio file (.mp3, .wav, or .m4a)</li>
            <li>Wait for transcription to complete</li>
        </ol>
        <h3>Using Speaker Diarization</h3>
        <ol>
            <li>Click "Settings"</li>
            <li>Enter your Hugging Face API key</li>
            <li>Enable "Use Speaker Diarization"</li>
            <li>Click "Save Settings"</li>
        </ol>
        <p>For more information, please refer to the README file.</p>
        """
        
        help_browser = QTextBrowser()
        help_browser.setHtml(help_text)
        layout.addWidget(help_browser)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
        self.setWindowTitle("Help")
        self.resize(400, 300)