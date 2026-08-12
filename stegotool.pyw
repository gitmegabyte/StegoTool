import sys
import subprocess
import os
import struct
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

# ============================================================================
# VERIFICA E INSTALLAZIONE DIPENDENZE
# ============================================================================

def ensure_dependencies_with_popup():
    """Check and install dependencies with progress popup"""
    global PIL_AVAILABLE, CRYPTO_AVAILABLE
    
    progress_window = tk.Tk()
    progress_window.title("Dependencies")
    progress_window.geometry("400x180")
    progress_window.resizable(False, False)
    progress_window.configure(bg="#1e1f24")
    
    progress_window.update_idletasks()
    width = 400
    height = 180
    x = (progress_window.winfo_screenwidth() // 2) - (width // 2)
    y = (progress_window.winfo_screenheight() // 2) - (height // 2)
    progress_window.geometry(f'{width}x{height}+{x}+{y}')
    
    title_label = tk.Label(progress_window, text="Preparing...", 
                          font=("Segoe UI", 12, "bold"), bg="#1e1f24", fg="#f0f0f0")
    title_label.pack(pady=(20, 5))
    
    status_label = tk.Label(progress_window, text="Checking dependencies...", 
                           font=("Segoe UI", 10), bg="#1e1f24", fg="#9a9ba3")
    status_label.pack(pady=5)
    
    progress_bar = ttk.Progressbar(progress_window, length=300, mode='indeterminate')
    progress_bar.pack(pady=10)
    progress_bar.start(10)
    
    progress_window.update()
    
    try:
        # Check Pillow
        try:
            from PIL import Image
            PIL_AVAILABLE = True
        except ImportError:
            status_label.config(text="Installing Pillow...")
            progress_window.update()
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "Pillow", "--quiet"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception("Pillow installation failed")
            import importlib
            importlib.invalidate_caches()
            from PIL import Image
            PIL_AVAILABLE = True
        
        # Check cryptography
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            CRYPTO_AVAILABLE = True
        except ImportError:
            status_label.config(text="Installing cryptography...")
            progress_window.update()
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "cryptography", "--quiet"],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception("cryptography installation failed")
            import importlib
            importlib.invalidate_caches()
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            CRYPTO_AVAILABLE = True
        
        status_label.config(text="✓ All dependencies installed!", fg="#3fbf3f")
        progress_bar.stop()
        progress_window.update()
        time.sleep(0.5)
        progress_window.destroy()
        return True, None
        
    except Exception as e:
        progress_bar.stop()
        progress_window.destroy()
        return False, str(e)

PIL_AVAILABLE = False
CRYPTO_AVAILABLE = False

# ============================================================================
# COSTANTI E TEMI
# ============================================================================

THEMES = {
    "light": {
        "WIN_BG":       "#f0f0f0",
        "SIDEBAR_BG":   "#eef1f5",
        "SECTION_BG":   "#d9dee5",
        "ITEM_BG":      "#ffffff",
        "ITEM_SEL_BG":  "#cfe6fb",
        "ITEM_HOV_BG":  "#e6f0fa",
        "BORDER":       "#a0a0a0",
        "BORDER_LIGHT": "#c8c8c8",
        "TEXT":         "#000000",
        "TEXT_DIM":     "#333333",
        "TEXT_MUTE":    "#666666",
        "ACCENT":       "#0a5fb4",
        "BTN_BG":       "#e1e1e1",
        "BTN_HOV":      "#ececec",
        "BTN_PRESS":    "#d6d6d6",
        "ENTRY_BG":     "#ffffff",
        "ENTRY_DISABLED": "#e8e8e8",
        "SUCCESS":      "#1a7d1a",
        "ERROR":        "#c0392b",
        "WARN":         "#b5890a",
        "INFO":         "#0a5fb4",
        "MENU_BG":      "#f0f0f0",
        "MENU_HOV":     "#cfe6fb",
    },
    "dark": {
        "WIN_BG":       "#1a1b1e",
        "SIDEBAR_BG":   "#25262c",
        "SECTION_BG":   "#2d2f36",
        "ITEM_BG":      "#25262c",
        "ITEM_SEL_BG":  "#374a63",
        "ITEM_HOV_BG":  "#2d3844",
        "BORDER":       "#3d3f46",
        "BORDER_LIGHT": "#4a4c54",
        "TEXT":         "#f0f0f0",
        "TEXT_DIM":     "#d0d0d0",
        "TEXT_MUTE":    "#b0b0b8",
        "ACCENT":       "#6b9fd5",
        "BTN_BG":       "#3a3b42",
        "BTN_HOV":      "#4a4b54",
        "BTN_PRESS":    "#2c2d33",
        "ENTRY_BG":     "#2d2f36",
        "ENTRY_DISABLED": "#2d2f36",  # Stesso colore anche quando disabilitato
        "SUCCESS":      "#4cbf4c",
        "ERROR":        "#e87065",
        "WARN":         "#e8c040",
        "INFO":         "#6b9fd5",
        "MENU_BG":      "#2d2f36",
        "MENU_HOV":     "#374a63",
    },
}

MAGIC_LSB = b'STEGO\x00'
MAGIC_APP = b'\x00HIDDEN_FILE_START\x00'
END_APP   = b'\x00HIDDEN_FILE_END\x00'
ENCRYPT_MARKER = b'ENCRYPTED_AES256_GCM_'

# ============================================================================
# CLASSI UI
# ============================================================================

class Toast:
    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors
        self.toasts = []
        self.max_toasts = 3

    def show(self, message, type_="success", duration=3000):
        C = self.colors
        toast = tk.Frame(self.parent, bg=C["ITEM_BG"])
        toast.configure(highlightbackground=C["BORDER"], highlightthickness=1)

        colors = {"success": C["SUCCESS"], "error": C["ERROR"], "warning": C["WARN"], "info": C["INFO"]}
        color = colors.get(type_, C["SUCCESS"])

        bar = tk.Frame(toast, bg=color, width=4)
        bar.pack(side="left", fill="y")

        content = tk.Frame(toast, bg=C["ITEM_BG"], padx=16, pady=12)
        content.pack(side="left", fill="both", expand=True)

        icon = "✓" if type_ == "success" else "✗" if type_ == "error" else "⚠" if type_ == "warning" else "ℹ"
        tk.Label(content, text=f"{icon}  {message}", bg=C["ITEM_BG"], fg=C["TEXT"],
                font=("Segoe UI", 10), anchor="w").pack(fill="x")

        toast.place(relx=1.0, x=-20, y=20 + len(self.toasts) * 60, anchor="ne")
        toast.place_forget()

        self.toasts.append(toast)
        if len(self.toasts) > self.max_toasts:
            old = self.toasts.pop(0)
            old.destroy()

        toast.place(relx=1.0, x=-20, y=20 + (len(self.toasts)-1) * 60, anchor="ne")
        toast.update_idletasks()

        def dismiss():
            try:
                if toast in self.toasts:
                    self.toasts.remove(toast)
                toast.destroy()
                self._reposition()
            except Exception:
                pass

        toast.after(duration, dismiss)
        toast.bind("<Button-1>", lambda e: dismiss())
        content.bind("<Button-1>", lambda e: dismiss())

    def _reposition(self):
        for i, t in enumerate(self.toasts):
            try:
                t.place(relx=1.0, x=-20, y=20 + i * 60, anchor="ne")
            except Exception:
                pass

class ClassicButton(tk.Frame):
    def __init__(self, parent, text, command, colors, width=None,
                 font=("Segoe UI", 9), padx=16, pady=6, **kwargs):
        super().__init__(parent, bg=parent.cget("bg"), **kwargs)
        self.command = command
        self.C = colors

        self.btn = tk.Label(self, text=text, bg=self.C["BTN_BG"], fg=self.C["TEXT"], font=font,
                           padx=padx, pady=pady, cursor="hand2",
                           relief="raised", bd=1, width=width)
        self.btn.pack()

        self.btn.bind("<Enter>", lambda e: self._set(self.C["BTN_HOV"]))
        self.btn.bind("<Leave>", lambda e: self._set(self.C["BTN_BG"]))
        self.btn.bind("<Button-1>", lambda e: self._set(self.C["BTN_PRESS"], sunken=True))
        self.btn.bind("<ButtonRelease-1>", self._release)
        self._enabled = True

    def _set(self, color, sunken=False):
        self.btn.config(bg=color, relief="sunken" if sunken else "raised")

    def _release(self, e):
        self.btn.config(bg=self.C["BTN_HOV"], relief="raised")
        if self.command and self._enabled:
            self.command()

    def set_state(self, enabled):
        self.btn.config(fg=self.C["TEXT"] if enabled else self.C["TEXT_MUTE"],
                        cursor="hand2" if enabled else "arrow")
        self._enabled = enabled

class FilePicker(tk.Frame):
    def __init__(self, parent, var, placeholder, command, colors, **kwargs):
        super().__init__(parent, bg=parent.cget("bg"), **kwargs)
        self.var = var
        self.placeholder = placeholder
        self.C = colors

        self.entry = tk.Entry(self, textvariable=var, bg=self.C["ENTRY_BG"], fg=self.C["TEXT"],
                             font=("Segoe UI", 9), relief="sunken", bd=1,
                             insertbackground=self.C["TEXT"], highlightthickness=0)
        self.entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 4))

        current = self.entry.get()
        if current.strip() == "":
            self.entry.insert(0, placeholder)
            self.entry.config(fg=self.C["TEXT_MUTE"])
        else:
            self.entry.config(fg=self.C["TEXT"])

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

        self.btn = tk.Label(self, text="...", bg=self.C["BTN_BG"], fg=self.C["TEXT"], font=("Segoe UI", 9, "bold"),
                           width=3, cursor="hand2", relief="raised", bd=1)
        self.btn.pack(side="right")
        self.btn.bind("<Enter>", lambda e: self.btn.config(bg=self.C["BTN_HOV"]))
        self.btn.bind("<Leave>", lambda e: self.btn.config(bg=self.C["BTN_BG"]))
        self.btn.bind("<Button-1>", lambda e: self.btn.config(relief="sunken"))
        self.btn.bind("<ButtonRelease-1>", lambda e: (self.btn.config(relief="raised"), command()))

    def _on_focus_in(self, e):
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=self.C["TEXT"])

    def _on_focus_out(self, e):
        if self.entry.get().strip() == "":
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.C["TEXT_MUTE"])

