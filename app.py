import os
import io
from flask import Flask, render_template, request, send_file, Response, stream_with_context, jsonify
from markdown2 import Markdown
from groq import Groq
import PyPDF2
import json
import time

app = Flask(__name__)
markdowner = Markdown()

# Set up Groq client
def get_api_key():
    key_file = os.path.join(os.path.dirname(__file__), 'api_key.txt')
    if os.path.exists(key_file):
        with open(key_file, 'r') as file:
            return file.read().strip()
    else:
        raise ValueError("API key file not found. Please create 'api_key.txt' with your Groq API key.")

api_key = get_api_key()
client = Groq(api_key=api_key)

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
    text = ""
    print(f"Total pages in PDF: {len(pdf_reader.pages)}")
    for i, page in enumerate(pdf_reader.pages):
        page_text = page.extract_text()
        text += page_text
        print(f"Page {i+1} extracted text length: {len(page_text)}")
    
    print("Total extracted text length:", len(text))
    print("First 500 characters of extracted text:")
    print(text[:500])
    print("Last 500 characters of extracted text:")
    print(text[-500:])
    return text

# Function to generate coherent notes in markdown using AI
def generate_coherent_notes(text):
    chunk_size = 3000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    all_notes = []

    for i, chunk in enumerate(chunks):
        prompt = f"Create detailed, coherent notes in markdown format based on the following content (part {i+1} of {len(chunks)}). Focus only on the information provided:\n\n{chunk}"
        print(f"Processing chunk {i+1} of {len(chunks)}")
        
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates detailed, coherent notes in markdown format. You only use the information provided in the user's message and do not include any external knowledge."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        all_notes.append(response.choices[0].message.content.strip())
        
        # Yield progress
        progress = (i + 1) / len(chunks) * 100
        yield json.dumps({"progress": progress})

    final_notes = "\n\n".join(all_notes)
    app.config['CURRENT_NOTES'] = final_notes
    yield json.dumps({"complete": True})

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files['file']
        
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_file)
        
        # Store the text for processing
        app.config['PDF_TEXT'] = pdf_text
        
        return render_template('index.html', processing=True)
    
    return render_template('index.html', processing=False)

@app.route('/process')
def process():
    def generate():
        pdf_text = app.config.get('PDF_TEXT', '')
        
        for update in generate_coherent_notes(pdf_text):
            yield f"data: {update}\n\n"
            time.sleep(0.1)  # Small delay to ensure browser receives updates

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/result')
def result():
    markdown_notes = app.config.get('CURRENT_NOTES', '')
    html_content = markdowner.convert(markdown_notes)
    return jsonify({"content": html_content})

@app.route('/download')
def download_notes():
    notes = app.config.get('CURRENT_NOTES', '')
    if not notes:
        return "No notes available for download", 400
    
    with open("notes.md", "w", encoding='utf-8') as f:
        f.write(notes)
    return send_file('notes.md', as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
