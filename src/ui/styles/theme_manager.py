from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import QObject, pyqtSignal

class ThemeManager(QObject):
    """Centralized theme management system for GatherScribe"""
    
    theme_changed = pyqtSignal(str)
    
    TOKYO_NIGHT = {
        # Base colors
        'background': '#1a1b26',
        'background_darker': '#16161e',
        'background_lighter': '#24283b',
        
        # Accent colors
        'accent_primary': '#bb9af7',    # Purple accent
        'accent_secondary': '#7aa2f7',   # Blue accent
        'accent_success': '#9ece6a',     # Green accent
        'accent_warning': '#e0af68',     # Orange accent
        'accent_error': '#f7768e',       # Red accent
        
        # Text colors
        'text_primary': '#c0caf5',
        'text_secondary': '#a9b1d6',
        'text_muted': '#565f89',
        
        # Border colors
        'border_primary': '#414868',
        'border_secondary': '#363b54',
        
        # Component specific
        'sidebar_bg': '#13141c',          # Darker than background
        'sidebar_hover': '#1c1d28',
        'input_bg': '#1f2335',
        'button_bg': '#7aa2f7',
        'button_hover': '#89b4fa',
        'button_active': '#6b91e4',
    }
    
    DEFAULT_LIGHT = {
        # Base colors
        'background': '#ffffff',
        'background_darker': '#f8f9fa',
        'background_lighter': '#ffffff',
        
        # Accent colors
        'accent_primary': '#7c3aed',    # Purple accent
        'accent_secondary': '#3b82f6',   # Blue accent
        'accent_success': '#22c55e',     # Green accent
        'accent_warning': '#f59e0b',     # Orange accent
        'accent_error': '#ef4444',       # Red accent
        
        # Text colors
        'text_primary': '#111827',
        'text_secondary': '#374151',
        'text_muted': '#6b7280',
        
        # Border colors
        'border_primary': '#e5e7eb',
        'border_secondary': '#f3f4f6',
        
        # Component specific
        'sidebar_bg': '#f1f5f9',
        'sidebar_hover': '#e2e8f0',
        'input_bg': '#ffffff',
        'button_bg': '#7c3aed',
        'button_hover': '#6d28d9',
        'button_active': '#5b21b6',
    }

    def __init__(self):
        super().__init__()
        self.current_theme = "default"
        self._transitions_enabled = True

    def get_colors(self, theme_name="default"):
        """Get color palette for specified theme"""
        return self.TOKYO_NIGHT if theme_name == "dark_midnight" else self.DEFAULT_LIGHT

    def get_stylesheet(self, theme_name="default", widget_type=None):
        """Get stylesheet for specified theme and widget type"""
        colors = self.get_colors(theme_name)
        
        base_styles = f"""
            /* Base styles */
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }}
            
            /* Main window styles */
            QMainWindow {{
                background-color: {colors['background']};
            }}
            
            /* Button styles */
            QPushButton {{
                background-color: {colors['button_bg']};
                color: {'#ffffff' if theme_name == 'dark_midnight' else '#ffffff'};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            
            QPushButton:hover {{
                background-color: {colors['button_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['button_active']};
            }}
            
            /* Input styles */
            QLineEdit, QTextEdit {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['border_primary']};
                border-radius: 6px;
                padding: 8px;
                color: {colors['text_primary']};
            }}
            
            /* Combobox styles */
            QComboBox {{
                background-color: {colors['input_bg']};
                border: 1px solid {colors['border_primary']};
                border-radius: 6px;
                padding: 8px;
                color: {colors['text_primary']};
            }}
            
            /* Sidebar specific styles */
            QWidget#sidebar {{
                background-color: {colors['sidebar_bg']};
                border-right: 1px solid {colors['border_primary']};
            }}
            
            QLabel#sidebar_title {{
                color: {colors['text_primary']};
                font-weight: bold;
                font-size: 15px;
                padding: 10px;
            }}
            
            /* Dialog styles */
            QDialog {{
                background-color: {colors['background']};
            }}
        """
        
        # Add transition styles if enabled
        if self._transitions_enabled:
            base_styles += """
                * {
                    transition: background-color 0.15s ease-in-out,
                              color 0.15s ease-in-out,
                              border-color 0.15s ease-in-out;
                }
            """
        
        return base_styles

    def apply_theme(self, widget, theme_name="default"):
        """Apply theme to widget and all its children"""
        stylesheet = self.get_stylesheet(theme_name, type(widget).__name__)
        widget.setStyleSheet(stylesheet)
        self.current_theme = theme_name
        self.theme_changed.emit(theme_name)

    def get_icon_suffix(self):
        """Get the appropriate icon suffix based on current theme"""
        return "_dark" if self.current_theme == "dark_midnight" else ""

    def enable_transitions(self, enabled=True):
        """Enable or disable theme transition animations"""
        self._transitions_enabled = enabled