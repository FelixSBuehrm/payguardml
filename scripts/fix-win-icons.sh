#!/bin/bash
# fix-win-icons.sh - Script to generate Windows icons from PNG images

echo "Generating Windows icons..."

# Make sure we're in the project root
cd "$(dirname "$0")/.."

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null && ! command -v magick &> /dev/null; then
    echo "ImageMagick is not installed. Please install it with 'brew install imagemagick'"
    exit 1
fi

# Use the 256x256 PNG to create a Windows .ico file
if [ -f "build/icon_256x256.png" ]; then
    echo "Converting PNG to ICO format..."
    if command -v magick &> /dev/null; then
        # Use 'magick' command if available (newer ImageMagick versions)
        magick build/icon_256x256.png -define icon:auto-resize=256,128,64,48,32,16 build/icon.ico
    else
        # Fall back to 'convert' for older ImageMagick versions
        convert build/icon_256x256.png -define icon:auto-resize=256,128,64,48,32,16 build/icon.ico
    fi
    echo "Windows icon file created: build/icon.ico"
else
    echo "Error: Source PNG file not found at build/icon_256x256.png"
    exit 1
fi

echo "Windows icons generated successfully."