class SidebarItem(tk.Frame):
    def __init__(self, parent, icon, text, command, colors, **kwargs):
        super().__init__(parent, bg=colors["ITEM_BG"], cursor="hand2", **kwargs)
        self.command = command
        self.selected = False
        self.C = colors
        self.configure(highlightbackground=self.C["BORDER_LIGHT"], highlightthickness=1)

        self.icon_lbl = tk.Label(self, text=icon, bg=self.C["ITEM_BG"], font=("Segoe UI", 16), width=3, fg=self.C["TEXT"])
        self.icon_lbl.pack(side="left", padx=(6, 0), pady=8)

        self.text_lbl = tk.Label(self, text=text, bg=self.C["ITEM_BG"], fg=self.C["TEXT"],
                                font=("Segoe UI", 10), anchor="w", justify="left")
        self.text_lbl.pack(side="left", padx=(4, 8), pady=8, fill="x", expand=True)

        for w in (self, self.icon_lbl, self.text_lbl):
            w.bind("<Button-1>", lambda e: self.command())
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        if not self.selected:
            self._paint(self.C["ITEM_HOV_BG"])

    def _on_leave(self, e):
        if not self.selected:
            self._paint(self.C["ITEM_BG"])

    def _paint(self, color):
        self.config(bg=color)
        self.icon_lbl.config(bg=color)
        self.text_lbl.config(bg=color)

    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self._paint(self.C["ITEM_SEL_BG"])
            self.configure(highlightbackground=self.C["ACCENT"], highlightthickness=2)
            self.text_lbl.config(fg=self.C["ACCENT"])
        else:
            self._paint(self.C["ITEM_BG"])
            self.configure(highlightbackground=self.C["BORDER_LIGHT"], highlightthickness=1)
            self.text_lbl.config(fg=self.C["TEXT"])

