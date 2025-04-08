from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_source):
    if isinstance(pdf_source, str):  # File path
        reader = PdfReader(pdf_source)
    else:
        raise ValueError("Unsupported PDF source type")
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text