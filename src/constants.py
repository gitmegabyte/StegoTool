# Disable __pycache__
import sys
sys.dont_write_bytecode = True

# Magic bytes
MAGIC_LSB = b'STEGO\x00'
MAGIC_APP = b'\x00HIDDEN_FILE_START\x00'
END_APP = b'\x00HIDDEN_FILE_END\x00'
ENCRYPT_MARKER = b'ENCRYPTED_AES256_GCM_'

# Themes
THEMES = {
    "light": {
        "WIN_BG": "#f0f0f0",
        "SIDEBAR_BG": "#eef1f5",
        "SECTION_BG": "#d9dee5",
        "ITEM_BG": "#ffffff",
        "ITEM_SEL_BG": "#cfe6fb",
        "ITEM_HOV_BG": "#e6f0fa",
        "BORDER": "#a0a0a0",
        "BORDER_LIGHT": "#c8c8c8",
        "TEXT": "#000000",
        "TEXT_DIM": "#333333",
        "TEXT_MUTE": "#666666",
        "ACCENT": "#0a5fb4",
        "BTN_BG": "#e1e1e1",
        "BTN_HOV": "#ececec",
        "BTN_PRESS": "#d6d6d6",
        "ENTRY_BG": "#ffffff",
        "ENTRY_DISABLED": "#e8e8e8",
        "SUCCESS": "#1a7d1a",
        "ERROR": "#c0392b",
        "WARN": "#b5890a",
        "INFO": "#0a5fb4",
        "MENU_BG": "#f0f0f0",
        "MENU_HOV": "#cfe6fb",
    },
    "dark": {
        "WIN_BG": "#1a1b1e",
        "SIDEBAR_BG": "#25262c",
        "SECTION_BG": "#2d2f36",
        "ITEM_BG": "#25262c",
        "ITEM_SEL_BG": "#374a63",
        "ITEM_HOV_BG": "#2d3844",
        "BORDER": "#3d3f46",
        "BORDER_LIGHT": "#4a4c54",
        "TEXT": "#f0f0f0",
        "TEXT_DIM": "#d0d0d0",
        "TEXT_MUTE": "#b0b0b8",
        "ACCENT": "#6b9fd5",
        "BTN_BG": "#3a3b42",
        "BTN_HOV": "#4a4b54",
        "BTN_PRESS": "#2c2d33",
        "ENTRY_BG": "#2d2f36",
        "ENTRY_DISABLED": "#2d2f36",
        "SUCCESS": "#4cbf4c",
        "ERROR": "#e87065",
        "WARN": "#e8c040",
        "INFO": "#6b9fd5",
        "MENU_BG": "#2d2f36",
        "MENU_HOV": "#374a63",
    },
}