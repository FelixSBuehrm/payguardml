# filepath: backend/llm_classifier.py
import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in .env file. LLM classification will be skipped.")
    genai_model = None
else:
    genai.configure(api_key=GEMINI_API_KEY)
    generation_config = {"temperature": 0.7, "top_p": 1, "top_k": 1, "max_output_tokens": 1024}
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    genai_model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                                  generation_config=generation_config,
                                  safety_settings=safety_settings)

def format_invoice_details_for_llm(invoice_prefix, row):
    details = [
        f"Document Number: {row.get(f'{invoice_prefix}_DOC_NO', 'N/A')}",
        f"Vendor Name: {row.get(f'{invoice_prefix}_VENDOR_NAME', 'N/A')}",
        f"Vendor ID: {row.get(f'{invoice_prefix}_VENDOR_ID', 'N/A')}",
        f"Amount: {row.get(f'{invoice_prefix}_AMOUNT', 'N/A')} {row.get(f'{invoice_prefix}_CURRENCY', '')}",
        f"Invoice Date: {pd.to_datetime(row.get(f'{invoice_prefix}_INVOICE_DATE')).strftime('%Y-%m-%d') if pd.notna(row.get(f'{invoice_prefix}_INVOICE_DATE')) else 'N/A'}",
        f"Description: {row.get(f'{invoice_prefix}_DESCRIPTION', 'N/A')}",
        f"Purchase Order: {row.get(f'{invoice_prefix}_PURCHASE_ORDER', 'N/A')}",
        f"Company Code: {row.get(f'{invoice_prefix}_COMPANY_CODE', 'N/A')}"
    ]
    return "\n".join(details)

def generate_llm_prompt(row):
    invoice1_details = format_invoice_details_for_llm("INV1", row)
    invoice2_details = format_invoice_details_for_llm("INV2", row)
    similarity_score = row.get('similarity', 'N/A')

    return f"""
Analyze the following pair of SAP invoices to determine the likelihood of them being duplicates.
SBERT similarity score: {similarity_score}.

Invoice 1:
{invoice1_details}

Invoice 2:
{invoice2_details}

Provide your analysis as a JSON object with keys "classification" (string: "Not likely", "Likely", or "Very likely"), "explanation" (string: brief reasoning), and "keyFactors" (list of 3-5 strings).
Example: {{"classification": "Likely", "explanation": "Amounts and vendor are identical, dates are close.", "keyFactors": ["identical amounts", "same vendor", "close invoice dates"]}}
JSON response:
"""

def call_gemini_api(prompt_text):
    if not genai_model:
        return {"classification": "Skipped", "explanation": "API key not configured", "keyFactors": []}
    try:
        response = genai_model.generate_content(prompt_text)
        response_text = response.text.strip()
        # Robust JSON extraction
        json_match = response_text[response_text.find('{'):response_text.rfind('}')+1]
        if json_match:
            return json.loads(json_match)
        else:
            print(f"Warning: Could not parse JSON from LLM response: {response_text}")
            return {"classification": "Error", "explanation": "LLM response parsing failed", "keyFactors": []}
    except Exception as e:
        print(f"Error calling Gemini API: {e}. Response: {response.text if 'response' in locals() else 'N/A'}")
        return {"classification": "Error", "explanation": str(e), "keyFactors": []}

def classify_pairs_with_llm(scored_pairs_df, batch_size=5, delay_between_calls=1, delay_between_batches=5):
    if not genai_model:
        print("Skipping LLM classification as API key is not configured.")
        output_df = scored_pairs_df.copy()
        output_df['llm_classification'] = "Skipped"
        output_df['llm_explanation'] = "API key not configured"
        output_df['llm_key_factors'] = [[] for _ in range(len(output_df))]
        return output_df

    results = []
    num_rows = len(scored_pairs_df)
    for i in range(0, num_rows, batch_size):
        batch_df = scored_pairs_df.iloc[i:i+batch_size]
        print(f"LLM Processing batch {i//batch_size + 1}/{(num_rows + batch_size -1)//batch_size}")
        
        batch_results = []
        for index, row in batch_df.iterrows():
            prompt = generate_llm_prompt(row)
            api_result = call_gemini_api(prompt)
            batch_results.append(api_result)
            if genai_model: time.sleep(delay_between_calls) # Rate limiting
        results.extend(batch_results)
        
        if i + batch_size < num_rows and genai_model:
            print(f"Waiting {delay_between_batches}s before next batch...")
            time.sleep(delay_between_batches)
    
    output_df = scored_pairs_df.copy()
    output_df['llm_classification'] = [r.get("classification", "Error") for r in results]
    output_df['llm_explanation'] = [r.get("explanation", "N/A") for r in results]
    output_df['llm_key_factors'] = [r.get("keyFactors", []) for r in results]
    return output_df
