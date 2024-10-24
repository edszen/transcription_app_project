from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)
    
    TOKYO_NIGHT = {
        # Base colors - matched to blue logo
        'background': '#1a1b26',
        'background_darker': '#16161e',
        'background_lighter': '#24283b',
        
        ## Sidebar specific - swapped base and hover colors
        'sidebar_bg': '#4AB8C9',          # Light blue from logo (now main color)
        'sidebar_hover': '#1f2335',       # Dark background (now hover color)
        'sidebar_active': '#292e42',      # Slightly lighter than hover
        'sidebar_text': '#FFFFFF',        # White text for contrast
        
        # Text colors
        'text_primary': '#c0caf5',
        'text_secondary': '#a9b1d6',
        'text_muted': '#565f89',
        
        # Border colors
        'border_primary': '#414868',
        'border_secondary': '#363b54',
        
        # Button colors
        'button_bg': '#7aa2f7',
        'button_hover': '#89b4fa',
        'button_active': '#6b91e4',
        
        # Component colors
        'input_bg': '#1f2335',
        'input_border': '#414868',
        'input_text': '#c0caf5',
        
        # Accent colors
        'accent_primary': '#bb9af7',    # Purple accent
        'accent_secondary': '#7aa2f7',   # Blue accent
        'accent_success': '#9ece6a',     # Green accent
        'accent_warning': '#e0af68',     # Orange accent
        'accent_error': '#f7768e',       # Red accent
        'accent_info': '#7dcfff',        # Light blue accent
        
        # Selection colors
        'selection_bg': '#bb9af7',
        'selection_text': '#ffffff',
    }
    
    DEFAULT_LIGHT = {
        # Base colors
        'background': '#ffffff',
        'background_darker': '#f8f9fa',
        'background_lighter': '#ffffff',
        
        # Sidebar specific - matched to beige logo
        'sidebar_bg': '#F5EFE6',          # Beige from logo (now main color)
        'sidebar_hover': '#e8e9ed',       # Light grey (now hover color)
        'sidebar_active': '#d8d9dd',      # Slightly darker than hover
        'sidebar_text': '#333333',        # Dark text for contrast
        
        # Text colors
        'text_primary': '#333333',
        'text_secondary': '#4a4a4a',
        'text_muted': '#6b7280',
        
        # Border colors
        'border_primary': '#e5e7eb',
        'border_secondary': '#f3f4f6',
        
        # Button colors
        'button_bg': '#826f8b',
        'button_hover': '#695f73',
        'button_active': '#574d5f',
        
        # Component colors
        'input_bg': '#ffffff',
        'input_border': '#e5e7eb',
        'input_text': '#333333',
        
        # Accent colors
        'accent_primary': '#826f8b',    # Purple accent
        'accent_secondary': '#695f73',   # Grey accent
        'accent_success': '#22c55e',     # Green accent
        'accent_warning': '#f59e0b',     # Orange accent
        'accent_error': '#ef4444',       # Red accent
        'accent_info': '#3b82f6',        # Blue accent
        
        # Selection colors
        'selection_bg': '#826f8b',
        'selection_text': '#ffffff',
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