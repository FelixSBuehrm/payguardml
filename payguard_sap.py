import pandas as pd
import numpy as np
import itertools
from typing import List, Dict, Any, Tuple
import uuid
from datetime import datetime

def compute_similarity_score(doc1: Dict[str, Any], doc2: Dict[str, Any]) -> float:
    """
    Placeholder for ML algorithm to compute similarity score between two payment documents.
    Will be implemented later.
    
    Args:
        doc1: First payment document data
        doc2: Second payment document data
        
    Returns:
        float: Similarity score between 0 and 1
    """
    # For now, return a random score for demonstration
    return np.random.uniform(0, 1)

def load_sap_data(bkpf_path: str, bseg_path: str, lfa1_path: str = None, limit_rows: int = None) -> pd.DataFrame:
    """
    Load and join SAP financial accounting tables
    
    Args:
        bkpf_path: Path to BKPF table (document header) CSV
        bseg_path: Path to BSEG table (document line items) CSV
        lfa1_path: Path to LFA1 table (vendor master) CSV (optional)
        limit_rows: Limit the number of rows to load from each table (for testing)
        
    Returns:
        pd.DataFrame: Joined payment document data
    """
    # Load individual tables
    print("Loading BKPF (document header) data...")
    if limit_rows:
        bkpf = pd.read_csv(bkpf_path, nrows=limit_rows, low_memory=False)
        print(f"Loaded {len(bkpf)} document headers (limited to {limit_rows} rows for testing).")
    else:
        bkpf = pd.read_csv(bkpf_path, low_memory=False)
        print(f"Loaded {len(bkpf)} document headers.")
    
    print("Loading BSEG (line items) data...")
    if limit_rows:
        bseg = pd.read_csv(bseg_path, nrows=limit_rows, low_memory=False)
        print(f"Loaded {len(bseg)} line items (limited to {limit_rows} rows for testing).")
    else:
        bseg = pd.read_csv(bseg_path, low_memory=False)
        print(f"Loaded {len(bseg)} line items.")
    
    # Join BKPF and BSEG (header and line items)
    print("Joining document headers with line items...")
    join_cols = ['mandt', 'bukrs', 'belnr', 'gjahr']
    
    # Ensure join columns are string type before merge
    for col in join_cols:
        if col in bkpf.columns:
            bkpf[col] = bkpf[col].astype(str)
        if col in bseg.columns:
            bseg[col] = bseg[col].astype(str)
    
    merged_df = pd.merge(bseg, bkpf, on=join_cols, how='inner', suffixes=('', '_head'))
    print(f"Merged data contains {len(merged_df)} records.")
    
    # If vendor master data is provided, join it as well
    if lfa1_path:
        print("Loading LFA1 (vendor master) data...")
        if limit_rows:
            lfa1 = pd.read_csv(lfa1_path, nrows=limit_rows, low_memory=False)
            print(f"Loaded {len(lfa1)} vendor records (limited to {limit_rows} rows for testing).")
        else:
            lfa1 = pd.read_csv(lfa1_path, low_memory=False)
            print(f"Loaded {len(lfa1)} vendor records.")
        
        # Checking vendor data before joining
        if 'name1' in lfa1.columns:
            vendor_names = lfa1['name1'].dropna()
            print(f"Found {len(vendor_names)} non-empty vendor names in LFA1 table")
            if not vendor_names.empty:
                print(f"Sample vendor names: {list(vendor_names.unique())[:3]}")
        
        # Join with vendor data
        print("Joining with vendor data...")
        vendor_join_cols = ['mandt', 'lifnr']
        
        # Ensure vendor join columns exist in both dataframes
        missing_cols = [col for col in vendor_join_cols if col not in merged_df.columns or col not in lfa1.columns]
        if missing_cols:
            print(f"WARNING: Missing vendor join columns: {missing_cols}")
            print(f"Merged data columns: {sorted(merged_df.columns)}")
            print(f"LFA1 columns: {sorted(lfa1.columns)}")
        
        # Ensure vendor join columns are string type
        for col in vendor_join_cols:
            if col in merged_df.columns:
                merged_df[col] = merged_df[col].astype(str)
            if col in lfa1.columns:
                lfa1[col] = lfa1[col].astype(str)
        
        # Analyze lifnr values before join
        if 'lifnr' in merged_df.columns and 'lifnr' in lfa1.columns:
            merged_lifnr = set(merged_df['lifnr'].dropna().unique())
            lfa1_lifnr = set(lfa1['lifnr'].dropna().unique())
            common_lifnr = merged_lifnr.intersection(lfa1_lifnr)
            print(f"BSEG contains {len(merged_lifnr)} unique vendor numbers")
            print(f"LFA1 contains {len(lfa1_lifnr)} unique vendor numbers")
            print(f"Found {len(common_lifnr)} common vendor numbers between tables")
            
            # Display sample vendor numbers for debugging
            print(f"Sample BSEG vendor numbers: {list(merged_lifnr)[:5]}")
            print(f"Sample LFA1 vendor numbers: {list(lfa1_lifnr)[:5]}")
        
        # Perform the join
        merged_df = pd.merge(merged_df, lfa1, on=vendor_join_cols, how='left', suffixes=('', '_vendor'))
        
        # Check for successful vendor name join
        if 'name1' in merged_df.columns:
            vendor_with_names = merged_df[merged_df['name1'].notna()]
            print(f"After join, {len(vendor_with_names)} out of {len(merged_df)} records have vendor names")
        
        print(f"Final merged data contains {len(merged_df)} records.")
    
    return merged_df

