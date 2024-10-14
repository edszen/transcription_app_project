import unittest
from PyQt5.QtWidgets import QApplication
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

print("Python path:", sys.path)

try:
    from src.ui.main_ui import TranscriptionApp
    print("TranscriptionApp imported successfully")
except ImportError as e:
    print(f"Error importing TranscriptionApp: {e}")

class TestTranscriptionApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])

    def setUp(self):
        self.window = TranscriptionApp()

    def test_import(self):
        self.assertTrue('TranscriptionApp' in globals())

    def test_initialization(self):
        self.assertIsNotNone(self.window)
        self.assertEqual(self.window.windowTitle(), 'GatherScribe')

    def test_ui_elements(self):
        self.assertIsNotNone(self.window.upload_button)
        self.assertEqual(self.window.upload_button.text(), 'Upload and Transcribe Audio')
        self.assertIsNotNone(self.window.cancel_button)
        self.assertEqual(self.window.cancel_button.text(), 'Cancel Transcription')
        self.assertIsNotNone(self.window.settings_button)
        self.assertEqual(self.window.settings_button.text(), 'Settings')
        self.assertIsNotNone(self.window.help_button)
        self.assertEqual(self.window.help_button.text(), 'Help')
        self.assertIsNotNone(self.window.progress_bar)
        self.assertFalse(self.window.progress_bar.isVisible())
        self.assertIsNotNone(self.window.text_area)
        self.assertTrue(self.window.text_area.isReadOnly())
        self.assertIsNotNone(self.window.chat_input)
        self.assertIsNotNone(self.window.chat_button)
        self.assertEqual(self.window.chat_button.text(), 'Ask ChatGPT')

    def test_update_transcribing_message(self):
        self.window.update_transcribing_message()
        self.assertEqual(self.window.text_area.toPlainText(), "Transcribing.")
        self.window.update_transcribing_message()
        self.assertEqual(self.window.text_area.toPlainText(), "Transcribing..")

    def test_initial_button_states(self):
        self.assertTrue(self.window.upload_button.isEnabled())
        self.assertFalse(self.window.cancel_button.isEnabled())

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

if __name__ == '__main__':
    unittest.main()