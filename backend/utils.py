import os
import tempfile
from fastapi import UploadFile
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from llama_cpp import Llama
import asyncio

MODEL_PATH = "/Users/gauravyadav/Desktop/GauravFIO/mistral-7b-instruct-v0.1.Q4_K_M.gguf copy"

# Load once
print("Loading Mistral model...")
llm = Llama(model_path=MODEL_PATH, n_ctx=2048, n_threads=8)
print("Model loaded.")

# Shared instructions
questions = {
    "Document Number": (
        "Extract the document number. It may appear as invoice number, bill number, reference number, or transaction number. "
        "Return only an alphanumeric code in the format like XXX/999."
    ),
    "Document Date": (
        "Extract the date of the document. It may appear as invoice date, issue date, or bill date. "
        "Return only the date in format DD-MM-YYYY."
    ),
    "Validity Till Date": (
        "Extract the expiry or due date of the document. Look for terms like validity period, due date, or termination date. "
        "Return only the date in format DD-MM-YYYY."
    ),
    "Document Currency": (
        "What currency is used in the document? It may be shown as currency symbol like ₹, $, or code like INR, USD, or full name like Rupees. "
        "Return the currency in short form like INR or USD."
    ),
    "Document Value (Amount)": (
        "What is the total payable amount in the document? Look for terms like total amount, invoice total, net payable, or total due. "
        "Return only the numeric amount like 23124.40."
    ),
    "Document Subtype": (
        "Is this an import or export document? Decide based on whether goods are being received or sent out. "
        "Return only one word: Import or Export."
    )
}

# Prompt building function
def build_prompt(field_name, document_text):
    return f"""### Instruction:
You are a reliable document parser. Extract the requested field from the document below.

### Document:
{document_text}

### Task:
{questions[field_name]}

### Answer:"""

# Field extraction function
def extract_field(field_name, document_text):
    prompt = build_prompt(field_name, document_text)
    response = llm(prompt, max_tokens=128, stop=["###"])
    return response["choices"][0]["text"].strip()

# Async file processor
async def process_document(file: UploadFile):
    # Save file to temp
    suffix = os.path.splitext(file.filename)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Load document for OCR
    if tmp_path.lower().endswith('.pdf'):
        doc = DocumentFile.from_pdf(tmp_path)
    elif tmp_path.lower().endswith(('.png', '.jpg', '.jpeg')):
        doc = DocumentFile.from_images(tmp_path)
    else:
        return {"error": "Unsupported file format"}

    # Run OCR
    predictor = ocr_predictor(pretrained=True)
    result = predictor(doc)
    document_text = result.render()

    # Parallel field extraction using asyncio
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, extract_field, label, document_text)
        for label in questions.keys()
    ]
    answers = await asyncio.gather(*tasks)

    return dict(zip(questions.keys(), answers))
