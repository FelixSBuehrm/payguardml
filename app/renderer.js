window.addEventListener('DOMContentLoaded', () => {
    // Hide loading indicator after a short delay to ensure UI elements are rendered
    setTimeout(() => {
        const loadingIndicator = document.getElementById('initial-loading');
        if (loadingIndicator) {
            loadingIndicator.classList.add('hidden');
            setTimeout(() => {
                loadingIndicator.style.display = 'none';
            }, 500); // Complete hiding after transition
        }
    }, 300);
    
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const runBtn = document.getElementById('run-btn');
    const fileNameDisplay = document.getElementById('file-name-display');
    const logsElement = document.getElementById('logs');
    const resultsContainer = document.getElementById('results-container');
    const jsonOutputPathElement = document.getElementById('json-output-path');
    const openOutputBtn = document.getElementById('open-output-btn');

    // New progress elements
    const progressSection = document.getElementById('progress-section');
    const statusText = document.getElementById('status-text');
    const progressBar = document.getElementById('progress-bar');
    
    // Cancel button
    const cancelButtonContainer = document.getElementById('cancel-button-container');
    const cancelBtn = document.getElementById('cancel-btn');

    // Settings Modal Elements
    const settingsIconContainer = document.getElementById('settings-icon-container');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsModalBtn = document.getElementById('close-settings-modal');
    const apiKeyInput = document.getElementById('api-key-input');
    const toggleApiKeyVisibilityBtn = document.getElementById('toggle-api-key-visibility');
    const saveApiKeyBtn = document.getElementById('save-api-key-btn');
    const settingsFeedback = document.getElementById('settings-feedback');

    let selectedFilePath = null;
    let isProcessing = false;
    let shouldAutoScroll = true; // Flag to control auto-scrolling
    let pythonProcessId = null; // Store the process ID for cancellation

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

            // Reset and show progress bar
            progressSection.style.display = 'block';
            updateProgress(0, "Initializing...");
            
            // Show cancel button
            cancelButtonContainer.style.display = 'flex';
            
            // Reset processing state
            isProcessing = true;
            shouldAutoScroll = true; // Reset auto-scroll flag

            runBtn.disabled = true;
            runBtn.textContent = 'Processing...';
            pythonProcessId = window.electronAPI.processCsv(selectedFilePath);
        }
    });
    
    // Cancel button
    cancelBtn.addEventListener('click', () => {
        if (isProcessing && pythonProcessId) {
            // Confirm cancellation
            if (confirm('Are you sure you want to cancel processing? This will stop the current analysis.')) {
                window.electronAPI.cancelProcessing(pythonProcessId);
                
                // Update UI to show cancellation
                updateProgress(0, "Processing cancelled by user");
                progressBar.style.backgroundColor = '#e74c3c';
                
                // Re-enable the run button
                resetRunButton();
                
                // Hide cancel button
                cancelButtonContainer.style.display = 'none';
                
                // Add to logs
                const cancelMsg = document.createElement('div');
                cancelMsg.className = 'error-text';
                cancelMsg.textContent = 'Processing cancelled by user';
                logsElement.appendChild(cancelMsg);
                
                isProcessing = false;
            }
        }
    });
    
    // Add scroll event listener to detect manual scrolling
    logsElement.addEventListener('scroll', () => {
        // If the user has scrolled up, disable auto-scroll
        const isScrolledToBottom = logsElement.scrollHeight - logsElement.clientHeight <= logsElement.scrollTop + 5;
        shouldAutoScroll = isScrolledToBottom;
    });

    // IPC Listeners
    window.electronAPI.onProcessingLog((log) => {
        // Add to logs container with formatting based on message type
        const formattedLog = formatLogMessage(log);
        
        // Only add to log container if the formatted log is not empty
        if (formattedLog) {
            // Add the formatted log to the container
            const logLine = document.createElement('div');
            logLine.innerHTML = formattedLog;
            logsElement.appendChild(logLine);
            
            // Only auto-scroll if the user hasn't scrolled up
            if (shouldAutoScroll) {
                logsElement.scrollTop = logsElement.scrollHeight;
            }
        }
        
        // Parse progress messages - improved to handle multi-line logs
        const lines = log.split('\n');
        for (const line of lines) {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith("PROGRESS:")) {
                console.log("Progress event detected:", trimmedLine);
                handleProgressMessage(trimmedLine);
            }
        }
    });

    window.electronAPI.onProcessingComplete((outputData) => {
        logsElement.textContent += '\nAnalysis finished successfully!\n';
        updateProgress(100, "Analysis complete!");
        
        // Reset processing state
        isProcessing = false;
        
        // Hide cancel button
        cancelButtonContainer.style.display = 'none';
        
        // Display JSON viewer instead of file path
        const outputPath = outputData.filePath;
        const jsonContent = outputData.jsonContent;
        
        // Create JSON viewer
        resultsContainer.style.display = 'block';
        
        // Replace file path with JSON viewer
        jsonOutputPathElement.innerHTML = '';
        
        // Create JSON viewer container
        const jsonViewerContainer = document.createElement('div');
        jsonViewerContainer.id = 'json-viewer';
        jsonViewerContainer.className = 'json-viewer';
        
        // Format the JSON for display
        const formattedJson = formatJsonForDisplay(jsonContent);
        jsonViewerContainer.innerHTML = formattedJson;
        
        // Add JSON viewer to output path element
        jsonOutputPathElement.appendChild(jsonViewerContainer);
        
        // Enhance PayGuard link with context
        enhancePayGuardLink(jsonContent);
        
        // Change open output button to download button
        openOutputBtn.textContent = 'Download JSON';
        openOutputBtn.onclick = () => {
            downloadJson(jsonContent, getFileNameFromPath(outputPath));
            // Notify backend to delete the file after download
            window.electronAPI.deleteOutputFile(outputPath);
        };
        
        resetRunButton();
    });

    window.electronAPI.onProcessingError((errorMsg) => {
        logsElement.textContent += `\nERROR: ${errorMsg}\n`;
        alert(`An error occurred: ${errorMsg}`);
        resetRunButton();
        progressSection.style.display = 'none'; // Hide progress on error
        
        // Reset processing state
        isProcessing = false;
        
        // Hide cancel button
        cancelButtonContainer.style.display = 'none';
    });

    function updateProgress(percentage, text) {
        // Update the progress bar width and text
        progressBar.style.width = `${percentage}%`;
        progressBar.textContent = `${percentage}%`;
        statusText.textContent = text;
        
        // Add progress info to logs with highlighting - simplified for better user experience
        const progressInfo = text;
        logsElement.innerHTML += `<div class="progress-highlight">${progressInfo}</div>`;
        logsElement.scrollTop = logsElement.scrollHeight;
        
        // Change color when complete
        if (percentage === 100) {
            progressBar.style.backgroundColor = '#2ecc71'; // Green
        }
    }

    function handleProgressMessage(message) {
        console.log("Processing progress message:", message);
        const parts = message.split(':');
        const progressType = parts[1];

        switch (progressType) {
            case "OVERALL_START":
                updateProgress(0, "Starting invoice analysis...");
                // Add initial section header to logs
                const initialHeader = document.createElement('div');
                initialHeader.className = 'log-section-header phase-data-prep';
                initialHeader.textContent = "DATA PREPARATION";
                logsElement.appendChild(initialHeader);
                logsElement.scrollTop = logsElement.scrollHeight;
                break;
            case "SBERT_START":
                updateProgress(5, "Starting similarity analysis...");
                // Add similarity analysis section header
                const sbertHeader = document.createElement('div');
                sbertHeader.className = 'log-section-header phase-analysis';
                sbertHeader.textContent = "SIMILARITY ANALYSIS";
                logsElement.appendChild(sbertHeader);
                logsElement.scrollTop = logsElement.scrollHeight;
                break;
            case "SBERT_PROGRESS":
                if (parts.length >= 4) {
                    const current = parseInt(parts[2], 10);
                    const total = parseInt(parts[3], 10);
                    // SBERT is 5-30% (25% range)
                    const sbertProgress = total > 0 ? (current / total) * 25 : 0;
                    const overallProgress = 5 + sbertProgress;
                    updateProgress(Math.round(overallProgress), 
                        `Comparing ${current} of ${total} invoice pairs...`);
                }
                break;
            case "SBERT_END":
                updateProgress(30, "Initial comparison complete. Starting detailed analysis...");
                break;
            case "LLM_CLASSIFICATION_START": // Overall LLM step start
                updateProgress(35, "Preparing detailed invoice analysis...");
                // Add classification section header
                const llmHeader = document.createElement('div');
                llmHeader.className = 'log-section-header phase-classification';
                llmHeader.textContent = "LLM CLASSIFICATION";
                logsElement.appendChild(llmHeader);
                logsElement.scrollTop = logsElement.scrollHeight;
                break;
            case "LLM_TOTAL_ITEMS":
                if (parts.length >= 3) {
                    const totalItems = parseInt(parts[2], 10);
                    // Store total items for later percentage calculations
                    window.llmTotalItems = totalItems;
                    updateProgress(35, `Preparing to examine ${totalItems} potential matches...`);
                }
                break;
            case "LLM_BATCH_START":
                if (parts.length >= 6) {
                    const currentBatch = parseInt(parts[2], 10);
                    const totalBatches = parseInt(parts[3], 10);
                    const startItem = parseInt(parts[4], 10);
                    const endItem = parseInt(parts[5], 10);
                    const totalItems = parseInt(parts[6], 10);
                    
                    // Calculate progress: LLM part is 35% to 90% (55% range)
                    const batchProgress = totalBatches > 0 ? ((currentBatch - 1) / totalBatches) * 55 : 0;
                    const overallProgress = 35 + batchProgress;
                    
                    console.log(`LLM Batch progress: ${currentBatch}/${totalBatches}, items ${startItem}-${endItem}/${totalItems}, overall: ${Math.round(overallProgress)}%`);
                    updateProgress(Math.round(overallProgress), 
                        `Processing batch ${currentBatch} of ${totalBatches}...`);
                    
                    // Create or update batch progress element
                    updateBatchProgress(currentBatch, totalBatches, startItem, endItem, totalItems);
                } else if (parts.length >= 4) {
                    // Fallback to the old format for backward compatibility
                    const currentBatch = parseInt(parts[2], 10);
                    const totalBatches = parseInt(parts[3], 10);
                    
                    // Calculate progress: LLM part is 35% to 90% (55% range)
                    const batchProgress = totalBatches > 0 ? ((currentBatch - 1) / totalBatches) * 55 : 0;
                    const overallProgress = 35 + batchProgress;
                    
                    console.log(`LLM Batch progress: ${currentBatch}/${totalBatches}, overall: ${Math.round(overallProgress)}%`);
                    updateProgress(Math.round(overallProgress), `Analyzing batch ${currentBatch} of ${totalBatches}...`);
                }
                break;
            case "LLM_ITEM_START":
                if (parts.length >= 4) {
                    const currentItem = parseInt(parts[2], 10);
                    const totalItems = parseInt(parts[3], 10);
                    
                    // Update item progress indicator
                    updateItemProgress(currentItem, totalItems, "processing");
                }
                break;
            case "LLM_ITEM_END":
                if (parts.length >= 5) {
                    const currentItem = parseInt(parts[2], 10);
                    const totalItems = parseInt(parts[3], 10);
                    const classification = parts[4];
                    
                    // Calculate progress: LLM part is 35% to 90% (55% range)
                    // Each item contributes to the progress
                    const itemProgress = totalItems > 0 ? (currentItem / totalItems) * 55 : 0;
                    const overallProgress = 35 + itemProgress;
                    
                    // Only update overall progress on item completion if we're not showing batch progress
                    if (!document.getElementById('batch-progress-container')) {
                        updateProgress(Math.round(overallProgress), 
                            `Completed item ${currentItem}/${totalItems} (${classification})`);
                    }
                    
                    // Update item progress indicator with result
                    updateItemProgress(currentItem, totalItems, "complete", classification);
                }
                break;
            case "LLM_ITEM_ERROR":
                if (parts.length >= 4) {
                    const currentItem = parseInt(parts[2], 10);
                    const totalItems = parseInt(parts[3], 10);
                    
                    // Update item progress indicator with error
                    updateItemProgress(currentItem, totalItems, "error");
                }
                break;
            case "LLM_BATCH_END":
                if (parts.length >= 5) {
                    const currentBatch = parseInt(parts[2], 10);
                    const totalBatches = parseInt(parts[3], 10);
                    const elapsedTime = parseFloat(parts[4]);
                    
                    // Calculate progress: LLM part is 35% to 90% (55% range)
                    const batchProgress = totalBatches > 0 ? (currentBatch / totalBatches) * 55 : 0;
                    const overallProgress = 35 + batchProgress;
                    
                    console.log(`LLM Batch completed: ${currentBatch}/${totalBatches}, time: ${elapsedTime}s, overall: ${Math.round(overallProgress)}%`);
                    updateProgress(Math.round(overallProgress), 
                        `Completed batch ${currentBatch} of ${totalBatches} in ${elapsedTime.toFixed(1)}s`);
                    
                    // Update batch progress
                    updateBatchProgressCompletion(currentBatch, totalBatches);
                } else if (parts.length >= 4) {
                    // Fallback to old format
                    const currentBatch = parseInt(parts[2], 10);
                    const totalBatches = parseInt(parts[3], 10);
                    
                    // Calculate progress: LLM part is 35% to 90% (55% range)
                    const batchProgress = totalBatches > 0 ? (currentBatch / totalBatches) * 55 : 0;
                    const overallProgress = 35 + batchProgress;
                    
                    console.log(`LLM Batch completed: ${currentBatch}/${totalBatches}, overall: ${Math.round(overallProgress)}%`);
                    updateProgress(Math.round(overallProgress), `Completed batch ${currentBatch} of ${totalBatches}`);
                }
                break;
            case "LLM_CLASSIFICATION_END": // Overall LLM step end
                updateProgress(90, "Analysis complete.");
                break;
            case "LLM_END": // This is from llm_classifier.py
                try {
                    if (parts.length >= 3) {
                        const resultStats = JSON.parse(parts[2]);
                        const statsString = Object.entries(resultStats)
                            .map(([key, value]) => `${key}: ${value}`)
                            .join(', ');
                        updateProgress(90, `Analysis finished. Results: ${statsString}`);
                    } else {
                        updateProgress(90, "Analysis finished.");
                    }
                } catch (e) {
                    console.error("Error parsing LLM results:", e);
                    updateProgress(90, "Analysis finished.");
                }
                // Clear any item progress indicators
                const itemProgressContainer = document.getElementById('item-progress-container');
                if (itemProgressContainer) {
                    itemProgressContainer.remove();
                }
                // Clear any batch progress indicators
                const batchProgressContainer = document.getElementById('batch-progress-container');
                if (batchProgressContainer) {
                    batchProgressContainer.remove();
                }
                break;
            case "FORMATTING_START":
                updateProgress(92, "Preparing final results...");
                // Add results section header
                const resultsHeader = document.createElement('div');
                resultsHeader.className = 'log-section-header phase-results';
                resultsHeader.textContent = "RESULTS PREPARATION";
                logsElement.appendChild(resultsHeader);
                logsElement.scrollTop = logsElement.scrollHeight;
                break;
            case "OVERALL_END":
                updateProgress(100, "Process completed!");
                break;
            default:
                console.log("Unknown progress type:", progressType);
                break;
        }
    }

    function resetRunButton() {
        runBtn.disabled = false;
        runBtn.textContent = 'Process Invoices';
        // Optionally hide progress bar again, or leave it at 100% / error state
        // progressSection.style.display = 'none'; 
        progressBar.style.backgroundColor = '#3498db'; // Reset color if changed
        
        // Reset processing state
        isProcessing = false;
        
        // Hide cancel button
        cancelButtonContainer.style.display = 'none';
    }

    // Format log messages based on message type with enhanced API call tracking
    function formatLogMessage(log) {
        // Filter out file paths and machine-specific details
        let cleanedLog = log;
        
        // Filter out absolute paths
        cleanedLog = cleanedLog.replace(/\/[^\s]+\/[^\s\/]+\.(?:csv|py|txt)/g, 'input file');
        
        // Filter out timestamps in square brackets
        cleanedLog = cleanedLog.replace(/\[\d{2}:\d{2}:\d{2}\]/g, '');
        
        // Filter out specific command lines
        if (cleanedLog.includes('Running SBERT prediction command:')) {
            return ''; // Skip verbose command logs
        }
        
        // Skip technical output logs
        if (cleanedLog.includes('[DEBUG]')) {
            // Only show user-relevant debug information
            if (cleanedLog.includes('Total possible pairs') || 
                cleanedLog.includes('After') || 
                cleanedLog.includes('candidate pairs')) {
                cleanedLog = cleanedLog.replace('[DEBUG] SBERT script stdout:', '').trim();
            } else {
                return ''; // Skip other debug logs
            }
        }
        
        // Create section headers for key process steps
        if (cleanedLog.includes('Step 1:')) {
            return `<div class="log-section-header">DATA PREPARATION</div>`;
        } else if (cleanedLog.includes('Step 2:')) {
            return `<div class="log-section-header">SIMILARITY ANALYSIS</div>`;
        } else if (cleanedLog.includes('Step 3:')) {
            return `<div class="log-section-header">LLM CLASSIFICATION</div>`;
        } else if (cleanedLog.includes('Step 4:')) {
            return `<div class="log-section-header">RESULTS PREPARATION</div>`;
        }
        
        // Format the remaining logs based on type
        if (cleanedLog.includes('[ERROR]')) {
            return `<span class="error-text">${cleanedLog}</span>`;
        } else if (cleanedLog.includes('[WARNING]')) {
            return `<span class="warning-text">${cleanedLog}</span>`;
        } else if (cleanedLog.includes('[INFO]')) {
            // Special formatting for API calls and responses
            if (cleanedLog.includes('Calling Gemini API')) {
                return ''; // Hide API call logs from user view
            } else if (cleanedLog.includes('Received Gemini API response')) {
                return ''; // Hide API response logs from user view
            } else if (cleanedLog.includes('Classified as')) {
                // Highlight classification results with color coding
                let classText = cleanedLog;
                if (cleanedLog.includes("'Not likely'")) {
                    classText = cleanedLog.replace(/'Not likely'/g, '<span class="classification-result not-likely-result">\'Not likely\'</span>');
                } else if (cleanedLog.includes("'Very likely'")) {
                    classText = cleanedLog.replace(/'Very likely'/g, '<span class="classification-result very-likely-result">\'Very likely\'</span>');
                } else if (cleanedLog.includes("'Likely'")) {
                    classText = cleanedLog.replace(/'Likely'/g, '<span class="classification-result likely-result">\'Likely\'</span>');
                }
                return `<span class="info-text">${classText}</span>`;
            } else if (cleanedLog.includes('Processing file:')) {
                return `<span class="info-text">Started processing input file</span>`;
            } else if (cleanedLog.includes('Output will be saved in:')) {
                return ''; // Hide output directory info from user
            } else if (cleanedLog.includes('Running SBERT')) {
                return `<span class="info-text">Running similarity analysis...</span>`;
            } else if (cleanedLog.includes('SBERT processing took')) {
                return `<span class="success-text">✓ Similarity analysis completed in ${cleanedLog.match(/\d+\.\d+/)[0]} seconds</span>`;
            } else if (cleanedLog.includes('Loading data from')) {
                return `<span class="info-text">Loading invoice data...</span>`;
            } else if (cleanedLog.includes('Processing')) {
                if (cleanedLog.includes('invoices')) {
                    return `<span class="info-text">Processing ${cleanedLog.match(/\d+/)[0]} invoices</span>`;
                }
            } else if (cleanedLog.includes('Generating candidate pairs')) {
                return `<span class="info-text">Identifying potential duplicate pairs...</span>`;
            } else if (cleanedLog.includes('Total possible pairs')) {
                return `<span class="info-text">Total possible pairs: ${cleanedLog.match(/\d+/)[0]}</span>`;
            } else if (cleanedLog.includes('Blocking by')) {
                return `<span class="info-text">Filtering by ${cleanedLog.match(/Blocking by ([^\.]+)/)[1]}</span>`;
            } else if (cleanedLog.includes('After')) {
                const match = cleanedLog.match(/After ([^:]+): (\d+)/);
                if (match) {
                    return `<span class="info-text">After filtering by ${match[1]}: ${match[2]} pairs</span>`;
                }
                return `<span class="info-text">${cleanedLog}</span>`;
            } else {
                return `<span class="info-text">${cleanedLog}</span>`;
            }
        } else if (cleanedLog.includes('[PROGRESS]')) {
            return `<span class="progress-highlight">${cleanedLog}</span>`;
        } else if (cleanedLog.startsWith('PROGRESS:')) {
            // Hide raw progress markers from the logs
            return '';
        } else {
            return cleanedLog;
        }
    }

    // Function to create or update the item progress indicators
    function updateItemProgress(currentItem, totalItems, status, classification = null) {
        // Get or create the item progress container
        let itemProgressContainer = document.getElementById('item-progress-container');
        if (!itemProgressContainer) {
            itemProgressContainer = document.createElement('div');
            itemProgressContainer.id = 'item-progress-container';
            itemProgressContainer.className = 'item-progress-container';
            
            // Add a header
            const header = document.createElement('div');
            header.className = 'item-progress-header';
            header.textContent = 'Processing progress:';
            itemProgressContainer.appendChild(header);
            
            // Create the items container
            const itemsContainer = document.createElement('div');
            itemsContainer.id = 'items-container';
            itemsContainer.className = 'items-container';
            itemProgressContainer.appendChild(itemsContainer);
            
            // Insert after progress bar container
            const progressSection = document.getElementById('progress-section');
            progressSection.appendChild(itemProgressContainer);
        }
        
        // Get or create the items container
        const itemsContainer = document.getElementById('items-container');
        
        // Get or create the specific item indicator
        let itemIndicator = document.getElementById(`item-${currentItem}`);
        if (!itemIndicator) {
            itemIndicator = document.createElement('div');
            itemIndicator.id = `item-${currentItem}`;
            itemIndicator.className = 'item-indicator';
            itemIndicator.dataset.item = currentItem;
            
            // Only show up to 50 individual items, then summarize
            if (totalItems <= 50 || currentItem % Math.ceil(totalItems / 50) === 0 || currentItem === totalItems) {
                itemsContainer.appendChild(itemIndicator);
            }
        }
        
        // Update the indicator based on status
        if (status === "processing") {
            itemIndicator.className = 'item-indicator item-processing';
            itemIndicator.title = `Processing item ${currentItem}/${totalItems}`;
        } else if (status === "complete") {
            itemIndicator.className = 'item-indicator item-complete';
            // Add a class based on classification
            if (classification) {
                if (classification.toLowerCase().includes('not likely')) {
                    itemIndicator.className += ' classification-not-likely';
                } else if (classification.toLowerCase().includes('likely')) {
                    if (classification.toLowerCase().includes('very')) {
                        itemIndicator.className += ' classification-very-likely';
                    } else {
                        itemIndicator.className += ' classification-likely';
                    }
                }
            }
            itemIndicator.title = `Item ${currentItem}/${totalItems}: ${classification || 'Completed'}`;
        } else if (status === "error") {
            itemIndicator.className = 'item-indicator item-error';
            itemIndicator.title = `Error processing item ${currentItem}/${totalItems}`;
        }
    }
    
    // Function to create or update batch progress
    function updateBatchProgress(currentBatch, totalBatches, startItem, endItem, totalItems) {
        // Get or create the batch progress container
        let batchProgressContainer = document.getElementById('batch-progress-container');
        if (!batchProgressContainer) {
            batchProgressContainer = document.createElement('div');
            batchProgressContainer.id = 'batch-progress-container';
            batchProgressContainer.className = 'batch-progress-container';
            
            // Add a header
            const header = document.createElement('div');
            header.className = 'batch-progress-header';
            header.textContent = 'Batch processing progress:';
            batchProgressContainer.appendChild(header);
            
            // Create the batches container
            const batchesContainer = document.createElement('div');
            batchesContainer.id = 'batches-container';
            batchesContainer.className = 'batches-container';
            batchProgressContainer.appendChild(batchesContainer);
            
            // Insert after progress bar container but before item progress
            const progressSection = document.getElementById('progress-section');
            const itemProgressContainer = document.getElementById('item-progress-container');
            if (itemProgressContainer) {
                progressSection.insertBefore(batchProgressContainer, itemProgressContainer);
            } else {
                progressSection.appendChild(batchProgressContainer);
            }
        }
        
        // Get the batches container
        const batchesContainer = document.getElementById('batches-container');
        
        // Create/update all batch indicators at once for better visualization
        for (let i = 1; i <= totalBatches; i++) {
            // Get or create batch indicator
            let batchIndicator = document.getElementById(`batch-${i}`);
            if (!batchIndicator) {
                batchIndicator = document.createElement('div');
                batchIndicator.id = `batch-${i}`;
                batchIndicator.className = i < currentBatch ? 'batch-indicator batch-complete' : 
                                          (i === currentBatch ? 'batch-indicator batch-current' : 
                                           'batch-indicator batch-pending');
                batchIndicator.title = `Batch ${i}/${totalBatches}`;
                batchesContainer.appendChild(batchIndicator);
            }
            
            // Update current batch with more details
            if (i === currentBatch) {
                batchIndicator.className = 'batch-indicator batch-current';
                batchIndicator.title = `Current batch: ${i}/${totalBatches} (items ${startItem}-${endItem} of ${totalItems})`;
            }
        }
    }
    
    // Function to update batch completion
    function updateBatchProgressCompletion(currentBatch, totalBatches) {
        const batchIndicator = document.getElementById(`batch-${currentBatch}`);
        if (batchIndicator) {
            batchIndicator.className = 'batch-indicator batch-complete';
            batchIndicator.title = `Completed batch ${currentBatch}/${totalBatches}`;
        }
    }

    // Format JSON for display in the viewer
    function formatJsonForDisplay(jsonObj) {
        try {
            // Prepare a summary view for better readability
            // Extract essential information for display
            let summary = {
                projectInfo: {
                    id: jsonObj.project_id,
                    name: jsonObj.project_name,
                    description: jsonObj.project_description,
                    created: jsonObj.created_at
                },
                statistics: {
                    totalPairs: jsonObj.invoice_pairs.length,
                    classifications: countClassifications(jsonObj.invoice_pairs)
                },
                sampleResults: jsonObj.invoice_pairs.slice(0, 5) // Show first 5 pairs
            };

            // Create a more readable presentation
            let html = `
                <div class="json-summary">
                    <h3>Project Information</h3>
                    <table class="json-table">
                        <tr><td>Name:</td><td>${summary.projectInfo.name}</td></tr>
                        <tr><td>Created:</td><td>${summary.projectInfo.created}</td></tr>
                        <tr><td>Description:</td><td>${summary.projectInfo.description}</td></tr>
                    </table>
                    
                    <h3>Analysis Results</h3>
                    <div class="classification-summary">
                        <p>Total pairs analyzed: <strong>${summary.statistics.totalPairs}</strong></p>
                        <div class="classification-bars">
                            ${createClassificationBars(summary.statistics.classifications)}
                        </div>
                    </div>
                    
                    <h3>Sample Results (first 5 pairs)</h3>
                    <div class="sample-results">
                        ${createSampleResults(summary.sampleResults)}
                    </div>
                    
                    <div class="view-full-json">
                        <button id="toggle-full-json" class="view-json-btn">View Full JSON</button>
                    </div>
                    
                    <div id="full-json-container" style="display: none;" class="full-json">
                        <pre>${syntaxHighlightJson(JSON.stringify(jsonObj, null, 2))}</pre>
                    </div>
                </div>
            `;
            
            // Add event listener for the toggle button after a small delay
            setTimeout(() => {
                const toggleButton = document.getElementById('toggle-full-json');
                if (toggleButton) {
                    toggleButton.addEventListener('click', function() {
                        const container = document.getElementById('full-json-container');
                        if (container.style.display === 'none') {
                            container.style.display = 'block';
                            this.textContent = 'Hide Full JSON';
                        } else {
                            container.style.display = 'none';
                            this.textContent = 'View Full JSON';
                        }
                    });
                }
            }, 100);
            
            return html;
        } catch (error) {
            console.error('Error formatting JSON:', error);
            // Fallback to simple JSON display if there's an error
            return `<pre>${syntaxHighlightJson(JSON.stringify(jsonObj, null, 2))}</pre>`;
        }
    }
    
    // Count classifications from invoice pairs
    function countClassifications(pairs) {
        const counts = {
            'Not likely': 0,
            'Likely': 0,
            'Very likely': 0,
            'Other': 0
        };
        
        pairs.forEach(pair => {
            const classification = pair.llm_classification || 'Other';
            if (counts[classification] !== undefined) {
                counts[classification]++;
            } else {
                counts['Other']++;
            }
        });
        
        return counts;
    }
    
    // Create visual bars for classification distribution
    function createClassificationBars(classifications) {
        const total = Object.values(classifications).reduce((a, b) => a + b, 0);
        if (total === 0) return '<p>No classification data available</p>';
        
        let html = '';
        const colors = {
            'Not likely': '#2ecc71',
            'Likely': '#f39c12',
            'Very likely': '#e74c3c',
            'Other': '#95a5a6'
        };
        
        Object.keys(classifications).forEach(key => {
            if (classifications[key] > 0) {
                const percentage = ((classifications[key] / total) * 100).toFixed(1);
                html += `
                    <div class="classification-bar-container">
                        <div class="classification-label">${key}: ${classifications[key]} (${percentage}%)</div>
                        <div class="classification-bar">
                            <div class="bar-fill" style="width: ${percentage}%; background-color: ${colors[key] || '#95a5a6'}"></div>
                        </div>
                    </div>
                `;
            }
        });
        
        return html;
    }
    
    // Create sample results display
    function createSampleResults(samples) {
        if (!samples || samples.length === 0) {
            return '<p>No sample data available</p>';
        }
        
        let html = '<div class="samples-container">';
        
        samples.forEach((pair, index) => {
            const classColor = pair.llm_classification === 'Not likely' ? '#2ecc71' : 
                              (pair.llm_classification === 'Likely' ? '#f39c12' : 
                              (pair.llm_classification === 'Very likely' ? '#e74c3c' : '#95a5a6'));
            
            html += `
                <div class="sample-pair">
                    <div class="sample-header">
                        <span class="sample-number">Pair ${index + 1}</span>
                        <span class="sample-classification" style="background-color: ${classColor}">
                            ${pair.llm_classification || 'Unknown'}
                        </span>
                        <span class="sample-similarity">Similarity: ${(pair.similarity * 100).toFixed(1)}%</span>
                    </div>
                    <div class="sample-content">
                        <div class="invoice-pair">
                            <div class="invoice">
                                <h4>Invoice 1</h4>
                                <p><strong>Doc:</strong> ${pair.invoice1.doc_no || 'N/A'}</p>
                                <p><strong>Vendor:</strong> ${pair.invoice1.vendor_name || 'N/A'}</p>
                                <p><strong>Amount:</strong> ${pair.invoice1.amount || 'N/A'} ${pair.invoice1.currency || ''}</p>
                                <p><strong>Date:</strong> ${pair.invoice1.invoice_date || 'N/A'}</p>
                            </div>
                            <div class="invoice">
                                <h4>Invoice 2</h4>
                                <p><strong>Doc:</strong> ${pair.invoice2.doc_no || 'N/A'}</p>
                                <p><strong>Vendor:</strong> ${pair.invoice2.vendor_name || 'N/A'}</p>
                                <p><strong>Amount:</strong> ${pair.invoice2.amount || 'N/A'} ${pair.invoice2.currency || ''}</p>
                                <p><strong>Date:</strong> ${pair.invoice2.invoice_date || 'N/A'}</p>
                            </div>
                        </div>
                        <div class="explanation">
                            <p><strong>Explanation:</strong> ${pair.llm_explanation || 'No explanation provided'}</p>
                            <p><strong>Key Factors:</strong> ${formatKeyFactors(pair.llm_key_factors)}</p>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }
    
    // Format key factors as a list
    function formatKeyFactors(factors) {
        if (!factors || factors.length === 0) {
            return 'None';
        }
        
        return factors.join(', ');
    }
    
    // Syntax highlighting for JSON
    function syntaxHighlightJson(json) {
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function(match) {
            let cls = 'json-number';
            if (/^"/.test(match)) {
                if (/:$/.test(match)) {
                    cls = 'json-key';
                } else {
                    cls = 'json-string';
                }
            } else if (/true|false/.test(match)) {
                cls = 'json-boolean';
            } else if (/null/.test(match)) {
                cls = 'json-null';
            }
            return '<span class="' + cls + '">' + match + '</span>';
        });
    }
    
    // Download JSON as a file
    function downloadJson(jsonObj, filename) {
        try {
            // Create a blob from the JSON data
            const jsonString = JSON.stringify(jsonObj, null, 2);
            const blob = new Blob([jsonString], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            
            // Create a download link and trigger it
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", url);
            downloadAnchorNode.setAttribute("download", filename || "analysis_results.json");
            document.body.appendChild(downloadAnchorNode); // Required for Firefox
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
            
            // Clean up the URL object after download
            setTimeout(() => {
                URL.revokeObjectURL(url);
            }, 100);
            
            // Show a success message
            logsElement.innerHTML += `<div class="info-text">[${new Date().toLocaleTimeString()}] [INFO] File downloaded successfully: ${filename}</div>`;
            logsElement.scrollTop = logsElement.scrollHeight;
            
            // Show the upload section with animation
            showUploadSection();
            
            return true;
        } catch (error) {
            console.error('Error downloading JSON:', error);
            logsElement.innerHTML += `<div class="error-text">[${new Date().toLocaleTimeString()}] [ERROR] Download failed: ${error.message}</div>`;
            logsElement.scrollTop = logsElement.scrollHeight;
            return false;
        }
    }
    
    // Function to show the upload section with animation
    function showUploadSection() {
        const uploadSection = document.getElementById('upload-section');
        if (uploadSection) {
            uploadSection.style.display = 'block';
            
            // Force a reflow before adding the class
            void uploadSection.offsetWidth;
            
            uploadSection.classList.add('fade-in');
            
            // Scroll to make the upload section visible
            setTimeout(() => {
                uploadSection.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }, 300);
        }
    }
    
    // Get filename from path
    function getFileNameFromPath(path) {
        if (!path) return "analysis_results.json";
        return path.split(/[\\/]/).pop() || "analysis_results.json";
    }

    // Function to enhance the PayGuard link with context from the results
    function enhancePayGuardLink(jsonContent) {
        const payguardLink = document.getElementById('payguard-link');
        if (!payguardLink || !jsonContent) return;
        
        // Count the number of "Likely" and "Very likely" duplicate pairs
        let likelyCount = 0;
        let veryLikelyCount = 0;
        
        if (jsonContent.invoice_pairs && Array.isArray(jsonContent.invoice_pairs)) {
            jsonContent.invoice_pairs.forEach(pair => {
                if (pair.llm_classification === 'Likely') {
                    likelyCount++;
                } else if (pair.llm_classification === 'Very likely') {
                    veryLikelyCount++;
                }
            });
        }
        
        const totalSuspicious = likelyCount + veryLikelyCount;
        
        // Update the link text based on the results
        if (totalSuspicious > 0) {
            // Create result badge
            const resultBadge = document.createElement('div');
            resultBadge.className = 'result-badge';
            resultBadge.innerHTML = `<span class="badge-count">${totalSuspicious}</span> potential duplicates found!`;
            
            // Add badge before the link
            const uploadCard = document.querySelector('.upload-card');
            if (uploadCard) {
                uploadCard.insertBefore(resultBadge, payguardLink);
            }
            
            // Update link text
            payguardLink.innerHTML = `Review Duplicates in PayGuard Web App
                <svg class="external-link-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M15 3h6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M10 14L21 3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>`;
        }
    }

    // Clean up listeners when the window is unloaded (optional, good practice)
    window.addEventListener('beforeunload', () => {
        window.electronAPI.removeAllProcessingListeners();
    });

    // Settings Modal Logic
    if (settingsIconContainer) {
        settingsIconContainer.addEventListener('click', async () => {
            settingsModal.style.display = 'flex'; // Use flex to center content
            settingsFeedback.textContent = ''; // Clear previous feedback
            try {
                const apiKey = await window.electronAPI.loadApiKey();
                if (apiKey) {
                    apiKeyInput.value = apiKey;
                } else {
                    apiKeyInput.value = '';
                }
            } catch (error) {
                console.error('Error loading API key:', error);
                settingsFeedback.textContent = 'Error loading API key.';
                settingsFeedback.style.color = 'red';
            }
        });
    }

    if (closeSettingsModalBtn) {
        closeSettingsModalBtn.addEventListener('click', () => {
            settingsModal.style.display = 'none';
        });
    }

    // Close modal if user clicks outside of the modal content
    window.addEventListener('click', (event) => {
        if (event.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });

    if (toggleApiKeyVisibilityBtn) {
        toggleApiKeyVisibilityBtn.addEventListener('click', () => {
            if (apiKeyInput.type === 'password') {
                apiKeyInput.type = 'text';
                toggleApiKeyVisibilityBtn.textContent = 'Hide';
            } else {
                apiKeyInput.type = 'password';
                toggleApiKeyVisibilityBtn.textContent = 'Show';
            }
        });
    }

    if (saveApiKeyBtn) {
        saveApiKeyBtn.addEventListener('click', async () => {
            const apiKey = apiKeyInput.value.trim();
            if (!apiKey) {
                settingsFeedback.textContent = 'API Key cannot be empty.';
                settingsFeedback.style.color = 'red';
                return;
            }
            try {
                await window.electronAPI.saveApiKey(apiKey);
                settingsFeedback.textContent = 'API Key saved successfully!';
                settingsFeedback.style.color = 'green';
                setTimeout(() => {
                    settingsModal.style.display = 'none';
                }, 1500); // Close modal after a short delay
            } catch (error) {
                console.error('Error saving API key:', error);
                settingsFeedback.textContent = 'Error saving API key.';
                settingsFeedback.style.color = 'red';
            }
        });
    }

    // Add event listener to the PayGuard link when it appears
    document.addEventListener('click', (event) => {
        if (event.target.closest('#payguard-link')) {
            // Prevent the default behavior of the link
            event.preventDefault();
            
            // Get the URL from the link
            const url = event.target.closest('#payguard-link').getAttribute('href');
            
            // Log the click for analytics
            console.log('User clicked on PayGuard web app link');
            logsElement.innerHTML += `<div class="info-text">[${new Date().toLocaleTimeString()}] [INFO] Opening PayGuard web interface in browser...</div>`;
            logsElement.scrollTop = logsElement.scrollHeight;
            
            // Open the URL in the default external browser
            window.electronAPI.openExternalLink(url);
            
            // Show a small tooltip confirmation
            const tooltip = document.createElement('div');
            tooltip.className = 'success-tooltip';
            tooltip.textContent = 'Opening PayGuard in browser!';
            document.body.appendChild(tooltip);
            
            // Remove tooltip after animation
            setTimeout(() => {
                tooltip.classList.add('fade-out');
                setTimeout(() => {
                    tooltip.remove();
                }, 500);
            }, 2000);
        }
    });
});
