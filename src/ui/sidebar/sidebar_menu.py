from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QToolButton, 
                             QLabel, QFrame, QMenu, QAction, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QSettings, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
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
        self.current_theme = "default"
        self.buttons = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 12, 6, 12) # More padding around edges
        layout.setSpacing(2) # More space between items
        
        # App title with native system font
        self.title_label = QLabel("GatherScribe")
        if os.name == 'posix':  # macOS
            self.title_label.setFont(QFont('.AppleSystemUIFont', 15))
        else:  # Windows
            self.title_label.setFont(QFont('Segoe UI', 15))
        self.title_label.setVisible(self.expanded)
        layout.addWidget(self.title_label)
        
        # Toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setIconSize(QSize(20, 20))
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        layout.addWidget(self.toggle_button)
        
        layout.addSpacing(4)
        
        # Main menu section
        main_menu = [
            ("Session", "session", True, [
                ("New Session", self.new_session_triggered.emit),
                ("Open Session", self.open_session_triggered.emit),
                ("Save Session", self.save_session_triggered.emit),
            ]),
            ("Edit", "edit", True, [
                ("Edit Speaker Names", self.edit_speaker_names_triggered.emit),
                ("Edit Speaker Colors", self.edit_speaker_colors_triggered.emit),
                ("Toggle Timestamps", lambda: self.toggle_timestamps_triggered.emit(True)),
            ]),
        ]
        
        self.create_menu_section(layout, main_menu)
        layout.addStretch()
        
        # Bottom menu section
        bottom_menu = [
            ("Help", "help", False, None),
            ("Settings", "settings", False, None),
            ("Close", "close", False, None),
        ]
        self.create_menu_section(layout, bottom_menu)
        
        # Set initial width and update state
        self.setFixedWidth(64 if not self.expanded else 220)
        self.buttons = []  # Initialize buttons list
        self.update_theme(self.current_theme)
        
    def create_menu_section(self, layout, items):
        for text, icon, has_menu, menu_items in items:
            button = QPushButton()
            
            # Set native font with proper size
            if os.name == 'posix':  # macOS
                button.setFont(QFont('.AppleSystemUIFont', 13))
            else:  # Windows
                button.setFont(QFont('Segoe UI', 13))
            
            button.setText(text if self.expanded else "")
            button.setProperty("text", text)
            button.setProperty("icon_base", icon)
            button.setIconSize(QSize(22, 22))
            button.setFixedHeight(36)
            
            if has_menu and menu_items:
                menu = QMenu()
                # Remove custom styling to keep native look
                for item_text, callback in menu_items:
                    action = menu.addAction(item_text)
                    action.triggered.connect(callback)
                button.setMenu(menu)
            else:
                if text == "Help":
                    button.clicked.connect(self.help_triggered.emit)
                elif text == "Settings":
                    button.clicked.connect(self.settings_triggered.emit)
                elif text == "Close":
                    button.clicked.connect(self.close_app_triggered.emit)
            
            if not self.expanded:
                button.setToolTip(text)
            
            self.buttons.append(button)
            layout.addWidget(button)

    def update_theme(self, theme):
        self.current_theme = theme
        
        # Modern color schemes
        if theme == "default":
            colors = {
                'bg': '#f5f5f5',
                'sidebar_bg': '#f0f0f0',
                'text': '#333333',
                'hover_bg': '#e5e5e5',
                'active_bg': '#d9d9d9',
                'menu_bg': '#ffffff',
                'border': '#e0e0e0'
            }
        else:  # dark theme
            colors = {
                'bg': '#1a1b26',
                'sidebar_bg': '#16171f',
                'text': '#c0caf5',
                'hover_bg': '#24283b',
                'active_bg': '#2f354d',
                'menu_bg': '#1f2335',
                'border': '#414868'
            }

        style = f"""
            QWidget {{
                background-color: {colors['sidebar_bg']};
                color: {colors['text']};
            }}
            
            QPushButton {{
                text-align: left;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                color: {colors['text']};
                background: transparent;
                font-size: 13px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['hover_bg']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['active_bg']};
            }}
            
            QMenu {{
                background-color: {colors['menu_bg']};
                border: 1px solid {colors['border']};
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 6px 20px;
            }}
            
            QMenu::item:selected {{
                background-color: {colors['hover_bg']};
            }}
            
            QLabel {{
                color: {colors['text']};
                padding: 8px 12px;
                font-weight: 600;
                font-size: 14px;
            }}
        """
        
        self.setStyleSheet(style)
        self.update_icons()

    def update_icons(self):
        # Update icons based on current theme
        suffix = "_dark" if self.current_theme == "dark_midnight" else ""
        
        for button in self.buttons:
            icon_base = button.property("icon_base")
            if icon_base:
                icon_path = f"{icon_base}{suffix}.png"
                button.setIcon(self.get_icon(icon_path))
        
        # Update toggle button icon
        toggle_icon = "menu-collapse" if self.expanded else "menu-expand"
        self.toggle_button.setIcon(self.get_icon(f"{toggle_icon}{suffix}.png"))

    def toggle_sidebar(self):
        target_width = 220 if not self.expanded else 64
        
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(150)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        self.animation.finished.connect(self.update_button_states)  # Update states after animation
        self.animation.start()
        
        self.expanded = not self.expanded
        self.settings.setValue("sidebar_expanded", self.expanded)
        self.update_icons()

    def update_button_states(self):
        self.title_label.setVisible(self.expanded)
        for button in self.buttons:
            text = button.property("text")
            if text:  # Check if text property exists
                button.setText(text if self.expanded else "")
                button.setToolTip("" if self.expanded else text)  # Show tooltips when collapsed

    def get_icon(self, icon_name):
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'assets', 'icons', icon_name)
        return QIcon(icon_path)