"""
Styles and theme for the main window UI.
Dark mode using zinc scale from the web app's globals.css.
"""

# ── Color Palette (zinc dark mode) ───────────────────────────

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
BLUE = "#60a5fa"            # blue-400

FONT = '"JetBrains Mono", "Cascadia Code", "Consolas", monospace'

# ── SVG Icons ────────────────────────────────────────────────

SVG_SETTINGS = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>'
SVG_CLOSE = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>'
SVG_EXTERNAL = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'
SVG_AUDIO_LINES = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10v3"/><path d="M6 6v11"/><path d="M10 3v18"/><path d="M14 8v7"/><path d="M18 5v13"/><path d="M22 10v3"/></svg>'
SVG_BACK = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>'
SVG_MODELS = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>'


# ── Style Helpers ────────────────────────────────────────────

def _btn(
    bg: str = "transparent",
    color: str = TEXT,
    hover_bg: str | None = None,
    hover_color: str | None = None,
    border: str = "none",
    radius: int = 4,
    font_size: int = 14,
    font_weight: str = "500",
    padding: str = "6px 12px",
) -> str:
    """Generate a QPushButton stylesheet with optional hover state."""
    base = (
        f"QPushButton {{"
        f" background-color: {bg};"
        f" border: {border};"
        f" border-radius: {radius}px;"
        f" color: {color};"
        f" font-size: {font_size}px;"
        f" font-weight: {font_weight};"
        f" padding: {padding};"
        f" }}"
    )
    if hover_bg or hover_color:
        hover_parts = []
        if hover_bg:
            hover_parts.append(f"background-color: {hover_bg};")
        if hover_color:
            hover_parts.append(f"color: {hover_color};")
        base += f" QPushButton:hover {{ {' '.join(hover_parts)} }}"
    return base


def _dot(color: str) -> str:
    return f"background-color: {color}; border-radius: 4px;"


def _label(color: str, font_size: int = 14, font_weight: str = "500") -> str:
    return f"color: {color}; font-size: {font_size}px; font-weight: {font_weight};"


# ── Global Stylesheet ────────────────────────────────────────

GLOBAL_STYLE = f"""
    QMainWindow {{ background-color: transparent; }}
    QWidget {{
        background-color: transparent;
        color: {TEXT};
        font-family: {FONT};
        font-size: 14px;
    }}
    QLabel {{ background: transparent; }}
    QCheckBox {{
        spacing: 8px; color: {TEXT_DIM}; background: transparent; padding: 4px 0;
    }}
    QCheckBox::indicator {{
        width: 16px; height: 16px; border-radius: 3px;
        border: 1px solid {BORDER}; background-color: {BG};
    }}
    QCheckBox::indicator:checked {{
        background-color: {PRIMARY}; border-color: {PRIMARY};
    }}
    QCheckBox:hover {{ color: {TEXT}; }}
    QComboBox {{
        background-color: {MUTED}; border: 1px solid {BORDER}; border-radius: 4px;
        padding: 6px 12px; color: {TEXT}; min-height: 20px;
    }}
    QComboBox:hover {{ border-color: {TEXT_DIM}; }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent; border-right: 4px solid transparent;
        border-top: 5px solid {TEXT}; margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {MUTED}; border: 1px solid {BORDER};
        color: {TEXT}; selection-background-color: {SECONDARY};
        outline: none;
    }}
    QComboBox QFrame {{
        background-color: {MUTED}; border: 1px solid {BORDER}; border-radius: 4px;
    }}
    QComboBox QAbstractItemView QScrollBar:vertical {{
        background: {MUTED};
    }}
    QComboBox QListView {{
        background-color: {MUTED};
    }}
    QComboBox QListView::item {{
        background-color: {MUTED}; color: {TEXT};
        padding: 4px 8px; min-height: 24px;
    }}
    QComboBox QListView::item:selected {{
        background-color: {SECONDARY};
    }}
    QLineEdit {{
        background-color: {BG}; border: 1px solid {BORDER}; border-radius: 4px;
        padding: 8px 10px; color: {TEXT}; letter-spacing: 2px;
    }}
    QLineEdit:focus {{ border-color: {TEXT_DIM}; }}
    QScrollBar:vertical {{ background: transparent; width: 6px; border: none; }}
    QScrollBar::handle:vertical {{
        background: {SECONDARY}; border-radius: 3px; min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""

# ── Status Dots ──────────────────────────────────────────────

DOT_IDLE = _dot(TEXT_DIM)
DOT_RECORDING = _dot(RED)
DOT_PROCESSING = _dot(AMBER)
DOT_SUCCESS = _dot(GREEN)
DOT_EDITING = _dot(BLUE)

# ── Header Buttons ───────────────────────────────────────────

HEADER_BUTTON = _btn(padding="4px", hover_bg=MUTED, font_weight="normal")
HEADER_BUTTON_CLOSE = _btn(padding="4px", hover_bg="rgba(239, 68, 68, 0.1)", font_weight="normal")
HEADER_BUTTON_ACTIVE = _btn(bg=MUTED, padding="4px", font_weight="normal")

# ── Format Tabs ──────────────────────────────────────────────

TAB_BUTTON = _btn(color=TEXT_DIM, radius=3, padding="4px 10px", hover_bg=MUTED, hover_color=TEXT)
TAB_BUTTON_ACTIVE = _btn(bg=PRIMARY, color=PRIMARY_FG, radius=3, padding="4px 10px")
TAB_BUTTON_DISABLED = _btn(color="rgba(113, 113, 122, 0.5)", radius=3, padding="4px 10px")

# ── Content ──────────────────────────────────────────────────

CONTENT_TEXT = f"""
    QTextEdit {{
        background-color: transparent; border: none;
        color: {TEXT}; font-size: 14px; padding: 0;
    }}
