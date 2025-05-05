"""
PayGuard LLM Analysis Module

This module adds LLM-based analysis to payment pairs to identify duplicate payments.
It includes both mock responses (for development) and real Gemini API integration (for production).
"""

import json
import random
import pandas as pd
from typing import Dict, Any, List, Optional

# Set to True to use the real Gemini API, False to use mock responses
USE_REAL_LLM = False

# Mock LLM sample responses for different scenarios
MOCK_RESPONSES = {
    "high_confidence_duplicate": {
        "explanation": "These documents appear to be duplicate payments for the same invoice. Both have identical amounts, the same vendor, and were processed within a short time period. The document numbers differ but this often happens when a payment is accidentally processed twice.",
        "duplicationProbability": 0.94,
        "keyFactors": ["identical amounts", "same vendor", "close timing", "similar document types"],
        "recommendedAction": "mark_as_duplicate"
    },
    "possible_duplicate": {
        "explanation": "These documents have similar but not identical amounts and share the same vendor. The small difference in amounts could be due to partial payments or adjustments, but the timing and other factors suggest these may be related transactions that should be reviewed.",
        "duplicationProbability": 0.68,
        "keyFactors": ["similar amounts", "same vendor", "suspicious timing"],
        "recommendedAction": "needs_review"
    },
    "likely_legitimate": {
        "explanation": "While these documents share some similarities, they appear to be legitimate separate payments. They have different amounts, different document types, and the timing suggests normal business operations rather than duplicate processing.",
        "duplicationProbability": 0.12,
        "keyFactors": ["different amounts", "different purpose", "normal timing"],
        "recommendedAction": "likely_legitimate"
    },
    "review_needed": {
        "explanation": "These transactions have some suspicious elements that warrant further investigation. The vendor information is missing and the amounts are identical, which could indicate a duplicate payment. However, the different document types suggest different purposes.",
        "duplicationProbability": 0.51,
        "keyFactors": ["identical amounts", "missing vendor information", "different document types"],
        "recommendedAction": "needs_review"
    }
}

def get_mock_response(doc1: Dict[str, Any], doc2: Dict[str, Any], amount_diff: float) -> Dict[str, Any]:
    """Generate a mock LLM analysis based on document characteristics"""
    
    # Determine which mock response to use based on document attributes
    if doc1.get('amount') == doc2.get('amount') and doc1.get('vendor_number') == doc2.get('vendor_number'):
        # Same amount, same vendor - likely duplicate
        response_type = "high_confidence_duplicate"
    elif amount_diff < 10 and doc1.get('vendor_number') == doc2.get('vendor_number'):
        # Similar amount, same vendor - possible duplicate
        response_type = "possible_duplicate"
    elif not doc1.get('vendor_number') or not doc2.get('vendor_number'):
        # Missing vendor info - needs review
        response_type = "review_needed"
    else:
        # Different details - likely legitimate
        response_type = "likely_legitimate"
    
    # Sometimes randomize to add variety
    if random.random() < 0.2:
        # 20% chance to pick a different response for more variety
        response_options = list(MOCK_RESPONSES.keys())
        response_options.remove(response_type)
        response_type = random.choice(response_options)
    
    # Return a copy of the mock response to avoid modifying the original
    return MOCK_RESPONSES[response_type].copy()

def analyze_pair_with_gemini(doc1: Dict[str, Any], doc2: Dict[str, Any], amount_diff: float) -> Dict[str, Any]:
    """Call Gemini API to analyze a document pair (placeholder implementation)"""
    if not USE_REAL_LLM:
        return get_mock_response(doc1, doc2, amount_diff)
    
    # This is where you would add the real Gemini API call
    # For now, this just returns a mock response even when USE_REAL_LLM is True
    
    try:
        # Uncomment this code when you're ready to use the real API
        """
        from google.generativeai import GenerativeModel
        
        model = GenerativeModel('gemini-pro')
        
        prompt = f'''
        Analyze these two financial documents for potential duplicate payment:
        
        DOCUMENT 1:
        - Document Number: {doc1.get('document_number', 'Unknown')}
        - Amount: {doc1.get('amount', 'Unknown')} {doc1.get('currency', 'Unknown')}
        - Document Type: {doc1.get('document_type', 'Unknown')}
        - Vendor: {doc1.get('vendor_name', 'Unknown')} ({doc1.get('vendor_number', 'Unknown')})
        - Company Code: {doc1.get('company_code', 'Unknown')}
        - Posting Text: {doc1.get('posting_text', 'N/A')}
        
        DOCUMENT 2:
        - Document Number: {doc2.get('document_number', 'Unknown')}
        - Amount: {doc2.get('amount', 'Unknown')} {doc2.get('currency', 'Unknown')}
        - Document Type: {doc2.get('document_type', 'Unknown')}
        - Vendor: {doc2.get('vendor_name', 'Unknown')} ({doc2.get('vendor_number', 'Unknown')})
        - Company Code: {doc2.get('company_code', 'Unknown')}
        - Posting Text: {doc2.get('posting_text', 'N/A')}
        
        Amount Difference: {amount_diff}
        
        Analyze the likelihood these are duplicate payments. Provide:
        1. A brief explanation of your assessment
        2. A duplication probability score between 0.0 and 1.0
        3. Key factors supporting your conclusion
        4. Recommended action (mark_as_duplicate, needs_review, or likely_legitimate)
        
        Format as JSON object.
        '''
        
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        return result
        """
        
        # Remove this line when implementing the real API call
        return get_mock_response(doc1, doc2, amount_diff)
        
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return {
            "explanation": "Failed to analyze with LLM API",
            "duplicationProbability": 0.5,
            "keyFactors": ["analysis error"],
            "recommendedAction": "needs_review"
        }

