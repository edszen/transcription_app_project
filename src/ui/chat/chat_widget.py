from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
                            QPushButton, QListWidget, QInputDialog, QScrollArea, QComboBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPalette
import json
import os
from src.utils.file_operations import FileOperations

class MessageWidget(QWidget):
    def __init__(self, sender, message, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.message = QTextEdit()
        self.message.setReadOnly(True)
        self.message.setPlainText(message)
        self.message.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        
        if sender == "You":
            self.message.setStyleSheet(self.message.styleSheet() + "QTextEdit { background-color: #e1ffc7; }")
            layout.setAlignment(Qt.AlignRight)
        else:
            self.message.setStyleSheet(self.message.styleSheet() + "QTextEdit { background-color: #ffffff; }")
            layout.setAlignment(Qt.AlignLeft)
        
        layout.addWidget(self.message)
        self.setLayout(layout)

class ChatWidget(QWidget):
    new_question = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chats = {}
        self.current_chat_id = None
        self.file_ops = FileOperations()
        self.init_ui()
        self.load_chats()

    def init_ui(self):
        layout = QVBoxLayout()

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

        # Rename chat button
        self.rename_chat_button = QPushButton("Rename Chat")
        self.rename_chat_button.clicked.connect(self.rename_chat)
        layout.addWidget(self.rename_chat_button)
        
        #Save chat button
        self.save_chat_button = QPushButton("Save Chat")
        self.save_chat_button.clicked.connect(self.save_chat)
        layout.addWidget(self.save_chat_button)

        self.setLayout(layout)
        
    def update_theme(self, theme):
        if theme == "default":
            self.setStyleSheet("""
                QTextEdit, QLineEdit {
                    background-color: white;
                    color: #333333;
                    border: 1px solid #b0b0b0;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #b0b0b0;
                }
            """)
        elif theme == "dark_midnight":
            self.setStyleSheet("""
                QTextEdit, QLineEdit {
                    background-color: #2d2d44;
                    color: #ffffff;
                    border: 1px solid #3d3d5c;
                }
                QPushButton {
                    background-color: #3d3d5c;
                    color: #ffffff;
                    border: 1px solid #4d4d6c;
                }
            """)

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
        
        message_widget = MessageWidget(sender, message)
        self.chat_layout.addWidget(message_widget)
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )
        
        self.chats[self.current_chat_id]['messages'].append({"sender": sender, "message": message})
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
                    self.add_message(message['sender'], message['message'])
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