from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextBrowser

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        help_text = """
        <h2>GatherScribe Help</h2>
        <h3>Getting Started</h3>
        <ol>
            <li>Click "Upload and Transcribe Audio"</li>
            <li>Select an audio file (.mp3, .wav, or .m4a)</li>
            <li>Wait for transcription to complete</li>
        </ol>

        <h3>Speaker Diarization</h3>
        <ol>
            <li>Click "Settings"</li>
            <li>Enter your Hugging Face API key</li>
            <li>Enable "Use Speaker Diarization"</li>
            <li>Click "Save Settings"</li>
        </ol>

        <h3>Chat Integration</h3>
        <ol>
            <li>Enter your OpenAI API key in Settings</li>
            <li>Select your preferred model</li>
            <li>Use the chat panel to interact with your transcript</li>
        </ol>

        <h3>Keyboard Shortcuts</h3>
        <table>
            <tr><td><b>Ctrl+N:</b></td><td>New Session</td></tr>
            <tr><td><b>Ctrl+O:</b></td><td>Open Session</td></tr>
            <tr><td><b>Ctrl+S:</b></td><td>Save Session</td></tr>
            <tr><td><b>Ctrl+Q:</b></td><td>Quit Application</td></tr>
        </table>

        <p>For more detailed information, please refer to the README file.</p>
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