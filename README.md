# StegoTool

Desktop application for hiding and extracting secret files inside images using steganography. Supports both **unencrypted** and **AES-256-GCM encrypted** payloads.

## Features
- Hide any file inside PNG, BMP, and JPEG images
- Automatic extraction of hidden files (detects LSB and APPEND methods)
- **AES-256-GCM encryption** to protect your data with a password
- Two hiding methods:
  - **LSB (Least Significant Bit)**: High stealth, hides data in pixel bits (limited by image size)
  - **APPEND**: No size limit, appends the file at the end of the image (image size increases slightly)
- Light / Dark theme support
- Modern interface with toast notifications

## Installation
Download `StegoTool.pyw` and run it. On first launch, the application will automatically install the required dependencies (`Pillow` and `cryptography`).

**Manual install (if needed):**
```bash
pip install Pillow cryptography
```

## Launchers

### Windows
Run `launch_windows.bat` to start the application. The script automatically checks Python and installs required dependencies.

### Unix-like (Linux/macOS)
Run `launch_unix_like.sh` to start the application:
```bash
chmod +x launch_unix_like.sh
./launch_unix_like.sh
```

The script automatically checks Python 3 and installs required dependencies.