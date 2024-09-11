from PyQt5.QtWidgets import QApplication
from ui import TranscriptionApp
if __name__ == "__main__":
    app = QApplication([])
    window = TranscriptionApp()
    app.exec_()
    
