from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QToolButton, 
                             QLabel, QFrame, QMenu, QAction)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon

class SidebarMenu(QWidget):
    new_session_triggered = pyqtSignal()
    load_session_triggered = pyqtSignal()
    open_session_triggered = pyqtSignal()
    save_session_triggered = pyqtSignal()
    edit_speaker_names_triggered = pyqtSignal()
    edit_speaker_colors_triggered = pyqtSignal()
    toggle_timestamps_triggered = pyqtSignal(bool)
    toggle_speaker_names_triggered = pyqtSignal(bool)
    help_triggered = pyqtSignal()
    settings_triggered = pyqtSignal()
    close_app_triggered = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = True
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toggle_button = QToolButton()
        self.toggle_button.setIcon(QIcon('src/assets/icons/close.png'))
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        layout.addWidget(self.toggle_button, alignment=Qt.AlignRight)

        self.buttons = []

        # Session button
        self.session_button = self.create_menu_button("Session", "file.png")
        self.session_menu = QMenu(self)
        self.session_menu.addAction("New Session", self.new_session_triggered.emit)
        self.session_menu.addAction("Load Session", self.load_session_triggered.emit)
        self.session_menu.addAction("Open Session", self.open_session_triggered.emit)
        self.session_menu.addAction("Save Session", self.save_session_triggered.emit)
        self.session_button.setMenu(self.session_menu)
        layout.addWidget(self.session_button)

        # Edit button
        self.edit_button = self.create_menu_button("Edit", "edit.png")
        self.edit_menu = QMenu(self)
        self.edit_menu.addAction("Edit Speaker Names", self.edit_speaker_names_triggered.emit)
        self.edit_menu.addAction("Edit Speaker Colors", self.edit_speaker_colors_triggered.emit)
        self.timestamps_action = self.edit_menu.addAction("Timestamps On/Off")
        self.timestamps_action.setCheckable(True)
        self.timestamps_action.toggled.connect(self.toggle_timestamps_triggered.emit)
        self.speaker_names_action = self.edit_menu.addAction("Show Speaker Names On/Off")
        self.speaker_names_action.setCheckable(True)
        self.speaker_names_action.toggled.connect(self.toggle_speaker_names_triggered.emit)
        self.edit_button.setMenu(self.edit_menu)
        layout.addWidget(self.edit_button)

        # Help button
        self.help_button = self.create_menu_button("Help", "help.png")
        self.help_button.clicked.connect(self.help_triggered.emit)
        layout.addWidget(self.help_button)

        # Settings button
        self.settings_button = self.create_menu_button("Settings", "settings.png")
        self.settings_button.clicked.connect(self.settings_triggered.emit)
        layout.addWidget(self.settings_button)

        # Close button
        self.close_button = self.create_menu_button("Close", "close.png")
        self.close_button.clicked.connect(self.close_app_triggered.emit)
        layout.addWidget(self.close_button)

        layout.addStretch()

        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
            }
            QPushButton {
                text-align: left;
                padding: 5px;
                border: none;
                color: white;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)

    def create_menu_button(self, text, icon_name):
        button = QPushButton(QIcon(f"src/assets/icons/{icon_name}"), text)
        button.setIconSize(QSize(24, 24))
        self.buttons.append(button)
        return button

    def toggle_sidebar(self):
        self.expanded = not self.expanded
        for button in self.buttons:
            button.setText(button.text() if self.expanded else "")
        self.toggle_button.setIcon(QIcon('src/assets/icons/close.png' if self.expanded else 'src/assets/icons/view.png'))
        self.setMaximumWidth(200 if self.expanded else 50)
        self.setMinimumWidth(200 if self.expanded else 50)