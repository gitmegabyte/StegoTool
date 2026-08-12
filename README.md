# StegoTool

StegoTool is a desktop application for hiding and extracting secret files inside images using steganography. It supports both **unencrypted** and **AES-256-GCM encrypted** payloads.

## Features
- Hide any file inside PNG, BMP, and JPEG images.
- Extract hidden files automatically (detects LSB and APPEND methods).
- **AES-256-GCM encryption** to protect your hidden data with a password.
- Two hiding methods:
  - **LSB (Least Significant Bit)**: Highly stealthy, hides data in pixel bits (limited by image size).
  - **APPEND**: No size limit, appends the secret file at the end of the image (image size increases slightly).
- Light / Dark theme support.
- Modern, user-friendly interface with toast notifications.

## Installation
Download `StegoTool.pyw` and run it. 
On the first launch, the app will automatically check and install the required dependencies (`Pillow` and `cryptography`).

**Manual install (if needed):**
```bash
pip install Pillow cryptography