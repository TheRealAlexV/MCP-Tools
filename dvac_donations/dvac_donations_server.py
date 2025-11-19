"""
### Recommended Prompt

I need you to extract donation data from a directory of PDF files using the `dvac_donations` MCP server.

1.  **Source Directory:** `[INSERT PATH TO DIRECTORY CONTAINING PDFS]`
    *   **IMPORTANT:** Use Get-ChildItem and Select-Object to get a list of all files in the directory.
2.  **Action:** Use the `extract_and_parse_donations` tool to process all PDF files in that directory.
    *   **IMPORTANT:** Process the files in batches of **5 PDFs at a time** to avoid MCP timeout limits.
    *   Wait for each batch to complete before sending the next one.
3.  **Output:** After all batches are processed, combine the results into a single list and use the `save_results_to_csv` tool to save the data to `[INSERT DESIRED CSV FILENAME]`.
    *   **IMPORTANT:** The `save_results_to_csv` tool handles the CSV creation. Do NOT attempt to write a script or create the file manually.
4.  **IMPORTANT:** Do not create or use any helper scripts (Python, Bash, PowerShell, etc.) for ANY part of this process. You are only to use direct LLM calls and MCP calls to the specified MCP server.

"""

from mcp.server.fastmcp import FastMCP
from pdf2image import convert_from_path
from PIL import Image
import io
import os
import base64
import sys
import json
import re
import csv
from typing import List, Dict, Any
import mcp.types as types
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize MCP
mcp = FastMCP("dvac_donations")

# Poppler Path (Update if different)
POPPLER_PATH = r"C:\poppler-25.11.0\Library\bin"

# API Configuration
def get_openrouter_client():
    """Initialize OpenAI client for OpenRouter with API key from environment."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

def convert_pdf_to_images(file_path: str, max_pages: int = 1) -> List[bytes]:
    """
    Convert a PDF file to a list of optimized JPEG image bytes.
    Args:
        file_path: Path to the PDF file
        max_pages: Maximum number of pages to process (default: 1)
    Returns:
        List of JPEG image bytes, one for each page
    """
    sys.stderr.write(f"DEBUG: Starting conversion for {file_path} with max_pages={max_pages}\n")
    
    try:
        # Convert PDF to images with a reasonable DPI, limiting pages at source
        # dpi=150 is often sufficient for OCR and faster than 200
        images = convert_from_path(file_path, poppler_path=POPPLER_PATH, dpi=150, last_page=max_pages)
        sys.stderr.write(f"DEBUG: Converted {len(images)} pages from PDF\n")
        
        image_bytes_list = []
        
        for i, img in enumerate(images):
            # Resize image to reduce payload size (target width: 1000px)
            target_width = 1000
            if img.width > target_width:
                ratio = target_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to grayscale to reduce file size
            img = img.convert('L')
            
            # Save as JPEG with aggressive quality setting to reduce payload
            img_byte_arr = io.BytesIO()
            # Quality 50 is usually readable for OCR but much smaller
            img.save(img_byte_arr, format='JPEG', quality=50, optimize=True)
            size_kb = len(img_byte_arr.getvalue()) / 1024
            sys.stderr.write(f"DEBUG: Processed page {i+1}, size: {size_kb:.2f} KB\n")
            image_bytes_list.append(img_byte_arr.getvalue())
        
        return image_bytes_list
    except Exception as e:
        sys.stderr.write(f"DEBUG: Error in convert_pdf_to_images: {str(e)}\n")
        raise e

@mcp.tool()
def extract_and_parse_donations(file_paths: List[str], max_pages: int = 1) -> str:
    """
    Extract donation data from PDF files using OpenRouter (Gemini) Vision API.
    Converts PDFs to images and uses AI vision to extract structured donation data.
    
    Args:
        file_paths: List of absolute paths to the PDF files.
        max_pages: Maximum number of pages to process per file (default: 1).
    
    Returns:
        JSON string containing extracted donation data with fields:
        - filename: Name of the PDF file
        - name: Donor name(s)
        - address: Donor address
        - amount: Donation amount
        - date: Donation date
    """
    sys.stderr.write(f"DEBUG: extract_and_parse_donations called with {len(file_paths)} files\n")
    
    if len(file_paths) > 5:
        return json.dumps({"error": "Too many files. Please process a maximum of 5 files at a time to avoid timeouts."})

    try:
        client = get_openrouter_client()
    except ValueError as e:
        return json.dumps({"error": str(e)})
    
    all_results = []
    
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        sys.stderr.write(f"DEBUG: Processing {filename}\n")
        
        try:
            # Convert PDF to images
            image_bytes_list = convert_pdf_to_images(file_path, max_pages=max_pages)
            
            if not image_bytes_list:
                all_results.append({
                    "filename": filename,
                    "error": "No images generated from PDF"
                })
                continue
            
            # Prepare content for OpenRouter/OpenAI format
            content_parts = []
            
            # Add prompt text
            prompt = """You are a highly accurate data extraction assistant. Your task is to extract specific donation details from the provided document image.

