import os
import re
import time
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from llama_cpp import Llama

# Path to your quantized Mistral GGUF model
model_path = "mistral-7b-instruct-v0.1.Q4_K_M.gguf copy"

# Instructions for each field
questions = {
    "Document Number": (
        "Extract the document number. It may also be referred to as invoice number, bill number, or reference number."
    ),
    "Document Date": (
        "Extract the date of the document. It may also appear as invoice date, issue date, or bill date."
    ),
    "Validity Till Date": (
        "Extract the date labeled “VALIDI UNTIL” or “VALID UNTIL” (or synonyms like “Expiry Date”, “Due Date”). "
        "The date will follow these labels and be in formats like D.MM.YYYY, DD/MM/YY, or DD-MM-YYYY. "
    ),
    "Document Currency": (
        "What currency is used in the document? "
        "It may be shown as currency symbol like ₹ or $ or currency name like INR, USD, or Rupees."
    ),
    "Document Value (Amount)": (
        "What is the total payable amount in the document? "
        "Look for terms like total amount, invoice total, net payable, or total due."
    ),
    "Document Subtype": (
        "Determine whether this is an import or export document. Consider if goods are being received or sent out."
    )
}

def clean_answer(label: str, text: str) -> str:
    """
    Strip out the core value from a verbose LLM answer, field by field.
    """
    # Document Number: alphanumeric codes
    if label == "Document Number":
        m = re.search(r'[\w\-\/]+', text)
        return m.group(0) if m else text.strip()

    # Document Date & Validity Till Date: date patterns
    if label in ["Document Date", "Validity Till Date"]:
        m = re.search(r'\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b', text)
        return m.group(0) if m else text.strip()

    # Document Currency: symbols, codes, or names → normalized
    if label == "Document Currency":
        m = re.search(
            r'\b(₹|\$|USD|INR|EUR|GBP|AUD|CAD|CHF|JPY|CNY|Rupees?|Dollars?)\b',
            text,
            re.I
        )
        if m:
            val = m.group(1).lower()
            if val.startswith('rupee'):
                return 'INR'
            if val.startswith('dollar'):
                return 'USD'
            return m.group(1).upper()
        return text.strip()

    # Document Value (Amount): numeric amounts
    if label == "Document Value (Amount)":
        m = re.search(r'[\d]+(?:\.\d+)?', text.replace(',', ''))
        return m.group(0) if m else text.strip()

    # Document Subtype: explicitly match import or export
    if label == "Document Subtype":
        m = re.search(r'\b(import|export)\b', text, re.I)
        return m.group(1).capitalize() if m else text.strip()

    # Fallback: return trimmed answer
    return text.strip()


def process_document(input_file_path: str) -> dict:
    """
    1. OCR the input PDF/image
    2. Run LLM to extract each field
    3. Print verbose answers to the backend console
    4. Return only the cleaned answers as a dict
    """
    # 1) Load document
    if input_file_path.lower().endswith('.pdf'):
        doc = DocumentFile.from_pdf(input_file_path)
    elif input_file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        doc = DocumentFile.from_images(input_file_path)
    else:
        raise ValueError("Unsupported file format. Use PDF or image (.jpg, .jpeg, .png)")

    # 2) OCR
    predictor = ocr_predictor(pretrained=True)
    result = predictor(doc)
    ocr_text = result.render()
    predictor = ocr_predictor(pretrained=True)
    result = predictor(doc)
    ocr_text = result.render()

    # Save OCR text to a file for reference (overwrite each time)
    with open("/Users/gauravyadav/Desktop/GauravFIO/input.txt", "w", encoding="utf-8") as f:
        f.write(ocr_text)
        
    # 3) Initialize LLM
    llm = Llama(
        model_path=model_path,
        n_ctx=2048,
        n_threads=8
    )

    # 4) Extract both verbose and clean answers
    extracted_verbose = {}
    extracted_clean   = {}

    for label, instruction in questions.items():
        prompt = f"""### Instruction:
You are an intelligent document parser. Based on the provided OCR-extracted text, extract only the required information as per the instruction below.

### Document:
{ocr_text}

### Task:
{instruction}

### Answer:"""

        response = llm(prompt, max_tokens=128, stop=["###"])
        answer = response["choices"][0]["text"].strip()

        extracted_verbose[label] = answer
        extracted_clean[label]   = clean_answer(label, answer)

    # 5) Print verbose answers in backend console
    print("\n--- Extracted Fields (Verbose) ---")
    for field, value in extracted_verbose.items():
        print(f"{field}: {value}")
    print("-----------------------------\n")

    # 6) Return only the clean values for the frontend
    return extracted_clean
