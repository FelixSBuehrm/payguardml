# filepath: backend/main.py
import argparse
import json
import os
import uuid
import time
from datetime import datetime
import pandas as pd
import sys

from pair_predictor import get_sbert_predictions
from llm_classifier import classify_pairs_with_llm
from utils import format_output_json, custom_json_serializer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(os.path.dirname(BASE_DIR), 'content')
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), 'output')

SBERT_MODEL_PATH = os.path.join(CONTENT_DIR, 'invoice_sbert')
THRESHOLD_PATH = os.path.join(CONTENT_DIR, 'best_threshold.txt')
PREDICT_PAIRS_SCRIPT_PATH = os.path.join(CONTENT_DIR, 'predict_pairs.py')

# Add a custom logging function
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

def delete_output_file(file_path):
    """
    Delete a file after it has been downloaded
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            log_message(f"Deleted output file: {file_path}", "INFO")
            
            # Check if the directory is now empty, and delete it if it is
            directory = os.path.dirname(file_path)
            if os.path.exists(directory) and not os.listdir(directory):
                os.rmdir(directory)
                log_message(f"Removed empty directory: {directory}", "INFO")
            return True
        else:
            log_message(f"File not found for deletion: {file_path}", "WARNING")
            return False
    except Exception as e:
        log_message(f"Error deleting file: {e}", "ERROR")
        return False

def cleanup_old_outputs(output_dir_base, max_age_days=7, keep_latest=5):
    """
    Clean up old output directories that are older than max_age_days,
    but always keep at least keep_latest number of directories
    """
    try:
        if not os.path.exists(output_dir_base):
            return
            
        # Get all run directories
        run_dirs = []
        for item in os.listdir(output_dir_base):
            item_path = os.path.join(output_dir_base, item)
            if os.path.isdir(item_path) and item.startswith("run_"):
                run_dirs.append(item_path)
        
        # Sort by creation time (newest first)
        run_dirs.sort(key=lambda x: os.path.getctime(x), reverse=True)
        
        # Always keep the latest n directories
        dirs_to_keep = run_dirs[:keep_latest]
        dirs_to_check = run_dirs[keep_latest:]
        
        # Check age for the rest
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        for dir_path in dirs_to_check:
            dir_age = current_time - os.path.getctime(dir_path)
            if dir_age > max_age_seconds:
                # Delete the directory and all its contents
                try:
                    for item in os.listdir(dir_path):
                        item_path = os.path.join(dir_path, item)
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                    os.rmdir(dir_path)
                    log_message(f"Cleaned up old output directory: {dir_path}", "INFO")
                except Exception as e:
                    log_message(f"Error cleaning up directory {dir_path}: {e}", "ERROR")
        
        return True
    except Exception as e:
        log_message(f"Error during cleanup: {e}", "ERROR")
        return False

def process_invoices(input_csv_path, output_dir_base, api_key=None):
    # Clean up old output directories first
    cleanup_old_outputs(output_dir_base)
    
    # Create a unique subdirectory for this run's outputs
    run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(output_dir_base, f"run_{run_timestamp}")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    log_message(f"Processing file: {input_csv_path}")
    log_message(f"Output will be saved in: {output_dir}")

    temp_sbert_output_csv = os.path.join(output_dir, "sbert_scored_pairs_temp.csv")
    
    # PROGRESS: Overall Start
    log_message("OVERALL_START", message_type="PROGRESS")
    log_message("Step 1: Getting SBERT similarity scores...", "INFO")
    
    # Force stdout flush to ensure immediate display
    sys.stdout.flush()
    
    scored_pairs_df = get_sbert_predictions(
        input_csv_path,
        PREDICT_PAIRS_SCRIPT_PATH,
        SBERT_MODEL_PATH,
        THRESHOLD_PATH,
        temp_sbert_output_csv
    )

    if scored_pairs_df.empty:
        log_message("No pairs found or SBERT prediction failed.", message_type="ERROR")
        return None

    log_message(f"Found {len(scored_pairs_df)} potential duplicate pairs from SBERT.", "INFO")
    sys.stdout.flush()

    log_message("Step 2: Classifying pairs with LLM...", "INFO")
    # PROGRESS: LLM Classification Start (overall, individual batches handled in llm_classifier)
    log_message("LLM_CLASSIFICATION_START", message_type="PROGRESS")
    sys.stdout.flush()
    
    # Start time for LLM processing
    llm_start_time = time.time()
    
    llm_results_df = classify_pairs_with_llm(scored_pairs_df, api_key=api_key)
    
    # Calculate LLM processing time
    llm_elapsed_time = time.time() - llm_start_time
    log_message(f"LLM classification completed in {llm_elapsed_time:.2f} seconds", "INFO")
    
    # PROGRESS: LLM Classification End (overall, individual batches handled in llm_classifier)
    log_message("LLM_CLASSIFICATION_END", message_type="PROGRESS")
    sys.stdout.flush()

    log_message("Step 3: Formatting output JSON...", "INFO")
    # PROGRESS: Formatting Start
    log_message("FORMATTING_START", message_type="PROGRESS")
    sys.stdout.flush()
    
    project_id = f"project-{uuid.uuid4()}"
    project_name = f"SAP Invoice Analysis - {os.path.basename(input_csv_path)}"
    project_description = "Analysis of SAP invoice pairs using SBERT and LLM."

    final_json_output = format_output_json(
        llm_results_df,
        project_id,
        project_name,
        project_description
    )

    output_filename = f"analysis_output_{run_timestamp}.json"
    output_filepath = os.path.join(output_dir, output_filename)

    with open(output_filepath, 'w') as f:
        json.dump(final_json_output, f, indent=2, default=custom_json_serializer)

    log_message(f"Processing complete. Output saved to: {output_filepath}", "INFO")
    # Print a special marker for the IPC process to capture the output path - with special format for easier parsing
    print(f"JSON_OUTPUT_PATH:{output_filepath}", flush=True)
    # PROGRESS: Overall End
    log_message("OVERALL_END", message_type="PROGRESS")
    sys.stdout.flush()
    
    # Return both the file path and the JSON content
    return {
        "filePath": output_filepath,
        "jsonContent": final_json_output
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process SAP invoice data.")
    parser.add_argument("--input", required=True, help="Path to the input CSV file.")
    parser.add_argument("--output_dir", default=DEFAULT_OUTPUT_DIR, help="Base directory to save the output JSON file.")
    parser.add_argument("--api_key", default=None, help="Gemini API Key.")
    
    args = parser.parse_args()

    result_file = process_invoices(args.input, args.output_dir, api_key=args.api_key)
    if result_file:
        # This specific print format can be caught by Electron's main process
        log_message(f"JSON_OUTPUT_PATH:{result_file}")
