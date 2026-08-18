#!/bin/bash
# StegoTool - Linux Launcher

cd "$(dirname "$0")"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found! Please install Python 3."
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
python3 -c "import PIL" 2>/dev/null || {
    echo "📦 Installing Pillow..."
    python3 -m pip install Pillow --quiet
}
python3 -c "from cryptography.fernet import Fernet" 2>/dev/null || {
    echo "📦 Installing cryptography..."
    python3 -m pip install cryptography --quiet
}

# Run the application
echo "🚀 Starting StegoTool..."
cd src
python3 run.py

exit 0
