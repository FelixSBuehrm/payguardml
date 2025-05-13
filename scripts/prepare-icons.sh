#!/bin/bash
# prepare-icons.sh - Script to prepare icons for all platforms before building

echo "Preparing application icons..."

# Create build directory if it doesn't exist
mkdir -p build

# Copy PNG icons to build directory
echo "Copying PNG icons..."
cp -f assets/icon_256x256.png build/
cp -f assets/icon_128x128.png build/

# Ensure we have .ico for Windows and .icns for macOS
if [ ! -f build/icon.ico ]; then
  echo "icon.ico not found, copying from existing files..."
  # If we already have an ico file, copy it
  if [ -f build/icon.ico ]; then
    cp -f build/icon.ico build/icon.ico
  else
    echo "Using PNG as fallback for Windows icon"
    cp -f assets/icon_256x256.png build/icon.ico
  fi
fi

# Check for macOS icon
if [ ! -f build/icon.icns ]; then
  echo "icon.icns not found, checking if we can create it..."
  
  # Check if we're on macOS and have iconutil
  if [[ "$OSTYPE" == "darwin"* ]] && command -v iconutil &> /dev/null; then
    echo "Creating .icns file using iconutil..."
    
    # Create iconset directory
    mkdir -p build/icon.iconset
    
    # Generate different sizes
    sips -z 16 16 assets/icon_256x256.png --out build/icon.iconset/icon_16x16.png
    sips -z 32 32 assets/icon_256x256.png --out build/icon.iconset/icon_16x16@2x.png
    sips -z 32 32 assets/icon_256x256.png --out build/icon.iconset/icon_32x32.png
    sips -z 64 64 assets/icon_256x256.png --out build/icon.iconset/icon_32x32@2x.png
    sips -z 128 128 assets/icon_256x256.png --out build/icon.iconset/icon_128x128.png
    sips -z 256 256 assets/icon_256x256.png --out build/icon.iconset/icon_128x128@2x.png
    sips -z 256 256 assets/icon_256x256.png --out build/icon.iconset/icon_256x256.png
    cp assets/icon_256x256.png build/icon.iconset/icon_256x256@2x.png
    
    # Convert iconset to icns
    iconutil -c icns build/icon.iconset -o build/icon.icns
    
    echo ".icns file created successfully"
  else
    echo "Cannot create .icns file, iconutil not available"
    echo "Using PNG as fallback for macOS icon"
    cp -f assets/icon_256x256.png build/icon.icns
  fi
fi

echo "Icons prepared successfully."
