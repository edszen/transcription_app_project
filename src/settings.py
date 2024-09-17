from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QCheckBox, QPushButton)
from PyQt5.QtCore import QSettings
from encryption_utils import EncryptionUtils

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("YourCompany", "AudioTranscriptionApp")
        self.encryption_utils = EncryptionUtils()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Diarization checkbox
        self.diarization_checkbox = QCheckBox("Enable Speaker Diarization")
        self.diarization_checkbox.setChecked(
            self.settings.value("use_diarization", False, type=bool)
        )
        layout.addWidget(self.diarization_checkbox)

        # API Key input layout
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("Hugging Face API Key:"))
        self.api_key_input = QLineEdit()
        
        # Load and decrypt the API key if it exists
        encrypted_key = self.settings.value("huggingface_api_key", "")
        if encrypted_key:
            decrypted_key = self.encryption_utils.decrypt(encrypted_key)
            self.api_key_input.setText(decrypted_key)
        
        api_key_layout.addWidget(self.api_key_input)
        layout.addLayout(api_key_layout)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.setWindowTitle("Transcription Settings")


    def save_settings(self):
        # Save the checkbox state
        use_diarization = self.diarization_checkbox.isChecked()
        self.settings.setValue("use_diarization", use_diarization)

        # Encrypt and save the API key
        api_key = self.api_key_input.text()
        encrypted_key = self.encryption_utils.encrypt(api_key)
        self.settings.setValue("huggingface_api_key", encrypted_key)

        self.accept()