#!/bin/bash
# Script to fix macOS icon sizes for better Dock icon appearance

ASSETS_DIR="../assets"
BUILD_DIR="../build"
DOCK_ICONSET_DIR="../build/dock_icon.iconset"

# Ensure we're in the scripts directory
cd "$(dirname "$0")"

# Make sure the dock_icon.iconset directory exists
mkdir -p "$DOCK_ICONSET_DIR"

echo "Creating macOS dock icon set..."

# Use the existing 128x128 and 256x256 PNGs
if [ -f "$ASSETS_DIR/icon_128x128.png" ]; then
    cp "$ASSETS_DIR/icon_128x128.png" "$DOCK_ICONSET_DIR/icon_128x128.png"
    echo "Copied 128x128 icon"

    # Create a 64x64 version
    sips -z 64 64 "$ASSETS_DIR/icon_128x128.png" --out "$DOCK_ICONSET_DIR/icon_64x64.png"
    echo "Created 64x64 icon"
    
    # Create a 32x32 version
    sips -z 32 32 "$ASSETS_DIR/icon_128x128.png" --out "$DOCK_ICONSET_DIR/icon_32x32.png"
    echo "Created 32x32 icon"
    
    # Create a 16x16 version
    sips -z 16 16 "$ASSETS_DIR/icon_128x128.png" --out "$DOCK_ICONSET_DIR/icon_16x16.png"
    echo "Created 16x16 icon"
fi

if [ -f "$ASSETS_DIR/icon_256x256.png" ]; then
    cp "$ASSETS_DIR/icon_256x256.png" "$DOCK_ICONSET_DIR/icon_256x256.png"
    echo "Copied 256x256 icon"
fi

# Generate .icns file using macOS iconutil
echo "Generating dock_icon.icns file..."
iconutil -c icns "$DOCK_ICONSET_DIR" -o "$BUILD_DIR/dock_icon.icns"

if [ $? -eq 0 ]; then
    echo "✅ Successfully created dock_icon.icns"
else
    echo "❌ Failed to create dock_icon.icns"
    exit 1
fi

echo "Done! The dock icon has been optimized for macOS."
