# Disable __pycache__
import sys
sys.dont_write_bytecode = True

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import time

from constants import THEMES
from core import (
    hide_lsb, hide_append, extract_lsb, extract_append,
    process_payload, save_file, is_encrypted
)


# ===== PROGRESS POPUP =====

class ProgressPopup:
    def __init__(self, parent, title="Processing..."):
        self.parent = parent
        self.result = None
        self.cancelled = False
        
        self.root = tk.Toplevel(parent)
        self.root.title(title)
        self.root.geometry("420x180")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1b1e")
        self.root.transient(parent)
        self.root.grab_set()
        
        # Center the window
        self.root.update_idletasks()
        width, height = 420, 180
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Icon
        tk.Label(self.root, text="⏳", bg="#1a1b1e", fg="#6b9fd5",
                font=("Segoe UI", 28)).pack(pady=(15, 5))
        
        # Status
        self.status_label = tk.Label(self.root, text="Processing...", bg="#1a1b1e", 
                                     fg="#f0f0f0", font=("Segoe UI", 11, "bold"))
        self.status_label.pack(pady=(5, 5))
        
        # Detail
        self.detail_label = tk.Label(self.root, text="", bg="#1a1b1e", 
                                     fg="#b0b0b8", font=("Segoe UI", 9))
        self.detail_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=300, mode='indeterminate')
        self.progress.pack(pady=5)
        self.progress.start(10)
        
        # Cancel button
        self.cancel_btn = tk.Button(self.root, text="Cancel", command=self._cancel,
                                   bg="#3a3b42", fg="#f0f0f0", font=("Segoe UI", 9),
                                   relief="raised", bd=1, padx=15, pady=3,
                                   activebackground="#4a4b54", activeforeground="#f0f0f0")
        self.cancel_btn.pack(pady=(10, 0))
        
        self.root.update()
    
    def update_status(self, text, detail=""):
        """Update status text"""
        self.status_label.config(text=text)
        self.detail_label.config(text=detail)
        self.root.update()
    
    def set_progress(self, value, max_value=100):
        """Set progress bar value (0-100)"""
        self.progress.stop()
        self.progress['mode'] = 'determinate'
        self.progress['value'] = (value / max_value) * 100
        self.root.update()
    
    def _cancel(self):
        self.cancelled = True
        self.status_label.config(text="Cancelling...")
        self.root.update()
    
    def close(self):
        """Close the popup"""
        self.progress.stop()
        self.root.destroy()


# ===== PASSWORD DIALOG =====

