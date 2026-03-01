"""
Styles and theme for the main window UI.
"""

# -- Color Palette --
BG = "#1a1a1a"
BG_SECONDARY = "#232323"
BG_HOVER = "#2a2a2a"
BORDER = "#333333"
TEXT = "#e0e0e0"
TEXT_DIM = "#777777"
TEXT_MUTED = "#555555"
ACCENT = "#6c8cbf"
ACCENT_HOVER = "#7d9dd0"
RED = "#c45c5c"
RED_HOVER = "#d46c6c"
GREEN = "#5c9a6c"

# -- SVG Icons (Lucide-style) --
SVG_MIC = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>'
SVG_SQUARE = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>'
SVG_COPY = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'
SVG_SETTINGS = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>'
SVG_BACK = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>'

# -- Global stylesheet --
GLOBAL_STYLE = f"""
    QMainWindow {{
        background-color: {BG};
    }}
    QWidget {{
        background-color: {BG};
        color: {TEXT};
        font-family: "Segoe UI", "Inter", "SF Pro Display", sans-serif;
        font-size: 13px;
    }}
    QLabel {{
        background: transparent;
    }}
    QCheckBox {{
        spacing: 8px;
        color: {TEXT_DIM};
        background: transparent;
        padding: 4px 0;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 3px;
        border: 1px solid {BORDER};
        background-color: {BG_SECONDARY};
    }}
    QCheckBox::indicator:checked {{
        background-color: {ACCENT};
        border-color: {ACCENT};
    }}
    QCheckBox:hover {{
        color: {TEXT};
    }}
    QComboBox {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 6px 12px;
        color: {TEXT};
        min-height: 20px;
    }}
    QComboBox:hover {{
        border-color: {TEXT_MUTED};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER};
        color: {TEXT};
        selection-background-color: {BG_HOVER};
    }}
    QLineEdit {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px 12px;
        color: {TEXT};
    }}
    QLineEdit:focus {{
        border-color: {ACCENT};
    }}
    QTextEdit {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 8px;
        color: {TEXT};
        selection-background-color: {ACCENT};
    }}
    QScrollBar:vertical {{
        background: {BG};
        width: 6px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 3px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
"""

# -- Component styles --
TRANSCRIPTION_TEXT = f"""
    QTextEdit {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 12px;
        color: {TEXT};
        font-size: 13px;
    }}
"""

ICON_BUTTON = f"""
    QPushButton {{
        background: transparent;
        border: none;
        border-radius: 6px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
    }}
"""

STATUS_LABEL = f"color: {TEXT_MUTED}; font-size: 11px;"

SECTION_LABEL = f"color: {TEXT_MUTED}; font-size: 10px; font-weight: bold; letter-spacing: 1px;"

SETTINGS_TITLE = f"color: {TEXT}; padding-left: 4px;"

FLAT_BUTTON = f"""
    QPushButton {{
        background-color: {BG_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        color: {TEXT_DIM};
        font-size: 12px;
        padding: 0 16px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        color: {TEXT};
    }}
"""

ACCENT_BUTTON = f"""
    QPushButton {{
        background-color: {ACCENT};
        border: none;
        border-radius: 6px;
        color: #ffffff;
        font-size: 12px;
        font-weight: bold;
        padding: 0 20px;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
"""

TOOLBAR_BUTTON = f"""
    QPushButton {{
        background: transparent;
        border: 1px solid {BORDER};
        border-radius: 6px;
        color: {TEXT_DIM};
        font-size: 12px;
        padding: 0 12px;
    }}
    QPushButton:hover {{
        background-color: {BG_HOVER};
        color: {TEXT};
        border-color: {TEXT_MUTED};
    }}
"""

RECORD_BUTTON_IDLE = f"""
    QPushButton {{
        background-color: {ACCENT};
        border: none;
        border-radius: 6px;
        color: #ffffff;
        font-size: 12px;
        font-weight: bold;
        padding: 0 12px;
    }}
    QPushButton:hover {{
        background-color: {ACCENT_HOVER};
    }}
"""

RECORD_BUTTON_RECORDING = f"""
    QPushButton {{
        background-color: {RED};
        border: none;
        border-radius: 6px;
        color: #ffffff;
        font-size: 12px;
        font-weight: bold;
        padding: 0 12px;
    }}
    QPushButton:hover {{
        background-color: {RED_HOVER};
    }}
"""

SEPARATOR = f"background-color: {BORDER};"
