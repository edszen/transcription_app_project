from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QToolButton, 
                             QLabel, QFrame, QMenu, QAction)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QFont
import os

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
        self.expanded = False
        self.settings = QSettings("SZ Apps", "GatherScribe")
        # Restore previous state
        self.expanded = self.settings.value("sidebar_expanded", False, type=bool)
        self.init_ui()


    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # More padding around edges
        layout.setSpacing(1) # More space between items
        
         # Add app title at top
        self.title_label = QLabel("GatherScribe")
        self.title_label.setFont(QFont('', 18, QFont.Bold))
        self.title_label.setVisible(False)  # Hidden when collapsed
        layout.addWidget(self.title_label)

        # Add expand/collapse button
        self.toggle_button = QToolButton()
        self.toggle_button.setIcon(self.get_icon('menu.png'))
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 5px;
                background: transparent;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        layout.addWidget(self.toggle_button)
        self.buttons = []
        
        # Create main menu buttons group
        self.create_menu_group(layout, [
            ("Session", "session.png", True),
            ("Edit", "edit.png", True),
        ])
        
        # Add stretch to push bottom buttons down
        layout.addStretch()
        
        # Create bottom buttons group
        self.create_menu_group(layout, [
            ("Help", "help.png", False),
            ("Settings", "settings.png", False),
            ("Close", "close.png", False),
        ])

        self.setStyleSheet("""
            QWidget {
                background-color: #1a1b26;
            }
        """)
        self.setFixedWidth(50)  # Start collapsed
        
    def update_theme(self, theme):
        base_style = """
            QWidget {
                background-color: %s;
            }
            QPushButton {
                border: none;
                padding: 8px 12px;
                text-align: left;
                color: %s;
                background-color: transparent;
                font-family: "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
                font-weight: normal;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: %s;
            }
            QMenu {
                background-color: %s;
                border: none;
                padding: 5px;
                border-radius: 6px;
                margin: 3px;
            }
            QMenu::item {
                padding: 6px 25px;
                color: %s;
                margin: 0px;
            }
            QMenu::item:selected {
                background-color: %s;
            }
            QLabel {
                color: %s;
                font-size: 14px;
                padding: 0px 10px;
                font-weight: normal;
                background-color: transparent;
            }
            QToolButton {
                border: none;
                padding: 5px;
                background: transparent;
                margin: 3px 5px;
            }
        """
        
        if theme == "default":
            colors = (
                '#f0f0f0',  # Widget background
                '#303030',  # Button text
                '#e0e0e0',  # Hover color - very subtle
                '#ffffff',  # Menu background
                '#303030',  # Menu text
                '#e0e0e0',  # Menu hover
                '#303030',  # Label text
            )
        else:  # dark_midnight
            colors = (
                '#1b1e23',  # Darker background matching PyDracula
                '#c3ccdf',  # Button text - soft white/blue
                '#2c313c',  # Hover color - slightly lighter than bg
                '#21252d',  # Menu background - dark but lighter than main bg
                '#c3ccdf',  # Menu text - same as button text
                '#2c313c',  # Menu hover - same as button hover
                '#c3ccdf',  # Label text - same as button text
            )
        self.setStyleSheet(base_style % colors)
                
        # Update icons for the new theme
        self.update_icons(theme)

    def update_icons(self, theme):
        # Update icons based on the theme
        icon_suffix = "_dark" if theme == "dark_midnight" else ""
        for button in self.buttons:
            icon_name = button.property("icon_name")
            if icon_name:
                new_icon = self.get_icon(f"{icon_name}{icon_suffix}.png")
                button.setIcon(new_icon)

        # Update toggle button icon
        toggle_icon = "menu-expand" if self.expanded else "menu-collapse"
        self.toggle_button.setIcon(self.get_icon(f"{toggle_icon}{icon_suffix}.png"))
    
    def create_menu_group(self, layout, buttons):
        for text, icon, has_menu in buttons:
            button = QPushButton()
            button.setText(text)
            button.setProperty("class", "sidebar-button")
            button.setProperty("text", text)
            button.setIcon(self.get_icon(icon))
            button.setIconSize(QSize(22, 22))  # Slightly larger icons
            button.setFixedHeight(35)  # Shorter height for denser menu
            
            # Add left margin for icon alignment
            button.setStyleSheet("""
                QPushButton {
                    padding-left: 15px;
                }
            """)
            
            if has_menu:
                menu = QMenu()
                menu.setStyleSheet("""
                    QMenu {
                        padding: 5px 0px;
                    }
                    QMenu::item {
                        height: 25px;
                    }
                """)
                if text == "Session":
                    menu.addAction("New Session", self.new_session_triggered.emit)
                    menu.addAction("Open Session", self.open_session_triggered.emit)
                    menu.addAction("Save Session", self.save_session_triggered.emit)
                elif text == "Edit":
                    menu.addAction("Edit Speaker Names", self.edit_speaker_names_triggered.emit)
                    menu.addAction("Edit Speaker Colors", self.edit_speaker_colors_triggered.emit)
                    menu.addAction("Toggle Timestamps", self.toggle_timestamps_triggered.emit)
                button.setMenu(menu)
            else:
                # Connect non-menu buttons
                if text == "Help":
                    button.clicked.connect(self.help_triggered.emit)
                elif text == "Settings":
                    button.clicked.connect(self.settings_triggered.emit)
                elif text == "Close":
                    button.clicked.connect(self.close_app_triggered.emit)

            button.setFixedHeight(50)  # Taller buttons
            
            self.buttons.append(button)
            layout.addWidget(button)
            
    def create_menu_buttons(self, layout):
        # Updated button creation with modern styling
        button_style = """
            QPushButton {
                text-align: left;
                padding: 12px 16px;
                border: none;
                border-radius: 6px;
                color: #e0e0e0;
                font-size: 14px;
                margin: 2px 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
            QMenu {
                background-color: #2c3e50;
                border: 1px solid #34495e;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
                color: white;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """
        
        # Update button creation with new style and spacing
        self.buttons = []
        button_configs = [
            ("Session", "file.png", self.session_menu),
            ("Edit", "edit.png", self.edit_menu),
            ("Help", "help.png", None),
            ("Settings", "settings.png", None),
        ]

        for text, icon, menu in button_configs:
            button = QPushButton()
            button.setStyleSheet(button_style)
            button.setIcon(self.get_icon(icon))
            button.setIconSize(QSize(24, 24))
            button.setText("")  # Start with no text (collapsed)
            button.setProperty("text", text)  # Store text for later
            button.setProperty("icon_name", icon.split('.')[0])
            
            if menu:
                button.setMenu(menu)
            
            layout.addWidget(button)
            self.buttons.append(button)

    def update_button_states(self):
        # Update buttons based on expanded state
        width = 200 if self.expanded else 50
        self.setMaximumWidth(width)
        self.setMinimumWidth(width)
        
        self.title_label.setVisible(self.expanded)
        
        for button in self.buttons:
            if self.expanded:
                button.setText(button.property("text"))
            else:
                button.setText("")

    def toggle_sidebar(self):
        self.expanded = not self.expanded
        width = 200 if self.expanded else 50
        self.setFixedWidth(width)
        self.title_label.setVisible(self.expanded)
        
        for button in self.buttons:
            if self.expanded:
                button.setText(button.property("text"))
            else:
                button.setText("")
        
    def get_icon(self, icon_name):
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'icons', icon_name)
        return QIcon(icon_path)