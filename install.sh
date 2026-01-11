#!/bin/bash

# ID Photo Maker Installation Script

APP_NAME="ID Photo Maker"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
DESKTOP_FILE="$HOME/.local/share/applications/id-photo-maker.desktop"
ICON_NAME="camera-photo" # Standard icon, can be replaced

echo "Installing $APP_NAME..."

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# 2. Check for Tkinter (System dependency)
# Simple check if we can import tkinter
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Warning: 'tkinter' python module not found."
    echo "Please install python3-tk (Debian/Ubuntu) or tk (Arch/Fedora)."
    read -p "Attempt to install automatically? (y/N) " confirm
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        if command -v pacman &> /dev/null; then
            sudo pacman -S tk --noconfirm
        elif command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y python3-tk
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y python3-tkinter
        else
            echo "Could not detect package manager. Please install 'tk' manually."
        fi
    fi
fi

# 3. Create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# 4. Install Python Dependencies
echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

# 5. Create Desktop Entry
echo "Creating desktop shortcut..."
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Comment=Create French Passport/ID Photos (35x45mm)
Exec="$VENV_DIR/bin/python3" "$APP_DIR/id_photo_maker.py"
Icon=$ICON_NAME
Terminal=false
Categories=Graphics;Photography;Utility;
StartupNotify=true
Path=$APP_DIR
EOF

# 6. Update Desktop Database
update-desktop-database "$HOME/.local/share/applications" &> /dev/null

echo "Installation Complete!"
echo "You can launch '$APP_NAME' from your application menu."