class SectionHeader(tk.Label):
    def __init__(self, parent, text, colors, **kwargs):
        super().__init__(parent, text=text, bg=colors["SECTION_BG"], fg=colors["TEXT"],
                         font=("Segoe UI", 9, "bold"), anchor="w", padx=8, pady=6, **kwargs)
        self.configure(highlightbackground=colors["BORDER"], highlightthickness=1)

class GroupBox(tk.LabelFrame):
    def __init__(self, parent, title, colors, **kwargs):
        super().__init__(parent, text=title, bg=colors["WIN_BG"], fg=colors["TEXT_DIM"],
                         font=("Segoe UI", 9), bd=1, relief="groove",
                         padx=12, pady=10, **kwargs)

class MenuBar(tk.Menu):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.C["MENU_BG"], fg=app.C["TEXT"])
        self.app = app
        self.parent = parent
        
        file_menu = tk.Menu(self, tearoff=0, bg=app.C["MENU_BG"], fg=app.C["TEXT"])
        file_menu.add_command(label="Exit", command=parent.quit)
        self.add_cascade(label="File", menu=file_menu)
        
        theme_menu = tk.Menu(self, tearoff=0, bg=app.C["MENU_BG"], fg=app.C["TEXT"])
        theme_menu.add_command(label="Light Theme", command=lambda: app._set_theme("light"))
        theme_menu.add_command(label="Dark Theme", command=lambda: app._set_theme("dark"))
        self.add_cascade(label="Theme", menu=theme_menu)

# ============================================================================
# PASSWORD DIALOG
# ============================================================================

class PasswordDialog:
    def __init__(self, parent, title="Password Required", prompt="Enter password:", 
                 confirm=False, optional=False):
        self.result = None
        self.optional = optional
        self.confirm = confirm
        self.parent = parent
        
        if hasattr(parent, 'C'):
            self.C = parent.C
        else:
            self.C = THEMES["dark"]
        
        height = 240 if confirm else 200
        if optional:
            height += 30
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"460x{height}")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=self.C["WIN_BG"])
        
        self.dialog.update_idletasks()
        width = 460
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        main_frame = tk.Frame(self.dialog, bg=self.C["WIN_BG"])
        main_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        if optional:
            tk.Label(main_frame, text=prompt, bg=self.C["WIN_BG"], fg=self.C["TEXT_DIM"],
                    font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 2))
            tk.Label(main_frame, text="(Leave empty for no encryption)", 
                    bg=self.C["WIN_BG"], fg=self.C["TEXT_MUTE"],
                    font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(0, 12))
        else:
            tk.Label(main_frame, text=prompt, bg=self.C["WIN_BG"], fg=self.C["TEXT_DIM"],
                    font=("Segoe UI", 11)).pack(anchor="w", pady=(0, 12))
        
        pwd_frame1 = tk.Frame(main_frame, bg=self.C["WIN_BG"])
        pwd_frame1.pack(fill="x", pady=4)
        
        tk.Label(pwd_frame1, text="Password:", bg=self.C["WIN_BG"], fg=self.C["TEXT"],
                font=("Segoe UI", 10), width=10, anchor="w").pack(side="left")
        
        self.password_entry = tk.Entry(pwd_frame1, show="•", width=28,
                                      font=("Segoe UI", 10),
                                      bg=self.C["ENTRY_BG"], fg=self.C["TEXT"],
                                      insertbackground=self.C["TEXT"],
                                      relief="sunken", bd=1)
        self.password_entry.pack(side="left", padx=(5, 5))
        self.password_entry.focus()
        
        self.show_pwd_var = tk.IntVar()
        show_btn = tk.Checkbutton(pwd_frame1, text="👁 Show", 
                                 variable=self.show_pwd_var,
                                 bg=self.C["WIN_BG"], fg=self.C["TEXT"],
                                 selectcolor=self.C["WIN_BG"],
                                 command=self._toggle_show,
                                 font=("Segoe UI", 9))
        show_btn.pack(side="left")
        
        self.confirm_entry = None
        if confirm:
            pwd_frame2 = tk.Frame(main_frame, bg=self.C["WIN_BG"])
            pwd_frame2.pack(fill="x", pady=4)
            
            tk.Label(pwd_frame2, text="Confirm:", bg=self.C["WIN_BG"], fg=self.C["TEXT"],
                    font=("Segoe UI", 10), width=10, anchor="w").pack(side="left")
            
            self.confirm_entry = tk.Entry(pwd_frame2, show="•", width=28,
                                         font=("Segoe UI", 10),
                                         bg=self.C["ENTRY_BG"], fg=self.C["TEXT"],
                                         insertbackground=self.C["TEXT"],
                                         relief="sunken", bd=1)
            self.confirm_entry.pack(side="left", padx=(5, 5))
            self.confirm_entry.bind("<Return>", lambda e: self._on_ok())
            
            show_btn2 = tk.Checkbutton(pwd_frame2, text="👁 Show", 
                                      variable=self.show_pwd_var,
                                      bg=self.C["WIN_BG"], fg=self.C["TEXT"],
                                      selectcolor=self.C["WIN_BG"],
                                      command=self._toggle_show,
                                      font=("Segoe UI", 9))
            show_btn2.pack(side="left")
        
        btn_frame = tk.Frame(main_frame, bg=self.C["WIN_BG"])
        btn_frame.pack(fill="x", pady=(20, 0))
        
        ok_btn = tk.Button(btn_frame, text="OK", command=self._on_ok,
                          width=10, font=("Segoe UI", 10),
                          bg=self.C["BTN_BG"], fg=self.C["TEXT"],
                          activebackground=self.C["BTN_HOV"],
                          activeforeground=self.C["TEXT"],
                          relief="raised", bd=1)
        ok_btn.pack(side="left", padx=3)
        
        if optional:
            skip_btn = tk.Button(btn_frame, text="Skip (No encryption)", 
                                command=self._on_skip,
                                width=16, font=("Segoe UI", 10),
                                bg=self.C["BTN_BG"], fg=self.C["TEXT"],
                                activebackground=self.C["BTN_HOV"],
                                activeforeground=self.C["TEXT"],
                                relief="raised", bd=1)
            skip_btn.pack(side="left", padx=3)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                              width=10, font=("Segoe UI", 10),
                              bg=self.C["BTN_BG"], fg=self.C["TEXT"],
                              activebackground=self.C["BTN_HOV"],
                              activeforeground=self.C["TEXT"],
                              relief="raised", bd=1)
        cancel_btn.pack(side="left", padx=3)
        
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())
        
        self.dialog.wait_window()
    
    def _toggle_show(self):
        show = self.show_pwd_var.get()
        self.password_entry.config(show="" if show else "•")
        if self.confirm_entry:
            self.confirm_entry.config(show="" if show else "•")
    
    def _on_ok(self):
        pwd = self.password_entry.get()
        
        if self.confirm:
            confirm = self.confirm_entry.get() if self.confirm_entry else ""
            if pwd != confirm:
                messagebox.showerror("Error", "Passwords do not match!")
                return
            if pwd and len(pwd) < 4:
                messagebox.showerror("Error", "Password must be at least 4 characters!")
                return
        
        self.result = pwd
        self.dialog.destroy()
    
    def _on_skip(self):
        self.result = ""
        self.dialog.destroy()
    
    def _on_cancel(self):
        self.result = None
        self.dialog.destroy()
    
    def get_password(self):
        return self.result

