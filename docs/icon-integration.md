# PayGuardML Icon Integration

This document explains how the application icons are integrated and how to build the application with proper icons for different platforms.

## Icon Files

- `assets/icon_256x256.png` - Main source icon (256x256 pixels)
- `assets/icon_128x128.png` - Smaller icon version (128x128 pixels)
- `build/icon.icns` - macOS icon format
- `build/icon.ico` - Windows icon format

## Building with Icons

The application uses the following scripts to manage icons:

1. `npm run prepare-icons` - Prepares all necessary icon files
   - Copies PNG icons to the build directory
   - Creates .icns file for macOS (if needed)
   - Ensures .ico file exists for Windows

2. When building the application:
   - `npm run dist:mac` - Builds for macOS with proper icon integration
   - `npm run dist:win` - Builds for Windows with proper icon integration
   - `npm run dist` - Builds for all platforms

## Manual Icon Creation

If needed, you can manually create icon files:

### macOS (.icns)

```bash
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
```

### Windows (.ico)

For Windows, you can use the ImageMagick command-line tool:

```bash
# Install ImageMagick if needed
brew install imagemagick

# Create .ico file with multiple resolutions
convert assets/icon_256x256.png -define icon:auto-resize=256,128,64,48,32,16 build/icon.ico
```

## Troubleshooting

If icons don't appear correctly:

1. Make sure all icon files exist in their expected locations
2. Run `npm run prepare-icons` to regenerate icon files
3. Restart the application with `npm start`
4. For distribution builds, use the appropriate npm script
