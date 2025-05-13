# filepath: backend/utils.py
import json
import uuid
from datetime import datetime
import pandas as pd
import numpy as np

def custom_json_serializer(obj):
    if isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    if isinstance(obj, (np.integer, np.floating, np.bool_)):
        return obj.item()
    if pd.isna(obj) or obj is None:
        return None
    if isinstance(obj, list) and all(isinstance(item, str) for item in obj): # For keyFactors
        return obj
    raise TypeError(f"Type {type(obj)} not serializable: {obj}")

def map_invoice_data_to_json(row, prefix):
    doc_no = row.get(f'{prefix}_DOC_NO')
    doc_no_str = str(doc_no) if pd.notna(doc_no) else None

    # Handle NaN for numeric and string fields appropriately
    amount = row.get(f'{prefix}_AMOUNT')
    amount_float = float(amount) if pd.notna(amount) else None
    
    vendor_id = row.get(f'{prefix}_VENDOR_ID')
    vendor_id_str = str(vendor_id) if pd.notna(vendor_id) and str(vendor_id).lower() != 'nan' else None

    vendor_name = row.get(f'{prefix}_VENDOR_NAME')
    vendor_name_str = str(vendor_name) if pd.notna(vendor_name) else None
    
    description = row.get(f'{prefix}_DESCRIPTION')
    description_str = str(description) if pd.notna(description) else ""

    currency = row.get(f'{prefix}_CURRENCY')
    currency_str = str(currency) if pd.notna(currency) else None
    
    company_code = row.get(f'{prefix}_COMPANY_CODE')
    company_code_str = str(company_code) if pd.notna(company_code) else None

    return {
        "number": doc_no_str,
        "amount": amount_float,
        "currency": currency_str,
        "documentType": "AB", # Default, as not in SBERT output
        "companyCode": company_code_str,
        "vendorNumber": vendor_id_str,
        "vendorName": vendor_name_str,
        "postingText": description_str,
        "debitCreditIndicator": "H", # Default, as not in SBERT output
        "sapLink": f"sap-link://doc/{doc_no_str}" if doc_no_str else None
    }

def format_output_json(processed_df, project_id, project_name, project_description):
    pairs_list = []
    for _, row in processed_df.iterrows():
        doc1_data = map_invoice_data_to_json(row, "INV1")
        doc2_data = map_invoice_data_to_json(row, "INV2")

        amount_diff = None
        if doc1_data["amount"] is not None and doc2_data["amount"] is not None:
            amount_diff = abs(doc1_data["amount"] - doc2_data["amount"])

        pair_data = {
            "id": str(uuid.uuid4()),
            "score": float(row.get('similarity', 0.0)) if pd.notna(row.get('similarity')) else 0.0,
            "status": "pending",
            "doc1": doc1_data,
            "doc2": doc2_data,
            "amountDiff": amount_diff,
            "reviewedBy": None,
            "reviewedAt": None,
            "reviewNotes": "",
            "llmAnalysis": {
                "classification": row.get('llm_classification', 'N/A'),
                "explanation": row.get('llm_explanation', 'N/A'),
                "keyFactors": row.get('llm_key_factors', []),
                # "duplicationProbability": 0.94, # Example field, LLM could provide this
                # "recommendedAction": "mark_as_duplicate" # Example field
            }
        }
        pairs_list.append(pair_data)

    return {
        "project": {
            "id": project_id,
            "name": project_name,
            "description": project_description,
            "createdAt": datetime.now().isoformat(),
            "lastUpdated": datetime.now().isoformat(),
            "totalPairs": len(pairs_list),
            "reviewedPairs": 0
        },
        "pairs": pairs_list
    }
