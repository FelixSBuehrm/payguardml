# PayGuard for SAP - Payment Document Pair Analysis

A specialized tool for identifying matching payment documents in SAP ERP financial accounting data.

## Overview

PayGuard for SAP processes SAP financial accounting data (BKPF, BSEG, and LFA1 tables) to identify potential pairs of related documents, such as invoices and their corresponding payments. It generates all possible document pairs and assigns a similarity score to each pair using a scoring algorithm.

## Features

- Load and join SAP financial accounting tables (BKPF, BSEG, LFA1)
- Preprocess SAP data with proper handling of date formats, amounts, and document relationships
- Apply core filters to select relevant invoices for analysis
- Generate document pairs with comprehensive metadata
- Score document pairs based on similarity (placeholder for ML algorithm)
- Filter pairs based on score, amount differences, and sign relationships
- Export results to CSV or Excel

## SAP Tables Used

1. **BKPF** - Accounting Document Header
   - Contains document header information like document type, dates, and posting periods

2. **BSEG** - Accounting Document Segment
   - Contains line item details like amounts, accounts, vendors, and posting keys

3. **LFA1** - Vendor Master (optional)
   - Contains vendor information to enrich the document data

## Core Filters

PayGuard implements the following core filters to focus the analysis on relevant invoice documents:

1. **Amount Filter**: Only includes documents with amount ≥ 500 (in document currency)
   - Ignores tiny invoices where duplicate risk/impact is negligible
   - Uses BSEG.WRBTR or the summed amount after aggregation

2. **Document Type Filter**: Only includes invoice document types
   - Focuses on vendor invoices (FI manual, MM logistics) 
   - Includes document types: KR, RE, MR
   - Excludes payments, credit memos, reversals, etc.

3. **Debit Sign Filter**: Only keeps normal payable lines with debit sign
   - Uses BSEG.SHKZG == 'S' (debit indicator)
   - Drops credits ('H') to avoid matching an invoice against its own credit note

These filters can be enabled or disabled via the command line parameter `--no-core-filters`.

## Usage

### Command Line Interface

```bash
python payguard_sap.py --bkpf bkpf.csv --bseg bseg.csv --lfa1 lfa1.csv --output results.csv --threshold 0.5
```

Arguments:
- `--bkpf`: Path to BKPF table CSV (required)
- `--bseg`: Path to BSEG table CSV (required)
- `--lfa1`: Path to LFA1 table CSV (optional)
- `--output`: Path to save output file (default: sap_payment_pairs.csv)
- `--threshold`: Minimum similarity score threshold (default: 0.5)
- `--max-pairs`: Maximum number of pairs to generate (optional)
- `--max-amount-diff`: Maximum absolute difference in amounts (optional)
- `--limit-rows`: Limit the number of rows to process (for testing)
- `--no-core-filters`: Disable core invoice filters

### Example Script

See `sap_example.py` for a complete example of how to use the tool:

```python
from payguard_sap import load_sap_data, preprocess_sap_data, generate_payment_document_pairs, filter_pairs

# Load and join SAP data
merged_data = load_sap_data('bkpf.csv', 'bseg.csv', 'lfa1.csv')

# Preprocess the data
processed_df = preprocess_sap_data(merged_data)

# Generate document pairs (limit to 1000 for demo)
pairs_df = generate_payment_document_pairs(processed_df, max_pairs=1000)

# Filter pairs
filtered_pairs = filter_pairs(
    pairs_df, 
    threshold=0.7,
    max_amount_diff=10.0,
    require_opposite_sign=True
)

# Save results
filtered_pairs.to_csv('results.csv', index=False)
```

## Output Format

The output file contains one row for each document pair with:
- `pair_id`: Unique identifier for the pair
- `score`: Similarity score (higher = more likely a match)
- Fields from both documents (prefixed with doc1_ and doc2_)
- Calculated features like `amount_diff`, `is_opposite_sign`, `same_vendor`, etc.

## SAP-Specific Considerations

- Document amounts are interpreted based on posting keys (bschl) and debit/credit indicators (shkzg)
- Document types are considered (common SAP types like KR for vendor invoices, ZP for payments)
- SAP date formats (YYYYMMDD) are properly converted
- Document numbers are combined with company code and fiscal year for uniqueness

## Future Enhancements

- Implement ML algorithm for computing similarity scores
- Add more SAP-specific features for matching
- Add support for other SAP tables (BSIK, BSAK, etc.)
- Optimize for large SAP datasets
- Add visualizations for matching results 