from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    Args:
        pdf_path (str): Path to the PDF file.
    Returns:
        str: Extracted text from the PDF.
    """
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Test the function
if __name__ == "__main__":
    pdf_path = "Medical_book.pdf" 
    extracted_text = extract_text_from_pdf(pdf_path)
    print(extracted_text)
