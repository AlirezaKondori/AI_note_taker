import os
import io
from flask import Flask, render_template, request, send_file, Response, jsonify
from markdown2 import Markdown
from groq import Groq
import PyPDF2
import json
import time
import pdfkit
import tempfile

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

# Set the path to wkhtmltopdf
WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

# Function to extract text from a PDF file
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Function to generate coherent notes in markdown using AI
def generate_coherent_notes(text):
    chunk_size = 3000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    all_notes = []

    for i, chunk in enumerate(chunks):
        prompt = f"Create detailed, coherent notes in markdown format based on the following content (part {i+1} of {len(chunks)}). Focus only on the information provided:\n\n{chunk}"
        
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
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        if file:
            pdf_text = extract_text_from_pdf(file)
            app.config['PDF_TEXT'] = pdf_text
            return jsonify({"message": "File uploaded successfully"}), 200
    return render_template('index.html')

@app.route('/process')
def process():
    def generate():
        pdf_text = app.config.get('PDF_TEXT', '')
        if not pdf_text:
            yield json.dumps({"error": "No PDF text found"})
            return
        
        for update in generate_coherent_notes(pdf_text):
            yield f"data: {update}\n\n"
            time.sleep(0.1)  # Small delay to ensure browser receives updates

    return Response(generate(), mimetype='text/event-stream')

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
    
    # Convert markdown to HTML
    html_content = markdowner.convert(notes)
    
    # Add some basic styling
    styled_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            h1, h2, h3 {{ color: #4a90e2; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as temp_html:
        temp_html.write(styled_html)
        temp_html_path = temp_html.name

    pdf_path = temp_html_path.replace('.html', '.pdf')
    
    try:
        # Generate PDF from the temporary HTML file
        pdfkit.from_file(temp_html_path, pdf_path, configuration=config)
        
        # Read the PDF file
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # Create a response with the PDF content
        response = Response(pdf_content, content_type='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename=generated_notes.pdf'
        return response

    finally:
        # Clean up temporary files
        try:
            os.remove(temp_html_path)
        except:
            pass
        try:
            os.remove(pdf_path)
        except:
            pass

if __name__ == "__main__":
    app.run(debug=True)
