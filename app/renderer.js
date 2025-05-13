window.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const runBtn = document.getElementById('run-btn');
    const fileNameDisplay = document.getElementById('file-name-display');
    const logsElement = document.getElementById('logs');
    const resultsContainer = document.getElementById('results-container');
    const jsonOutputPathElement = document.getElementById('json-output-path');
    const openOutputBtn = document.getElementById('open-output-btn');

    let selectedFilePath = null;

    // Drag and Drop
    dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        event.stopPropagation();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', (event) => {
        event.preventDefault();
        event.stopPropagation();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (event) => {
        event.preventDefault();
        event.stopPropagation();
        dropZone.classList.remove('dragover');

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.name.endsWith('.csv')) {
                handleFile(file);
            } else {
                alert('Please drop a CSV file.');
            }
        }
    });

    // Browse button
    browseBtn.addEventListener('click', async () => {
        const filePath = await window.electronAPI.openFileDialog();
        if (filePath) {
            selectedFilePath = filePath;
            fileNameDisplay.textContent = `Selected: ${filePath.split(/[\\/]/).pop()}`;
            runBtn.disabled = false;
        }
    });

    // Hidden file input (alternative for browse)
    fileInput.addEventListener('change', (event) => {
        const files = event.target.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    function handleFile(file) {
        selectedFilePath = file.path; // Electron gives full path for dropped/selected files
        fileNameDisplay.textContent = `Selected: ${file.name}`;
        runBtn.disabled = false;
    }

    // Run button
    runBtn.addEventListener('click', () => {
        if (selectedFilePath) {
            logsElement.textContent = ''; // Clear previous logs
            resultsContainer.style.display = 'none';
            jsonOutputPathElement.textContent = '';
            runBtn.disabled = true;
            runBtn.textContent = 'Processing...';
            window.electronAPI.processCsv(selectedFilePath);
        }
    });

    // IPC Listeners
    window.electronAPI.onProcessingLog((log) => {
        logsElement.textContent += log;
        logsElement.scrollTop = logsElement.scrollHeight; // Auto-scroll
    });

    window.electronAPI.onProcessingComplete((outputPath) => {
        logsElement.textContent += '\nProcessing finished successfully!\n';
        resultsContainer.style.display = 'block';
        jsonOutputPathElement.textContent = outputPath;
        openOutputBtn.onclick = () => {
            // To get the directory, we need to strip the filename from the outputPath
            const outputDir = outputPath.substring(0, outputPath.lastIndexOf(process.platform === 'win32' ? '\\' : '/'));
            window.electronAPI.openOutputFolder(outputDir);
        };
        resetRunButton();
    });

    window.electronAPI.onProcessingError((errorMsg) => {
        logsElement.textContent += `\nERROR: ${errorMsg}\n`;
        alert(`An error occurred: ${errorMsg}`);
        resetRunButton();
    });

    function resetRunButton() {
        runBtn.disabled = false;
        runBtn.textContent = 'Process Invoices';
    }

    // Clean up listeners when the window is unloaded (optional, good practice)
    window.addEventListener('beforeunload', () => {
        window.electronAPI.removeAllProcessingListeners();
    });
});
