import os
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
import argparse
from tqdm import tqdm
import gc

def row_to_sentence(row):
    '''
    Convert a row to a sentence using a deterministic template.

    Args:
        row: DataFrame row

    Returns:
        String sentence representation
    '''
    # Handle missing values
    vendor_name = row['VENDOR_NAME'] if not pd.isna(row['VENDOR_NAME']) and row['VENDOR_NAME'] != '' else "unknown"
    vendor_id = row['VENDOR_ID'] if not pd.isna(row['VENDOR_ID']) and row['VENDOR_ID'] != '' else "unknown"

    # Format invoice date
    try:
        invoice_date = row['INVOICE_DATE'].strftime('%Y-%m-%d') if not pd.isna(row['INVOICE_DATE']) else "unknown"
    except:
        invoice_date = "unknown"

    # Format amount
    try:
        amount = f"{float(row['AMOUNT']):.2f}" if not pd.isna(row['AMOUNT']) else "unknown"
    except:
        amount = "unknown"

    currency = row['CURRENCY'] if not pd.isna(row['CURRENCY']) and row['CURRENCY'] != '' else "unknown"
    cost_center = row['COST_CENTER'] if not pd.isna(row['COST_CENTER']) and row['COST_CENTER'] != '' else "unknown"
    tax_code = row['TAX_CODE'] if not pd.isna(row['TAX_CODE']) and row['TAX_CODE'] != '' else "unknown"
    payment_terms = row['PAYMENT_TERMS'] if not pd.isna(row['PAYMENT_TERMS']) and row['PAYMENT_TERMS'] != '' else "unknown"
    purchase_order = row['PURCHASE_ORDER'] if not pd.isna(row['PURCHASE_ORDER']) and row['PURCHASE_ORDER'] != '' else "unknown"
    description = row['DESCRIPTION'] if not pd.isna(row['DESCRIPTION']) and row['DESCRIPTION'] != '' else "unknown"

    # Combine into template
    template = (
        f"Invoice from {vendor_name} ({vendor_id}) "
        f"dated {invoice_date} for {amount} {currency}. "
        f"PO: {purchase_order}. Cost centre {cost_center}. Tax {tax_code}. Terms {payment_terms}. "
        f"Description: {description}."
    )

    return template

