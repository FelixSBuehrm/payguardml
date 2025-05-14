#!/bin/bash
# build-all-platforms.sh - Script to build for all supported platforms

echo "Building Findec for all platforms..."

# 1. Build for macOS ARM64
echo "----------------------------------------------"
echo "Building for macOS ARM64..."
echo "----------------------------------------------"
npm run dist:mac-arm
echo ""

# 2. Build for macOS x64 (Intel)
echo "----------------------------------------------"
echo "Building for macOS Intel (x64)..."
echo "----------------------------------------------"
npm run dist:mac-intel
echo ""

# 3. Build for macOS Universal (both ARM and Intel)
echo "----------------------------------------------"
echo "Building for macOS Universal (ARM + Intel)..."
echo "----------------------------------------------"
npm run dist:mac-universal
echo ""

# 4. Build for Windows x64
echo "----------------------------------------------"
echo "Building for Windows x64..."
echo "----------------------------------------------"
npm run dist:win-x64
echo ""

echo "All builds complete! Check the dist directory for your packages."
