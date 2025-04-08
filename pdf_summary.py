import PyPDF2
from transformers import pipeline
import re
from tqdm import tqdm

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

# Function to split text into sentences
def split_text_into_sentences(text):
    sentences = re.split(r'(?<=[.!?]) +', text)  # Split by sentence boundaries
    return sentences

# Function to split text into chunks without exceeding the token limit
def split_text_into_chunks(sentences, max_tokens=400):  # Smaller chunks for better control
    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence.split())
        if current_length + sentence_length <= max_tokens:
            current_chunk.append(sentence)
            current_length += sentence_length
        else:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# Function to summarize the text
def summarize_text(text, max_length=150, min_length=70):
    # Using a larger model for better summaries, may need GPU for faster results
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn") 

    sentences = split_text_into_sentences(text)
    chunks = split_text_into_chunks(sentences, max_tokens=400)  # Smaller chunks for better summarization control
    summaries = []

    # Limit the number of chunks to process a maximum of 3 for concise summary
    chunks_to_process = chunks[:3]

    # Summarize chunks in batches
    batch_size = 3  # Number of chunks to process at once
    for i in tqdm(range(0, len(chunks_to_process), batch_size), desc="Summarizing chunks"):
        batch = chunks_to_process[i:i + batch_size]
        try:
            batch_summaries = summarizer(batch, max_length=max_length, min_length=min_length, do_sample=False)
            summaries.extend([summary['summary_text'] for summary in batch_summaries])
        except Exception as e:
            print(f"Error summarizing batch: {e}")

    return " ".join(summaries)

# Main execution block
if __name__ == '__main__':
    # Path to your PDF file
    pdf_path = 'Medical_book.pdf'

    # Extract text from the PDF
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)

    # Summarize the extracted text
    print("Summarizing text...")
    summary = summarize_text(text)

    # Print the summary
    print("\nSummary of the PDF:")
    print(summary)
