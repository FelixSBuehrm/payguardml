const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let store; // Declare store, will be initialized asynchronously
let mainWindow;

// Determine if the app is packaged
const isDev = process.env.NODE_ENV !== 'production'; // This might be more reliable
const isPackaged = app.isPackaged;

// Adjust projectRoot determination
let projectRoot;
if (isPackaged) {
    // For packaged app, assuming backend and content are bundled relative to resourcesPath
    // This often means they are in extraResources, e.g., projectRoot/backend -> resources/backend
    projectRoot = process.resourcesPath; 
} else {
    // In development, app.getAppPath() is the project root directory (where package.json is)
    projectRoot = app.getAppPath();
}

// Determine icon path based on platform and packaging state
function getIconPath() {
    const appRootPath = app.getAppPath();
    
    // For Mac, use a simple approach for window icons
    if (process.platform === 'darwin') {
        // Simple fallback mechanism - just try a few common locations
        const iconPath = path.join(appRootPath, 'assets', 'icon_128x128.png');
        return iconPath;
    } else if (process.platform === 'win32') {
        return path.join(appRootPath, 'build', 'icon.ico');
    } else {
        // Linux and others use .png
        return path.join(appRootPath, 'assets', 'icon_256x256.png');
    }
}

function createWindow() {
    // Create the browser window first before any dynamic imports or async operations
    mainWindow = new BrowserWindow({
        width: 800,
        height: 750,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            devTools: isDev // Enable DevTools only in development
        },
        show: false, // Don't show until ready-to-show
        icon: getIconPath()
    });

    // Set up the ready-to-show event
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Load the index.html file
    mainWindow.loadFile(path.join(__dirname, 'index.html'));

    // Only open DevTools in development mode and only if explicitly requested
    // Comment this out to disable automatic DevTools opening
    // if (isDev) {
    //     mainWindow.webContents.openDevTools();
    // }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(async () => { // Make the callback async
    // On macOS, set the dock icon - simple approach to improve startup time
    if (process.platform === 'darwin') {
        const iconPath = path.join(app.getAppPath(), 'assets', 'icon_128x128.png');
        try {
            app.dock.setIcon(iconPath);
        } catch (err) {
            console.warn('Could not set dock icon:', err.message);
        }
        
        try {
            // Dynamically import fix-path - use a timeout to not block startup
            setTimeout(async () => {
                try {
                    const fixPathModule = await import('fix-path');
                    if (fixPathModule && fixPathModule.default) {
                        const fixPath = fixPathModule.default; // Access the default export
                        fixPath();
                        console.log('PATH fixed for macOS using dynamic import.');
                    } else {
                        console.log('fix-path module loaded but default export not found');
                    }
                } catch (err) {
                    console.error('Failed to dynamically import or run fix-path.', err.message);
                }
            }, 500); // Delay this non-critical operation
        } catch (err) {
            console.error('Failed to set up fix-path import.');
        }
    }

    try {
        // Create window first, then initialize store asynchronously
        createWindow();
        
        // Dynamically import electron-store after window is created
        setTimeout(async () => {
            try {
                const StoreModule = await import('electron-store');
                if (StoreModule && StoreModule.default) {
                    const Store = StoreModule.default; // Access the default export which is the class
                    store = new Store(); // Initialize store
                    console.log('Electron-store initialized successfully.');
                } else {
                    console.error('Electron-store module loaded but default export not found');
                }
            } catch (err) {
                console.error('Failed to initialize electron-store:', err.message);
                // Only show error dialog if this is a critical failure and the window exists
                if (mainWindow) {
                    dialog.showErrorBox('Initialization Error', 'Failed to load essential components. Please restart the application.');
                }
            }
        }, 100);
    } catch (err) {
        console.error('Failed to start application:', err);
        dialog.showErrorBox('Startup Error', `Failed to start the application: ${err.message}`);
        app.quit();
    }

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

// IPC handler for file dialog
ipcMain.handle('dialog:openFile', async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
        properties: ['openFile'],
        filters: [
            { name: 'CSV Files', extensions: ['csv'] }
        ]
    });
    if (canceled || filePaths.length === 0) {
        return null;
    }
    return filePaths[0];
});

// IPC handler to open output folder
ipcMain.on('open-output-folder', (event, folderPath) => {
    shell.openPath(folderPath).catch(err => {
        console.error("Failed to open output folder:", err);
        event.sender.send('processing-log', `ERROR: Could not open folder ${folderPath}.`);
    });
});

