#!/usr/bin/env python3
"""
StegoTool - Steganography Tool
Main entry point (works on Windows and Linux)
"""

import sys
import subprocess
import tkinter as tk
from tkinter import ttk
import time
import os
import platform

# Disable __pycache__
sys.dont_write_bytecode = True


class LoadingPopup:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("StegoTool")
        self.root.geometry("420x200")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1b1e")
        self.root.overrideredirect(True)
        
        self.root.update_idletasks()
        width, height = 420, 200
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        tk.Label(self.root, text="🔐", bg="#1a1b1e", fg="#6b9fd5",
                font=("Segoe UI", 32)).pack(pady=(15, 5))
        tk.Label(self.root, text="StegoTool", bg="#1a1b1e", fg="#f0f0f0",
                font=("Segoe UI", 14, "bold")).pack(pady=(0, 5))
        
        self.status_label = tk.Label(self.root, text="Starting...", bg="#1a1b1e", 
                                     fg="#b0b0b8", font=("Segoe UI", 10))
        self.status_label.pack(pady=(5, 8))
        
        self.progress = ttk.Progressbar(self.root, length=300, mode='indeterminate')
        self.progress.pack(pady=8)
        self.progress.start(10)
        
        self.root.update()
    
    def update_status(self, text):
        self.status_label.config(text=text)
        self.root.update()
    
    def close(self):
        self.progress.stop()
        self.root.destroy()


def main():
    popup = LoadingPopup()
    
    try:
        # Check if running on Linux, use 'python3' if needed
        if platform.system() == "Linux" and sys.executable.endswith("python"):
            # We're using 'python' but need to ensure it's Python 3
            pass
        
        # Pillow
        try:
            from PIL import Image
        except ImportError:
            popup.update_status("Installing Pillow...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "Pillow", "--quiet"
            ])
            from PIL import Image
        
        # Cryptography
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            popup.update_status("Installing Cryptography...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "cryptography", "--quiet"
            ])
            from cryptography.fernet import Fernet
        
        popup.close()
        
        # Now import ui from the same directory
        from ui import StegoTool
        root = tk.Tk()
        app = StegoTool(root)
        root.mainloop()
        
    except Exception as e:
        popup.update_status(f"Error: {str(e)[:30]}...")
        time.sleep(1.5)
        popup.close()
        import tkinter.messagebox as mb
        mb.showerror("Error", f"Cannot start StegoTool:\n\n{str(e)}")


if __name__ == "__main__":
    main()