**FIELDS TO EXTRACT:**

1.  **Donor Name:**
    *   Locate the donor's name, typically found in the top section or on a check.
    *   **Exclude** organization names (e.g., "Ambulance Corps"), headers, or form labels.
    *   If multiple names are present (e.g., "John & Jane Doe"), include both.

2.  **Address:**
    *   Extract the full mailing address (Street, City, State, Zip).
    *   **CRITICAL:** The address MUST be a single line string. Replace any line breaks with a comma and a space (e.g., "123 Main St, Anytown, NY 12345").

3.  **Amount:**
    *   Extract the donation amount in USD.
    *   Look for the '$' symbol, "DOLLARS", or "AMOUNT" labels.
    *   **Format:** Return as a decimal string (e.g., "25.00").
    *   **Correction:** If you see a large integer like "2500" that clearly represents $25.00, convert it to "25.00".

4.  **Date:**
    *   Extract the date of the donation.
    *   **Format:** Convert to MM/DD/YYYY format (e.g., 11/06/2025).

**OUTPUT FORMAT:**

Return **ONLY** a valid JSON object with the following structure. Do not include markdown formatting (like ```json) or any other text.

{
  "name": "extracted name or null",
  "address": "single line address string or null",
  "amount": "decimal string or null",
  "date": "MM/DD/YYYY or null"
}"""

            content_parts.append({"type": "text", "text": prompt})

            # Add images
            for img_bytes in image_bytes_list:
                base64_image = base64.b64encode(img_bytes).decode('utf-8')
                content_parts.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                })
            
            # Call OpenRouter API
            sys.stderr.write(f"DEBUG: Calling OpenRouter API for {filename}...\n")
            # Using google/gemini-2.5-flash as requested
            response = client.chat.completions.create(
                model="google/gemini-2.5-flash",
                messages=[
                    {
                        "role": "user",
                        "content": content_parts
                    }
                ],
                max_tokens=1024,
                temperature=0.1 # Low temperature for more deterministic extraction
            )
            
            sys.stderr.write(f"DEBUG: Full API response: {response}\n")
            
            # Parse response
            if response.choices and response.choices[0].message.content:
                response_text = response.choices[0].message.content.strip()
                sys.stderr.write(f"DEBUG: API response text for {filename}: {response_text}\n")
            else:
                response_text = ""
                sys.stderr.write(f"DEBUG: Empty response content for {filename}\n")
            sys.stderr.write(f"DEBUG: Claude response for {filename}: {response_text}\n")
            
            # Extract JSON from response (handle cases where there might be extra text)
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text)
            if json_match:
                extracted_data = json.loads(json_match.group())
                extracted_data['filename'] = filename
                
                # Post-processing: Ensure address is single line
                if extracted_data.get('address'):
                    extracted_data['address'] = extracted_data['address'].replace('\n', ', ').replace('\r', '')
                    
                all_results.append(extracted_data)
            else:
                all_results.append({
                    "filename": filename,
                    "error": "Could not parse JSON from API response",
                    "raw_response": response_text
                })
                
        except Exception as e:
            sys.stderr.write(f"DEBUG: Error processing {filename}: {str(e)}\n")
            all_results.append({
                "filename": filename,
                "error": str(e)
            })
    
    sys.stderr.write("DEBUG: extract_and_parse_donations finished\n")
    return json.dumps(all_results, indent=2)

@mcp.tool()
def save_results_to_csv(data: List[Dict[str, Any]], output_file: str) -> str:
    """
    Save extracted donation data to a CSV file.
    
    Args:
        data: List of donation dictionaries (from extract_and_parse_donations)
        output_file: Absolute path to the output CSV file
        
    Returns:
        Success message or error string
    """
    sys.stderr.write(f"DEBUG: save_results_to_csv called with {len(data)} records for {output_file}\n")
    
    try:
        if not data:
            return "No data to save."
        
        # Ensure directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        fieldnames = ["filename", "name", "address", "amount", "date"]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                # Filter row to only include known fields and ensure address is single line
                filtered_row = {}
                for k in fieldnames:
                    val = row.get(k, '')
                    if k == 'address' and isinstance(val, str):
                        val = val.replace('\n', ', ').replace('\r', '')
                    filtered_row[k] = val
                writer.writerow(filtered_row)
                
        return f"Successfully saved {len(data)} records to {output_file}"
    except Exception as e:
        sys.stderr.write(f"DEBUG: Error saving CSV: {str(e)}\n")
        return f"Error saving CSV: {str(e)}"


if __name__ == "__main__":
    mcp.run()
