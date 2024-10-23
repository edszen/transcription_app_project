from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QLineEdit, QComboBox)
from PyQt5.QtCore import Qt

class ThemePreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Preview title
        title = QLabel("Theme Preview")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Sample components
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Input:"))
        input_layout.addWidget(QLineEdit("Sample text input"))
        layout.addLayout(input_layout)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(QPushButton("Primary Button"))
        button_layout.addWidget(QPushButton("Secondary"))
        layout.addLayout(button_layout)
        
        combo_layout = QHBoxLayout()
        combo = QComboBox()
        combo.addItems(["Option 1", "Option 2", "Option 3"])
        combo_layout.addWidget(QLabel("Dropdown:"))
        combo_layout.addWidget(combo)
        layout.addLayout(combo_layout)
        
        self.setLayout(layout)
        self.setMinimumWidth(300)