def predict_duplicates(df, model_path, threshold_path, output_path='duplicates.csv', batch_size=250000, output_csv_path=None):
    '''
    Predict duplicates in a dataframe using the trained model.

    Args:
        df: DataFrame containing invoice data
        model_path: Path to the saved model
        threshold_path: Path to the saved threshold
        output_path: Path to save the duplicates CSV
        batch_size: Number of pairs to process in each batch
        output_csv_path: Path to save the output CSV of scored pairs
    '''
    # Load model and threshold
    print(f"Loading model from {model_path}")
    model = SentenceTransformer(model_path)

    # Use GPU if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)

    with open(threshold_path, 'r') as f:
        threshold = float(f.read().strip())

    print(f"Using similarity threshold: {threshold}")

    # Create sentences for all invoices
    print(f"Processing {len(df)} invoices")

    # Create a map of DOC_NO to index for faster lookups
    doc_no_to_idx = {doc_no: idx for idx, doc_no in enumerate(df['DOC_NO'])}
    
    # Create a set to track unique document numbers to prevent self-matching
    unique_doc_numbers = set(df['DOC_NO'])
    print(f"Number of unique document numbers: {len(unique_doc_numbers)}")

    # Filter out exact duplicates (where all column values are identical)
    print("Filtering out exact duplicates from the dataset...")
    original_count = len(df)
    df = df.drop_duplicates(keep='first')
    exact_duplicate_count = original_count - len(df)
    
    if exact_duplicate_count > 0:
        print(f"Removed {exact_duplicate_count} exact duplicate rows (all columns have identical values)")
        print(f"Dataset size reduced from {original_count} to {len(df)} rows")
        
        # Reset the index to ensure continuous indices after removing duplicates
        df = df.reset_index(drop=True)
        
        # Update the DOC_NO to index mapping with the new indices
        doc_no_to_idx = {doc_no: idx for idx, doc_no in enumerate(df['DOC_NO'])}
    else:
        print("No exact duplicates found in the dataset")

    # Create sentence cache with the updated indices
    sentence_cache = {}
    for idx, row in df.iterrows():
        sentence = row_to_sentence(row)
        sentence_cache[idx] = sentence

    # Generate candidate pairs using the same blocking strategy as in training
    print("Generating candidate pairs with blocking strategy...")

    N = len(df)
    total_possible_pairs = N * (N - 1) // 2
    print(f"Total possible pairs without blocking: {total_possible_pairs}")

    # Set for candidate pairs to avoid duplicates
    candidate_pairs = set()

    # 1. BLOCKING BY VENDOR_ID
    print("Blocking by VENDOR_ID...")
    vendor_groups = df.groupby('VENDOR_ID').indices
    for vendor_id, indices in vendor_groups.items():
        if len(indices) < 2:
            continue

        # Add all pairs within this vendor group
        for i, idx1 in enumerate(indices):
            doc1_no = df.iloc[idx1]['DOC_NO']
            for idx2 in indices[i+1:]:
                doc2_no = df.iloc[idx2]['DOC_NO']
                # Skip if document numbers are the same (self-matching)
                if doc1_no == doc2_no:
                    continue
                candidate_pairs.add((min(idx1, idx2), max(idx1, idx2)))

    print(f"After VENDOR_ID blocking: {len(candidate_pairs)} candidate pairs")

    # 2. BLOCKING BY VENDOR_NAME PREFIX (first 4 chars)
    print("Blocking by VENDOR_NAME prefix...")
    vendor_name_prefix_groups = {}
    for idx, vendor_name in enumerate(df['VENDOR_NAME']):
        if pd.isna(vendor_name) or vendor_name == '':
            continue

        prefix = str(vendor_name)[:4] if len(str(vendor_name)) >= 4 else str(vendor_name)
        if prefix not in vendor_name_prefix_groups:
            vendor_name_prefix_groups[prefix] = []
        vendor_name_prefix_groups[prefix].append(idx)

    for prefix, indices in vendor_name_prefix_groups.items():
        if len(indices) < 2:
            continue

        for i, idx1 in enumerate(indices):
            doc1_no = df.iloc[idx1]['DOC_NO']
            for idx2 in indices[i+1:]:
                doc2_no = df.iloc[idx2]['DOC_NO']
                # Skip if document numbers are the same (self-matching)
                if doc1_no == doc2_no:
                    continue
                candidate_pairs.add((min(idx1, idx2), max(idx1, idx2)))

    print(f"After VENDOR_NAME prefix blocking: {len(candidate_pairs)} candidate pairs")

    # 3. BLOCKING BY PURCHASE_ORDER
    print("Blocking by PURCHASE_ORDER...")
    po_groups = df.groupby('PURCHASE_ORDER').indices
    for po, indices in po_groups.items():
        if pd.isna(po) or po == '' or len(indices) < 2:
            continue

        for i, idx1 in enumerate(indices):
            doc1_no = df.iloc[idx1]['DOC_NO']
            for idx2 in indices[i+1:]:
                doc2_no = df.iloc[idx2]['DOC_NO']
                # Skip if document numbers are the same (self-matching)
                if doc1_no == doc2_no:
                    continue
                candidate_pairs.add((min(idx1, idx2), max(idx1, idx2)))

    print(f"After PURCHASE_ORDER blocking: {len(candidate_pairs)} candidate pairs")

    # 4. BLOCKING BY DESCRIPTION
    print("Blocking by DESCRIPTION...")
    desc_groups = df.groupby('DESCRIPTION').indices
    for desc, indices in desc_groups.items():
        if pd.isna(desc) or desc == '' or len(indices) < 2:
            continue

        for i, idx1 in enumerate(indices):
            doc1_no = df.iloc[idx1]['DOC_NO']
            for idx2 in indices[i+1:]:
                doc2_no = df.iloc[idx2]['DOC_NO']
                # Skip if document numbers are the same (self-matching)
                if doc1_no == doc2_no:
                    continue
                candidate_pairs.add((min(idx1, idx2), max(idx1, idx2)))

    print(f"After DESCRIPTION blocking: {len(candidate_pairs)} candidate pairs")

    # 5. BLOCKING BY AMOUNT AND CURRENCY
    print("Blocking by AMOUNT and CURRENCY...")
    amount_currency_groups = df.groupby(['AMOUNT', 'CURRENCY']).indices
    for (amount, currency), indices in amount_currency_groups.items():
        if pd.isna(amount) or pd.isna(currency) or len(indices) < 2:
            continue

        for i, idx1 in enumerate(indices):
            doc1_no = df.iloc[idx1]['DOC_NO']
            for idx2 in indices[i+1:]:
                doc2_no = df.iloc[idx2]['DOC_NO']
                # Skip if document numbers are the same (self-matching)
                if doc1_no == doc2_no:
                    continue
                candidate_pairs.add((min(idx1, idx2), max(idx1, idx2)))

    # Convert set to list for easier processing
    candidate_pairs = list(candidate_pairs)

    print(f"Generated {len(candidate_pairs)} candidate pairs after all blocking")
    print(f"Reduction: {1 - len(candidate_pairs)/total_possible_pairs:.2%} of pairs filtered out")

    # Initialize batch processing
    print("Processing candidate pairs in batches...")
    duplicate_dfs = []
    current_batch = []

    # Process pairs in batches
    for pair_idx, (idx1, idx2) in enumerate(tqdm(candidate_pairs)):
        current_batch.append((idx1, idx2))

        # Process batch when it reaches the desired size or final batch
        if len(current_batch) >= batch_size or pair_idx == len(candidate_pairs) - 1:
            batch_result = process_candidate_batch(current_batch, df, model, device, sentence_cache, threshold)
            if not batch_result.empty:
                duplicate_dfs.append(batch_result)
            current_batch = []

            # Free memory
            gc.collect()

    # Combine all batches
    if duplicate_dfs:
        final_duplicates_df = pd.concat(duplicate_dfs, ignore_index=True)

        # Sort by similarity score
        final_duplicates_df = final_duplicates_df.sort_values('similarity', ascending=False)

        print(f"Found {len(final_duplicates_df)} potential duplicates")
        if output_csv_path:
            final_duplicates_df.to_csv(output_csv_path, index=False)
            print(f"Saved scored pairs to {output_csv_path}")
        return final_duplicates_df
    else:
        print("No duplicates found")
        # Create empty DataFrame with proper column structure
        empty_df = pd.DataFrame(columns=['similarity'] +
                               [f'INV1_{col}' for col in df.columns] +
                               [f'INV2_{col}' for col in df.columns])
        if output_csv_path:
            empty_df.to_csv(output_csv_path, index=False)
            print(f"Saved empty DataFrame to {output_csv_path}")
        return empty_df