// IPC handler for processing CSV
ipcMain.on('process-csv', async (event, csvPath) => { // Added async here
    const backendDir = path.join(projectRoot, 'backend');
    const mainPyScript = path.join(backendDir, 'main.py');
    const outputBaseDir = path.join(projectRoot, 'output'); // Output dir relative to corrected projectRoot

    let pythonExecutable;
    if (isDev && process.platform === 'darwin') {
        // IMPORTANT: User's specific path confirmed via `python -c "import sys; print(sys.executable)"`
        pythonExecutable = '/opt/anaconda3/envs/findec_env/bin/python'; 
        const fs = require('fs');
        if (!fs.existsSync(pythonExecutable)) {
            console.error(`Specified Python path for dev does not exist: ${pythonExecutable}. Falling back to python3. Please verify the path.`);
            event.sender.send('processing-error', `Developer Python path error: ${pythonExecutable} not found. Please update in main.js or ensure Conda environment is active and discoverable.`);
            pythonExecutable = 'python3'; // Fallback
        } else {
            console.log(`Using development Python path for macOS: ${pythonExecutable}`);
        }
    } else if (process.platform === 'win32') {
        pythonExecutable = 'python';
        // Later, for packaged app on Windows, this would point to bundled Python
    } else {
        pythonExecutable = 'python3';
        // Later, for packaged app on Linux/macOS, this would point to bundled Python
    }

    console.log(`Project root: ${projectRoot}`);
    console.log(`Backend directory: ${backendDir}`);
    console.log(`Python executable: ${pythonExecutable}`);

    const scriptArgs = [
        mainPyScript,
        '--input', csvPath,
        '--output_dir', outputBaseDir
    ];

    // Retrieve API key and add to args if it exists
    const apiKey = store.get('geminiApiKey');
    if (apiKey) {
        scriptArgs.push('--api_key', apiKey);
        console.log('Using stored API key for Python script.');
    } else {
        console.log('No API key found in store. Python script will try to use .env or default.');
    }

    console.log(`Spawning Python: ${pythonExecutable} \"${scriptArgs.join('\" \"')}\"`);

    const pythonProcess = spawn(pythonExecutable, scriptArgs, {
        cwd: backendDir, // Correct working directory for the main python script
        env: { ...process.env } // Ensure the child process inherits the environment
    });
    
    // Store process ID and notify renderer
    const processId = pythonProcess.pid;
    event.sender.send('process-started', processId);
    
    // Store the process in a map so we can kill it later if requested
    if (!global.runningProcesses) {
        global.runningProcesses = new Map();
    }
    global.runningProcesses.set(processId, pythonProcess);

    let fullOutput = "";
    pythonProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(`Python stdout: ${output}`);
        fullOutput += output;
        
        // Send the output to the renderer process
        if (event && event.sender) {
            event.sender.send('processing-log', output);
        }
    });

    pythonProcess.stderr.on('data', (data) => {
        const errorOutput = data.toString();
        console.error(`Python stderr: ${errorOutput}`);
        
        // Send the error to the renderer process
        if (event && event.sender) {
            event.sender.send('processing-log', `ERROR: ${errorOutput}`);
        }
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python script exited with code ${code}`);
        
        // Remove process from the map
        if (global.runningProcesses && processId) {
            global.runningProcesses.delete(processId);
        }
        
        if (code === 0) {
            // Look for the JSON_OUTPUT_PATH marker
            const pathMatch = fullOutput.match(/JSON_OUTPUT_PATH:(.*?)(\r|\n|$)/);
            if (pathMatch && pathMatch[1]) {
                const jsonPath = pathMatch[1].trim();
                console.log(`Found JSON output path: ${jsonPath}`);
                
                // Read the JSON file to include its content
                try {
                    const fs = require('fs');
                    if (fs.existsSync(jsonPath)) {
                        const fileContent = fs.readFileSync(jsonPath, 'utf8');
                        try {
                            const jsonContent = JSON.parse(fileContent);
                            
                            // Send both path and content to the renderer
                            event.sender.send('processing-complete', {
                                filePath: jsonPath,
                                jsonContent: jsonContent
                            });
                        } catch (parseErr) {
                            console.error('Error parsing JSON file:', parseErr);
                            event.sender.send('processing-error', `Error parsing JSON file: ${parseErr.message}`);
                        }
                    } else {
                        console.error(`JSON file does not exist at path: ${jsonPath}`);
                        event.sender.send('processing-error', `JSON file not found at: ${jsonPath}`);
                    }
                } catch (err) {
                    console.error('Error reading JSON file:', err);
                    event.sender.send('processing-error', `Error reading output JSON: ${err.message}`);
                }
            } else {
                console.error('Could not find JSON_OUTPUT_PATH in output');
                console.log('Full output:', fullOutput);
                event.sender.send('processing-error', 'Could not find JSON_OUTPUT_PATH in Python script output. Check logs.');
            }
        } else {
            event.sender.send('processing-error', `Python script failed with code ${code}. Check logs.`);
        }
    });

    pythonProcess.on('error', (err) => {
        console.error('Failed to start Python subprocess.', err);
        
        // Remove process from the map
        if (global.runningProcesses && processId) {
            global.runningProcesses.delete(processId);
        }
        
        let detailedError = `Failed to start Python process: ${err.message}. Ensure Python is installed and in the system PATH accessible by GUI applications.`;
        if (err.code === 'ENOENT') {
            detailedError += ` The command '${pythonExecutable}' was not found. Please verify your Python installation and PATH configuration. On macOS, GUI apps might not inherit your shell's full PATH; consider using 'fix-path' module or providing an absolute path to Python if issues persist.`;
        }
        event.sender.send('processing-error', detailedError);
    });
});

