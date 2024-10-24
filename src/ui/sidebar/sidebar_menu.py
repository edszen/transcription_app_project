from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QToolButton, 
                             QLabel, QFrame, QMenu, QAction, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QSettings, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap
import os
from src.ui.styles.theme_manager import ThemeManager

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
        self.setObjectName("sidebar")
        
        # Initialize properties
        self.expanded = False
        self.settings = QSettings("SZ Apps", "GatherScribe")
        self.theme_manager = ThemeManager()
        self.current_theme = self.settings.value("app_theme", "default").lower()
        self.buttons = []
        
        # Initialize UI
        self.init_ui()
        self.setFixedWidth(80)  # Increased from 64 to accommodate larger icons
        self.update_button_states()
        
        # Apply initial theme
        self.update_theme(self.current_theme)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)  # Increased margins
        layout.setSpacing(4)  # Increased spacing
        
        # Logo container with much larger fixed height
        self.logo_container = QLabel()
        self.logo_container.setAlignment(Qt.AlignCenter)
        self.logo_container.setFixedHeight(140)  # Much larger height for logo
        layout.addWidget(self.logo_container)
        
        layout.addSpacing(16)  # More space after logo
        
        # Toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setIconSize(QSize(28, 28))
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        layout.addWidget(self.toggle_button)
        
        layout.addSpacing(16)
        
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
        
    def get_icon_path(self, icon_name):
        """Get the appropriate icon path based on current theme"""
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'assets', 'icons')
        
        suffix = "_dark" if self.current_theme == "dark_midnight" else ""
        icon_filename = f"{icon_name}{suffix}.png"
        
        icon_path = os.path.join(base_path, icon_filename)
        return icon_path if os.path.exists(icon_path) else ""
        
    def create_menu_section(self, layout, items):
        for text, icon, has_menu, menu_items in items:
            button = QPushButton()
            
            # Set larger font size
            if os.name == 'posix':
                button.setFont(QFont('.AppleSystemUIFont', 14))
            else:
                button.setFont(QFont('Segoe UI', 14))
            
            # Set icon
            icon_path = self.get_icon_path(icon)
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(32, 32))  # Larger icons
            
            # Store the text as a property and set it based on expanded state
            button.setProperty("text", text)
            button.setText(text if self.expanded else "")
            
            # Set fixed height and styling
            button.setFixedHeight(50)
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 15px;
                }
            """)
            
            if not self.expanded:
                button.setToolTip(text)
            
            # ... (rest of the button setup remains the same)
            
            self.buttons.append(button)
            layout.addWidget(button)
            
    def update_logo(self):
        """Update logo based on current theme and sidebar state"""
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'assets', 'icons')
        
        if self.expanded:
            # Use letters-only logo when expanded
            logo_file = "logo_letters_only_dark.png" if self.current_theme == "dark_midnight" else "logo_letters_only.png"
        else:
            # Use icon-only logo when collapsed
            logo_file = "logo_dark.png" if self.current_theme == "dark_midnight" else "logo.png"
            
        logo_path = os.path.join(base_path, logo_file)
        
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Much larger logo sizes
            scaled_height = 120 if self.expanded else 80
            scaled_pixmap = pixmap.scaledToHeight(scaled_height, Qt.SmoothTransformation)
            self.logo_container.setPixmap(scaled_pixmap)
            self.logo_container.setAlignment(Qt.AlignCenter)

    def update_theme(self, theme_name):
        """Update sidebar theme and logo"""
        self.current_theme = theme_name
        colors = self.theme_manager.get_colors(theme_name)
        
        # Apply theme styles (keep existing styles)
        self.setStyleSheet(f"""
            QWidget#sidebar {{
                background-color: {colors['sidebar_bg']};
                border-right: 1px solid {colors['border_primary']};
            }}
            
            QLabel {{
                color: {colors['text_primary']};
                font-weight: 500;
            }}
            
            QPushButton {{
                background-color: transparent;
                color: {colors['text_primary']};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                text-align: left;
                margin: 2px 4px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['sidebar_hover']};
            }}
        """)
        
        # Update icons and logo
        self.update_logo()
        for button in self.buttons:
            icon_base = button.property("icon_base")
            if icon_base:
                icon_path = self.get_icon_path(icon_base)
                if icon_path:
                    button.setIcon(QIcon(icon_path))
        
        # Update toggle button icon
        toggle_icon = "menu_collapse" if self.expanded else "menu_expand"
        toggle_icon_path = self.get_icon_path(toggle_icon)
        if toggle_icon_path:
            self.toggle_button.setIcon(QIcon(toggle_icon_path))
        
    def toggle_sidebar(self):
        target_width = 260 if not self.expanded else 80
        
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.expanded = not self.expanded
        self.update_button_states()
        self.update_logo()
        self.animation.start()
        
    def update_button_states(self):
        """Update button states and text visibility"""
        for button in self.buttons:
            text = button.property("text")
            if self.expanded:
                button.setText(text)
                button.setToolTip("")
            else:
                button.setText("")
                button.setToolTip(text)