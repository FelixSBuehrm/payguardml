#!/bin/bash
# quick-arm64-build.sh - Script to quickly build for ARM64 architecture

echo "Building PayGuard for ARM64 architecture..."

# Ensure node modules are installed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Prepare icons
echo "Preparing icons..."
./scripts/prepare-icons.sh

# Create a temporary electron-builder.yml file with optimized settings
cat > electron-builder-arm64.yml <<EOL
appId: com.findec.app
productName: PayGuard
files:
  - app/**/*
  - build/**/*.{icns,ico,png}
  - assets/**/*.{icns,ico,png}
  - node_modules/**/*
  - package.json
mac:
  icon: build/icon.icns
  target: zip
  hardenedRuntime: true
  gatekeeperAssess: false
  artifactName: "\${productName}-\${version}-arm64.\${ext}"
  category: public.app-category.finance
extraResources:
  - from: backend
    to: backend
  - from: content
    to: content
compression: store
asar: false
EOL

# Run the build with the temporary config
echo "Running ARM64 build with optimized settings..."
npx electron-builder --mac --arm64 --config electron-builder-arm64.yml

# Clean up
rm electron-builder-arm64.yml

echo "Build complete. Check the dist directory for your ARM64 package."
