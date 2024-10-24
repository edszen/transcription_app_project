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
        
        # Important: Remove any hardcoded background color
        self.setAttribute(Qt.WA_StyledBackground, True)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)  # Increased margins
        layout.setSpacing(4)  # Increased spacing
        
        # Logo container with much larger fixed height
        self.logo_container = QLabel()
        self.logo_container.setAlignment(Qt.AlignCenter)
        self.logo_container.setFixedHeight(180)  # Increased height
        self.logo_container.setMinimumWidth(64)  # Minimum width for logo
        layout.addWidget(self.logo_container)
        
        layout.addSpacing(16)  # More space after logo
        
        # Toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setIconSize(QSize(32, 32))
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
            # Create button with text directly
            button = QPushButton()
            
            # IMPORTANT: Set text as both property AND button text
            button.setText(text)  # Set initial text
            button.setProperty("actualText", text)  # Store text as property with different name
            
            # Set larger font size
            if os.name == 'posix':
                button.setFont(QFont('.AppleSystemUIFont', 14))
            else:
                button.setFont(QFont('Segoe UI', 14))
            
            # Set icon
            icon_path = self.get_icon_path(icon)
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
                button.setIconSize(QSize(32, 32))
            
            button.setFixedHeight(50)
            
            # Clear text if not expanded
            if not self.expanded:
                button.setText("")
            
            # Add button to layout and store reference
            self.buttons.append(button)
            layout.addWidget(button)
            
            # Set up connections
            if has_menu and menu_items:
                menu = QMenu()
                for item_text, callback in menu_items:
                    action = menu.addAction(item_text)
                    action.triggered.connect(callback)
                button.setMenu(menu)
            else:
                # Direct button connections
                if text == "Help":
                    button.clicked.connect(self.help_triggered.emit)
                elif text == "Settings":
                    button.clicked.connect(self.settings_triggered.emit)
                elif text == "Close":
                    button.clicked.connect(self.close_app_triggered.emit)
            
    def update_logo(self):
        """Update logo based on current theme and sidebar state"""
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                            'assets', 'icons')
        
        # Use SVG logo path
        if self.expanded:
            # Use letters-only logo when expanded
            logo_file = "logo_letters_only_dark.svg" if self.current_theme == "dark_midnight" else "logo_letters_only.svg"
        else:
            # Use icon-only logo when collapsed
            logo_file = "logo_dark.svg" if self.current_theme == "dark_midnight" else "logo.svg"
            
        logo_path = os.path.join(base_path, logo_file)
        
        if os.path.exists(logo_path):
            # For SVG files, we'll use QSvgWidget
            if logo_path.endswith('.svg'):
                if not hasattr(self, 'svg_widget'):
                    from PyQt5.QtSvg import QSvgWidget
                    self.svg_widget = QSvgWidget()
                    # Replace the logo_container with the svg_widget
                    self.layout().replaceWidget(self.logo_container, self.svg_widget)
                    self.logo_container.deleteLater()
                    self.logo_container = self.svg_widget
                
                self.svg_widget.load(logo_path)
                # Set size based on sidebar state
                if self.expanded:
                    self.svg_widget.setFixedSize(200, 200)  # Larger size when expanded
                else:
                    self.svg_widget.setFixedSize(160, 160)  # Larger size when collapsed
                
            else:  # Fallback to PNG if SVG doesn't exist
                pixmap = QPixmap(logo_path)
                # Much larger logo sizes
                scaled_height = 200 if self.expanded else 160  # Increased sizes
                scaled_pixmap = pixmap.scaledToHeight(scaled_height, Qt.SmoothTransformation)
                self.logo_container.setPixmap(scaled_pixmap)
                self.logo_container.setAlignment(Qt.AlignCenter)

    def update_theme(self, theme_name):
        """Update sidebar theme and logo"""
        self.current_theme = theme_name
        colors = self.theme_manager.get_colors(theme_name)
        
        # Apply theme-specific styles
        self.setStyleSheet(f"""
            QWidget#sidebar {{
                background-color: {colors['sidebar_bg']};
                border: none;
            }}
            
            QPushButton {{
                background-color: transparent;
                color: {colors['sidebar_text']};
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                text-align: left;
                margin: 2px 4px;
                font-size: 14px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['sidebar_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['sidebar_active']};
            }}
            
            QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }}
            
            QToolButton:hover {{
                background-color: {colors['sidebar_hover']};
            }}
        """)
        
        self.update_logo()
        
        # Update button icons
        for button in self.buttons:
            icon_base = button.property("icon_base")
            if icon_base:
                icon_path = self.get_icon_path(icon_base)
                if icon_path:
                    button.setIcon(QIcon(icon_path))
        
        # Update toggle button
        toggle_icon = "menu_collapse" if self.expanded else "menu_expand"
        toggle_icon_path = self.get_icon_path(toggle_icon)
        if toggle_icon_path:
            self.toggle_button.setIcon(QIcon(toggle_icon_path))
        
    def toggle_sidebar(self):
        print("Toggle sidebar called")  # Debug print
        target_width = 260 if not self.expanded else 80
        
        # Set the expanded state before updating buttons
        self.expanded = not self.expanded
        print(f"Expanded state: {self.expanded}")  # Debug print
        
        # Update button states immediately
        self.update_button_states()
        
        # Create and start animation
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
        
        # Update logo after animation
        self.update_logo()
        
    def update_button_states(self):
        for button in self.buttons:
            actual_text = button.property("actualText")
            if self.expanded:
                button.setText(actual_text)
            else:
                button.setText("")
                button.setToolTip(actual_text)