# ============================================================================
# CRYPTO FUNCTIONS
# ============================================================================

def derive_key(password: str, salt: bytes = None) -> tuple:
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        import base64
    except ImportError:
        raise Exception("Cryptography library not available")
    
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_data(data: bytes, password: str) -> bytes:
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise Exception("Cryptography library not available")
    
    key, salt = derive_key(password)
    f = Fernet(key)
    encrypted = f.encrypt(data)
    return salt + encrypted

def decrypt_data(encrypted_data: bytes, password: str) -> bytes:
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise Exception("Cryptography library not available")
    
    salt = encrypted_data[:16]
    ciphertext = encrypted_data[16:]
    
    key, _ = derive_key(password, salt)
    f = Fernet(key)
    return f.decrypt(ciphertext)

def is_encrypted(payload: bytes) -> bool:
    return payload.startswith(ENCRYPT_MARKER)

# ============================================================================
# APPLICAZIONE PRINCIPALE
# ============================================================================

class StegoTool:
    def __init__(self, root):
        self.root = root
        self.root.title("StegoTool - Steganography Tool")
        self.root.geometry("980x680")
        self.root.minsize(860, 600)

        self.theme_name = "dark"
        self.C = THEMES[self.theme_name]

        self.hide_image = tk.StringVar()
        self.hide_file = tk.StringVar()
        self.hide_output = tk.StringVar()
        self.hide_method = tk.StringVar(value="lsb")
        self.use_encryption = tk.BooleanVar(value=False)
        self.extract_image = tk.StringVar()
        self.extract_dir = tk.StringVar(value=str(Path.home() / "Desktop"))

        self.current_page = "hide"
        self.pages = {}
        self.sidebar_items = {}

        self._build_ui()

    def _set_theme(self, name):
        if name == self.theme_name:
            return
        self.theme_name = name
        self.C = THEMES[name]
        self.body.destroy()
        self._build_ui()

    def _build_ui(self):
        C = self.C
        self.root.configure(bg=C["WIN_BG"])
        self.toast = Toast(self.root, C)
        self._apply_ttk_style(C)

        self.menubar = MenuBar(self.root, self)
        self.root.config(menu=self.menubar)

        self.body = tk.Frame(self.root, bg=C["WIN_BG"])
        self.body.pack(fill="both", expand=True)

        main_row = tk.Frame(self.body, bg=C["WIN_BG"])
        main_row.pack(fill="both", expand=True, side="top")

        sidebar = tk.Frame(main_row, bg=C["SIDEBAR_BG"], width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        SectionHeader(sidebar, "Data Hiding", C).pack(fill="x", pady=(8, 0))

        item_hide = SidebarItem(sidebar, "📝", "Hide Data", lambda: self._select_page("hide"), C)
        item_hide.pack(fill="x", padx=6, pady=(8, 4))
        self.sidebar_items["hide"] = item_hide

        item_extract = SidebarItem(sidebar, "📂", "Extract Data", lambda: self._select_page("extract"), C)
        item_extract.pack(fill="x", padx=6, pady=4)
        self.sidebar_items["extract"] = item_extract

        tk.Frame(main_row, bg=C["BORDER"], width=1).pack(side="left", fill="y")

        content_outer = tk.Frame(main_row, bg=C["WIN_BG"])
        content_outer.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(content_outer, bg=C["WIN_BG"], padx=24, pady=20)
        self.content.pack(fill="both", expand=True)

        self.pages = {}
        self.pages["hide"] = self._build_hide_page(self.content)
        self.pages["extract"] = self._build_extract_page(self.content)

        self._select_page(self.current_page)

    def _apply_ttk_style(self, C):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=C["ENTRY_BG"],
                        background=C["BTN_BG"],
                        foreground=C["TEXT"],
                        arrowcolor=C["TEXT"],
                        bordercolor=C["BORDER"],
                        lightcolor=C["ENTRY_BG"],
                        darkcolor=C["ENTRY_BG"])
        style.map("TCombobox",
                 fieldbackground=[("readonly", C["ENTRY_BG"])],
                 foreground=[("readonly", C["TEXT"])],
                 selectbackground=[("readonly", C["ENTRY_BG"])],
                 selectforeground=[("readonly", C["TEXT"])])
        self.root.option_add("*TCombobox*Listbox.background", C["ENTRY_BG"])
        self.root.option_add("*TCombobox*Listbox.foreground", C["TEXT"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", C["ITEM_SEL_BG"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", C["TEXT"])

    def _select_page(self, name):
        self.current_page = name
        for key, item in self.sidebar_items.items():
            item.set_selected(key == name)
        for key, page in self.pages.items():
            if key == name:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()

    def _build_hide_page(self, parent):
        C = self.C
        page = tk.Frame(parent, bg=C["WIN_BG"])

        tk.Label(page, text="Hide data in innocuous-looking files", bg=C["WIN_BG"], fg=C["TEXT"],
                font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(page, text="Hides a secret file inside a cover image (optional AES-256 encryption).",
                bg=C["WIN_BG"], fg=C["TEXT_MUTE"], font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 16))

        tk.Label(page, text="File to hide", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w")
        FilePicker(page, self.hide_file, "Click to select the secret file...",
                  self._browse_hide_file, C).pack(fill="x", pady=(2, 12))

        tk.Label(page, text="Cover image", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(page, text="(Will be used as container for the file)",
                bg=C["WIN_BG"], fg=C["TEXT_MUTE"], font=("Segoe UI", 8, "italic")).pack(anchor="w")
        FilePicker(page, self.hide_image, "Click to select an image...",
                  self._browse_image, C).pack(fill="x", pady=(2, 12))

        tk.Label(page, text="Output stego file", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w")
        FilePicker(page, self.hide_output, "Click to choose where to save the image...",
                  self._browse_save, C).pack(fill="x", pady=(2, 14))

        opts = GroupBox(page, "Options", C)
        opts.pack(fill="x", pady=(0, 8))

        # Hiding method
        row = tk.Frame(opts, bg=C["WIN_BG"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Hiding method", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9), width=20, anchor="w").pack(side="left")

        method_box = ttk.Combobox(row, state="readonly", width=32, font=("Segoe UI", 9),
                                 values=["LSB — hidden in image pixels",
                                         "APPEND — appended at end of file"])
        method_box.current(0 if self.hide_method.get() == "lsb" else 1)
        method_box.pack(side="left", fill="x", expand=True)
        method_box.bind("<<ComboboxSelected>>",
                        lambda e: self.hide_method.set("lsb" if method_box.current() == 0 else "append"))

        tk.Label(opts, text="LSB: recommended for PNG/BMP, very stealth but size limited.\n"
                            "APPEND: no size limit, file grows slightly.",
                bg=C["WIN_BG"], fg=C["TEXT_MUTE"], font=("Segoe UI", 8), justify="left").pack(anchor="w", pady=(6, 8))

        # ========================================================================
        # ENCRYPTION CHECKBOX - DISATTIVATO DI DEFAULT
        # ========================================================================
        encrypt_frame = tk.Frame(opts, bg=C["WIN_BG"])
        encrypt_frame.pack(fill="x", pady=(0, 4))
        
        self.encrypt_check = tk.Checkbutton(encrypt_frame, text="🔐 Encrypt with AES-256-GCM",
                                           variable=self.use_encryption,
                                           bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                                           font=("Segoe UI", 9, "bold"),
                                           selectcolor=C["WIN_BG"],
                                           command=self._toggle_encryption_fields)
        self.encrypt_check.pack(side="left")
        
        tk.Label(encrypt_frame, text="(Recommended for security)",
                bg=C["WIN_BG"], fg=C["TEXT_MUTE"], font=("Segoe UI", 8, "italic")).pack(side="left", padx=(8, 0))

        # ========================================================================
        # PASSWORD FIELDS - UN SINGOLO BOTTONE "SHOW" PER ENTRAMBI
        # ========================================================================
        pwd_frame = tk.Frame(opts, bg=C["WIN_BG"])
        pwd_frame.pack(fill="x", pady=(8, 4))
        
        # Password 1
        row1 = tk.Frame(pwd_frame, bg=C["WIN_BG"])
        row1.pack(fill="x", pady=2)
        
        tk.Label(row1, text="Password:", bg=C["WIN_BG"], fg=C["TEXT"],
                font=("Segoe UI", 9), width=20, anchor="w").pack(side="left")
        
        # Entry con sfondo scuro SEMPRE (anche quando disabilitato)
        self.pwd_entry = tk.Entry(row1, show="•", width=25, 
                                 font=("Segoe UI", 9),
                                 bg=C["ENTRY_BG"],  # Sempre sfondo scuro
                                 fg=C["TEXT"],      # Sempre testo bianco
                                 insertbackground=C["TEXT"],
                                 relief="sunken", bd=1,
                                 state="disabled",
                                 disabledbackground=C["ENTRY_BG"],  # Stesso sfondo anche quando disabilitato
                                 disabledforeground=C["TEXT"])      # Stesso colore testo anche quando disabilitato
        self.pwd_entry.pack(side="left", padx=(0, 5))
        
        # Password 2 (conferma)
        row2 = tk.Frame(pwd_frame, bg=C["WIN_BG"])
        row2.pack(fill="x", pady=2)
        
        tk.Label(row2, text="Confirm:", bg=C["WIN_BG"], fg=C["TEXT"],
                font=("Segoe UI", 9), width=20, anchor="w").pack(side="left")
        
        # Entry con sfondo scuro SEMPRE (anche quando disabilitato)
        self.confirm_entry = tk.Entry(row2, show="•", width=25,
                                     font=("Segoe UI", 9),
                                     bg=C["ENTRY_BG"],  # Sempre sfondo scuro
                                     fg=C["TEXT"],      # Sempre testo bianco
                                     insertbackground=C["TEXT"],
                                     relief="sunken", bd=1,
                                     state="disabled",
                                     disabledbackground=C["ENTRY_BG"],  # Stesso sfondo anche quando disabilitato
                                     disabledforeground=C["TEXT"])      # Stesso colore testo anche quando disabilitato
        self.confirm_entry.pack(side="left", padx=(0, 5))

        # ========================================================================
        # UNICO CHECKBOX SHOW
        # ========================================================================
        # Il checkbox si trova alla fine della riga delle password. 
        # Quando cliccato, mostra entrambi i campi.
        # Nota: abbiamo messo 'self.show_pwd_var' su una riga specifica sopra, 
        # ma lo condividiamo per entrambi.
        self.show_pwd_var = tk.IntVar()
        self.show_pwd_btn = tk.Checkbutton(row1, text="👁 Show", 
                                          variable=self.show_pwd_var,
                                          bg=C["WIN_BG"], fg=C["TEXT"],
                                          selectcolor=C["WIN_BG"],
                                          state="disabled",
                                          command=self._toggle_show_pwd)
        self.show_pwd_btn.pack(side="left")

        btn_row = tk.Frame(page, bg=C["WIN_BG"])
        btn_row.pack(fill="x", pady=(10, 0))
        self.hide_btn = ClassicButton(btn_row, "Hide Data", self._do_hide, C,
                                     font=("Segoe UI", 9, "bold"), padx=22, pady=8)
        self.hide_btn.pack(side="right")

        return page

    def _toggle_encryption_fields(self):
        """Abilita/disabilita i campi password quando si clicca sulla checkbox"""
        if self.use_encryption.get():
            # Attiva i campi (lo sfondo rimane scuro)
            self.pwd_entry.config(state="normal")
            self.confirm_entry.config(state="normal")
            self.show_pwd_btn.config(state="normal")
            self.pwd_entry.focus()
        else:
            # Disattiva i campi (lo sfondo rimane scuro)
            self.pwd_entry.config(state="disabled")
            self.confirm_entry.config(state="disabled")
            self.show_pwd_btn.config(state="disabled")
            self.show_pwd_var.set(0)
            self.pwd_entry.config(show="•")
            self.confirm_entry.config(show="•")
            # Svuota i campi
            self.pwd_entry.delete(0, tk.END)
            self.confirm_entry.delete(0, tk.END)

    def _toggle_show_pwd(self):
        """Mostra o nasconde entrambe le password contemporaneamente"""
        if self.show_pwd_var.get():
            self.pwd_entry.config(show="")
            self.confirm_entry.config(show="")
        else:
            self.pwd_entry.config(show="•")
            self.confirm_entry.config(show="•")

    def _build_extract_page(self, parent):
        C = self.C
        page = tk.Frame(parent, bg=C["WIN_BG"])

        tk.Label(page, text="Extract hidden data from a file", bg=C["WIN_BG"], fg=C["TEXT"],
                font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(page, text="Recover the secret file (supports both encrypted and unencrypted).",
                bg=C["WIN_BG"], fg=C["TEXT_MUTE"], font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 16))

        tk.Label(page, text="Image with hidden file", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w")
        FilePicker(page, self.extract_image, "Click to select the image...",
                  self._browse_extract_image, C).pack(fill="x", pady=(2, 12))

        tk.Label(page, text="Destination folder", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w")
        FilePicker(page, self.extract_dir, "Click to choose the output folder...",
                  self._browse_dir, C).pack(fill="x", pady=(2, 14))

        info = GroupBox(page, "How it works", C)
        info.pack(fill="x", pady=(0, 18))
        tk.Label(info, text="🔐 If the file was encrypted, you MUST provide the correct password.\n"
                            "📄 If the file was NOT encrypted, it will be extracted directly.\n\n"
                            "The tool automatically detects whether encryption was used.",
                bg=C["WIN_BG"], fg=C["TEXT_MUTE"], font=("Segoe UI", 9), justify="left").pack(anchor="w")

        btn_row = tk.Frame(page, bg=C["WIN_BG"])
        btn_row.pack(fill="x")
        self.extract_btn = ClassicButton(btn_row, "Extract Data", self._do_extract, C,
                                        font=("Segoe UI", 9, "bold"), padx=22, pady=8)
        self.extract_btn.pack(side="right")

        return page

    def _browse_image(self):
        path = filedialog.askopenfilename(title="Select cover image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff"), ("All files", "*.*")])
        if path:
            self.hide_image.set(path)

    def _browse_hide_file(self):
        path = filedialog.askopenfilename(title="Select file to hide",
                                         filetypes=[("All files", "*.*")])
        if path:
            self.hide_file.set(path)

    def _browse_save(self):
        path = filedialog.asksaveasfilename(title="Save output image",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("BMP", "*.bmp"), ("JPEG", "*.jpg"), ("All", "*.*")])
        if path:
            self.hide_output.set(path)

    def _browse_extract_image(self):
        path = filedialog.askopenfilename(title="Select image with hidden file",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All files", "*.*")])
        if path:
            self.extract_image.set(path)

    def _browse_dir(self):
        path = filedialog.askdirectory(title="Select destination folder")
        if path:
            self.extract_dir.set(path)

    def _set_busy(self, busy):
        self.hide_btn.set_state(not busy)
        self.extract_btn.set_state(not busy)
        self.root.config(cursor="wait" if busy else "")

    # ========================================================================
    # HIDE OPERATIONS
    # ========================================================================

    def _do_hide(self):
        try:
            from PIL import Image
        except ImportError:
            self.toast.show("Pillow library not available", "error")
            return
        
        if self.use_encryption.get():
            try:
                from cryptography.fernet import Fernet
            except ImportError:
                self.toast.show("Cryptography library not available. Install: pip install cryptography", "error")
                return
            
        img = self.hide_image.get()
        fil = self.hide_file.get()
        out = self.hide_output.get()
        method = self.hide_method.get()

        placeholders = ["", "Click to select an image...",
                       "Click to select the secret file...",
                       "Click to choose where to save the image..."]

        if img in placeholders or not Path(img).exists():
            self.toast.show("Select a valid cover image", "error")
            return
        if fil in placeholders or not Path(fil).exists():
            self.toast.show("Select a valid file to hide", "error")
            return
        if out in placeholders:
            self.toast.show("Specify where to save the output", "error")
            return

        password = None
        if self.use_encryption.get():
            password = self.pwd_entry.get()
            confirm = self.confirm_entry.get()
            
            if not password:
                self.toast.show("Password cannot be empty when encryption is enabled", "error")
                return
            if password != confirm:
                self.toast.show("Passwords do not match!", "error")
                return
            if len(password) < 4:
                self.toast.show("Password must be at least 4 characters!", "error")
                return

        self._set_busy(True)

        def task():
            try:
                if method == "lsb":
                    result = self._hide_lsb(img, fil, out, password)
                else:
                    result = self._hide_append(img, fil, out, password)

                if result:
                    if password:
                        self.root.after(0, lambda: self.toast.show("File hidden with AES-256 encryption!", "success"))
                    else:
                        self.root.after(0, lambda: self.toast.show("File hidden without encryption", "success"))
                else:
                    self.root.after(0, lambda: self.toast.show("Operation failed", "error"))
            except Exception as e:
                self.root.after(0, lambda: self.toast.show(f"Error: {str(e)}", "error"))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=task, daemon=True).start()

    def _hide_lsb(self, image_path, file_path, output_path, password):
        from PIL import Image
        
        file_path = Path(file_path)
        with open(file_path, 'rb') as f:
            file_data = f.read()

        if password:
            try:
                encrypted_data = encrypt_data(file_data, password)
                file_name = file_path.name.encode('utf-8')
                payload = ENCRYPT_MARKER + struct.pack('>H', len(file_name)) + file_name + encrypted_data
            except Exception as e:
                raise Exception(f"Encryption failed: {e}")
        else:
            file_name = file_path.name.encode('utf-8')
            payload = struct.pack('>H', len(file_name)) + file_name + file_data

        header = MAGIC_LSB + struct.pack('>I', len(payload)) + payload

        img = Image.open(image_path)
        if img.mode not in ('RGB', 'RGBA', 'L'):
            img = img.convert('RGB')

        if img.mode == 'RGBA':
            img = img.convert('RGB')

        pixels = list(img.getdata())
        total = len(pixels)
        capacity = total * 1 if img.mode == 'L' else total * 3
        bits_needed = len(header) * 8

        if bits_needed > capacity:
            raise Exception(f"File too large for this image. Max size: {capacity//8} bytes")

        bits = []
        for byte in header:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)

        new_pixels = []
        bit_idx = 0
        for pixel in pixels:
            if img.mode == 'L':
                if bit_idx < len(bits):
                    new_pixels.append((pixel & 0xFE) | bits[bit_idx])
                    bit_idx += 1
                else:
                    new_pixels.append(pixel)
            else:
                r, g, b = pixel[:3]
                if bit_idx < len(bits):
                    r = (r & 0xFE) | bits[bit_idx]; bit_idx += 1
                if bit_idx < len(bits):
                    g = (g & 0xFE) | bits[bit_idx]; bit_idx += 1
                if bit_idx < len(bits):
                    b = (b & 0xFE) | bits[bit_idx]; bit_idx += 1
                new_pixels.append((r, g, b))

        new_img = Image.new(img.mode, img.size)
        new_img.putdata(new_pixels)
        new_img.save(output_path)
        return True

    def _hide_append(self, image_path, file_path, output_path, password):
        file_path = Path(file_path)
        with open(file_path, 'rb') as f:
            file_data = f.read()

        if password:
            try:
                encrypted_data = encrypt_data(file_data, password)
                file_name = file_path.name.encode('utf-8')
                payload = ENCRYPT_MARKER + struct.pack('>H', len(file_name)) + file_name + encrypted_data
            except Exception as e:
                raise Exception(f"Encryption failed: {e}")
        else:
            file_name = file_path.name.encode('utf-8')
            payload = struct.pack('>H', len(file_name)) + file_name + file_data

        with open(image_path, 'rb') as f:
            image_data = f.read()

        full_payload = MAGIC_APP + struct.pack('>I', len(payload)) + payload + END_APP

        with open(output_path, 'wb') as f:
            f.write(image_data)
            f.write(full_payload)
        return True

    # ========================================================================
    # EXTRACT OPERATIONS
    # ========================================================================

    def _do_extract(self):
        try:
            from PIL import Image
        except ImportError:
            self.toast.show("Pillow library not available", "error")
            return
        
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            self.toast.show("Cryptography library not available. Install: pip install cryptography", "error")
            return
            
        img = self.extract_image.get()
        out = self.extract_dir.get()

        placeholders = ["", "Click to select the image...",
                       "Click to choose the output folder..."]

        if img in placeholders or not Path(img).exists():
            self.toast.show("Select a valid image", "error")
            return
        if out in placeholders:
            out = str(Path.home() / "Desktop")
            self.extract_dir.set(out)

        pwd_dialog = PasswordDialog(
            self.root,
            title="Password (Optional)",
            prompt="Enter password if the file is encrypted:",
            optional=True,
            confirm=False
        )
        password = pwd_dialog.get_password()
        if password is None:
            return

        self._set_busy(True)

        def task():
            try:
                found = False
                if self._extract_lsb(img, out, password):
                    found = True
                elif self._extract_append(img, out, password):
                    found = True

                if not found:
                    self.root.after(0, lambda: self.toast.show("No hidden file found", "warning"))
            except Exception as e:
                error_msg = str(e)
                if "Invalid token" in error_msg or "decryption" in error_msg:
                    self.root.after(0, lambda: self.toast.show("Wrong password! Decryption failed.", "error"))
                else:
                    self.root.after(0, lambda: self.toast.show(f"Error: {error_msg}", "error"))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=task, daemon=True).start()

    def _extract_lsb(self, image_path, output_dir, password):
        from PIL import Image
        
        img = Image.open(image_path)
        if img.mode not in ('RGB', 'RGBA', 'L'):
            img = img.convert('RGB')
        pixels = list(img.getdata())

        bits = []
        for pixel in pixels:
            if img.mode == 'L':
                bits.append(pixel & 1)
            else:
                bits.append(pixel[0] & 1)
                bits.append(pixel[1] & 1)
                bits.append(pixel[2] & 1)

        data = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                if i + j < len(bits):
                    byte = (byte << 1) | bits[i + j]
                else:
                    byte = byte << 1
            data.append(byte)

        data = bytes(data)
        pos = data.find(MAGIC_LSB)
        if pos == -1:
            return False

        idx = pos + len(MAGIC_LSB)
        payload_len = struct.unpack('>I', data[idx:idx+4])[0]
        idx += 4
        payload = data[idx:idx+payload_len]

        return self._process_payload(payload, output_dir, password)

    def _extract_append(self, image_path, output_dir, password):
        with open(image_path, 'rb') as f:
            data = f.read()

        start = data.find(MAGIC_APP)
        if start == -1:
            return False

        idx = start + len(MAGIC_APP)
        payload_len = struct.unpack('>I', data[idx:idx+4])[0]
        idx += 4
        payload = data[idx:idx+payload_len]
        
        return self._process_payload(payload, output_dir, password)

    def _process_payload(self, payload, output_dir, password):
        if is_encrypted(payload):
            if not password:
                return False
            
            try:
                idx = len(ENCRYPT_MARKER)
                name_len = struct.unpack('>H', payload[idx:idx+2])[0]
                idx += 2
                file_name = payload[idx:idx+name_len].decode('utf-8')
                idx += name_len
                
                encrypted_data = payload[idx:]
                decrypted_data = decrypt_data(encrypted_data, password)
                return self._save_file(file_name, decrypted_data, output_dir)
            except Exception as e:
                raise Exception(f"Decryption failed: {e}")
        else:
            try:
                name_len = struct.unpack('>H', payload[:2])[0]
                idx = 2
                file_name = payload[idx:idx+name_len].decode('utf-8')
                idx += name_len
                file_data = payload[idx:]
                return self._save_file(file_name, file_data, output_dir)
            except Exception as e:
                raise Exception(f"Extraction failed: {e}")

    def _save_file(self, file_name, file_data, output_dir):
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        original_name = Path(file_name)
        extracted_name = f"{original_name.stem}_extracted{original_name.suffix}"
        path = out / extracted_name

        counter = 1
        original = path
        while path.exists():
            path = out / f"{original.stem}_{counter}{original.suffix}"
            counter += 1

        with open(path, 'wb') as f:
            f.write(file_data)

        self.root.after(0, lambda: self.toast.show(f"File extracted: {path.name}", "success"))
        return True

# ============================================================================
# MAIN
# ============================================================================

def main():
    success, error_msg = ensure_dependencies_with_popup()
    
    if not success:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Installation Error",
            f"Cannot install required dependencies.\n\n"
            f"Error: {error_msg}\n\n"
            f"Please install manually:\n"
            f"pip install Pillow cryptography"
        )
        root.destroy()
        sys.exit(1)
    
    root = tk.Tk()
    app = StegoTool(root)
    root.mainloop()

if __name__ == '__main__':
    main()