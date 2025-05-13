#!/usr/bin/env python3
"""
Predict script to monitor progress of the content/predict_pairs.py script
and send progress updates to the UI.
"""
import os
import sys
import time
import threading
import subprocess
from datetime import datetime

def log_message(message, message_type="INFO"):
    """Log a message with timestamp and type."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] [{message_type}] {message}"
    
    print(formatted_message, flush=True)
    if message_type == "ERROR":
        print(formatted_message, file=sys.stderr, flush=True)
    
    if message_type == "PROGRESS":
        print(f"PROGRESS:{message}", flush=True)

def monitor_sbert_progress(filepath, interval=1.0):
    """
    Monitor the SBERT process by checking the output file and log files.
    Send progress updates to the UI.
    """
    start_time = time.time()
    log_message(f"Starting progress monitor for SBERT process", "INFO")
    
    # This is a placeholder for monitoring - in a real implementation, 
    # you would parse log files or use IPC to get actual progress.
    progress_markers = [10, 25, 50, 75, 90, 100]
    for progress in progress_markers:
        time.sleep(interval)  # Simulate work being done
        log_message(f"SBERT_PROGRESS:{progress}:100", "PROGRESS")
        
    log_message(f"SBERT processing monitor completed in {time.time() - start_time:.2f} seconds", "INFO")

if __name__ == "__main__":
    # This script would be called as a wrapper around the main process
    command = sys.argv[1:]
    
    if not command:
        log_message("No command provided to execute", "ERROR")
        sys.exit(1)
        
    log_message(f"Executing command: {' '.join(command)}", "INFO")
    
    # Start the progress monitor in a separate thread
    progress_thread = threading.Thread(
        target=monitor_sbert_progress, 
        args=("output.csv", 2.0)
    )
    progress_thread.daemon = True
    progress_thread.start()
    
    # Execute the actual command
    try:
        process = subprocess.Popen(
            command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Stream stdout in real-time
        for line in process.stdout:
            print(line.strip(), flush=True)
            
        # Get the exit code
        process.wait()
        exit_code = process.returncode
        
        if exit_code != 0:
            stderr = process.stderr.read()
            log_message(f"Process exited with non-zero code {exit_code}", "ERROR")
            log_message(f"Error output: {stderr}", "ERROR")
            sys.exit(exit_code)
            
        log_message("Process completed successfully", "INFO")
        sys.exit(0)
            
    except Exception as e:
        log_message(f"Error executing command: {str(e)}", "ERROR")
        sys.exit(1)
