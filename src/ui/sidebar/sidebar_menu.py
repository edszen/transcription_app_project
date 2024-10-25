from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QToolButton, 
                             QLabel, QFrame, QMenu, QAction, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QSettings, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor, QPixmap
import os
from src.ui.styles.theme_manager import ThemeManager

class SidebarButton(QPushButton):
    def __init__(self, text, icon_path, parent=None):
        super().__init__(parent)
        self.setText("")  # Clear default text
        self.setProperty("actualText", text)
        
        # Create horizontal layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 4, 16, 4) # Increased right margin
        self.layout.setSpacing(16)  # Space between icon and text
        
        # Create and set up icon label
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(48, 48)  # Fixed size for icon container
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            scaled_pixmap = pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        # Create and set up text label with size policy
        self.text_label = QLabel(text)
        self.text_label.setVisible(False)
        self.text_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # Ensure text doesn't get clipped
        self.text_label.setMinimumWidth(100)  # Minimum width for text
        
        # Add widgets to layout
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.text_label, 1)  # Give text label stretch factor
        
        # Style settings
        self.setFixedHeight(56)  # Slightly increased height
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
    def setExpanded(self, expanded):
        """Toggle text visibility and adjust width"""
        self.text_label.setVisible(expanded)
        if expanded:
            self.setMinimumWidth(200)  # Ensure enough width when expanded
        else:
            self.setMinimumWidth(64)  # Collapsed width
        
    def updateIcon(self, icon_path):
        """Update the button's icon"""
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            scaled_pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)

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
        self.update_logo()
        
        # Important: Remove any hardcoded background color
        self.setAttribute(Qt.WA_StyledBackground, True)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)  # Increased margins
        layout.setSpacing(4)  # Increased spacing
        
        # Container widget for the logo to maintain consistent spacing
        logo_widget = QWidget()
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignCenter)  # Center align the logo container
        
        # Logo container with much larger fixed height
        self.logo_container = QLabel()
        self.logo_container.setAlignment(Qt.AlignCenter)
        self.logo_container.setMinimumWidth(64)
        self.logo_container.setFixedHeight(180)
        logo_layout.addWidget(self.logo_container)
        
        # Add logo widget to main layout
        layout.addWidget(logo_widget)
        
        # Create a fixed-width container for the toggle button
        toggle_container = QWidget()
        toggle_container.setFixedWidth(64)  # Match the collapsed sidebar width
        toggle_layout = QHBoxLayout(toggle_container)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setAlignment(Qt.AlignLeft)  # Ensure left alignment
        
        #layout.addSpacing(16)  # More space after logo
        
        # Toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setFixedSize(64, 64)  # Fixed size for the button
        toggle_icon_path = self.get_icon_path("menu_expand")
        if os.path.exists(toggle_icon_path):
            original_pixmap = QPixmap(toggle_icon_path)
            scaled_pixmap = original_pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.toggle_button.setIcon(QIcon(scaled_pixmap))
        self.toggle_button.setIconSize(QSize(96, 96))
        self.toggle_button.setStyleSheet("""
            QToolButton {
                padding: 0px;
                margin: 0px;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        # Add toggle button to its container with left alignment
        toggle_layout.addWidget(self.toggle_button)
        toggle_layout.addStretch()  # This pushes the button to the left
        
        # Add toggle container to main layout
        layout.addWidget(toggle_container)
        #layout.addWidget(self.toggle_button, 0, Qt.AlignCenter)
        
        #layout.addSpacing(16)
        
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
            # Create custom button
            icon_path = self.get_icon_path(icon)
            button = SidebarButton(text, icon_path, self)
            
            # Store reference and add to layout
            self.buttons.append(button)
            layout.addWidget(button, 0, Qt.AlignLeft)
            
            # Set up menu if needed
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
        
        if self.expanded:
            logo_file = "logo_letters_only_dark.svg" if self.current_theme == "dark_midnight" else "logo_letters_only.svg"
        else:
            logo_file = "logo_dark.svg" if self.current_theme == "dark_midnight" else "logo.svg"
            
        logo_path = os.path.join(base_path, logo_file)
        
        if os.path.exists(logo_path):
            if logo_path.endswith('.svg'):
                if not hasattr(self, 'svg_widget'):
                    from PyQt5.QtSvg import QSvgWidget
                    self.svg_widget = QSvgWidget()
                    # Don't replace the container, add the SVG widget to it
                    self.logo_container.setLayout(QVBoxLayout())
                    self.logo_container.layout().addWidget(self.svg_widget)
                    self.logo_container.layout().setContentsMargins(0, 0, 0, 0)
                    self.logo_container.layout().setAlignment(Qt.AlignCenter)  # Center in container
                
                self.svg_widget.load(logo_path)
                # Calculate sizes while maintaining aspect ratio
                if self.expanded:
                    # For expanded state, set width and let height adjust naturally
                    natural_size = self.svg_widget.sizeHint()
                    aspect_ratio = natural_size.width() / natural_size.height()
                    target_width = 200
                    natural_height = int(target_width / aspect_ratio)
                    self.svg_widget.setFixedSize(target_width, natural_height)
                    self.logo_container.setMinimumWidth(200)
                else:
                    # For collapsed state, keep it 64x64
                    self.svg_widget.setFixedSize(64, 64)
                    self.logo_container.setMinimumWidth(64)
                    
                self.svg_widget.setVisible(True)
            else:
                # Fallback to PNG handling
                pixmap = QPixmap(logo_path)
                if self.expanded:
                    scaled_pixmap = pixmap.scaledToWidth(200, Qt.SmoothTransformation)
                else:
                    scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_container.setPixmap(scaled_pixmap)
                self.logo_container.setVisible(True)
                
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
        target_width = 220 if not self.expanded else 80
        
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
        """Update button states when sidebar toggles"""
        for button in self.buttons:
            button.setExpanded(self.expanded)
            if not self.expanded:
                button.setToolTip(button.property("actualText"))
            else:
                button.setToolTip("")