class PasswordDialog:
    def __init__(self, parent, title="Password Required", prompt="Enter password:"):
        self.result = None
        self.C = parent.C if hasattr(parent, 'C') else THEMES["dark"]

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("460x250")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=self.C["WIN_BG"])
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the window
        x = (self.dialog.winfo_screenwidth() - 460) // 2
        y = (self.dialog.winfo_screenheight() - 250) // 2
        self.dialog.geometry(f'+{x}+{y}')

        main = tk.Frame(self.dialog, bg=self.C["WIN_BG"])
        main.pack(fill="both", expand=True, padx=30, pady=25)

        # Icon
        tk.Label(main, text="🔐", bg=self.C["WIN_BG"], fg=self.C["ACCENT"],
                font=("Segoe UI", 28)).pack(pady=(0, 8))

        # Prompt
        tk.Label(main, text=prompt, bg=self.C["WIN_BG"], fg=self.C["TEXT_DIM"],
                font=("Segoe UI", 11)).pack(anchor="center", pady=(0, 12))

        # Password entry with Show button
        pwd_frame = tk.Frame(main, bg=self.C["WIN_BG"])
        pwd_frame.pack(pady=4)

        self.pwd_entry = tk.Entry(pwd_frame, show="•", width=25, font=("Segoe UI", 10),
                                 bg=self.C["ENTRY_BG"], fg=self.C["TEXT"],
                                 insertbackground=self.C["TEXT"], 
                                 relief="sunken", bd=1)
        self.pwd_entry.pack(side="left", padx=(0, 5), ipady=2)
        self.pwd_entry.focus()
        
        # Show password button
        self.show_var = tk.IntVar(value=0)
        self.show_btn = tk.Button(pwd_frame, text="👁", command=self._toggle_show,
                                 bg=self.C["BTN_BG"], fg=self.C["TEXT"],
                                 font=("Segoe UI", 9), width=3,
                                 relief="raised", bd=1,
                                 activebackground=self.C["BTN_HOV"])
        self.show_btn.pack(side="left")
        
        # Bind Enter key to confirm
        self.pwd_entry.bind("<Return>", lambda e: self._on_ok())

        # Buttons - CANCEL first, then OK
        btn_frame = tk.Frame(main, bg=self.C["WIN_BG"])
        btn_frame.pack(fill="x", pady=(18, 0))

        # Cancel button (first)
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=self._on_cancel,
                              width=12, bg=self.C["BTN_BG"], fg=self.C["TEXT"],
                              font=("Segoe UI", 9),
                              relief="raised", bd=1,
                              activebackground=self.C["BTN_HOV"],
                              activeforeground=self.C["TEXT"])
        cancel_btn.pack(side="left", padx=5, expand=True)

        # OK button (second - Accent color)
        ok_btn = tk.Button(btn_frame, text="OK", command=self._on_ok,
                          width=12, bg=self.C["ACCENT"], fg="white",
                          font=("Segoe UI", 9, "bold"),
                          relief="raised", bd=1,
                          activebackground=self.C["BTN_HOV"],
                          activeforeground="white")
        ok_btn.pack(side="left", padx=5, expand=True)

        # Escape key to cancel
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())
        
        # Make sure dialog stays on top
        self.dialog.lift()
        self.dialog.focus_force()
        
        self.dialog.wait_window()

    def _toggle_show(self):
        """Toggle password visibility"""
        if self.show_var.get():
            self.pwd_entry.config(show="")
            self.show_var.set(0)
        else:
            self.pwd_entry.config(show="•")
            self.show_var.set(1)

    def _on_ok(self):
        pwd = self.pwd_entry.get()
        if not pwd:
            messagebox.showerror("Error", "Password cannot be empty!")
            return
        if len(pwd) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters!")
            return
        self.result = pwd
        self.dialog.destroy()

    def _on_cancel(self):
        self.result = None
        self.dialog.destroy()

    def get_password(self):
        return self.result

# ===== MENU BAR =====

class MenuBar(tk.Menu):
    def __init__(self, parent, app):
        super().__init__(parent, bg=app.C["MENU_BG"], fg=app.C["TEXT"])
        self.app = app
        self.parent = parent
        
        file_menu = tk.Menu(self, tearoff=0, bg=app.C["MENU_BG"], fg=app.C["TEXT"])
        file_menu.add_command(label="Exit", command=parent.quit)
        self.add_cascade(label="File", menu=file_menu)
        
        # Theme: Dark first, Light second
        theme_menu = tk.Menu(self, tearoff=0, bg=app.C["MENU_BG"], fg=app.C["TEXT"])
        theme_menu.add_command(label="Dark Theme", command=lambda: app._set_theme("dark"))
        theme_menu.add_command(label="Light Theme", command=lambda: app._set_theme("light"))
        self.add_cascade(label="Theme", menu=theme_menu)
        
        help_menu = tk.Menu(self, tearoff=0, bg=app.C["MENU_BG"], fg=app.C["TEXT"])
        help_menu.add_command(label="About", command=self._show_info)
        self.add_cascade(label="?", menu=help_menu)
    
    def _show_info(self):
        messagebox.showinfo(
            "StegoTool",
            "StegoTool v1.0\n\n"
            "Hide files in images using steganography.\n"
            "Supports LSB and APPEND methods with AES-256 encryption.\n\n"
            "© 2026"
        )


# ===== TOAST NOTIFICATIONS =====

