import unittest
from PyQt5.QtWidgets import QApplication
from src.ui.main_ui import TranscriptionApp
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestTranscriptionApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self):
        self.window = TranscriptionApp()

    def test_initialization(self):
        self.assertIsNotNone(self.window)
        self.assertEqual(self.window.windowTitle(), 'Audio Transcription App')

    def test_ui_elements(self):
        self.assertIsNotNone(self.window.upload_button)
        self.assertIsNotNone(self.window.cancel_button)
        self.assertIsNotNone(self.window.settings_button)
        self.assertIsNotNone(self.window.help_button)
        self.assertIsNotNone(self.window.progress_bar)
        self.assertIsNotNone(self.window.text_area)
        self.assertIsNotNone(self.window.chat_input)
        self.assertIsNotNone(self.window.chat_button)

    def test_update_transcribing_message(self):
        self.window.update_transcribing_message()
        self.assertEqual(self.window.text_area.toPlainText(), "Transcribing.")

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

if __name__ == '__main__':
    unittest.main()
