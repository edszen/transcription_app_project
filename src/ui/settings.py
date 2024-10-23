# src/ui/settings.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QCheckBox, QPushButton, QComboBox)
from PyQt5.QtCore import QSettings
from utils.encryption import EncryptionUtils
from src import config
from src.ui.styles.theme_manager import ThemeManager
from src.ui.styles.theme_preview import ThemePreviewWidget

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("SZ Apps", "GatherScribe")
        self.encryption_utils = EncryptionUtils()
        self.theme_manager = ThemeManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create main settings area
        settings_layout = QHBoxLayout()
        
        # Left side: Settings controls
        controls_layout = QVBoxLayout()
        
        # API Settings group
        self._create_api_settings(controls_layout)
        
        # Theme Settings group
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Default", "Dark/Midnight"])
        current_theme = self.settings.value("app_theme", "Default")
        self.theme_combo.setCurrentText(current_theme)
        self.theme_combo.currentTextChanged.connect(self._on_theme_preview)
        theme_layout.addWidget(self.theme_combo)
        controls_layout.addLayout(theme_layout)
        
        # Right side: Theme preview
        self.preview_widget = ThemePreviewWidget()
        
        # Add both sides to main layout
        settings_layout.addLayout(controls_layout)
        settings_layout.addWidget(self.preview_widget)
        layout.addLayout(settings_layout)

        # Save button at bottom
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)

        self.setLayout(layout)
        self.setWindowTitle("Settings")
        
        # Apply current theme to preview
        self._on_theme_preview(current_theme)

    def _create_api_settings(self, layout):
        # Diarization checkbox
        self.diarization_checkbox = QCheckBox("Enable Speaker Diarization")
        self.diarization_checkbox.setChecked(
            self.settings.value("use_diarization", False, type=bool)
        )
        layout.addWidget(self.diarization_checkbox)

        # API Key inputs
        self._add_api_input(layout, "Hugging Face API Key:", "huggingface_api_key", True)
        self._add_api_input(layout, "OpenAI API Key:", "openai_api_key", False)

        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("OpenAI Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(config.AVAILABLE_MODELS)
        current_model = self.settings.value("openai_model", config.CHATGPT_MODEL)
        self.model_combo.setCurrentText(current_model)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

    def _add_api_input(self, layout, label, setting_key, encrypt=False):
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel(label))
        input_field = QLineEdit()
        
        if encrypt:
            encrypted_value = self.settings.value(setting_key, "")
            if encrypted_value:
                decrypted_value = self.encryption_utils.decrypt(encrypted_value)
                input_field.setText(decrypted_value)
        else:
            input_field.setText(self.settings.value(setting_key, ""))
            
        setattr(self, f"{setting_key}_input", input_field)
        input_layout.addWidget(input_field)
        layout.addLayout(input_layout)

    def _on_theme_preview(self, theme_name):
        """Update the preview widget with selected theme"""
        theme = "dark_midnight" if theme_name == "Dark/Midnight" else "default"
        self.theme_manager.apply_theme(self.preview_widget, theme)

    def save_settings(self):
        # Save API and feature settings
        self.settings.setValue("use_diarization", self.diarization_checkbox.isChecked())
        
        # Save API keys
        hf_api_key = self.huggingface_api_key_input.text()
        encrypted_hf_key = self.encryption_utils.encrypt(hf_api_key)
        self.settings.setValue("huggingface_api_key", encrypted_hf_key)
        
        self.settings.setValue("openai_api_key", self.openai_api_key_input.text())
        self.settings.setValue("openai_model", self.model_combo.currentText())
        
        # Save theme setting
        selected_theme = self.theme_combo.currentText()
        if selected_theme == "Dark/Midnight":
            self.settings.setValue("app_theme", "dark_midnight")
        else:
            self.settings.setValue("app_theme", "default")

        self.accept()