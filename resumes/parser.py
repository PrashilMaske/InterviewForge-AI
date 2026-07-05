import os
import fitz  # PyMuPDF
import pdfplumber
import docx
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file, trying PyMuPDF first and pdfplumber as fallback."""
    text = ""
    try:
        # Try PyMuPDF
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text()
        doc.close()
    except Exception as e:
        # Fallback to pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e2:
            raise ValueError(f"Failed to parse PDF file: {e2}")
    return text

def extract_text_from_docx(file_path):
    """Extract text from a Word document (.docx) file."""
    try:
        doc = docx.Document(file_path)
        fullText = []
        for para in doc.paragraphs:
            fullText.append(para.text)
        return '\n'.join(fullText)
    except Exception as e:
        raise ValueError(f"Failed to parse DOCX file: {e}")

def extract_text(file_path):
    """Extracts raw text from a document based on its extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext in ['.txt', '.md']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def extract_entities_with_spacy(text):
    """Uses spaCy to extract simple Named Entities (names, universities, years, skills guess)"""
    if not nlp:
        return {"persons": [], "organizations": []}
    
    doc = nlp(text[:10000])  # Process first 10,000 characters to keep it quick
    persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    
    return {
        "persons": list(set(persons))[:5],
        "organizations": list(set(orgs))[:10]
    }
