const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    processCsv: (filePath) => {
        ipcRenderer.send('process-csv', filePath);
        // Return a promise that resolves with the process ID
        return new Promise((resolve) => {
            ipcRenderer.once('process-started', (_event, processId) => {
                resolve(processId);
            });
        });
    },
    cancelProcessing: (processId) => ipcRenderer.send('cancel-processing', processId),
    onProcessingLog: (callback) => ipcRenderer.on('processing-log', (_event, log) => callback(log)),
    onProcessingComplete: (callback) => ipcRenderer.on('processing-complete', (_event, outputPath) => callback(outputPath)),
    onProcessingError: (callback) => ipcRenderer.on('processing-error', (_event, errorMsg) => callback(errorMsg)),
    openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),
    openOutputFolder: (folderPath) => ipcRenderer.send('open-output-folder', folderPath),
    removeAllProcessingListeners: () => {
        ipcRenderer.removeAllListeners('processing-log');
        ipcRenderer.removeAllListeners('processing-complete');
        ipcRenderer.removeAllListeners('processing-error');
    },
    // API Key Management
    saveApiKey: (apiKey) => ipcRenderer.invoke('save-api-key', apiKey),
    loadApiKey: () => ipcRenderer.invoke('load-api-key'),
    // File management
    deleteOutputFile: (filePath) => ipcRenderer.send('delete-output-file', filePath)
});
