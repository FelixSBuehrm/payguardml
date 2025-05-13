# filepath: backend/llm_classifier.py
import os
import time
import json
import pandas as pd
import sys
import re
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

GEMINI_API_KEY_ENV = os.getenv("GEMINI_API_KEY")  # Renamed to avoid conflict

def log_message(message, message_type="INFO"):
    """
    Log a message to both stdout and stderr if it's an error
    to ensure visibility in both UI and terminal.
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] [{message_type}] {message}"
    
    print(formatted_message, flush=True)
    if message_type == "ERROR":
        print(formatted_message, file=sys.stderr, flush=True)
    
    # For progress updates, add a special marker for the UI
    if message_type == "PROGRESS":
        print(f"PROGRESS:{message}", flush=True)

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

def extract_retry_delay(error_message):
    """Extract retry_delay value from the API error message."""
    try:
        match = re.search(r'retry_delay\s*{\s*seconds:\s*(\d+)\s*}', error_message)
        if match:
            return int(match.group(1))
        return 60  # Default retry delay if not found
    except Exception:
        return 60  # Default retry delay if there's any error

def call_gemini_api(prompt_text, genai_model_instance, item_num=None, total_items=None):  # Added item tracking
    if not genai_model_instance:  # Check passed instance
        return {"classification": "Skipped", "explanation": "API key not configured or model not initialized", "keyFactors": []}
    try:
        # Add real-time logging of the API call with more specific steps
        if item_num and total_items:
            log_message(f"Calling Gemini API for item {item_num}/{total_items}...", "INFO")
            # Add a specific PROGRESS marker for individual item start
            print(f"PROGRESS:LLM_ITEM_START:{item_num}:{total_items}", flush=True)
        
        # Flush stdout to ensure logs appear immediately
        sys.stdout.flush()
        
        # Log the prompt preparation
        log_message(f"Preparing prompt for item {item_num}/{total_items}", "INFO")
        sys.stdout.flush()
        
        # Make the API call with timing information
        start_time = time.time()
        log_message(f"Sending request to Gemini API...", "INFO")
        sys.stdout.flush()
        
        response = genai_model_instance.generate_content(prompt_text)  # Use passed instance
        
        # Log the API call timing
        elapsed_time = time.time() - start_time
        log_message(f"Gemini API response received in {elapsed_time:.2f} seconds", "INFO")
        sys.stdout.flush()
        
        response_text = response.text.strip()
        
        # Log the response receipt
        if item_num and total_items:
            log_message(f"Processing response for item {item_num}/{total_items}", "INFO")
            sys.stdout.flush()
            
        # Robust JSON extraction
        json_match = response_text[response_text.find('{'):response_text.rfind('}')+1]
        if json_match:
            result = json.loads(json_match)
            # Log a summary of the classification
            classification = result.get("classification", "Unknown")
            log_message(f"Item {item_num}/{total_items}: Classified as '{classification}'", "INFO")
            
            # Add a specific PROGRESS marker for individual item completion
            print(f"PROGRESS:LLM_ITEM_END:{item_num}:{total_items}:{classification}", flush=True)
            sys.stdout.flush()
            return result
        else:
            log_message(f"Warning: Could not parse JSON from LLM response: {response_text}", "WARNING")
            # Add an error progress marker
            print(f"PROGRESS:LLM_ITEM_ERROR:{item_num}:{total_items}", flush=True)
            sys.stdout.flush()
            return {"classification": "Error", "explanation": "LLM response parsing failed", "keyFactors": []}
    except Exception as e:
        error_message = str(e)
        log_message(f"Error calling Gemini API: {e}", "ERROR")
        
        # Handle rate limit errors (HTTP 429)
        if "429" in error_message:
            retry_delay = extract_retry_delay(error_message)
            log_message(f"Rate limit exceeded. API suggests retry in {retry_delay} seconds.", "WARNING")
            # Return a more specific rate limit error with the actual delay value
            error_result = {
                "classification": "Error", 
                "explanation": f"API call error: 429 You exceeded your current quota, please check your plan and billing details.", 
                "keyFactors": [],
                "retry_delay": retry_delay  # Add the retry delay to the result
            }
            print(f"PROGRESS:LLM_ITEM_ERROR:{item_num}:{total_items}", flush=True)
            sys.stdout.flush()
            return error_result
        
        print(f"PROGRESS:LLM_ITEM_ERROR:{item_num}:{total_items}", flush=True)
        sys.stdout.flush()
        return {"classification": "Error", "explanation": f"API call error: {error_message}", "keyFactors": []}

def classify_pairs_with_llm(scored_pairs_df, api_key=None, batch_size=2, delay_between_calls=4, delay_between_batches=10):  # Process 2 invoices at once
    # Reduced to 15 requests per minute (4 second delay = ~15 messages/minute)
    current_api_key = api_key if api_key else GEMINI_API_KEY_ENV
    genai_model_instance = None  # Initialize instance

    if not current_api_key:
        log_message("Warning: Gemini API Key not provided via argument or .env file. LLM classification will be skipped.", "WARNING")
    else:
        try:
            log_message("Configuring Gemini API...", "INFO")
            sys.stdout.flush()
            
            genai.configure(api_key=current_api_key)
            generation_config = {"temperature": 0.7, "top_p": 1, "top_k": 1, "max_output_tokens": 1024}
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            ]
            genai_model_instance = genai.GenerativeModel(model_name="gemini-1.5-flash",
                                                  generation_config=generation_config,
                                                  safety_settings=safety_settings)
            log_message("Gemini API configured successfully.", "INFO")
            sys.stdout.flush()
        except Exception as e:
            log_message(f"Error configuring Gemini API: {e}. LLM classification will be skipped.", "ERROR")
            sys.stdout.flush()
            # genai_model_instance remains None

    if not genai_model_instance:  # Check if instance was created
        log_message("Skipping LLM classification as API key is not configured or model initialization failed.", "WARNING")
        output_df = scored_pairs_df.copy()
        output_df['llm_classification'] = "Skipped"
        output_df['llm_explanation'] = "API key not configured or model initialization failed"
        output_df['llm_key_factors'] = [[] for _ in range(len(output_df))]
        return output_df

    results = []
    num_rows = len(scored_pairs_df)
    log_message(f"Starting LLM classification for {num_rows} invoice pairs", "INFO")
    sys.stdout.flush()
    
    # Print overall LLM process start
    print(f"PROGRESS:LLM_TOTAL_ITEMS:{num_rows}", flush=True)
    
    for i in range(0, num_rows, batch_size):
        batch_df = scored_pairs_df.iloc[i:i+batch_size]
        current_batch_number = i//batch_size + 1
        total_batches = (num_rows + batch_size -1)//batch_size
        
        # PROGRESS: LLM Batch with more detailed information
        print(f"PROGRESS:LLM_BATCH_START:{current_batch_number}:{total_batches}:{i+1}:{min(i+batch_size, num_rows)}:{num_rows}", flush=True)
        log_message(f"LLM Processing batch {current_batch_number}/{total_batches} (items {i+1}-{min(i+batch_size, num_rows)} of {num_rows})", "INFO")
        sys.stdout.flush()
        
        batch_results = []
        batch_start_time = time.time()
        
        for idx, (index, row) in enumerate(batch_df.iterrows()):
            item_num = i + idx + 1
            prompt = generate_llm_prompt(row)
            log_message(f"Processing item {item_num}/{num_rows} in batch {current_batch_number}", "INFO")
            sys.stdout.flush()
            
            # Process the item with added detail
            api_result = call_gemini_api(prompt, genai_model_instance, item_num, num_rows)  # Pass instance
            batch_results.append(api_result)
            
            # Check if we hit a rate limit and need to adjust our delay
            current_delay = delay_between_calls
            if "retry_delay" in api_result:
                # We hit a rate limit, use the suggested retry delay from the API
                current_delay = api_result["retry_delay"]
                log_message(f"Rate limit hit: Using API suggested delay of {current_delay}s for next request", "WARNING")
            
            # Rate limiting with feedback
            if idx < len(batch_df) - 1 and genai_model_instance and current_delay > 0:
                log_message(f"Rate limiting: waiting {current_delay}s before next API call...", "INFO")
                sys.stdout.flush()
                time.sleep(current_delay)  # Use the current_delay (either default or from API)
        
        results.extend(batch_results)
        
        # Batch completion timing and progress update
        batch_elapsed_time = time.time() - batch_start_time
        log_message(f"Batch {current_batch_number}/{total_batches} completed in {batch_elapsed_time:.2f} seconds", "INFO")
        sys.stdout.flush()
        
        # Progress update after batch completion with more detailed information
        print(f"PROGRESS:LLM_BATCH_END:{current_batch_number}:{total_batches}:{batch_elapsed_time:.2f}", flush=True)
        log_message(f"Completed batch {current_batch_number}/{total_batches}", "INFO")
        sys.stdout.flush()

        if i + batch_size < num_rows and genai_model_instance and delay_between_batches > 0:
            log_message(f"Waiting {delay_between_batches}s before next batch...", "INFO")
            sys.stdout.flush()
            time.sleep(delay_between_batches)
    
    output_df = scored_pairs_df.copy()
    output_df['llm_classification'] = [r.get("classification", "Error") for r in results]
    output_df['llm_explanation'] = [r.get("explanation", "N/A") for r in results]
    output_df['llm_key_factors'] = [r.get("keyFactors", []) for r in results]
    
    # Count classification results
    classification_counts = output_df['llm_classification'].value_counts().to_dict()
    log_message(f"LLM Classification complete. Results: {classification_counts}", "INFO")
    sys.stdout.flush()
    
    # PROGRESS: LLM End with classification counts
    print(f"PROGRESS:LLM_END:{json.dumps(classification_counts)}", flush=True)
    return output_df
