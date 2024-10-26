from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
                            QPushButton, QListWidget, QInputDialog, QScrollArea, QComboBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPalette
from src.ui.styles.theme_manager import ThemeManager
from src.ui.media.media_player import MediaPlayer
import json
import os
from src.utils.file_operations import FileOperations

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
        
    pass

class ChatWidget(QWidget):
    new_question = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = ThemeManager()
        self.chats = {}
        self.current_chat_id = None
        self.file_ops = FileOperations()
        self.current_theme = "default"  # Track current theme
        self.init_ui()
        self.load_chats()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Media Player at the top
        self.media_player = MediaPlayer()
        layout.addWidget(self.media_player)

        # Chat history
        self.chat_history = QScrollArea()
        self.chat_history.setWidgetResizable(True)
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_history.setWidget(self.chat_content)
        layout.addWidget(self.chat_history)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_question)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        # Chat management
        chat_management_layout = QHBoxLayout()
        self.clear_button = QPushButton("Clear Chat")
        self.clear_button.clicked.connect(self.clear_chat)
        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.clicked.connect(self.new_chat)
        chat_management_layout.addWidget(self.clear_button)
        chat_management_layout.addWidget(self.new_chat_button)
        layout.addLayout(chat_management_layout)

        # Saved chats dropdown
        self.saved_chats = QComboBox()
        self.saved_chats.currentTextChanged.connect(self.load_chat)
        layout.addWidget(self.saved_chats)

        # Bottom buttons row
        bottom_buttons_layout = QHBoxLayout()

        # Rename chat button
        self.rename_chat_button = QPushButton("Rename Chat")
        self.rename_chat_button.clicked.connect(self.rename_chat)
        
        #Save chat button
        self.save_chat_button = QPushButton("Save Chat")
        self.save_chat_button.clicked.connect(self.save_chat)

        # Add buttons to bottom layout with stretch to push them together
        bottom_buttons_layout.addWidget(self.rename_chat_button)
        bottom_buttons_layout.addWidget(self.save_chat_button)
        
        layout.addLayout(bottom_buttons_layout)

        self.setLayout(layout)
        
    def update_theme(self, theme):
        self.current_theme = theme  # Store current theme
        colors = self.theme_manager.get_colors(theme)
        
        # Main theme styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
            }}
            
            QTextEdit, QLineEdit {{
                background-color: {colors['input_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border_primary']};
                border-radius: 6px;
                padding: 8px;
            }}
            
            QPushButton {{
                background-color: {colors['button_bg']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['button_active']};
            }}
            
            QComboBox {{
                background-color: {colors['input_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border_primary']};
                border-radius: 6px;
                padding: 6px;
            }}
            
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QScrollBar:vertical {{
                background-color: {colors['background']};
                width: 14px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {colors['border_primary']};
                min-height: 30px;
                border-radius: 7px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {colors['border_secondary']};
            }}
        """)
        
        # Update all message widgets
        for i in range(self.chat_layout.count()):
            widget = self.chat_layout.itemAt(i).widget()
            if isinstance(widget, MessageWidget):
                widget.apply_theme(theme)
                
    def set_audio_file(self, file_path):
        """Load audio file into the media player"""
        if hasattr(self, 'media_player'):
            self.media_player.load_media(file_path)

    def cleanup(self):
        """Clean up resources before widget is destroyed"""
        if hasattr(self, 'media_player'):
            self.media_player.cleanup()

    def send_question(self):
        question = self.input_field.toPlainText().strip()
        if question:
            self.add_message("You", question)
            self.input_field.clear()
            self.new_question.emit(question)

    def add_response(self, response):
        self.add_message("ChatGPT", response)

    def add_message(self, sender, message):
        if self.current_chat_id is None:
            self.new_chat()
        
        # Create message widget with theme manager
        message_widget = MessageWidget(
            sender=sender,
            message=message,
            theme_manager=self.theme_manager,
            parent=self
        )
        
        # Apply current theme to new message
        message_widget.apply_theme(self.current_theme)
        
        self.chat_layout.addWidget(message_widget)
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )
        
        self.chats[self.current_chat_id]['messages'].append({
            "sender": sender,
            "message": message
        })
        self.save_chats()

    def clear_chat(self):
        for i in reversed(range(self.chat_layout.count())): 
            self.chat_layout.itemAt(i).widget().setParent(None)
        if self.current_chat_id and self.current_chat_id in self.chats:
            self.chats[self.current_chat_id]['messages'] = []
            self.save_chats()

    def new_chat(self):
        chat_id = f"Chat {len(self.chats) + 1}"
        self.chats[chat_id] = {"name": chat_id, "messages": []}
        self.current_chat_id = chat_id
        self.saved_chats.addItem(chat_id)
        self.saved_chats.setCurrentText(chat_id)
        self.clear_chat()
        self.save_chats()

    def rename_chat(self):
        if self.current_chat_id and self.current_chat_id in self.chats:
            new_name, ok = QInputDialog.getText(self, "Rename Chat", "Enter new name:", text=self.chats[self.current_chat_id]['name'])
            if ok and new_name:
                old_id = self.current_chat_id
                self.chats[old_id]['name'] = new_name
                new_id = new_name
                self.chats[new_id] = self.chats.pop(old_id)
                self.current_chat_id = new_id
                index = self.saved_chats.findText(old_id)
                if index >= 0:
                    self.saved_chats.setItemText(index, new_name)
                self.save_chats()

    def load_chat(self, chat_name):
        for chat_id, chat_data in self.chats.items():
            if chat_data['name'] == chat_name:
                self.current_chat_id = chat_id
                self.clear_chat()
                for message in chat_data['messages']:
                    message_widget = MessageWidget(
                        sender=message['sender'],
                        message=message['message'],
                        theme_manager=self.theme_manager,
                        parent=self
                    )
                    message_widget.apply_theme(self.current_theme)
                    self.chat_layout.addWidget(message_widget)
                break

    def save_chats(self):
        with open('chats.json', 'w') as f:
            json.dump(self.chats, f)
            
    def save_chat(self):
        if self.current_chat_id and self.current_chat_id in self.chats:
            self.file_ops.save_session(self.get_transcript(), self.chats[self.current_chat_id]['messages'])


    def load_chats(self):
        if os.path.exists('chats.json'):
            with open('chats.json', 'r') as f:
                self.chats = json.load(f)
            self.saved_chats.clear()
            for chat_id, chat_data in self.chats.items():
                self.saved_chats.addItem(chat_data['name'])