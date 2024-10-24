from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)
    
class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)
    
    # Dark theme colors updated to match example
    TOKYO_NIGHT = {
        # Base colors
        'background': '#2D3142',          # Deep blue-gray (Primary background)
        'background_darker': '#2D3142',    # Same as primary for cards
        'background_lighter': '#363A4F',   # Content background
        
        # Sidebar specific
        'sidebar_bg': '#2D3142',          # Same as primary background
        'sidebar_hover': '#363A4F',       # Slightly lighter for hover
        'sidebar_active': '#363A4F',      # Same as hover
        'sidebar_text': '#FFFFFF',        # White text
        
        # Text colors
        'text_primary': '#FFFFFF',        # White
        'text_secondary': '#E0E0E0',      # Light gray for regular text
        'text_muted': '#CCCCCC',         # Slightly darker gray
        
        # Border colors
        'border_primary': '#363A4F',
        'border_secondary': '#2D3142',
        
        # Button colors
        'button_bg': '#9D91C4',          # Soft purple as primary button color
        'button_hover': '#aea3d0',       # Lighter purple for hover
        'button_active': '#8c82b3',      # Darker purple for active
        
        # Component colors
        'input_bg': '#363A4F',           # Content background color
        'input_border': '#2D3142',       # Primary background color
        'input_text': '#E0E0E0',         # Regular text color
        
        # Accent colors
        'accent_primary': '#9D91C4',      # Matching button color
        'accent_secondary': '#FF9966',    # Softer orange for occasional use
        'accent_success': '#9ece6a',      # Keeping existing accent colors
        'accent_warning': '#e0af68',      # for notifications and status
        'accent_error': '#f7768e',        # indicators
        'accent_info': '#7dcfff',
        
        # Selection colors
        'selection_bg': '#FF7733',
        'selection_text': '#FFFFFF',
    }
    
    DEFAULT_LIGHT = {
        # Base colors
        'background': '#F8F9FA',          # Soft white (Primary background)
        'background_darker': '#F8F9FA',    # Same as primary for cards
        'background_lighter': '#FFFFFF',   # Pure white for content
        
        # Sidebar specific
        'sidebar_bg': '#2D3142',          # Dark blue-gray for logo area
        'sidebar_hover': '#363A4F',       # Slightly lighter for hover
        'sidebar_active': '#363A4F',      # Same as hover
        'sidebar_text': '#FFFFFF',        # White text
        
        # Text colors
        'text_primary': '#2D3142',        # Dark blue-gray
        'text_secondary': '#4F5569',      # Regular text color
        'text_muted': '#6b7280',         # Muted text
        
        # Border colors
        'border_primary': '#E9ECEF',
        'border_secondary': '#F8F9FA',
        
        # Button colors
        'button_bg': '#2D3142',          # Dark blue-gray matching sidebar
        'button_hover': '#363A4F',       # Slightly lighter for hover
        'button_active': '#252836',      # Slightly darker for active
        
        # Component colors
        'input_bg': '#FFFFFF',           # Pure white
        'input_border': '#E9ECEF',       # Light border
        'input_text': '#2D3142',         # Dark blue-gray text
        
        # Accent colors
        'accent_primary': '#2D3142',      # Matching button color
        'accent_secondary': '#FF7733',    # Keeping orange as secondary accent
        'accent_success': '#22c55e',      # Keeping existing accent colors
        'accent_warning': '#f59e0b',      # for notifications and status
        'accent_error': '#ef4444',        # indicators
        'accent_info': '#3b82f6',
        
        # Selection colors
        'selection_bg': '#FF7733',
        'selection_text': '#FFFFFF',
    }

    def __init__(self):
        super().__init__()
        self.current_theme = "default"

    def get_colors(self, theme_name="default"):
        """Get color palette for specified theme"""
        return self.TOKYO_NIGHT if theme_name == "dark_midnight" else self.DEFAULT_LIGHT

    def get_stylesheet(self, theme_name="default"):
        """Get stylesheet for specified theme"""
        colors = self.get_colors(theme_name)
        
        return f"""
            QWidget#sidebar {{
                background-color: {colors['sidebar_bg']};
                border-right: 1px solid {colors['sidebar_hover']};
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
            
            QLabel {{
                color: {colors['sidebar_text']};
            }}
            
            QTextEdit {{
                background-color: {colors['input_bg']};
                color: {colors['input_text']};
                border: 1px solid {colors['input_border']};
                border-radius: 6px;
                padding: 8px;
                selection-background-color: {colors['selection_bg']};
                selection-color: {colors['selection_text']};
            }}
            
            QLineEdit {{
                background-color: {colors['input_bg']};
                color: {colors['input_text']};
                border: 1px solid {colors['input_border']};
                border-radius: 6px;
                padding: 8px;
                selection-background-color: {colors['selection_bg']};
                selection-color: {colors['selection_text']};
            }}
        """

    def apply_theme(self, widget, theme_name="default"):
        """Apply theme to widget and all its children"""
        stylesheet = self.get_stylesheet(theme_name)
        widget.setStyleSheet(stylesheet)
        self.current_theme = theme_name
        self.theme_changed.emit(theme_name)

    def get_icon_suffix(self):
        """Get the appropriate icon suffix based on current theme"""
        return "_dark" if self.current_theme == "dark_midnight" else ""