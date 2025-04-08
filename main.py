import tkinter as tk
from tkinter import filedialog, messagebox
from app import process_multiple_pdfs, generate_response
from speech_handler import record_and_respond
import os

class DocTalkAI:
    def __init__(self, root):
        self.root = root
        self.root.title("DocTalk AI")
        self.root.geometry("600x400")

        # UI Elements
        self.label = tk.Label(root, text="Welcome to DocTalk AI", font=("Arial", 14))
        self.label.pack(pady=10)

        self.upload_btn = tk.Button(root, text="Upload PDFs", command=self.upload_pdfs)
        self.upload_btn.pack(pady=5)

        self.question_label = tk.Label(root, text="Ask a question:")
        self.question_label.pack(pady=5)

        self.question_entry = tk.Entry(root, width=50)
        self.question_entry.pack(pady=5)

        self.ask_btn = tk.Button(root, text="Ask (Text)", command=self.ask_question)
        self.ask_btn.pack(pady=5)

        self.speech_btn = tk.Button(root, text="Ask (Speech)", command=self.ask_speech)
        self.speech_btn.pack(pady=5)

        self.response_text = tk.Text(root, height=10, width=70)
        self.response_text.pack(pady=10)

        self.pdf_files = []

    def upload_pdfs(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if files:
            self.pdf_files = list(files)
            process_multiple_pdfs(self.pdf_files)
            messagebox.showinfo("Success", f"Uploaded and processed {len(self.pdf_files)} PDFs!")
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(tk.END, f"Processed PDFs: {', '.join([os.path.basename(f) for f in self.pdf_files])}\n")

    def ask_question(self):
        query = self.question_entry.get()
        if not query:
            messagebox.showwarning("Input Error", "Please enter a question!")
            return
        response = generate_response(query)
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, response)
        self.question_entry.delete(0, tk.END)

    def ask_speech(self):
        response = record_and_respond()
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, response)

if __name__ == "__main__":
    root = tk.Tk()
    app = DocTalkAI(root)
    root.mainloop()