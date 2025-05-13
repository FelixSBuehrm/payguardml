// Generate icons for different platforms
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// Check if imagemagick is installed
function checkImageMagick() {
    return new Promise((resolve, reject) => {
        const process = spawn('convert', ['--version']);
        
        process.on('error', (err) => {
            console.error('ImageMagick is not installed. Please install it to generate icons.');
            console.error('On macOS: brew install imagemagick');
            console.error('On Windows: Download from https://imagemagick.org/script/download.php');
            console.error('On Linux: Use your package manager, e.g., apt-get install imagemagick');
            reject(err);
        });
        
        process.on('close', (code) => {
            if (code === 0) {
                resolve(true);
            } else {
                reject(new Error(`ImageMagick check exited with code ${code}`));
            }
        });
    });
}

// Generate .icns file for macOS
function generateIcns(sourceFile, targetFile) {
    return new Promise((resolve, reject) => {
        console.log('Generating .icns file...');
        
        // Create temporary iconset directory
        const iconsetDir = path.join(path.dirname(targetFile), 'icon.iconset');
        
        if (!fs.existsSync(iconsetDir)) {
            fs.mkdirSync(iconsetDir, { recursive: true });
        }
        
        // Define icon sizes
        const sizes = [16, 32, 64, 128, 256, 512, 1024];
        const commands = [];
        
        // Generate commands for each size
        sizes.forEach(size => {
            commands.push({
                args: [sourceFile, '-resize', `${size}x${size}`, path.join(iconsetDir, `icon_${size}x${size}.png`)]
            });
            commands.push({
                args: [sourceFile, '-resize', `${size*2}x${size*2}`, path.join(iconsetDir, `icon_${size}x${size}@2x.png`)]
            });
        });
        
        // Execute commands sequentially
        const executeCommands = (commands, index = 0) => {
            if (index >= commands.length) {
                // All commands executed, now convert iconset to .icns
                const icnsProcess = spawn('iconutil', ['-c', 'icns', iconsetDir, '-o', targetFile]);
                
                icnsProcess.on('error', (err) => {
                    console.error('Error generating .icns file:', err);
                    reject(err);
                });
                
                icnsProcess.on('close', (code) => {
                    if (code === 0) {
                        console.log('.icns file generated successfully');
                        
                        // Cleanup iconset directory
                        fs.rmSync(iconsetDir, { recursive: true, force: true });
                        
                        resolve();
                    } else {
                        reject(new Error(`iconutil exited with code ${code}`));
                    }
                });
                
                return;
            }
            
            const { args } = commands[index];
            const process = spawn('convert', args);
            
            process.on('error', (err) => {
                console.error('Error executing command:', err);
                reject(err);
            });
            
            process.on('close', (code) => {
                if (code === 0) {
                    executeCommands(commands, index + 1);
                } else {
                    reject(new Error(`convert exited with code ${code}`));
                }
            });
        };
        
        executeCommands(commands);
    });
}

// Generate .ico file for Windows
function generateIco(sourceFile, targetFile) {
    return new Promise((resolve, reject) => {
        console.log('Generating .ico file...');
        
        // Define icon sizes for Windows (16, 32, 48, 64, 128, 256)
        const sizes = [16, 32, 48, 64, 128, 256];
        
        // Create temporary directory for individual size PNGs
        const tempDir = path.join(path.dirname(targetFile), 'temp_icons');
        
        if (!fs.existsSync(tempDir)) {
            fs.mkdirSync(tempDir, { recursive: true });
        }
        
        // Generate PNGs of all sizes
        const commands = sizes.map(size => ({
            args: [sourceFile, '-resize', `${size}x${size}`, path.join(tempDir, `icon_${size}.png`)]
        }));
        
        // Execute commands sequentially
        const executeCommands = (commands, index = 0) => {
            if (index >= commands.length) {
                // All PNGs generated, now combine them into an .ico file
                const args = ['-background', 'none', '-density', '72x72'];
                
                // Add all the generated PNGs as input
                sizes.forEach(size => {
                    args.push(path.join(tempDir, `icon_${size}.png`));
                });
                
                // Add output file
                args.push('-colors', '256', targetFile);
                
                const icoProcess = spawn('convert', args);
                
                icoProcess.on('error', (err) => {
                    console.error('Error generating .ico file:', err);
                    reject(err);
                });
                
                icoProcess.on('close', (code) => {
                    if (code === 0) {
                        console.log('.ico file generated successfully');
                        
                        // Cleanup temporary directory
                        fs.rmSync(tempDir, { recursive: true, force: true });
                        
                        resolve();
                    } else {
                        reject(new Error(`convert exited with code ${code}`));
                    }
                });
                
                return;
            }
            
            const { args } = commands[index];
            const process = spawn('convert', args);
            
            process.on('error', (err) => {
                console.error('Error executing command:', err);
                reject(err);
            });
            
            process.on('close', (code) => {
                if (code === 0) {
                    executeCommands(commands, index + 1);
                } else {
                    reject(new Error(`convert exited with code ${code}`));
                }
            });
        };
        
        executeCommands(commands);
    });
}

// Main function
async function main() {
    try {
        // Ensure ImageMagick is installed
        await checkImageMagick();
        
        // Create build directory if it doesn't exist
        const buildDir = path.join(__dirname, '..', 'build');
        if (!fs.existsSync(buildDir)) {
            fs.mkdirSync(buildDir, { recursive: true });
        }
        
        // Source icon (highest resolution PNG)
        const sourceIcon = path.join(__dirname, '..', 'assets', 'icon_256x256.png');
        
        // Check if source icon exists
        if (!fs.existsSync(sourceIcon)) {
            throw new Error('Source icon not found: ' + sourceIcon);
        }
        
        // Generate .icns for macOS
        const icnsFile = path.join(buildDir, 'icon.icns');
        if (process.platform === 'darwin') {
            await generateIcns(sourceIcon, icnsFile);
        } else {
            console.log('Skipping .icns generation on non-macOS platform');
        }
        
        // Generate .ico for Windows
        const icoFile = path.join(buildDir, 'icon.ico');
        await generateIco(sourceIcon, icoFile);
        
        console.log('Icon generation completed successfully');
    } catch (err) {
        console.error('Error generating icons:', err);
        process.exit(1);
    }
}

// Run the main function
main();
