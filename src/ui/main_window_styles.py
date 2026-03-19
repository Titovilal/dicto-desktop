"""
Styles and theme for the main window UI.
Dark mode using zinc scale from the web app's globals.css.
"""

# -- Color Palette (zinc dark mode) --
BG = "#09090b"              # zinc-950  --background
MUTED = "#18181b"           # zinc-900  --muted / --accent
SECONDARY = "#27272a"       # zinc-800  --secondary / --border
BORDER = "#27272a"          # zinc-800  --border
TEXT = "#f4f4f5"            # zinc-100  --foreground
TEXT_DIM = "#71717a"        # zinc-500  --muted-foreground
PRIMARY = "#d4d4d8"         # zinc-300  --primary
PRIMARY_FG = "#18181b"      # zinc-900  --primary-foreground
RED = "#ef4444"             # red-500
RED_HOVER = "#dc2626"       # red-600
AMBER = "#fbbf24"           # amber-400
GREEN = "#34d399"           # emerald-400

# -- SVG Icons --
SVG_SETTINGS = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>'
SVG_CLOSE = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>'
SVG_EXTERNAL = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'
SVG_AUDIO_LINES = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10v3"/><path d="M6 6v11"/><path d="M10 3v18"/><path d="M14 8v7"/><path d="M18 5v13"/><path d="M22 10v3"/></svg>'
SVG_BACK = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>'

# -- Global stylesheet --
GLOBAL_STYLE = f"""
    QMainWindow {{
        background-color: transparent;
    }}
    QWidget {{
        background-color: transparent;
        color: {TEXT};
        font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
        font-size: 14px;
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
        background-color: {BG};
    }}
    QCheckBox::indicator:checked {{
        background-color: {PRIMARY};
        border-color: {PRIMARY};
    }}
    QCheckBox:hover {{
        color: {TEXT};
    }}
    QComboBox {{
        background-color: {BG};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 6px 12px;
        color: {TEXT};
        min-height: 20px;
    }}
    QComboBox:hover {{
        border-color: {TEXT_DIM};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {TEXT};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {BG};
        border: 1px solid {BORDER};
        color: {TEXT};
        selection-background-color: {MUTED};
    }}
    QLineEdit {{
        background-color: {BG};
        border: 1px solid {BORDER};
        border-radius: 4px;
        padding: 8px 10px;
        color: {TEXT};
    }}
    QLineEdit:focus {{
        border-color: {TEXT_DIM};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {SECONDARY};
        border-radius: 3px;
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
"""

# -- Status dot --
DOT_IDLE = f"background-color: {TEXT_DIM}; border-radius: 4px;"
DOT_RECORDING = f"background-color: {RED}; border-radius: 4px;"
DOT_PROCESSING = f"background-color: {AMBER}; border-radius: 4px;"
DOT_SUCCESS = f"background-color: {GREEN}; border-radius: 4px;"

# -- Header buttons --
HEADER_BUTTON = f"""
    QPushButton {{
        background: transparent;
        border: none;
        border-radius: 4px;
        padding: 4px;
    }}
    QPushButton:hover {{
        background-color: {MUTED};
    }}
"""

HEADER_BUTTON_CLOSE = f"""
    QPushButton {{
        background: transparent;
        border: none;
        border-radius: 4px;
        padding: 4px;
    }}
    QPushButton:hover {{
        background-color: rgba(239, 68, 68, 0.1);
    }}
"""

HEADER_BUTTON_ACTIVE = f"""
    QPushButton {{
        background-color: {MUTED};
        border: none;
        border-radius: 4px;
        padding: 4px;
    }}
"""

# -- Format tabs --
TAB_BUTTON = f"""
    QPushButton {{
        background: transparent;
        border: none;
        border-radius: 3px;
        color: {TEXT_DIM};
        font-size: 14px;
        font-weight: 500;
        padding: 2px 8px;
    }}
    QPushButton:hover {{
        background-color: {MUTED};
        color: {TEXT};
    }}
"""

TAB_BUTTON_ACTIVE = f"""
    QPushButton {{
        background-color: {PRIMARY};
        border: none;
        border-radius: 3px;
        color: {PRIMARY_FG};
        font-size: 14px;
        font-weight: 500;
        padding: 2px 8px;
    }}
"""

