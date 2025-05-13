# filepath: backend/pair_predictor.py
import subprocess
import pandas as pd
import os
import sys

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
    
    print(f"Running SBERT prediction: {' '.join(command)}")
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True, cwd=os.path.dirname(predict_script_path))
        print("SBERT script stdout:", process.stdout)
        if process.stderr:
            print("SBERT script stderr:", process.stderr)

        if os.path.exists(temp_output_csv_path):
            scored_pairs_df = pd.read_csv(temp_output_csv_path)
            # Ensure date columns are parsed correctly if predict_pairs.py doesn't save them as datetime objects
            for col in scored_pairs_df.columns:
                if 'DATE' in col.upper():
                    try:
                        scored_pairs_df[col] = pd.to_datetime(scored_pairs_df[col], errors='coerce')
                    except Exception:
                        pass # Keep as string if conversion fails
            return scored_pairs_df
        else:
            print(f"Error: SBERT script did not produce output file: {temp_output_csv_path}")
            return pd.DataFrame()
    except subprocess.CalledProcessError as e:
        print(f"Error running SBERT script: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return pd.DataFrame()
    except FileNotFoundError:
        print(f"Error: Python interpreter or script not found. Command: {' '.join(command)}")
        return pd.DataFrame()
