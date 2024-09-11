from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog

class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.upload_button = QPushButton('Upload Audio')
        self.upload_button.clicked.connect(self.upload_file)
        
        self.transcription_label = QLabel('Transcribed Text:')
        
        layout.addWidget(self.upload_button)
        layout.addWidget(self.transcription_label)
        
        self.setLayout(layout)
        self.setWindowTitle('Audio Transcription App')
        self.show()
        
    def upload_file(self):
        #Implement later
        pass