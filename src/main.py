import sys
from PyQt5.QtWidgets import QApplication
from ui import TranscriptionApp
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def main():
    app = QApplication(sys.argv)
    window = TranscriptionApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()