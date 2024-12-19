#!/bin/bash

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python installation
if ! command_exists python3; then
    echo "Python3 is not installed. Installing Python3..."
    sudo apt update && sudo apt install -y python3
else
    echo "Python3 is already installed."
fi

# Check for pip installation
if ! command_exists pip3; then
    echo "pip3 is not installed. Installing pip3..."
    sudo apt update && sudo apt install -y python3-pip
else
    echo "pip3 is already installed."
fi

# Check for FFmpeg installation
if ! command_exists ffmpeg; then
    echo "FFmpeg is not installed. Installing FFmpeg..."
    sudo apt update && sudo apt install -y ffmpeg
else
    echo "FFmpeg is already installed."
fi

# Create a Python virtual environment
VENV_DIR="whisper_env"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "Python virtual environment already exists."
fi

# Activate the virtual environment
source $VENV_DIR/bin/activate

# Upgrade pip in the virtual environment
echo "Upgrading pip in the virtual environment..."
pip install --upgrade pip

# Install required Python packages
echo "Installing required dependencies..."
pip install -r requirements.txt

# Check for Whisper dependencies
REQUIRED_PACKAGES=(
    "whisper"
    "sounddevice"
    "numpy"
    "scipy"
    "tkinter"
    "pyperclip"
)

for PACKAGE in "${REQUIRED_PACKAGES[@]}"; do
    if ! pip show "$PACKAGE" >/dev/null 2>&1; then
        echo "Installing $PACKAGE..."
        pip install "$PACKAGE"
    else
        echo "$PACKAGE is already installed."
    fi
done

# Deactivate the virtual environment
echo "Setup complete. Deactivating virtual environment."
deactivate

# Final message
echo "The environment setup is complete. Activate it using: source $VENV_DIR/bin/activate"

echo "Running build_linux.py" 
python build_linux.py