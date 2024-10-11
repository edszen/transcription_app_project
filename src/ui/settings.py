from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QCheckBox, QPushButton, QComboBox)
from PyQt5.QtCore import QSettings
from utils.encryption import EncryptionUtils
from src import config

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("SZ Apps", "GatherScribe")
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

        # Hugging Face API Key input
        hf_api_key_layout = QHBoxLayout()
        hf_api_key_layout.addWidget(QLabel("Hugging Face API Key:"))
        self.hf_api_key_input = QLineEdit()
        encrypted_hf_key = self.settings.value("huggingface_api_key", "")
        if encrypted_hf_key:
            decrypted_hf_key = self.encryption_utils.decrypt(encrypted_hf_key)
            self.hf_api_key_input.setText(decrypted_hf_key)
        hf_api_key_layout.addWidget(self.hf_api_key_input)
        layout.addLayout(hf_api_key_layout)
        
        # OpenAI API Key input (Not encrypted)
        openai_api_key_layout = QHBoxLayout()
        openai_api_key_layout.addWidget(QLabel("OpenAI API Key:"))
        self.openai_api_key_input = QLineEdit()
        self.openai_api_key_input.setText(self.settings.value("openai_api_key", ""))
        openai_api_key_layout.addWidget(self.openai_api_key_input)
        layout.addLayout(openai_api_key_layout)

        # OpenAI Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("OpenAI Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(config.AVAILABLE_MODELS)
        current_model = self.settings.value("openai_model", config.CHATGPT_MODEL)
        self.model_combo.setCurrentText(current_model)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.setWindowTitle("Transcription Settings")


    def save_settings(self):
        # Save diarization setting
        use_diarization = self.diarization_checkbox.isChecked()
        self.settings.setValue("use_diarization", use_diarization)

        # Encrypt and save Hugging Face API key
        hf_api_key = self.hf_api_key_input.text()
        encrypted_hf_key = self.encryption_utils.encrypt(hf_api_key)
        self.settings.setValue("huggingface_api_key", encrypted_hf_key)

        # Save OpenAI API key
        openai_api_key = self.openai_api_key_input.text()
        self.settings.setValue("openai_api_key", openai_api_key)

        # Save selected OpenAI model
        selected_model = self.model_combo.currentText()
        self.settings.setValue("openai_model", selected_model)

        self.accept()