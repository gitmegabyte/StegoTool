#!/usr/bin/env python3
"""
StegoTool - Unified Launcher
Works on both Windows and Linux
"""

import sys
import os
import platform

# Add src directory to path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Run the main application
try:
    from stegotool import main
    main()
except ImportError as e:
    print(f"Error importing stegotool: {e}")
    print("Make sure you're running from the project root directory.")
    sys.exit(1)