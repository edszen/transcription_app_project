from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
                            QPushButton, QListWidget, QInputDialog, QScrollArea, QComboBox
                            , QMessageBox, QFileDialog)
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
        # Main layout with no margins to maximize space
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # Minimize spacing between elements
        
        # Create a container for the top section (media player and chat)
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        
        # Media Player at the top
        self.media_player = MediaPlayer()
        layout.addWidget(self.media_player)

        # Chat history
        self.chat_history = QScrollArea()
        self.chat_history.setWidgetResizable(True)
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setContentsMargins(10, 10, 10, 10)
        self.chat_history.setWidget(self.chat_content)

        # Set a minimum height for chat history to ensure proper spacing
        self.chat_history.setMinimumHeight(400)
        top_layout.addWidget(self.chat_history)
        
        # Input area
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 0, 10, 0)
        
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_question)
        self.send_button.setFixedHeight(40)  # Match button height
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        top_layout.addWidget(input_container)

        # Chat management buttons
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(12, 0, 12, 16)
        buttons_layout.setSpacing(10)
        
        self.clear_button = QPushButton("Clear Chat")
        self.new_chat_button = QPushButton("New Chat")
        self.clear_button.clicked.connect(self.clear_chat)
        self.new_chat_button.clicked.connect(self.new_chat)
        
        # Set fixed height for management buttons
        self.clear_button.setFixedHeight(42)
        self.new_chat_button.setFixedHeight(42)
        
        buttons_layout.addWidget(self.clear_button)
        buttons_layout.addWidget(self.new_chat_button)
        top_layout.addWidget(buttons_container)

        # Saved chats dropdown
        dropdown_container = QWidget()
        dropdown_layout = QVBoxLayout(dropdown_container)
        dropdown_layout.setContentsMargins(15, 0, 14, 0)
        
        self.saved_chats = QComboBox()
        self.saved_chats.setFixedHeight(30)  # Match height
        self.saved_chats.currentTextChanged.connect(self.load_chat)
        dropdown_layout.addWidget(self.saved_chats)
        top_layout.addWidget(dropdown_container)

        # Bottom buttons container with fixed height
        bottom_container = QWidget()
        bottom_container.setFixedHeight(70)  # Match the transcription widget button height
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(12, 0, 12, 0)
        bottom_layout.setSpacing(10)

        # Rename and Save chat buttons
        self.rename_chat_button = QPushButton("Rename Chat")
        self.save_chat_button = QPushButton("Save Chat")
        
        # Set fixed height for bottom buttons
        self.rename_chat_button.setFixedHeight(42)
        self.save_chat_button.setFixedHeight(42)
        
        self.rename_chat_button.clicked.connect(self.rename_chat)
        self.save_chat_button.clicked.connect(self.save_chat)

        bottom_layout.addWidget(self.rename_chat_button)
        bottom_layout.addWidget(self.save_chat_button)

        # Add all containers to main layout
        layout.addWidget(top_container, 1)  # Give top container stretch factor
        layout.addWidget(bottom_container)  # Bottom container without stretch
        
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
        """Clear current chat while preserving others"""
        # Clear the display
        for i in reversed(range(self.chat_layout.count())): 
            self.chat_layout.itemAt(i).widget().setParent(None)
            
        # Clear the messages for current chat only
        if self.current_chat_id and self.current_chat_id in self.chats:
            self.chats[self.current_chat_id]['messages'] = []
            self.save_chats()

    def new_chat(self):
        """Create a new chat while preserving history"""
        chat_id = f"Chat {len(self.chats) + 1}"
        self.chats[chat_id] = {
            "name": chat_id,
            "messages": []
        }
        self.current_chat_id = chat_id
        self.saved_chats.addItem(chat_id)
        self.saved_chats.setCurrentText(chat_id)
        
        # Clear only the display, not the stored messages
        for i in reversed(range(self.chat_layout.count())): 
            self.chat_layout.itemAt(i).widget().setParent(None)
        
        # Save the updated chat list
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
        """Load a specific chat from history"""
        if not chat_name:
            return
            
        for chat_id, chat_data in self.chats.items():
            if chat_data['name'] == chat_name:
                self.current_chat_id = chat_id
                
                # Clear the display
                for i in reversed(range(self.chat_layout.count())): 
                    self.chat_layout.itemAt(i).widget().setParent(None)
                    
                # Reload the messages
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
        """Save chat history to local storage"""
        chats_file = os.path.join(self.file_ops.sessions_dir, 'chat_history.json')
        try:
            with open(chats_file, 'w', encoding='utf-8') as f:
                json.dump(self.chats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving chat history: {str(e)}")
            
    def save_chat(self):
        """Save the current chat session with option to include transcript"""
        if not self.current_chat_id or not self.current_chat_id in self.chats:
            QMessageBox.warning(self, "Save Error", "No active chat to save.")
            return

        # Ask user what to save
        reply = QMessageBox.question(
            self,
            "Save Options",
            "Would you like to save the chat with the transcript?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )

        if reply == QMessageBox.Cancel:
            return

        # Get parent window to access transcript
        main_window = self.window()
        transcript = ""
        if reply == QMessageBox.Yes and hasattr(main_window, 'transcription_app'):
            transcript = main_window.transcription_app.transcription_widget.get_transcript()

        # Get save file path with format options
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            'Save Chat',
            os.path.join(self.file_ops.sessions_dir, f"{self.chats[self.current_chat_id]['name']}"),
            'Text Files (*.txt);;JSON Files (*.json)'
        )

        if not file_path:
            return

        try:
            chat_data = {
                'chat_name': self.chats[self.current_chat_id]['name'],
                'messages': self.chats[self.current_chat_id]['messages'],
                'transcript': transcript if transcript else ""
            }

            if file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(chat_data, f, indent=2, ensure_ascii=False)
            else:  # Save as text
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Chat: {chat_data['chat_name']}\n\n")
                    if transcript:
                        f.write("TRANSCRIPT:\n")
                        f.write("-" * 50 + "\n")
                        f.write(transcript)
                        f.write("\n" + "-" * 50 + "\n\n")
                    f.write("CHAT HISTORY:\n")
                    f.write("-" * 50 + "\n")
                    for msg in chat_data['messages']:
                        f.write(f"{msg['sender']}: {msg['message']}\n")

            QMessageBox.information(
                self,
                "Save Success",
                "Chat has been saved successfully."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save chat: {str(e)}"
            )
            
    def load_chats(self):
        """Load chat history from local storage"""
        chats_file = os.path.join(self.file_ops.sessions_dir, 'chat_history.json')
        if os.path.exists(chats_file):
            try:
                with open(chats_file, 'r', encoding='utf-8') as f:
                    self.chats = json.load(f)
                self.saved_chats.clear()
                for chat_id, chat_data in self.chats.items():
                    self.saved_chats.addItem(chat_data['name'])
            except Exception as e:
                print(f"Error loading chat history: {str(e)}")
                
    def get_chat_history(self):
        """Get the chat history for the current chat"""
        if self.current_chat_id and self.current_chat_id in self.chats:
            return self.chats[self.current_chat_id]['messages']
        return []

    def set_chat_history(self, chat_history):
        """Load a saved chat history"""
        self.clear_chat()
        if chat_history:
            # Create a new chat if none exists
            if not self.current_chat_id:
                self.new_chat()
                
            # Add each message from the history
            for message in chat_history:
                message_widget = MessageWidget(
                    sender=message['sender'],
                    message=message['message'],
                    theme_manager=self.theme_manager,
                    parent=self
                )
                message_widget.apply_theme(self.current_theme)
                self.chat_layout.addWidget(message_widget)
                
            # Update the chat's message history
            self.chats[self.current_chat_id]['messages'] = chat_history
            self.save_chats()

    def clear(self):
        """Clear the entire chat widget state"""
        self.clear_chat()
        self.current_chat_id = None
        self.chats = {}
        self.saved_chats.clear()