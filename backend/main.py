# filepath: backend/main.py
import argparse
import json
import os
import uuid
from datetime import datetime
import pandas as pd

from pair_predictor import get_sbert_predictions
from llm_classifier import classify_pairs_with_llm
from utils import format_output_json, custom_json_serializer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(os.path.dirname(BASE_DIR), 'content')
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), 'output')

SBERT_MODEL_PATH = os.path.join(CONTENT_DIR, 'invoice_sbert')
THRESHOLD_PATH = os.path.join(CONTENT_DIR, 'best_threshold.txt')
PREDICT_PAIRS_SCRIPT_PATH = os.path.join(CONTENT_DIR, 'predict_pairs.py')

def process_invoices(input_csv_path, output_dir_base):
    # Create a unique subdirectory for this run's outputs
    run_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(output_dir_base, f"run_{run_timestamp}")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Processing file: {input_csv_path}")
    print(f"Output will be saved in: {output_dir}")

    temp_sbert_output_csv = os.path.join(output_dir, "sbert_scored_pairs_temp.csv")
    
    print("Step 1: Getting SBERT similarity scores...")
    scored_pairs_df = get_sbert_predictions(
        input_csv_path,
        PREDICT_PAIRS_SCRIPT_PATH,
        SBERT_MODEL_PATH,
        THRESHOLD_PATH,
        temp_sbert_output_csv
    )

    if scored_pairs_df.empty:
        print("No pairs found or SBERT prediction failed.")
        return None

    print(f"Found {len(scored_pairs_df)} potential duplicate pairs from SBERT.")

    print("Step 2: Classifying pairs with LLM...")
    llm_results_df = classify_pairs_with_llm(scored_pairs_df)

    print("Step 3: Formatting output JSON...")
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

    print(f"Processing complete. Output saved to: {output_filepath}")
    return output_filepath

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process SAP invoice data.")
    parser.add_argument("--input", required=True, help="Path to the input CSV file.")
    parser.add_argument("--output_dir", default=DEFAULT_OUTPUT_DIR, help="Base directory to save the output JSON file.")
    
    args = parser.parse_args()

    result_file = process_invoices(args.input, args.output_dir)
    if result_file:
        # This specific print format can be caught by Electron's main process
        print(f"JSON_OUTPUT_PATH:{result_file}")
