import os
from flask import Flask, request, jsonify, render_template, g
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import pinecone
import PyPDF2
import tiktoken
from sentence_transformers import SentenceTransformer
from transformers import pipeline
from pdf_utils import extract_text_from_pdf
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'pdfs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB limit

# Handle 413 Payload Too Large errors
@app.errorhandler(RequestEntityTooLarge)
def handle_payload_too_large(error):
    return jsonify({'error': 'File size exceeds the maximum limit of 50 MB'}), 413

# Pinecone configuration
API_KEY = "pcsk_6LBQCc_LoqA5KkN3KJNequdFfrQwnNDQGYEPEXCb1syNyCixkNDKgmn7u9QFnhUuEA67m3"
INDEX_NAME = "doctalk"

def get_pinecone_index():
    if not hasattr(g, 'pinecone_index'):
        try:
            logger.info("Initializing Pinecone client...")
            pc = pinecone.Pinecone(api_key=API_KEY)
            logger.info(f"Pinecone client initialized: {pc}")
            indexes = pc.list_indexes()
            logger.info(f"Existing indexes: {indexes}")
            if INDEX_NAME not in [idx['name'] for idx in indexes]:
                logger.info(f"Creating index '{INDEX_NAME}'...")
                pc.create_index(
                    name=INDEX_NAME,
                    dimension=384,
                    metric="euclidean",
                    spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1")
                )
                logger.info(f"Index '{INDEX_NAME}' created.")
            g.pinecone_index = pc.Index(INDEX_NAME)
            logger.info(f"Index type: {type(g.pinecone_index)}")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    return g.pinecone_index

model = SentenceTransformer('all-MiniLM-L6-v2')
enc = tiktoken.get_encoding("cl100k_base")

def chunk_text(text, chunk_size=1000):
    tokens = enc.encode(text)
    chunks = [tokens[i:i+chunk_size] for i in range(0, len(tokens), chunk_size)]
    return [enc.decode(chunk) for chunk in chunks]

def generate_embeddings(text_chunks):
    return model.encode(text_chunks)

def store_embeddings_in_pinecone(embeddings, text_chunks, pdf_name):
    index = get_pinecone_index()
    logger.info(f"Before upsert, index type: {type(index)}")
    for idx, (embedding, chunk) in enumerate(zip(embeddings, text_chunks)):
        try:
            index.upsert(vectors=[(f"{pdf_name}_{idx}", embedding, {"text": chunk, "pdf_name": pdf_name})])
        except AttributeError as e:
            logger.error(f"Error in upsert: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in upsert: {e}")
            raise

def query_pinecone(query, top_k=3):
    index = get_pinecone_index()
    query_embedding = model.encode([query])[0].tolist()
    result = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    pdf_scores = {}
    for match in result['matches']:
        pdf_name = match['metadata'].get("pdf_name")
        pdf_scores[pdf_name] = pdf_scores.get(pdf_name, 0) + match['score']
    best_pdf = max(pdf_scores, key=pdf_scores.get) if pdf_scores else None
    relevant_chunks = [match['metadata']['text'] for match in result['matches'] if match['metadata'].get("pdf_name") == best_pdf]
    return relevant_chunks, best_pdf

def summarize_text(text, max_input_length=1024):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    if len(text.split()) > max_input_length:
        text = " ".join(text.split()[:max_input_length])
    summary = summarizer(text, max_length=150, min_length=50, do_sample=False)
    return summary[0]['summary_text']

def generate_response(query, max_input_length=1024):
    relevant_chunks, best_pdf = query_pinecone(query)
    combined_text = " ".join(relevant_chunks)
    summarized_response = summarize_text(combined_text, max_input_length)
    return f"[From: {best_pdf}]\n{summarized_response}" if best_pdf else "No relevant information found."

def process_multiple_pdfs(pdf_files):
    for pdf_path in pdf_files:
        pdf_text = extract_text_from_pdf(pdf_path)
        chunks = chunk_text(pdf_text)
        embeddings = generate_embeddings(chunks)
        store_embeddings_in_pinecone(embeddings, chunks, os.path.basename(pdf_path))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdfs():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    files = request.files.getlist('files')
    pdf_paths = []
    for file in files:
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            pdf_paths.append(file_path)
    if pdf_paths:
        process_multiple_pdfs(pdf_paths)
        return jsonify({'message': f"Processed {len(pdf_paths)} PDFs successfully!"}), 200
    return jsonify({'error': 'No valid PDF files uploaded'}), 400

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'No question provided'}), 400
    response = generate_response(query)
    return jsonify({'response': response}), 200

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5001)