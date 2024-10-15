from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QListWidget, QInputDialog
from PyQt5.QtCore import pyqtSignal, Qt
import json
import os

class ChatWidget(QWidget):
    new_question = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chats = {}
        self.current_chat_id = None
        self.init_ui()
        self.load_chats()

    def init_ui(self):
        layout = QVBoxLayout()

        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.chat_history)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.send_question)
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

        # Saved chats
        self.saved_chats = QListWidget()
        self.saved_chats.setMaximumHeight(100)  # Limit the height of the saved chats list
        self.saved_chats.itemClicked.connect(self.load_chat)
        layout.addWidget(self.saved_chats)

        # Rename chat button
        self.rename_chat_button = QPushButton("Rename Chat")
        self.rename_chat_button.clicked.connect(self.rename_chat)
        layout.addWidget(self.rename_chat_button)

        self.setLayout(layout)

    def send_question(self):
        question = self.input_field.text().strip()
        if question:
            self.add_message("You", question)
            self.input_field.clear()
            self.new_question.emit(question)

    def add_response(self, response):
        self.add_message("ChatGPT", response)

    def add_message(self, sender, message):
        if self.current_chat_id is None:
            self.new_chat()
        
        self.chat_history.append(f"<p><b>{sender}:</b> {message}</p>")
        self.chats[self.current_chat_id]['messages'].append({"sender": sender, "message": message})
        self.save_chats()

    def clear_chat(self):
        self.chat_history.clear()
        if self.current_chat_id:
            self.chats[self.current_chat_id]['messages'] = []
            self.save_chats()

    def new_chat(self):
        chat_id = f"Chat {len(self.chats) + 1}"
        self.chats[chat_id] = {"name": chat_id, "messages": []}
        self.current_chat_id = chat_id
        self.saved_chats.addItem(chat_id)
        self.clear_chat()
        self.save_chats()

    def rename_chat(self):
        if self.current_chat_id:
            new_name, ok = QInputDialog.getText(self, "Rename Chat", "Enter new name:", text=self.chats[self.current_chat_id]['name'])
            if ok and new_name:
                self.chats[self.current_chat_id]['name'] = new_name
                self.saved_chats.currentItem().setText(new_name)
                self.save_chats()

    def load_chat(self, item):
        chat_id = item.text()
        self.current_chat_id = chat_id
        self.chat_history.clear()
        for message in self.chats[chat_id]['messages']:
            self.chat_history.append(f"<p><b>{message['sender']}:</b> {message['message']}</p>")

    def save_chats(self):
        with open('chats.json', 'w') as f:
            json.dump(self.chats, f)

    def load_chats(self):
        if os.path.exists('chats.json'):
            with open('chats.json', 'r') as f:
                self.chats = json.load(f)
            self.saved_chats.clear()
            for chat_id, chat_data in self.chats.items():
                self.saved_chats.addItem(chat_data['name'])