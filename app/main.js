const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;

// Determine if the app is packaged
const isDev = process.env.NODE_ENV !== 'production';
const isPackaged = app.isPackaged;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 750,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            nodeIntegration: false,
            devTools: isDev // Enable DevTools only in development
        },
        icon: path.join(__dirname, isPackaged ? '../build/icon.png' : '../build/icon.png') // Adjust path for packaged app
    });

    mainWindow.loadFile(path.join(__dirname, 'index.html'));

    if (isDev) {
        mainWindow.webContents.openDevTools();
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(() => {
    createWindow();

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
ipcMain.on('process-csv', (event, csvPath) => {
    // Adjust base path depending on whether the app is packaged or in development
    const basePath = isPackaged ? path.join(process.resourcesPath, '..') : path.join(app.getAppPath(), '..'); 
    
    const backendDir = path.join(basePath, 'backend');
    const mainPyScript = path.join(backendDir, 'main.py');
    const outputBaseDir = path.join(basePath, 'output');
    const contentDir = path.join(basePath, 'content'); // For predict_pairs.py, model, etc.

    // Determine Python executable path
    // This is a simplified approach. For robust cross-platform packaging,
    // consider bundling a Python runtime or using a more sophisticated path detection.
    let pythonExecutable = 'python3';
    if (process.platform === 'win32') {
        pythonExecutable = 'python'; // Or path to bundled python.exe
    }
    // Example: if you bundle python in a 'python-dist' folder within resources:
    // if (isPackaged && process.platform === 'win32') {
    //    pythonExecutable = path.join(process.resourcesPath, 'python-dist', 'python.exe');
    // } else if (isPackaged && process.platform === 'darwin') {
    //    pythonExecutable = path.join(process.resourcesPath, 'python-dist', 'bin', 'python3');
    // }

    console.log(`Base path for resources: ${basePath}`);
    console.log(`Backend directory: ${backendDir}`);
    console.log(`Content directory: ${contentDir}`);
    console.log(`Python executable: ${pythonExecutable}`);
    console.log(`Spawning Python: ${pythonExecutable} "${mainPyScript}" --input "${csvPath}" --output_dir "${outputBaseDir}"`);

    const pythonProcess = spawn(pythonExecutable, [
        mainPyScript,
        '--input', csvPath,
        '--output_dir', outputBaseDir
    ], {
        cwd: backendDir // Set working directory for python script to backend/
                       // This helps if main.py uses relative paths to other backend modules
                       // and if predict_pairs.py (called by main.py) expects to be run from content/
                       // The cwd for subprocess.run in pair_predictor.py is set to content/
    });

    let fullOutput = "";
    pythonProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(`Python stdout: ${output}`);
        fullOutput += output;
        event.sender.send('processing-log', output);
    });

    pythonProcess.stderr.on('data', (data) => {
        const errorOutput = data.toString();
        console.error(`Python stderr: ${errorOutput}`);
        event.sender.send('processing-log', `ERROR: ${errorOutput}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Python script exited with code ${code}`);
        if (code === 0) {
            const match = fullOutput.match(/JSON_OUTPUT_PATH:(.*)/);
            if (match && match[1]) {
                const jsonPath = match[1].trim();
                event.sender.send('processing-complete', jsonPath);
            } else {
                event.sender.send('processing-error', 'Could not find JSON_OUTPUT_PATH in Python script output. Check logs.');
            }
        } else {
            event.sender.send('processing-error', `Python script failed with code ${code}. Check logs.`);
        }
    });

    pythonProcess.on('error', (err) => {
        console.error('Failed to start Python subprocess.', err);
        event.sender.send('processing-error', `Failed to start Python process: ${err.message}. Ensure Python is installed and in PATH.`);
    });
});
