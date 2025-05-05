"""
Features for PayGuard ML Algorithm

This module outlines potential features to consider for the machine learning algorithm
that will determine the similarity between payment document pairs.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime

def extract_features(doc1: Dict[str, Any], doc2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract features from a pair of payment documents for use in the ML algorithm.
    
    Args:
        doc1: First payment document data
        doc2: Second payment document data
        
    Returns:
        Dict[str, Any]: Features dictionary
    """
    features = {}
    
    # 1. Amount-based features
    features['amount_diff'] = abs(abs(float(doc1.get('amount', 0))) - abs(float(doc2.get('amount', 0))))
    features['amount_ratio'] = safe_ratio(abs(float(doc1.get('amount', 0))), abs(float(doc2.get('amount', 0))))
    
    # Check if one amount is positive and one is negative (payment & invoice)
    amount1 = float(doc1.get('amount', 0))
    amount2 = float(doc2.get('amount', 0))
    features['is_opposite_sign'] = 1 if amount1 * amount2 < 0 else 0
    
    # 2. Document type features
    features['same_doc_type'] = 1 if doc1.get('document_type') == doc2.get('document_type') else 0
    
    # Check if one is an invoice (KR/KM) and one is a payment (ZP)
    doc1_type = doc1.get('document_type', '')
    doc2_type = doc2.get('document_type', '')
    features['is_invoice_payment_pair'] = 1 if ((doc1_type in ['KR', 'KM'] and doc2_type == 'ZP') or 
                                               (doc2_type in ['KR', 'KM'] and doc1_type == 'ZP')) else 0
    
    # 3. Vendor features
    features['same_vendor'] = 1 if doc1.get('vendor_number') == doc2.get('vendor_number') else 0
    features['same_vendor_name'] = string_similarity(str(doc1.get('vendor_name', '')), 
                                                    str(doc2.get('vendor_name', '')))
    
    # 4. Reference features
    features['same_reference'] = 1 if doc1.get('reference') == doc2.get('reference') else 0
    features['same_assignment'] = 1 if doc1.get('assignment_nr') == doc2.get('assignment_nr') else 0
    
    # 5. Date-based features
    # Days between document dates
    doc1_date = parse_date(doc1.get('document_date', ''))
    doc2_date = parse_date(doc2.get('document_date', ''))
    features['days_between_doc_dates'] = date_difference_days(doc1_date, doc2_date)
    
    # Days between accounting dates
    doc1_acc_date = parse_date(doc1.get('accounting_date', ''))
    doc2_acc_date = parse_date(doc2.get('accounting_date', ''))
    features['days_between_acc_dates'] = date_difference_days(doc1_acc_date, doc2_acc_date)
    
    # 6. Company and cost center features
    features['same_company_code'] = 1 if doc1.get('company_code') == doc2.get('company_code') else 0
    features['same_cost_center'] = 1 if doc1.get('cost_center') == doc2.get('cost_center') else 0
    
    # 7. Purchasing document features
    features['same_purchasing_doc'] = 1 if doc1.get('purchasing_doc') == doc2.get('purchasing_doc') else 0
    
    # 8. Text similarity features
    features['posting_text_similarity'] = string_similarity(str(doc1.get('posting_text', '')), 
                                                           str(doc2.get('posting_text', '')))
    features['position_text_similarity'] = string_similarity(str(doc1.get('position_text', '')), 
                                                            str(doc2.get('position_text', '')))
    
    # 9. Currency features
    features['same_currency'] = 1 if doc1.get('currency') == doc2.get('currency') else 0
    
    # 10. Clearing document features
    features['same_clearing_doc'] = 1 if (doc1.get('clearing_doc') and 
                                         doc1.get('clearing_doc') == doc2.get('clearing_doc')) else 0
    
    return features

def safe_ratio(a: float, b: float) -> float:
    """
    Calculate ratio safely handling division by zero
    """
    if b == 0 or a == 0:
        return 0
    if a >= b:
        return a / b
    else:
        return b / a

def string_similarity(str1: str, str2: str) -> float:
    """
    Calculate simple string similarity (0-1)
    """
    if not str1 or not str2:
        return 0
    
    # Convert to lowercase and remove spaces
    str1 = str1.lower().strip()
    str2 = str2.lower().strip()
    
    if str1 == str2:
        return 1.0
    
    # Simple Jaccard similarity
    set1 = set(str1.split())
    set2 = set(str2.split())
    
    if not set1 or not set2:
        return 0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0

def parse_date(date_str: str) -> datetime:
    """
    Parse date string to datetime object
    """
    if not date_str:
        return None
    
    try:
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y']:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    except Exception:
        pass
    
    return None

def date_difference_days(date1: datetime, date2: datetime) -> int:
    """
    Calculate difference between dates in days
    """
    if date1 is None or date2 is None:
        return -1  # Indicate missing date
    
    try:
        delta = abs((date1 - date2).days)
        return delta
    except Exception:
        return -1

def feature_importance_analysis():
    """
    Placeholder for feature importance analysis.
    This would analyze which features are most important for determining matches.
    """
    important_features = [
        'amount_diff',
        'is_opposite_sign',
        'same_vendor',
        'same_reference',
        'same_assignment',
        'days_between_doc_dates',
        'same_company_code',
        'same_currency'
    ]
    
    return important_features

def recommended_features_for_ml():
    """
    Returns the recommended subset of features to use for the ML model
    """
    return [
        # Primary indicators
        'amount_diff',
        'is_opposite_sign',
        'same_vendor',
        'same_reference',
        'same_assignment',
        'days_between_doc_dates',
        
        # Secondary indicators
        'same_company_code',
        'same_currency',
        'is_invoice_payment_pair',
        'same_purchasing_doc',
        'posting_text_similarity',
        
        # Tertiary indicators
        'same_cost_center',
        'vendor_name_similarity',
        'position_text_similarity',
        'days_between_acc_dates'
    ] 