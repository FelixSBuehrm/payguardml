"""
Example script demonstrating how to use PayGuard for SAP payment document pairing
"""

import pandas as pd
from payguard_sap import load_sap_data, preprocess_sap_data, generate_payment_document_pairs, filter_pairs, filter_invoices_by_amount

# File paths for SAP tables
bkpf_path = 'bkpf.csv'
bseg_path = 'bseg.csv'
lfa1_path = 'lfa1.csv'

# Testing with limited data (first 200 rows)
limit_rows = 100000

# Load and join SAP data with row limit
print("Loading and joining SAP data...")
merged_data = load_sap_data(bkpf_path, bseg_path, lfa1_path, limit_rows=limit_rows)

# Check for vendor name in the raw data
print("\nChecking for vendor name in raw data:")
if 'name1' in merged_data.columns:
    non_empty_vendor_names = merged_data['name1'].dropna().unique()
    print(f"Found {len(non_empty_vendor_names)} unique vendor names in the 'name1' column")
    print("Sample vendor names from LFA1 table:", list(non_empty_vendor_names)[:5])
else:
    print("WARNING: 'name1' column not found in the merged data")
    
# Show join columns used for vendors
print("\nVendor join info:")
if 'lifnr' in merged_data.columns:
    non_empty_vendor_numbers = merged_data['lifnr'].dropna().unique()
    print(f"Found {len(non_empty_vendor_numbers)} unique vendor numbers in the 'lifnr' column")
    print("Sample vendor numbers:", list(non_empty_vendor_numbers)[:5])
else:
    print("WARNING: 'lifnr' column not found in the merged data")

# Preprocess the data - now includes filtering for debit entries and invoice document types
print("\nPreprocessing data...")
processed_df = preprocess_sap_data(merged_data)

# Display sample of the preprocessed data
print("\nSample of preprocessed data:")
if 'document_number' in processed_df.columns and 'amount' in processed_df.columns:
    sample_columns = [
        'document_number', 'amount', 'currency', 'document_type', 
        'vendor_number', 'vendor_name', 'company_code', 'debit_credit_indicator'
    ]
    existing_columns = [col for col in sample_columns if col in processed_df.columns]
    print(processed_df[existing_columns].head())
    
    # Check if vendor_name is being properly mapped
    print("\nVendor name info after preprocessing:")
    if 'vendor_name' in processed_df.columns:
        non_empty_vendors = processed_df[processed_df['vendor_name'] != '']
        print(f"Records with non-empty vendor name: {len(non_empty_vendors)} out of {len(processed_df)}")
        if not non_empty_vendors.empty:
            print("Sample vendor names after preprocessing:", list(non_empty_vendors['vendor_name'].unique())[:5])
        else:
            print("WARNING: No non-empty vendor names found after preprocessing")
    else:
        print("WARNING: 'vendor_name' column not found after preprocessing")
else:
    print(processed_df.iloc[:, :10].head())  # Just show first 10 columns

# For testing, print all document types in the dataset
if 'document_type' in processed_df.columns:
    unique_doc_types = processed_df['document_type'].unique()
    print(f"\nUnique document types in test data: {unique_doc_types}")

# Apply amount filter
print("\nApplying amount filter...")
filtered_df = filter_invoices_by_amount(processed_df, min_amount=500)

# Generate document pairs
print("\nGenerating document pairs...")
pairs_df = generate_payment_document_pairs(filtered_df)

if not pairs_df.empty:
    print(f"Generated {len(pairs_df)} document pairs.")
    
    # Check if vendor names are in the pairs data
    print("\nVendor info in generated pairs:")
    if 'doc1_vendor_name' in pairs_df.columns:
        non_empty_doc1 = pairs_df[pairs_df['doc1_vendor_name'] != '']
        print(f"Pairs with non-empty doc1_vendor_name: {len(non_empty_doc1)} out of {len(pairs_df)}")
        if not non_empty_doc1.empty:
            print("Sample doc1_vendor_name values:", list(non_empty_doc1['doc1_vendor_name'].unique())[:5])
    else:
        print("WARNING: 'doc1_vendor_name' column not found in pairs data")
    
    # Show a few columns from the resulting pairs
    print("\nSample of generated pairs (before similarity filtering):")
    sample_columns = [
        'pair_id', 'score', 'doc1_number', 'doc1_amount', 'doc1_document_type',
        'doc2_number', 'doc2_amount', 'doc2_document_type', 'amount_diff',
        'doc1_vendor_name', 'doc2_vendor_name'  # Added vendor names to sample
    ]
    # Make sure all these columns exist before displaying
    existing_columns = [col for col in sample_columns if col in pairs_df.columns]
    print(pairs_df[existing_columns].head())
    
    # Filter pairs with higher threshold
    threshold = 0.7  # Higher threshold for demonstration
    print(f"\nFiltering pairs with similarity score ≥ {threshold}...")
    filtered_pairs = filter_pairs(pairs_df, threshold=threshold)
    print(f"Retained {len(filtered_pairs)} pairs after filtering.")
    
    # Show filtered pairs
    print("\nTop filtered pairs:")
    print(filtered_pairs[existing_columns].head())
    
    # Export the results
    output_file = 'sap_example_results.csv'
    filtered_pairs.to_csv(output_file, index=False)
    print(f"\nResults exported to {output_file}")
else:
    print("No document pairs were generated. Check your data and preprocessing steps.")

# Generate a report with counts
print("\n======= SUMMARY REPORT =======")
print(f"Total documents processed: {len(processed_df)}")
print(f"Documents after amount filtering: {len(filtered_df)}")
print(f"Total pairs generated: {len(pairs_df) if not pairs_df.empty else 0}")
print(f"Pairs after similarity filtering: {len(filtered_pairs) if 'filtered_pairs' in locals() and not filtered_pairs.empty else 0}")
print("==============================") 