class Toast:
    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors
        self.toasts = []

    def show(self, message, type_="success", duration=3000):
        C = self.colors
        toast = tk.Frame(self.parent, bg=C["ITEM_BG"])
        toast.configure(highlightbackground=C["BORDER"], highlightthickness=1)

        colors = {"success": C["SUCCESS"], "error": C["ERROR"], 
                  "warning": C["WARN"], "info": C["INFO"]}
        color = colors.get(type_, C["SUCCESS"])

        bar = tk.Frame(toast, bg=color, width=4)
        bar.pack(side="left", fill="y")

        content = tk.Frame(toast, bg=C["ITEM_BG"], padx=16, pady=12)
        content.pack(side="left", fill="both", expand=True)

        icon = "✓" if type_ == "success" else "✗" if type_ == "error" else "⚠" if type_ == "warning" else "ℹ"
        tk.Label(content, text=f"{icon}  {message}", bg=C["ITEM_BG"], fg=C["TEXT"],
                font=("Segoe UI", 10), anchor="w").pack(fill="x")

        toast.place(relx=1.0, x=-20, y=20 + len(self.toasts) * 60, anchor="ne")
        self.toasts.append(toast)

        if len(self.toasts) > 3:
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
            except:
                pass

        toast.after(duration, dismiss)
        toast.bind("<Button-1>", lambda e: dismiss())

    def _reposition(self):
        for i, t in enumerate(self.toasts):
            try:
                t.place(relx=1.0, x=-20, y=20 + i * 60, anchor="ne")
            except:
                pass


# ===== CUSTOM WIDGETS =====

class FilePicker(tk.Frame):
    def __init__(self, parent, var, placeholder, command, colors):
        super().__init__(parent, bg=parent.cget("bg"))
        self.var = var
        self.placeholder = placeholder
        self.C = colors

        self.entry = tk.Entry(self, textvariable=var, bg=self.C["ENTRY_BG"], fg=self.C["TEXT"],
                             font=("Segoe UI", 9), relief="sunken", bd=1,
                             insertbackground=self.C["TEXT"])
        self.entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 4))

        if not var.get():
            self.entry.insert(0, placeholder)
            self.entry.config(fg=self.C["TEXT_MUTE"])

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

        self.btn = tk.Label(self, text="...", bg=self.C["BTN_BG"], fg=self.C["TEXT"],
                           font=("Segoe UI", 9, "bold"), width=3, cursor="hand2",
                           relief="raised", bd=1)
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
        if not self.entry.get().strip():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=self.C["TEXT_MUTE"])


class SidebarItem(tk.Frame):
    def __init__(self, parent, icon, text, command, colors):
        super().__init__(parent, bg=colors["ITEM_BG"], cursor="hand2")
        self.command = command
        self.selected = False
        self.C = colors
        self.configure(highlightbackground=self.C["BORDER_LIGHT"], highlightthickness=1)

        self.icon_lbl = tk.Label(self, text=icon, bg=self.C["ITEM_BG"], font=("Segoe UI", 16),
                                width=3, fg=self.C["TEXT"])
        self.icon_lbl.pack(side="left", padx=(6, 0), pady=8)

        self.text_lbl = tk.Label(self, text=text, bg=self.C["ITEM_BG"], fg=self.C["TEXT"],
                                font=("Segoe UI", 10), anchor="w")
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


# ===== MAIN APPLICATION =====

