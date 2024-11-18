from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PyQt5.QtCore import Qt
from src.ui.styles.theme_manager import ThemeManager

class MessageWidget(QWidget):
    def __init__(self, sender, message, theme_manager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.sender = sender  # Store sender for theme application
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)  # Tighter margins
        
        self.message = QTextEdit()
        self.message.setReadOnly(True)
        self.message.setPlainText(message)
        self.message.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.message.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Auto-adjust height based on content
        doc_height = self.message.document().size().height()
        self.message.setFixedHeight(min(max(doc_height + 20, 40), 200))
        
        layout.addWidget(self.message)
        self.setLayout(layout)
        
        # Apply initial theme
        self.apply_theme("default")
        
    def apply_theme(self, theme):
        colors = self.theme_manager.get_colors(theme)
        if self.sender == "You":
            bg_color = colors['accent_secondary']
            text_color = '#ffffff'
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            bg_color = colors['input_bg']
            text_color = colors['text_primary']
            self.setLayoutDirection(Qt.LeftToRight)
            
        self.message.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
                border: 1px solid {colors['border_primary']};
            }}
        """)