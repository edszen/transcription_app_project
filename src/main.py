import sys
from PyQt5.QtWidgets import QApplication
from src.ui import TranscriptionApp

def main():
    app = QApplication(sys.argv)
    window = TranscriptionApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()