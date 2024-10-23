from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QToolButton, 
                             QLabel, QFrame, QMenu, QAction, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QSettings, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
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
        self.setFixedWidth(64)
        self.update_button_states()
        
        # Apply initial theme
        self.update_theme(self.current_theme)

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
        
    def get_icon_path(self, icon_name):
        """Get the appropriate icon path based on current theme"""
        base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               'assets', 'icons')
        
        suffix = "_dark" if self.current_theme == "dark_midnight" else ""
        icon_filename = f"{icon_name}{suffix}.png"
        
        icon_path = os.path.join(base_path, icon_filename)
        return icon_path if os.path.exists(icon_path) else ""
        
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

    def update_theme(self, theme_name):
        """Update sidebar theme"""
        self.current_theme = theme_name
        colors = self.theme_manager.get_colors(theme_name)
        
        # Apply theme styles
        self.setStyleSheet(f"""
            QWidget#sidebar {{
                background-color: {colors['sidebar_bg']};
                border-right: 1px solid {colors['border_primary']};
            }}
            
            QLabel {{
                color: {colors['text_primary']};
            }}
            
            QPushButton {{
                background-color: transparent;
                color: {colors['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                text-align: left;
                margin: 2px 4px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['sidebar_hover']};
            }}
            
            QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px;
                margin: 2px 4px;
            }}
            
            QToolButton:hover {{
                background-color: {colors['sidebar_hover']};
            }}
            
            QMenu {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border_primary']};
                border-radius: 6px;
                padding: 4px;
            }}
            
            QMenu::item {{
                padding: 4px 24px;
                border-radius: 4px;
            }}
            
            QMenu::item:selected {{
                background-color: {colors['sidebar_hover']};
            }}
        """)
        
        # Update icons for current theme
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

        
    def apply_theme_styles(self):
        """Apply theme styles to the sidebar"""
        if self.current_theme == "dark_midnight":
            self.setStyleSheet("""
                QWidget#sidebar {
                    background-color: #16161e;
                    border-right: 1px solid #414868;
                }
                
                QLabel {
                    color: #c0caf5;
                }
                
                QPushButton {
                    background-color: transparent;
                    color: #c0caf5;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 12px;
                    text-align: left;
                    margin: 2px 4px;
                }
                
                QPushButton:hover {
                    background-color: #24283b;
                }
                
                QToolButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    padding: 4px;
                    margin: 2px 4px;
                }
                
                QToolButton:hover {
                    background-color: #24283b;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget#sidebar {
                    background-color: #f8f9fa;
                    border-right: 1px solid #e0e0e0;
                }
                
                QLabel {
                    color: #333333;
                }
                
                QPushButton {
                    background-color: transparent;
                    color: #333333;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 12px;
                    text-align: left;
                    margin: 2px 4px;
                }
                
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
                
                QToolButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    padding: 4px;
                    margin: 2px 4px;
                }
                
                QToolButton:hover {
                    background-color: #f0f0f0;
                }
            """)

    def toggle_sidebar(self):
        """Toggle sidebar with smooth animation"""
        target_width = 220 if not self.expanded else 64
        
        # Create animation
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)  # Slightly faster animation
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)  # Smoother curve
        
        # Update state before animation
        self.expanded = not self.expanded
        self.update_button_states()
        
        # Start animation
        self.animation.start()
        
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