def preprocess_sap_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess SAP data to prepare it for pairing:
    1. Converts date and amount fields
    2. Maps standard field names
    3. Filters for relevant documents (credit entries/payments, payment document types)
    
    Args:
        df: Raw SAP data (BKPF + BSEG + optionally LFA1)
        
    Returns:
        pd.DataFrame: Preprocessed data ready for pairing
    """
    # Create a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Debug info - check for original vendor data
    if 'name1' in processed_df.columns:
        non_empty_name1 = processed_df['name1'].notna() & (processed_df['name1'] != '')
        print(f"DEBUG: Raw data has {non_empty_name1.sum()} non-empty name1 values out of {len(processed_df)} records")
        if non_empty_name1.any():
            print(f"DEBUG: Sample name1 values: {processed_df.loc[non_empty_name1, 'name1'].iloc[:3].tolist()}")
            
            # Debug vendor & document types mapping
            if 'blart' in processed_df.columns:
                # Show which document types have vendor names
                doc_types_with_vendors = processed_df[non_empty_name1]['blart'].value_counts().to_dict()
                print(f"DEBUG: Document types with vendor names: {doc_types_with_vendors}")
                
                # Count vendors for our target document types
                target_types = ['AB', 'KZ', 'DZ', 'ZP', 'ZV']
                target_docs = processed_df['blart'].isin(target_types)
                target_with_vendors = processed_df[target_docs & non_empty_name1]
                print(f"DEBUG: Payment document records with vendor names: {len(target_with_vendors)} out of {target_docs.sum()}")
    else:
        print("DEBUG: name1 column not found in raw data")
    
    # Remove columns that are completely empty
    print("Removing empty columns...")
    null_cols = processed_df.columns[processed_df.isna().all()]
    processed_df = processed_df.drop(columns=null_cols)
    print(f"Removed {len(null_cols)} empty columns.")
    
    # Handle missing values - but don't fill vendor name with empty string
    vendor_name_temp = None
    if 'name1' in processed_df.columns:
        vendor_name_temp = processed_df['name1'].copy()
    
    processed_df = processed_df.fillna('')
    
    # Restore vendor name values
    if vendor_name_temp is not None:
        processed_df['name1'] = vendor_name_temp
    
    # Convert date fields (SAP dates are often in format YYYYMMDD)
    date_columns = ['bldat', 'budat', 'cpudt', 'aedat', 'upddt', 'wwert', 'augdt', 'valut', 'zfbdt']
    
    print("Converting date fields...")
    for col in date_columns:
        if col in processed_df.columns:
            # First ensure the column is string type
            processed_df[col] = processed_df[col].astype(str)
            # Remove any empty strings to avoid conversion errors
            processed_df[col] = processed_df[col].replace('', pd.NA)
            
            # Convert YYYYMMDD string to datetime
            try:
                processed_df[col] = pd.to_datetime(processed_df[col], format='%Y%m%d', errors='coerce')
            except:
                # If that fails, try standard date parsing
                processed_df[col] = pd.to_datetime(processed_df[col], errors='coerce')
    
    # Convert amount fields to numeric
    amount_columns = ['dmbtr', 'wrbtr', 'kzbtr', 'pswbt', 'hwbas', 'fwbas', 'hwzuz', 'fwzuz']
    
    print("Converting amount fields...")
    for col in amount_columns:
        if col in processed_df.columns:
            processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce').fillna(0)
    
    # Map standard fields to SAP fields
    field_mapping = {
        'amount': 'wrbtr',  # Document amount in document currency
        'currency': 'waers',  # Currency key
        'document_type': 'blart',  # Document type
        'company_code': 'bukrs',  # Company code
        'vendor_number': 'lifnr',  # Vendor account number
        'sap_client': 'mandt',  # Client
        'fiscal_year': 'gjahr',  # Fiscal year
        'accounting_date': 'budat',  # Posting date
        'document_date': 'bldat',  # Document date
        'user_name': 'usnam',  # User name
        'clearing_doc': 'augbl',  # Document number of the clearing document
        'clearing_date': 'augdt',  # Clearing date
        'reference': 'xblnr',  # Reference document number
        'vendor_name': 'name1',  # Vendor name (from LFA1)
        'posting_text': 'sgtxt',  # Text
        'entry_date': 'cpudt',  # Entry date
        'assignment_nr': 'zuonr',  # Assignment number
        'debit_credit_indicator': 'shkzg',  # Debit/credit indicator
    }
    
    print("Mapping standard field names...")
    
    # Debug mapping process
    for std_field, sap_field in field_mapping.items():
        if sap_field in processed_df.columns:
            # Before mapping
            if std_field == 'vendor_name':
                non_empty = processed_df[sap_field].notna() & (processed_df[sap_field] != '')
                print(f"DEBUG: Before mapping, {sap_field} column has {non_empty.sum()} non-empty values")
                if non_empty.any():
                    print(f"DEBUG: Sample {sap_field} values: {processed_df.loc[non_empty, sap_field].iloc[:3].tolist()}")
            
            # Perform the mapping
            processed_df[std_field] = processed_df[sap_field]
            
            # After mapping
            if std_field == 'vendor_name':
                non_empty = processed_df[std_field].notna() & (processed_df[std_field] != '')
                print(f"DEBUG: After mapping, {std_field} column has {non_empty.sum()} non-empty values")
                if non_empty.any():
                    print(f"DEBUG: Sample mapped values: {processed_df.loc[non_empty, std_field].iloc[:3].tolist()}")
        else:
            if std_field == 'vendor_name':
                print(f"DEBUG: {sap_field} column not found for mapping {std_field}")
    
    # Use document number (belnr) directly
    if 'belnr' in processed_df.columns:
        print("Using original document number (belnr) directly...")
        processed_df['document_number'] = processed_df['belnr']
    
    # Filter for credit entries only (payments to vendors)
    if 'debit_credit_indicator' in processed_df.columns:
        print("Filtering for credit entries (outgoing payments) only...")
        initial_count = len(processed_df)
        credit_mask = processed_df['debit_credit_indicator'] == 'H'
        processed_df = processed_df[credit_mask]
        print(f"Removed {initial_count - len(processed_df)} debit entries, {len(processed_df)} credit entries remain.")
        
        # Debug vendor name after filtering
        if 'vendor_name' in processed_df.columns:
            non_empty_vendor = processed_df['vendor_name'].notna() & (processed_df['vendor_name'] != '')
            print(f"DEBUG: After credit filtering, vendor_name column has {non_empty_vendor.sum()} non-empty values out of {len(processed_df)}")
    
    # Create a backup of vendor information before payment type filtering
    vendor_data = None
    if 'vendor_name' in processed_df.columns and 'lifnr' in processed_df.columns:
        vendor_data = processed_df[['belnr', 'lifnr', 'vendor_name']].copy()
        # Count non-empty vendor names
        non_empty_vendor = vendor_data['vendor_name'].notna() & (vendor_data['vendor_name'] != '')
        print(f"DEBUG: Backed up {non_empty_vendor.sum()} vendor names before document type filtering")
    
    # Filter for payment document types only
    if 'document_type' in processed_df.columns:
        print("Filtering for payment document types only...")
        initial_count = len(processed_df)
        # Common SAP payment document types: 
        # ZP (payment doc), AB (accounting doc), KZ (vendor payment), ZV (payment request), DZ (payment request)
        # Note: You may need to adjust these based on your specific SAP implementation
        payment_types = ['ZP', 'AB', 'KZ', 'ZV', 'DZ']
        
        # Check if any of these document types exist in the data
        existing_types = set(processed_df['document_type'].unique())
        valid_payment_types = [t for t in payment_types if t in existing_types]
        
        # If no recognized payment types, don't filter by document type
        if valid_payment_types:
            payment_type_mask = processed_df['document_type'].isin(valid_payment_types)
            processed_df = processed_df[payment_type_mask]
            print(f"Removed {initial_count - len(processed_df)} non-payment documents, {len(processed_df)} payment documents remain.")
            print(f"Payment document types found: {valid_payment_types}")
            
            # Debug vendor name after document type filtering
            if 'vendor_name' in processed_df.columns:
                non_empty_vendor = processed_df['vendor_name'].notna() & (processed_df['vendor_name'] != '')
                print(f"DEBUG: After document type filtering, vendor_name column has {non_empty_vendor.sum()} non-empty values")
        else:
            print(f"No recognized payment types found in the data. Document types present: {list(existing_types)}")
            print("Skipping document type filtering.")
    
    # Restore vendor information if it was lost in filtering
    if vendor_data is not None and 'vendor_name' in processed_df.columns:
        non_empty_before = processed_df['vendor_name'].notna() & (processed_df['vendor_name'] != '')
        vendor_count_before = non_empty_before.sum()
        
        if vendor_count_before == 0:
            print("DEBUG: No vendor names found after filtering. Attempting to restore from backup...")
            # Merge to restore vendor information
            processed_df = pd.merge(
                processed_df,
                vendor_data[['belnr', 'vendor_name']],
                on='belnr',
                how='left',
                suffixes=('', '_restored')
            )
            
            # Update vendor name with restored values where current is empty
            mask = processed_df['vendor_name'].isna() | (processed_df['vendor_name'] == '')
            if 'vendor_name_restored' in processed_df.columns:
                processed_df.loc[mask, 'vendor_name'] = processed_df.loc[mask, 'vendor_name_restored']
                # Remove the temporary column
                processed_df = processed_df.drop(columns=['vendor_name_restored'])
            
            # Check the result
            non_empty_after = processed_df['vendor_name'].notna() & (processed_df['vendor_name'] != '')
            print(f"DEBUG: After restoration, vendor_name column has {non_empty_after.sum()} non-empty values")
    
    # Calculate absolute amount
    if 'amount' in processed_df.columns:
        # Ensure amount is numeric
        if not pd.api.types.is_numeric_dtype(processed_df['amount']):
            processed_df['amount'] = pd.to_numeric(processed_df['amount'], errors='coerce').fillna(0)
        
        processed_df['amount_abs'] = processed_df['amount'].abs()
    
    # Ensure vendor name is preserved even with missing values
    if 'vendor_name' in processed_df.columns:
        # Final check on vendor names
        non_empty_vendor = processed_df['vendor_name'].notna() & (processed_df['vendor_name'] != '')
        print(f"DEBUG: Final vendor_name check: {non_empty_vendor.sum()} non-empty values out of {len(processed_df)}")
        if non_empty_vendor.any():
            print(f"DEBUG: Sample vendor names at end of preprocessing: {processed_df.loc[non_empty_vendor, 'vendor_name'].iloc[:3].tolist()}")
    
    return processed_df

def filter_invoices_by_amount(df: pd.DataFrame, min_amount: float = 500) -> pd.DataFrame:
    """
    Filter invoices by amount (company-specific filter)
    
    Args:
        df: Preprocessed SAP data
        min_amount: Minimum amount threshold
        
    Returns:
        pd.DataFrame: Filtered data containing only invoices with amount >= min_amount
    """
    print(f"Applying amount filter (amount >= {min_amount})...")
    
    if 'amount_abs' in df.columns:
        initial_count = len(df)
        filtered_df = df[df['amount_abs'] >= min_amount]
        print(f"Amount filter: {initial_count - len(filtered_df)} records removed, {len(filtered_df)} remain.")
        return filtered_df
    else:
        print("Warning: 'amount_abs' column not found, skipping amount filter")
        return df

def generate_payment_document_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate pairs of payment-related documents
    
    Args:
        df: Preprocessed SAP data
        
    Returns:
        pd.DataFrame: DataFrame with all pairs and their combined information
    """
    # Get unique documents by grouping
    if 'document_number' in df.columns:
        # Group by document number and calculate sum of amounts per document
        print("Grouping documents by document number...")
        
        # Get columns that exist in the dataframe for aggregation
        agg_fields = {}
        
        # Add columns if they exist
        for col in ['amount', 'currency', 'document_type', 'company_code', 'vendor_number', 'sap_client', 
                   'fiscal_year', 'accounting_date', 'document_date', 'user_name', 'clearing_doc', 
                   'clearing_date', 'reference', 'vendor_name', 'posting_text', 'entry_date', 'assignment_nr',
                   'debit_credit_indicator', 'amount_abs']:
            if col in df.columns:
                agg_fields[col] = 'first'
        
        # Group by document number
        grouped_docs = df.groupby('document_number').agg(agg_fields).reset_index()
        
        print(f"Found {len(grouped_docs)} unique documents after grouping.")
        
        # Create pairs using itertools.combinations
        print("Generating all possible document pairs...")
        records = grouped_docs.to_dict('records')
        pairs = list(itertools.combinations(records, 2))
        
        print(f"Generated {len(pairs)} document pairs.")
        
        # Create a new DataFrame for the pairs
        pairs_data = []
        
        print("Creating pair data structures...")
        for idx, (doc1, doc2) in enumerate(pairs):
            # Generate a unique pair ID
            pair_id = str(uuid.uuid4())
            
            # Compute similarity score
            score = compute_similarity_score(doc1, doc2)
            
            # Initialize pair data with basic fields
            pair_data = {
                'pair_id': pair_id,
                'score': score,
                'doc1_number': doc1.get('document_number', ''),
                'doc2_number': doc2.get('document_number', ''),
            }
            
            # Add fields from both documents if they exist
            for field in ['amount', 'currency', 'document_type', 'company_code', 'vendor_number', 
                          'sap_client', 'fiscal_year', 'accounting_date', 'document_date', 'user_name', 
                          'clearing_doc', 'clearing_date', 'reference', 'vendor_name', 'posting_text', 
                          'entry_date', 'assignment_nr', 'debit_credit_indicator', 'amount_abs']:
                if field in doc1:
                    pair_data[f'doc1_{field}'] = doc1.get(field, '')
                if field in doc2:
                    pair_data[f'doc2_{field}'] = doc2.get(field, '')
            
            # Calculate amount difference for convenience
            if 'amount_abs' in doc1 and 'amount_abs' in doc2:
                doc1_amount = float(doc1.get('amount_abs', 0))
                doc2_amount = float(doc2.get('amount_abs', 0))
                pair_data['amount_diff'] = abs(doc1_amount - doc2_amount)
            
            pairs_data.append(pair_data)
        
        return pd.DataFrame(pairs_data)
    else:
        print("Error: 'document_number' field not found in the data.")
        return pd.DataFrame()

