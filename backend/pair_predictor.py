# filepath: backend/pair_predictor.py
import subprocess
import pandas as pd
import os
import sys
import time
from datetime import datetime

def log_message(message, message_type="INFO"):
    """
    Log a message to both stdout and stderr if it's an error
    to ensure visibility in both UI and terminal.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] [{message_type}] {message}"
    
    print(formatted_message, flush=True)
    if message_type == "ERROR":
        print(formatted_message, file=sys.stderr, flush=True)
    
    # For progress updates, add a special marker for the UI
    if message_type == "PROGRESS":
        print(f"PROGRESS:{message}", flush=True)

def get_sbert_predictions(input_csv_path, predict_script_path, model_path, threshold_path, temp_output_csv_path):
    """
    Runs the predict_pairs.py script and returns its output as a DataFrame.
    Requires predict_pairs.py to be modified to accept an --output_csv argument.
    """
    command = [
        sys.executable, # Use the same Python interpreter running this script
        predict_script_path,
        "--input", input_csv_path,
        "--model", model_path,
        "--threshold", threshold_path,
        "--output_csv", temp_output_csv_path
    ]
    
    log_message(f"Running SBERT prediction command: {' '.join(command)}", "INFO")
    log_message("Starting SBERT similarity analysis", "PROGRESS")
    try:
        # PROGRESS: Starting SBERT
        print("PROGRESS:SBERT_START")
        
        # Start time for measuring performance
        start_time = time.time()
        
        process = subprocess.run(command, capture_output=True, text=True, check=True, cwd=os.path.dirname(predict_script_path))
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        log_message(f"SBERT processing took {elapsed_time:.2f} seconds", "INFO")
        
        log_message("SBERT script stdout:", "DEBUG")
        print(process.stdout)
        
        if process.stderr:
            log_message("SBERT script stderr:", "WARNING")
            print(process.stderr)
            
        # PROGRESS: SBERT Done
        log_message("SBERT similarity analysis completed", "PROGRESS")
        print("PROGRESS:SBERT_END")

        if os.path.exists(temp_output_csv_path):
            log_message(f"Loading SBERT results from {temp_output_csv_path}", "INFO")
            scored_pairs_df = pd.read_csv(temp_output_csv_path)
            
            # Log some statistics about the results
            log_message(f"SBERT found {len(scored_pairs_df)} candidate pairs", "INFO")
            
            # Ensure date columns are parsed correctly if predict_pairs.py doesn't save them as datetime objects
            for col in scored_pairs_df.columns:
                if 'DATE' in col.upper():
                    try:
                        scored_pairs_df[col] = pd.to_datetime(scored_pairs_df[col], errors='coerce')
                    except Exception as e:
                        log_message(f"Warning: Could not convert column {col} to datetime: {str(e)}", "WARNING")
            
            # Log some similarity stats if available
            if 'similarity_score' in scored_pairs_df.columns:
                log_message(f"Similarity score stats: min={scored_pairs_df['similarity_score'].min():.4f}, " 
                           f"max={scored_pairs_df['similarity_score'].max():.4f}, "
                           f"mean={scored_pairs_df['similarity_score'].mean():.4f}", "INFO")
            
            return scored_pairs_df
        else:
            log_message(f"Error: SBERT script did not produce output file: {temp_output_csv_path}", "ERROR")
            return pd.DataFrame()
    except subprocess.CalledProcessError as e:
        log_message(f"Error running SBERT script: {e}", "ERROR")
        log_message(f"Stdout: {e.stdout}", "ERROR")
        log_message(f"Stderr: {e.stderr}", "ERROR")
        return pd.DataFrame()
    except FileNotFoundError:
        log_message(f"Error: Python interpreter or script not found. Command: {' '.join(command)}", "ERROR")
        return pd.DataFrame()
    except Exception as e:
        log_message(f"Unexpected error in SBERT processing: {str(e)}", "ERROR")
        return pd.DataFrame()
        return pd.DataFrame()
