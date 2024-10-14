from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QListWidget
from PyQt5.QtCore import pyqtSignal, Qt

class ChatWidget(QWidget):
    new_question = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
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

        # Clear button
        self.clear_button = QPushButton("Clear Chat")
        self.clear_button.clicked.connect(self.clear_chat)
        layout.addWidget(self.clear_button)

        # Saved chats
        self.saved_chats = QListWidget()
        layout.addWidget(self.saved_chats)

        # Save current chat button
        self.save_chat_button = QPushButton("Save Current Chat")
        self.save_chat_button.clicked.connect(self.save_current_chat)
        layout.addWidget(self.save_chat_button)

        self.setLayout(layout)

    def send_question(self):
        question = self.input_field.text().strip()
        if question:
            self.chat_history.append(f"<div style='text-align: right;'><b>You:</b> {question}</div>")
            self.input_field.clear()
            self.new_question.emit(question)

    def add_response(self, response):
        self.chat_history.append(f"<div style='text-align: left;'><b>ChatGPT:</b> {response}</div>")

    def clear_chat(self):
        self.chat_history.clear()

    def save_current_chat(self):
        chat_content = self.chat_history.toPlainText()
        if chat_content:
            self.saved_chats.addItem(f"Chat {self.saved_chats.count() + 1}")
            # You might want to actually save the content to a file or database here

    def load_saved_chat(self, item):
        # This method would load a saved chat when selected
        # For now, we'll just print the selected item
        print(f"Selected chat: {item.text()}")