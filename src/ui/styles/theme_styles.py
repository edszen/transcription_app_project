class ThemeStyles:
    """Handles application-wide theming"""
    
    @staticmethod
    def get_theme_colors(theme="default"):
        """Get color palette for specified theme"""
        if theme == "default":
            return {
                'sidebar_bg': '#f8f9fa',
                'main_bg': '#ffffff',
                'text': '#333333',
                'hover_bg': '#f0f0f0',
                'border': '#e0e0e0',
            }
        else:  # dark theme
            return {
                'sidebar_bg': '#16161e',
                'main_bg': '#1a1b26',
                'text': '#c0caf5',
                'hover_bg': '#24283b',
                'border': '#414868',
            }

    @staticmethod
    def get_sidebar_styles(colors):
        """Get styles specific to sidebar"""
        return f"""
            QWidget#sidebar {{
                background-color: {colors['sidebar_bg']};
                border-right: 1px solid {colors['border']};
            }}
            
            QLabel#sidebar_title {{
                color: {colors['text']};
                font-weight: bold;
                font-size: 15px;
                padding: 10px;
            }}
            
            QPushButton {{
                background-color: transparent;
                color: {colors['text']};
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                text-align: left;
            }}
            
            QPushButton:hover {{
                background-color: {colors['hover_bg']};
            }}
        """

    @staticmethod
    def apply_theme(widget, theme="default"):
        """Apply theme to a widget"""
        colors = ThemeStyles.get_theme_colors(theme)
        if widget.objectName() == "sidebar":
            widget.setStyleSheet(ThemeStyles.get_sidebar_styles(colors))