"""

IDLE_TEXT = _label(TEXT_DIM, font_weight="normal")
IDLE_TEXT_BOLD = _label(TEXT)

RECORDING_LABEL = _label(RED)
PROCESSING_LABEL = _label(AMBER)
EDITING_LABEL = _label(BLUE)

TIMER_RECORDING = _label("#f87171", font_weight="normal")
TIMER_PROCESSING = _label(AMBER, font_weight="normal")
TIMER_EDITING = _label(BLUE, font_weight="normal")

# ── Footer Buttons ───────────────────────────────────────────

RECORD_BUTTON_IDLE = _btn(bg=PRIMARY, color=PRIMARY_FG, hover_bg="rgba(244, 244, 245, 0.8)")
RECORD_BUTTON_RECORDING = _btn(bg="#dc2626", color="white", hover_bg="#b91c1c")
RECORD_BUTTON_PROCESSING = _btn(bg=AMBER, color=PRIMARY_FG)
RECORD_BUTTON_EDITING = _btn(bg=BLUE, color=PRIMARY_FG)

FOOTER_TEXT_BUTTON = _btn(color=TEXT_DIM, padding="6px 8px", hover_color=TEXT, font_weight="normal")
FOOTER_TEXT_BUTTON_SUCCESS = _btn(bg="transparent", color=GREEN, padding="6px 8px")

# ── Settings ─────────────────────────────────────────────────

SECTION_LABEL = _label(TEXT_DIM, font_size=11, font_weight="bold") + " letter-spacing: 1px;"
SETTINGS_TITLE = f"color: {TEXT}; padding-left: 4px;"

ICON_BUTTON = _btn(padding="0", hover_bg=MUTED, font_weight="normal")

FLAT_BUTTON = _btn(
    bg=MUTED, border=f"1px solid {BORDER}",
    font_size=13, padding="0 12px", hover_bg=SECONDARY,
)

ACCENT_BUTTON = _btn(
    bg=PRIMARY, color=PRIMARY_FG,
    font_size=13, font_weight="bold", padding="0 16px",
    hover_bg="rgba(244, 244, 245, 0.8)",
)

SEPARATOR = f"background-color: {BORDER};"

# ── Tray Menu ────────────────────────────────────────────────

TRAY_MENU_STYLE = f"""
    QMenu {{
        background-color: {MUTED}; border: 1px solid {BORDER};
        border-radius: 8px; padding: 4px;
        font-family: {FONT}; font-size: 14px;
    }}
    QMenu::item {{
        background-color: transparent; color: {TEXT};
        padding: 6px 16px 6px 12px; border-radius: 4px; margin: 1px 2px;
    }}
    QMenu::item:selected {{ background-color: {SECONDARY}; color: {TEXT}; }}
    QMenu::item:disabled {{ color: {TEXT_DIM}; }}
    QMenu::separator {{ height: 1px; background-color: {BORDER}; margin: 4px 8px; }}
"""
