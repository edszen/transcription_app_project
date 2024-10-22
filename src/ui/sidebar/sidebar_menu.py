from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QToolButton, 
                             QLabel, QFrame, QMenu, QAction, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QSettings, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
import os
from src.ui.styles.theme_styles import ThemeStyles

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
        self.setObjectName("sidebar")  # Important for styling
        self.expanded = False
        self.settings = QSettings("SZ Apps", "GatherScribe")
        # Restore previous state
        self.expanded = self.settings.value("sidebar_expanded", False, type=bool)
        self.current_theme = "default"
        self.buttons = []
        self.init_ui()
        # Force initial state
        self.setFixedWidth(64)  # Start collapsed
        self.update_button_states()

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
        """Create menu section with proper styling and states"""
        for text, icon, has_menu, menu_items in items:
            button = QPushButton()
            
            # Set native font with proper size
            if os.name == 'posix':  # macOS
                button.setFont(QFont('.AppleSystemUIFont', 13))
            else:  # Windows
                button.setFont(QFont('Segoe UI', 13))
            
            # Set icon
            icon_path = self.get_icon_path(icon)
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
            
            # Only set text if expanded
            button.setText("" if not self.expanded else text)
            button.setProperty("text", text)
            button.setProperty("icon_base", icon)
            button.setIconSize(QSize(22, 22))
            button.setFixedHeight(36)
            
            # Set tooltip only when collapsed
            if not self.expanded:
                button.setToolTip(text)
            
            if has_menu and menu_items:
                menu = QMenu()
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
            
            self.buttons.append(button)
            layout.addWidget(button)

    def update_theme(self, theme):
        """Update theme and icons"""
        self.current_theme = theme
        
        # Force icon updates
        for button in self.buttons:
            icon_base = button.property("icon_base")
            if icon_base:
                icon_path = self.get_icon_path(icon_base)
                button.setIcon(QIcon(icon_path))
        
        # Update toggle button icon
        toggle_icon = "menu-collapse" if self.expanded else "menu-expand"
        toggle_icon_path = self.get_icon_path(toggle_icon)
        self.toggle_button.setIcon(QIcon(toggle_icon_path))
        
        # Apply theme styles
        ThemeStyles.apply_theme(self, theme)

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
        """Toggle sidebar expansion with animation"""
        target_width = 220 if not self.expanded else 64
        
        # Update button states immediately to prevent text flash
        self.expanded = not self.expanded
        self.update_button_states()
        
        # Animate the width change
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(150)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        self.animation.start()
        
        # Save state
        self.settings.setValue("sidebar_expanded", self.expanded)
        self.update_theme(self.current_theme)  # Use update_theme instead of update_icons

    def update_button_states(self):
        """Update button states based on sidebar expansion"""
        self.title_label.setVisible(self.expanded)
        for button in self.buttons:
            if not self.expanded:
                button.setText("")  # Ensure text is completely empty when collapsed
                button.setToolTip(button.property("text"))
            else:
                button.setText(button.property("text"))
                button.setToolTip("")  # Show tooltips when collapsed

    def get_icon_path(self, icon_name):
        """Get the appropriate icon path based on current theme"""
        theme_suffix = "_dark" if self.current_theme == "dark_midnight" else ""
        icon_filename = f"{icon_name}{theme_suffix}.png"
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'assets', 'icons')
        icon_path = os.path.join(base_path, icon_filename)
        
        # Verify icon exists, otherwise use default
        if not os.path.exists(icon_path):
            icon_path = os.path.join(base_path, f"{icon_name}.png")
        
        return icon_path