def filter_pairs(pairs_df: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
    """
    Filter pairs based on similarity score
    
    Args:
        pairs_df: DataFrame with all pairs
        threshold: Minimum similarity score threshold
        
    Returns:
        pd.DataFrame: Filtered pairs
    """
    print(f"Filtering pairs with similarity score ≥ {threshold}...")
    filtered_df = pairs_df[pairs_df['score'] >= threshold]
    print(f"Retained {len(filtered_df)} pairs after filtering.")
    
    return filtered_df.sort_values('score', ascending=False)

def main(bkpf_path: str, bseg_path: str, lfa1_path: str = None, output_path: str = 'sap_payment_pairs.csv', 
         score_threshold: float = 0.5, min_amount: float = 500, limit_rows: int = None):
    """
    Main function to process SAP payment documents and generate pairs
    
    Args:
        bkpf_path: Path to BKPF table CSV
        bseg_path: Path to BSEG table CSV
        lfa1_path: Path to LFA1 table CSV (optional)
        output_path: Path to save the output
        score_threshold: Minimum similarity score to include in results
        min_amount: Minimum amount for invoices
        limit_rows: Limit the number of rows to load from each table (for testing)
    """
    print("Starting SAP payment document pairing...")
    
    # Load and join SAP data
    merged_data = load_sap_data(bkpf_path, bseg_path, lfa1_path, limit_rows)
    
    # Preprocess the data, including filtering for debit entries and invoice document types
    print("Preprocessing data...")
    processed_df = preprocess_sap_data(merged_data)
    
    # Apply amount filter
    filtered_df = filter_invoices_by_amount(processed_df, min_amount)
    
    # Generate payment document pairs
    print("Generating document pairs...")
    pairs_df = generate_payment_document_pairs(filtered_df)
    
    if pairs_df.empty:
        print("No pairs were generated. Check your data and preprocessing steps.")
        return None
    
    print(f"Generated {len(pairs_df)} pairs.")
    
    # Filter pairs by similarity score
    filtered_pairs = filter_pairs(pairs_df, threshold=score_threshold)
    
    print(f"Saving {len(filtered_pairs)} filtered pairs to {output_path}...")
    
    # Save to output file
    if output_path.endswith('.csv'):
        filtered_pairs.to_csv(output_path, index=False)
    elif output_path.endswith(('.xlsx', '.xls')):
        filtered_pairs.to_excel(output_path, index=False)
    else:
        # Default to CSV if extension not recognized
        filtered_pairs.to_csv(output_path, index=False)
    
    print("Done!")
    
    return filtered_pairs

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate payment document pairs from SAP data")
    parser.add_argument("--bkpf", required=True, help="Path to BKPF table CSV")
    parser.add_argument("--bseg", required=True, help="Path to BSEG table CSV")
    parser.add_argument("--lfa1", help="Path to LFA1 table CSV (optional)")
    parser.add_argument("--output", default="sap_payment_pairs.csv", help="Path to save output file")
    parser.add_argument("--threshold", type=float, default=0.5, help="Similarity score threshold")
    parser.add_argument("--min-amount", type=float, default=500, help="Minimum amount for invoices")
    parser.add_argument("--limit-rows", type=int, help="Limit the number of rows to process (for testing)")
    
    args = parser.parse_args()
    
    main(
        args.bkpf, 
        args.bseg, 
        args.lfa1, 
        args.output, 
        args.threshold,
        args.min_amount,
        args.limit_rows
    ) 