TAB_BUTTON_DISABLED = f"""
    QPushButton {{
        background: transparent;
        border: none;
        border-radius: 3px;
        color: rgba(113, 113, 122, 0.5);
        font-size: 14px;
        font-weight: 500;
        padding: 2px 8px;
    }}
"""

# -- Content --
CONTENT_TEXT = f"""
    QTextEdit {{
        background-color: transparent;
        border: none;
        color: {TEXT};
        font-size: 14px;
        padding: 0;
    }}
"""

IDLE_TEXT = f"color: {TEXT_DIM}; font-size: 14px;"
IDLE_TEXT_BOLD = f"color: {TEXT}; font-size: 14px; font-weight: 500;"

RECORDING_LABEL = f"color: {RED}; font-size: 14px; font-weight: 500;"
PROCESSING_LABEL = f"color: {AMBER}; font-size: 14px; font-weight: 500;"

TIMER_RECORDING = f"color: #f87171; font-size: 14px;"
TIMER_PROCESSING = f"color: {AMBER}; font-size: 14px;"

# -- Footer --
RECORD_BUTTON_IDLE = f"""
    QPushButton {{
        background-color: {PRIMARY};
        border: none;
        border-radius: 4px;
        color: {PRIMARY_FG};
        font-size: 14px;
        font-weight: 500;
        padding: 6px 12px;
    }}
    QPushButton:hover {{
        background-color: rgba(244, 244, 245, 0.8);
    }}
"""

RECORD_BUTTON_RECORDING = f"""
    QPushButton {{
        background-color: #dc2626;
        border: none;
        border-radius: 4px;
        color: white;
        font-size: 14px;
        font-weight: 500;
        padding: 6px 12px;
    }}
    QPushButton:hover {{
        background-color: #b91c1c;
    }}
"""

RECORD_BUTTON_PROCESSING = f"""
    QPushButton {{
        background-color: {AMBER};
        border: none;
        border-radius: 4px;
        color: {PRIMARY_FG};
        font-size: 14px;
        font-weight: 500;
        padding: 6px 12px;
    }}
"""

FOOTER_TEXT_BUTTON = f"""
    QPushButton {{
        background: transparent;
        border: none;
        color: {TEXT_DIM};
        font-size: 14px;
        padding: 6px 8px;
    }}
    QPushButton:hover {{
        color: {TEXT};
    }}
"""

FOOTER_TEXT_BUTTON_SUCCESS = f"""
    QPushButton {{
        background: transparent;
        border: none;
        color: {GREEN};
        font-size: 14px;
        font-weight: 500;
        padding: 6px 8px;
    }}
"""

# -- Settings --
SECTION_LABEL = f"color: {TEXT_DIM}; font-size: 11px; font-weight: bold; letter-spacing: 1px;"
SETTINGS_TITLE = f"color: {TEXT}; padding-left: 4px;"

ICON_BUTTON = f"""
    QPushButton {{
        background: transparent;
        border: none;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        background-color: {MUTED};
    }}
"""

FLAT_BUTTON = f"""
    QPushButton {{
        background-color: {MUTED};
        border: 1px solid {BORDER};
        border-radius: 4px;
        color: {TEXT};
        font-size: 13px;
        padding: 0 12px;
    }}
    QPushButton:hover {{
        background-color: {SECONDARY};
    }}
"""

ACCENT_BUTTON = f"""
    QPushButton {{
        background-color: {PRIMARY};
        border: none;
        border-radius: 4px;
        color: {PRIMARY_FG};
        font-size: 13px;
        font-weight: bold;
        padding: 0 16px;
    }}
    QPushButton:hover {{
        background-color: rgba(244, 244, 245, 0.8);
    }}
"""

SEPARATOR = f"background-color: {BORDER};"

# -- Tray menu --
TRAY_MENU_STYLE = f"""
    QMenu {{
        background-color: {MUTED};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 4px;
        font-family: "JetBrains Mono", "Cascadia Code", "Consolas", monospace;
        font-size: 14px;
    }}
    QMenu::item {{
        background-color: transparent;
        color: {TEXT};
        padding: 6px 16px 6px 12px;
        border-radius: 4px;
        margin: 1px 2px;
    }}
    QMenu::item:selected {{
        background-color: {SECONDARY};
        color: {TEXT};
    }}
    QMenu::item:disabled {{
        color: {TEXT_DIM};
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {BORDER};
        margin: 4px 8px;
    }}
"""