// IPC handler for canceling processing
ipcMain.on('cancel-processing', (event, processId) => {
    console.log(`Request to cancel process with ID: ${processId}`);
    
    if (global.runningProcesses && global.runningProcesses.has(processId)) {
        const process = global.runningProcesses.get(processId);
        
        try {
            // Attempt to kill the process and its children
            if (process.pid) {
                if (process.platform === 'win32') {
                    // On Windows, use taskkill to terminate the process tree
                    spawn('taskkill', ['/pid', process.pid, '/f', '/t']);
                } else {
                    // On Unix-like systems, send SIGTERM to the process group
                    process.kill('SIGTERM');
                    
                    // Also try to kill any child processes by process group
                    // This works better on macOS and Linux
                    try {
                        spawn('pkill', ['-TERM', '-P', process.pid.toString()]);
                    } catch (err) {
                        console.error('Error killing child processes:', err);
                    }
                }
                
                console.log(`Process with ID ${processId} terminated`);
                event.sender.send('processing-log', `Process canceled by user.`);
                global.runningProcesses.delete(processId);
            }
        } catch (error) {
            console.error(`Error terminating process ${processId}:`, error);
            event.sender.send('processing-error', `Failed to cancel process: ${error.message}`);
        }
    } else {
        console.warn(`Process with ID ${processId} not found or already terminated`);
    }
});

// IPC Handlers for API Key Management
ipcMain.handle('save-api-key', async (event, apiKey) => {
    try {
        store.set('geminiApiKey', apiKey);
        console.log('API Key saved successfully.');
        return { success: true };
    } catch (error) {
        console.error('Failed to save API key:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('load-api-key', async () => {
    try {
        const apiKey = store.get('geminiApiKey');
        if (apiKey) {
            console.log('API Key loaded successfully.');
            return apiKey;
        }
        console.log('No API Key found in store.');
        return null;
    } catch (error) {
        console.error('Failed to load API key:', error);
        throw error; // Rethrow to be caught by renderer
    }
});

// IPC handler for deleting output files
ipcMain.on('delete-output-file', async (event, filePath) => {
    const backendDir = path.join(projectRoot, 'backend');
    const mainPyScript = path.join(backendDir, 'main.py');
    
    // Determine the appropriate Python executable
    let pythonExecutable;
    if (isDev && process.platform === 'darwin') {
        pythonExecutable = '/opt/anaconda3/envs/findec_env/bin/python';
        const fs = require('fs');
        if (!fs.existsSync(pythonExecutable)) {
            console.error(`Specified Python path for dev does not exist: ${pythonExecutable}. Falling back to python3.`);
            pythonExecutable = 'python3'; // Fallback
        }
    } else if (process.platform === 'win32') {
        pythonExecutable = 'python';
    } else {
        pythonExecutable = 'python3';
    }
    
    const scriptArgs = [
        '-c',
        `import sys; sys.path.append('${backendDir}'); from main import delete_output_file; delete_output_file('${filePath}')`
    ];
    
    console.log(`Deleting output file: ${filePath}`);
    
    const pythonProcess = spawn(pythonExecutable, scriptArgs, {
        cwd: backendDir,
        env: { ...process.env }
    });
    
    pythonProcess.stdout.on('data', (data) => {
        console.log(`File deletion stdout: ${data.toString()}`);
    });
    
    pythonProcess.stderr.on('data', (data) => {
        console.error(`File deletion stderr: ${data.toString()}`);
    });
    
    pythonProcess.on('close', (code) => {
        console.log(`File deletion process exited with code ${code}`);
        if (code === 0) {
            console.log('Output file deleted successfully');
        } else {
            console.error('Failed to delete output file');
        }
    });
    
    pythonProcess.on('error', (err) => {
        console.error('Failed to start file deletion process:', err);
    });
});

// Cleanup on exit
app.on('will-quit', () => {
    // Run cleanup script to delete any temporary files
    const backendDir = path.join(projectRoot, 'backend');
    
    // Determine Python executable
    let pythonExecutable;
    if (process.platform === 'darwin') {
        pythonExecutable = isDev ? '/opt/anaconda3/envs/findec_env/bin/python' : 'python3';
    } else if (process.platform === 'win32') {
        pythonExecutable = 'python';
    } else {
        pythonExecutable = 'python3';
    }
    
    // Run cleanup only if Python is available
    try {
        const cleanupProcess = spawn(pythonExecutable, [
            '-c',
            `import sys; sys.path.append('${backendDir}'); from main import cleanup_old_outputs; import os; cleanup_old_outputs('${path.join(projectRoot, 'output')}', max_age_days=1, keep_latest=3)`
        ], {
            cwd: backendDir,
            env: { ...process.env },
            detached: false,
            stdio: 'ignore'
        });
        
        cleanupProcess.unref(); // Allow the app to exit even if this process is still running
        console.log('Cleanup process started');
    } catch (err) {
        console.error('Failed to start cleanup process:', err);
    }
});