def process_candidate_batch(batch, df, model, device, sentence_cache, threshold):
    '''
    Process a batch of candidate pairs and return duplicates.

    Args:
        batch: List of (idx1, idx2) tuples
        df: DataFrame containing invoice data
        model: Trained SBERT model
        device: Device to run model on
        sentence_cache: Dictionary mapping indices to sentence representations
        threshold: Similarity threshold

    Returns:
        DataFrame of duplicates
    '''
    # Get sentences for encoding
    batch_indices = set()
    for idx1, idx2 in batch:
        batch_indices.add(idx1)
        batch_indices.add(idx2)

    batch_indices = list(batch_indices)
    
    # Safely get sentences, using int conversion to avoid numpy int64 issues
    batch_sentences = []
    for idx in batch_indices:
        # Convert numpy.int64 to Python int if needed
        idx = int(idx)
        if idx in sentence_cache:
            batch_sentences.append(sentence_cache[idx])
        else:
            # If the index isn't in the cache (which shouldn't happen with reset_index), 
            # generate the sentence on the fly
            batch_sentences.append(row_to_sentence(df.iloc[idx]))
            # Add to cache for future use
            sentence_cache[idx] = batch_sentences[-1]

    # Create index mapping for this batch
    batch_idx_map = {idx: i for i, idx in enumerate(batch_indices)}

    # Encode sentences
    embeddings = model.encode(batch_sentences, convert_to_tensor=True, device=device)

    # Compute similarities and find duplicates
    duplicates = []
    for idx1, idx2 in batch:
        # Extra check to ensure we're not comparing an invoice with itself
        doc1_no = df.iloc[idx1]['DOC_NO']
        doc2_no = df.iloc[idx2]['DOC_NO']
        if doc1_no == doc2_no:
            print(f"Warning: Skipping self-comparison for document {doc1_no}")
            continue
            
        emb_idx1 = batch_idx_map[idx1]
        emb_idx2 = batch_idx_map[idx2]

        emb1 = embeddings[emb_idx1]
        emb2 = embeddings[emb_idx2]

        similarity = torch.dot(emb1, emb2) / (torch.norm(emb1) * torch.norm(emb2))
        similarity = similarity.item()

        if similarity >= threshold:
            record = {'similarity': similarity}

            # Add columns for first invoice with prefix INV1_
            for col in df.columns:
                record[f'INV1_{col}'] = df.iloc[idx1][col]

            # Add columns for second invoice with prefix INV2_
            for col in df.columns:
                record[f'INV2_{col}'] = df.iloc[idx2][col]

            duplicates.append(record)

    if duplicates:
        # Create dataframe from duplicates
        duplicates_df = pd.DataFrame(duplicates)

        # Reorder columns to have all INV1_ columns first, then INV2_, then similarity
        inv1_cols = [col for col in duplicates_df.columns if col.startswith('INV1_')]
        inv2_cols = [col for col in duplicates_df.columns if col.startswith('INV2_')]

        # New column order with similarity at the end
        new_col_order = inv1_cols + inv2_cols + ['similarity']

        # Reorder DataFrame columns
        duplicates_df = duplicates_df[new_col_order]

        return duplicates_df
    else:
        return pd.DataFrame()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Predict invoice duplicates')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV file')
    parser.add_argument('--model', type=str, default='invoice_sbert', help='Path to model directory')
    parser.add_argument('--threshold', type=str, default='best_threshold.txt', help='Path to threshold file')
    parser.add_argument('--output', type=str, default='duplicates.csv', help='Path to output CSV file for duplicates (legacy, primarily for direct script execution)')
    parser.add_argument('--batch-size', type=int, default=250000, help='Batch size for processing')
    parser.add_argument("--output_csv", help="Path to save the output CSV of scored pairs.")

    args = parser.parse_args()

    # Set random seed for reproducibility
    os.environ['PYTHONHASHSEED'] = '42'

    # Load data
    print(f"Loading data from {args.input}")
    df = pd.read_csv(args.input, dtype=str, sep=';')

    # Convert numeric and date columns
    df['AMOUNT'] = pd.to_numeric(df['AMOUNT'], errors='coerce')
    df['INVOICE_DATE'] = pd.to_datetime(df['INVOICE_DATE'], errors='coerce', format='mixed')

    # Predict duplicates
    result_df = predict_duplicates(df, args.model, args.threshold, args.output, args.batch_size, args.output_csv)

    # If --output_csv is not given, and the script is run directly,
    # it might still be useful to print to console or save to the default args.output.
    # The backend script will always provide --output_csv.
    if not args.output_csv and not result_df.empty:
        print("Outputting to console as --output_csv was not specified:")
        print(result_df.to_string())
    elif not args.output_csv and result_df.empty:
        print("No duplicates found and --output_csv was not specified.")