def add_llm_analysis_to_pairs(pairs_df: pd.DataFrame) -> pd.DataFrame:
    """Process all pairs in the dataframe and add LLM analysis"""
    
    results_df = pairs_df.copy()
    results_df['llm_analysis'] = None
    
    print(f"Adding LLM analysis for {len(pairs_df)} document pairs...")
    
    # Process each pair
    for idx, row in pairs_df.iterrows():
        # Create doc1 and doc2 dictionaries
        doc1 = {col[5:]: row[col] for col in row.index if col.startswith('doc1_')}
        doc2 = {col[5:]: row[col] for col in row.index if col.startswith('doc2_')}
        
        # Add document numbers (stored differently)
        doc1['document_number'] = row['doc1_number']
        doc2['document_number'] = row['doc2_number']
        
        # Call LLM (or mock)
        amount_diff = row.get('amount_diff', 0)
        analysis_result = analyze_pair_with_gemini(doc1, doc2, amount_diff)
        
        # Store result as JSON string
        results_df.at[idx, 'llm_analysis'] = json.dumps(analysis_result)
        
        # Print progress
        if idx % 100 == 0:
            print(f"Processed {idx}/{len(pairs_df)} pairs...")
    
    print(f"LLM analysis complete. {'Used mock responses.' if not USE_REAL_LLM else 'Used real Gemini API.'}")
    return results_df

def export_pairs_with_analysis_to_json(pairs_df: pd.DataFrame, output_path: str) -> None:
    """Export the pairs with LLM analysis to a JSON structure suitable for the web app"""
    
    # Create the project information
    project_data = {
        "project": {
            "id": "sample-project-1",
            "name": "Sample Project Advanced ML",
            "description": "SAP payment pairs analysis using machine learning",
            "createdAt": pd.Timestamp.now().isoformat(),
            "lastUpdated": pd.Timestamp.now().isoformat(),
            "totalPairs": len(pairs_df),
            "reviewedPairs": 0
        },
        "pairs": []
    }
    
    # Process each pair
    for idx, row in pairs_df.iterrows():
        # Parse the LLM analysis
        llm_analysis = {}
        if row.get('llm_analysis'):
            try:
                llm_analysis = json.loads(row['llm_analysis'])
            except:
                llm_analysis = MOCK_RESPONSES["review_needed"].copy()
        
        # Create the pair object
        pair_data = {
            "id": row.get("pair_id", f"pair-{idx}"),
            "score": float(row.get("score", 0)),
            "status": "pending",
            "doc1": {
                "number": row.get("doc1_number", ""),
                "amount": float(row.get("doc1_amount", 0)),
                "currency": row.get("doc1_currency", ""),
                "documentType": row.get("doc1_document_type", ""),
                "companyCode": row.get("doc1_company_code", ""),
                "vendorNumber": row.get("doc1_vendor_number", ""),
                "vendorName": row.get("doc1_vendor_name", ""),
                "postingText": row.get("doc1_posting_text", ""),
                "debitCreditIndicator": row.get("doc1_debit_credit_indicator", ""),
                "sapLink": f"sap-link://doc/{row.get('doc1_number', '')}"
            },
            "doc2": {
                "number": row.get("doc2_number", ""),
                "amount": float(row.get("doc2_amount", 0)),
                "currency": row.get("doc2_currency", ""),
                "documentType": row.get("doc2_document_type", ""),
                "companyCode": row.get("doc2_company_code", ""),
                "vendorNumber": row.get("doc2_vendor_number", ""),
                "vendorName": row.get("doc2_vendor_name", ""),
                "postingText": row.get("doc2_posting_text", ""),
                "debitCreditIndicator": row.get("doc2_debit_credit_indicator", ""),
                "sapLink": f"sap-link://doc/{row.get('doc2_number', '')}"
            },
            "amountDiff": float(row.get("amount_diff", 0)),
            "reviewedBy": None,
            "reviewedAt": None,
            "reviewNotes": "",
            "llmAnalysis": llm_analysis
        }
        
        # Add to the pairs array
        project_data["pairs"].append(pair_data)
    
    # Write to JSON file
    with open(output_path, 'w') as f:
        json.dump(project_data, f, indent=2)
    
    print(f"Exported {len(pairs_df)} pairs with LLM analysis to {output_path}")

if __name__ == "__main__":
    # Test the module with a sample pair
    doc1 = {"document_number": "1000001", "amount": 1000.0, "vendor_number": "V123"}
    doc2 = {"document_number": "1000002", "amount": 1000.0, "vendor_number": "V123"}
    
    analysis = analyze_pair_with_gemini(doc1, doc2, 0.0)
    print(json.dumps(analysis, indent=2)) 