class StegoTool:
    def __init__(self, root):
        self.root = root
        self.root.title("StegoTool")
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

        self.menubar = MenuBar(self.root, self)
        self.root.config(menu=self.menubar)

        self.body = tk.Frame(self.root, bg=C["WIN_BG"])
        self.body.pack(fill="both", expand=True)

        main_row = tk.Frame(self.body, bg=C["WIN_BG"])
        main_row.pack(fill="both", expand=True)

        sidebar = tk.Frame(main_row, bg=C["SIDEBAR_BG"], width=180)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="StegoTool", bg=C["SIDEBAR_BG"], fg=C["TEXT"],
                font=("Segoe UI", 14, "bold")).pack(pady=(12, 8))

        item_hide = SidebarItem(sidebar, "📝", "Hide", lambda: self._select_page("hide"), C)
        item_hide.pack(fill="x", padx=6, pady=4)
        self.sidebar_items["hide"] = item_hide

        item_extract = SidebarItem(sidebar, "📂", "Extract", lambda: self._select_page("extract"), C)
        item_extract.pack(fill="x", padx=6, pady=4)
        self.sidebar_items["extract"] = item_extract

        tk.Frame(main_row, bg=C["BORDER"], width=1).pack(side="left", fill="y")

        self.content = tk.Frame(main_row, bg=C["WIN_BG"], padx=24, pady=20)
        self.content.pack(side="left", fill="both", expand=True)

        self.pages["hide"] = self._build_hide_page(self.content)
        self.pages["extract"] = self._build_extract_page(self.content)

        self._select_page("hide")

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

        tk.Label(page, text="Hide Data", bg=C["WIN_BG"], fg=C["TEXT"],
                font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(page, text="Hide a secret file inside an image",
                bg=C["WIN_BG"], fg=C["TEXT_MUTE"], font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 16))

        tk.Label(page, text="File to hide", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w")
        FilePicker(page, self.hide_file, "Select file...", self._browse_hide_file, C).pack(fill="x", pady=(2, 10))

        tk.Label(page, text="Cover image", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w")
        FilePicker(page, self.hide_image, "Select image...", self._browse_image, C).pack(fill="x", pady=(2, 10))

        tk.Label(page, text="Save as", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w")
        FilePicker(page, self.hide_output, "Choose path...", self._browse_save, C).pack(fill="x", pady=(2, 14))

        opts = tk.LabelFrame(page, text="Options", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                            font=("Segoe UI", 9), bd=1, relief="groove", padx=12, pady=10)
        opts.pack(fill="x", pady=(0, 12))

        row = tk.Frame(opts, bg=C["WIN_BG"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Method", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9), width=12, anchor="w").pack(side="left")

        method_box = ttk.Combobox(row, state="readonly", width=35, font=("Segoe UI", 9),
                                 values=["LSB (pixel-based)", "APPEND (file end)"])
        method_box.current(0)
        method_box.pack(side="left", fill="x", expand=True)
        method_box.bind("<<ComboboxSelected>>",
                       lambda e: self.hide_method.set("lsb" if method_box.current() == 0 else "append"))

        encrypt_frame = tk.Frame(opts, bg=C["WIN_BG"])
        encrypt_frame.pack(fill="x", pady=(8, 4))

        self.encrypt_check = tk.Checkbutton(encrypt_frame, text="🔐 Encrypt with AES-256",
                                           variable=self.use_encryption,
                                           bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                                           font=("Segoe UI", 9),
                                           selectcolor=C["WIN_BG"],
                                           command=self._toggle_encryption)
        self.encrypt_check.pack(side="left")

        pwd_frame = tk.Frame(opts, bg=C["WIN_BG"])
        pwd_frame.pack(fill="x", pady=(4, 0))

        row1 = tk.Frame(pwd_frame, bg=C["WIN_BG"])
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Password:", bg=C["WIN_BG"], fg=C["TEXT"],
                font=("Segoe UI", 9), width=12, anchor="w").pack(side="left")
        self.pwd_entry = tk.Entry(row1, show="•", width=25, font=("Segoe UI", 9),
                                 bg=C["ENTRY_BG"], fg=C["TEXT"],
                                 insertbackground=C["TEXT"],
                                 relief="sunken", bd=1, state="disabled",
                                 disabledbackground=C["ENTRY_BG"],
                                 disabledforeground=C["TEXT"])
        self.pwd_entry.pack(side="left", padx=(0, 5))

        row2 = tk.Frame(pwd_frame, bg=C["WIN_BG"])
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="Confirm:", bg=C["WIN_BG"], fg=C["TEXT"],
                font=("Segoe UI", 9), width=12, anchor="w").pack(side="left")
        self.confirm_entry = tk.Entry(row2, show="•", width=25, font=("Segoe UI", 9),
                                     bg=C["ENTRY_BG"], fg=C["TEXT"],
                                     insertbackground=C["TEXT"],
                                     relief="sunken", bd=1, state="disabled",
                                     disabledbackground=C["ENTRY_BG"],
                                     disabledforeground=C["TEXT"])
        self.confirm_entry.pack(side="left", padx=(0, 5))

        self.show_pwd_var = tk.IntVar()
        self.show_btn = tk.Checkbutton(row1, text="👁 Show", variable=self.show_pwd_var,
                                      bg=C["WIN_BG"], fg=C["TEXT"],
                                      selectcolor=C["WIN_BG"],
                                      state="disabled",
                                      command=self._toggle_show)
        self.show_btn.pack(side="left")

        btn_row = tk.Frame(page, bg=C["WIN_BG"])
        btn_row.pack(fill="x", pady=(10, 0))
        self.hide_btn = tk.Button(btn_row, text="Hide File", command=self._do_hide,
                                 bg=C["ACCENT"], fg="white", font=("Segoe UI", 9, "bold"),
                                 padx=22, pady=8, relief="raised", bd=1,
                                 activebackground=C["BTN_HOV"], activeforeground=C["TEXT"])
        self.hide_btn.pack(side="right")

        return page

    def _toggle_encryption(self):
        if self.use_encryption.get():
            self.pwd_entry.config(state="normal")
            self.confirm_entry.config(state="normal")
            self.show_btn.config(state="normal")
            self.pwd_entry.focus()
        else:
            self.pwd_entry.config(state="disabled")
            self.confirm_entry.config(state="disabled")
            self.show_btn.config(state="disabled")
            self.show_pwd_var.set(0)
            self.pwd_entry.config(show="•")
            self.confirm_entry.config(show="•")
            self.pwd_entry.delete(0, tk.END)
            self.confirm_entry.delete(0, tk.END)

    def _toggle_show(self):
        if self.show_pwd_var.get():
            self.pwd_entry.config(show="")
            self.confirm_entry.config(show="")
        else:
            self.pwd_entry.config(show="•")
            self.confirm_entry.config(show="•")

    def _build_extract_page(self, parent):
        C = self.C
        page = tk.Frame(parent, bg=C["WIN_BG"])

        tk.Label(page, text="Extract Data", bg=C["WIN_BG"], fg=C["TEXT"],
                font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Label(page, text="Recover hidden file from image",
                bg=C["WIN_BG"], fg=C["TEXT_MUTE"], font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 16))

        tk.Label(page, text="Image with hidden file", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w")
        FilePicker(page, self.extract_image, "Select image...", self._browse_extract_image, C).pack(fill="x", pady=(2, 12))

        tk.Label(page, text="Destination folder", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                font=("Segoe UI", 9, "bold")).pack(anchor="w")
        FilePicker(page, self.extract_dir, "Select folder...", self._browse_dir, C).pack(fill="x", pady=(2, 14))

        info = tk.LabelFrame(page, text="Info", bg=C["WIN_BG"], fg=C["TEXT_DIM"],
                            font=("Segoe UI", 9), bd=1, relief="groove", padx=12, pady=10)
        info.pack(fill="x", pady=(0, 18))
        tk.Label(info, text="The tool automatically detects if encryption was used.\n"
                            "If encrypted, you'll be prompted for the password.",
                bg=C["WIN_BG"], fg=C["TEXT_MUTE"], font=("Segoe UI", 9), justify="left").pack(anchor="w")

        btn_row = tk.Frame(page, bg=C["WIN_BG"])
        btn_row.pack(fill="x")
        self.extract_btn = tk.Button(btn_row, text="Extract File", command=self._do_extract,
                                    bg=C["ACCENT"], fg="white", font=("Segoe UI", 9, "bold"),
                                    padx=22, pady=8, relief="raised", bd=1,
                                    activebackground=C["BTN_HOV"], activeforeground=C["TEXT"])
        self.extract_btn.pack(side="right")

        return page

    # ===== BROWSE FUNCTIONS =====

    def _browse_image(self):
        path = filedialog.askopenfilename(title="Select cover image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp *.tiff"), ("All", "*.*")])
        if path:
            self.hide_image.set(path)

    def _browse_hide_file(self):
        path = filedialog.askopenfilename(title="Select file to hide", filetypes=[("All", "*.*")])
        if path:
            self.hide_file.set(path)

    def _browse_save(self):
        path = filedialog.asksaveasfilename(title="Save image", defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("BMP", "*.bmp"), ("JPEG", "*.jpg"), ("All", "*.*")])
        if path:
            self.hide_output.set(path)

    def _browse_extract_image(self):
        path = filedialog.askopenfilename(title="Select image with hidden file",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All", "*.*")])
        if path:
            self.extract_image.set(path)

    def _browse_dir(self):
        path = filedialog.askdirectory(title="Select destination folder")
        if path:
            self.extract_dir.set(path)

    # ===== OPERATIONS WITH PROGRESS POPUP =====

    def _set_cursor_safe(self, cursor):
        """Set cursor safely across platforms"""
        try:
            self.root.config(cursor=cursor)
        except tk.TclError:
            # Fallback for Linux
            if cursor == "wait":
                try:
                    self.root.config(cursor="watch")
                except:
                    pass
            elif cursor == "watch":
                try:
                    self.root.config(cursor="wait")
                except:
                    pass
            else:
                try:
                    self.root.config(cursor="")
                except:
                    pass

    def _do_hide(self):
        img = self.hide_image.get()
        fil = self.hide_file.get()
        out = self.hide_output.get()
        method = self.hide_method.get()

        placeholders = ["", "Select image...", "Select file...", "Choose path..."]

        if img in placeholders or not Path(img).exists():
            self.toast.show("Select a valid cover image", "error")
            return
        if fil in placeholders or not Path(fil).exists():
            self.toast.show("Select a valid file to hide", "error")
            return
        if out in placeholders:
            self.toast.show("Specify output location", "error")
            return

        password = None
        if self.use_encryption.get():
            password = self.pwd_entry.get()
            confirm = self.confirm_entry.get()
            if not password:
                self.toast.show("Password required", "error")
                return
            if password != confirm:
                self.toast.show("Passwords do not match", "error")
                return
            if len(password) < 4:
                self.toast.show("Password must be at least 4 characters", "error")
                return

        # Show progress popup
        progress = ProgressPopup(self.root, "Hiding File...")
        progress.update_status("Starting...", "Preparing to hide file")
        
        self.hide_btn.config(state="disabled")
        self.extract_btn.config(state="disabled")
        self._set_cursor_safe("watch")

        def task():
            try:
                progress.update_status("Reading files...", "Loading cover image and secret file")
                progress.set_progress(10, 100)
                time.sleep(0.1)
                
                progress.update_status("Processing...", f"Using {method.upper()} method")
                progress.set_progress(30, 100)
                time.sleep(0.1)
                
                if method == "lsb":
                    result = hide_lsb(img, fil, out, password)
                else:
                    result = hide_append(img, fil, out, password)
                
                progress.set_progress(80, 100)
                progress.update_status("Finalizing...", "Saving output file")
                time.sleep(0.1)
                
                progress.set_progress(100, 100)
                
                if result:
                    msg = "File hidden!" + (" (encrypted)" if password else "")
                    self.root.after(0, lambda: self.toast.show(msg, "success"))
                else:
                    self.root.after(0, lambda: self.toast.show("Operation failed", "error"))
                
                progress.close()
                
            except Exception as e:
                progress.close()
                self.root.after(0, lambda: self.toast.show(f"Error: {str(e)}", "error"))
            finally:
                self.root.after(0, lambda: self.hide_btn.config(state="normal"))
                self.root.after(0, lambda: self.extract_btn.config(state="normal"))
                self.root.after(0, lambda: self._set_cursor_safe(""))

        threading.Thread(target=task, daemon=True).start()

    def _do_extract(self):
        img = self.extract_image.get()
        out = self.extract_dir.get()

        placeholders = ["", "Select image...", "Select folder..."]

        if img in placeholders or not Path(img).exists():
            self.toast.show("Select a valid image", "error")
            return
        if out in placeholders:
            out = str(Path.home() / "Desktop")
            self.extract_dir.set(out)

        # Show progress popup
        progress = ProgressPopup(self.root, "Extracting File...")
        progress.update_status("Starting...", "Preparing to extract hidden file")
        
        self.hide_btn.config(state="disabled")
        self.extract_btn.config(state="disabled")
        self._set_cursor_safe("watch")

        def task():
            try:
                progress.update_status("Reading image...", "Loading image file")
                progress.set_progress(10, 100)
                time.sleep(0.1)
                
                progress.update_status("Searching for hidden data...", "Checking LSB method")
                progress.set_progress(30, 100)
                time.sleep(0.1)
                
                payload = extract_lsb(img)
                if not payload:
                    progress.update_status("Searching...", "Checking APPEND method")
                    progress.set_progress(50, 100)
                    payload = extract_append(img)
                
                if not payload:
                    progress.close()
                    self.root.after(0, lambda: self.toast.show("No hidden file found", "warning"))
                    self.root.after(0, lambda: self.hide_btn.config(state="normal"))
                    self.root.after(0, lambda: self.extract_btn.config(state="normal"))
                    self.root.after(0, lambda: self._set_cursor_safe(""))
                    return
                
                # Check if encrypted
                if is_encrypted(payload):
                    progress.close()
                    # Ask for password on main thread
                    self.root.after(0, lambda: self._ask_password_and_extract(payload, out))
                    return
                
                # Not encrypted - extract directly
                progress.update_status("Processing...", "Extracting file (no encryption)")
                progress.set_progress(70, 100)
                time.sleep(0.1)
                
                file_name, file_data = process_payload(payload, None)
                
                progress.update_status("Saving file...", f"Saving: {file_name}")
                progress.set_progress(85, 100)
                time.sleep(0.1)
                
                path = save_file(file_name, file_data, out)
                
                progress.set_progress(100, 100)
                progress.update_status("Done!", f"File extracted successfully")
                time.sleep(0.2)
                
                self.root.after(0, lambda: self.toast.show(f"Extracted: {path.name}", "success"))
                progress.close()
                
                self.root.after(0, lambda: self.hide_btn.config(state="normal"))
                self.root.after(0, lambda: self.extract_btn.config(state="normal"))
                self.root.after(0, lambda: self._set_cursor_safe(""))

            except Exception as e:
                progress.close()
                self.root.after(0, lambda: self.toast.show(f"Error: {str(e)}", "error"))
                self.root.after(0, lambda: self.hide_btn.config(state="normal"))
                self.root.after(0, lambda: self.extract_btn.config(state="normal"))
                self.root.after(0, lambda: self._set_cursor_safe(""))

        threading.Thread(target=task, daemon=True).start()

    def _ask_password_and_extract(self, payload, out):
        """Called when encrypted file is detected"""
        pwd_dialog = PasswordDialog(self.root, "Password Required", 
                                   "This file is encrypted. Enter password:")
        password = pwd_dialog.get_password()
        
        if password is None:
            # User cancelled
            self.hide_btn.config(state="normal")
            self.extract_btn.config(state="normal")
            self._set_cursor_safe("")
            self.toast.show("Extraction cancelled", "warning")
            return
        
        # Show progress for decryption
        progress = ProgressPopup(self.root, "Decrypting...")
        progress.update_status("Decrypting...", "Please wait")
        
        def decrypt_task():
            try:
                progress.update_status("Processing...", "Decrypting file")
                progress.set_progress(50, 100)
                time.sleep(0.1)
                
                file_name, file_data = process_payload(payload, password)
                
                progress.update_status("Saving file...", f"Saving: {file_name}")
                progress.set_progress(80, 100)
                time.sleep(0.1)
                
                path = save_file(file_name, file_data, out)
                
                progress.set_progress(100, 100)
                progress.update_status("Done!", f"File extracted successfully")
                time.sleep(0.2)
                
                self.root.after(0, lambda: self.toast.show(f"Extracted: {path.name}", "success"))
                progress.close()
                
            except Exception as e:
                progress.close()
                error_msg = str(e)
                if "Invalid token" in error_msg or "decryption" in error_msg or "password" in error_msg.lower():
                    self.root.after(0, lambda: self.toast.show("Wrong password! Extraction failed.", "error"))
                else:
                    self.root.after(0, lambda: self.toast.show(f"Error: {error_msg}", "error"))
            finally:
                self.root.after(0, lambda: self.hide_btn.config(state="normal"))
                self.root.after(0, lambda: self.extract_btn.config(state="normal"))
                self.root.after(0, lambda: self._set_cursor_safe(""))
        
        threading.Thread(target=decrypt_task, daemon=True).start()