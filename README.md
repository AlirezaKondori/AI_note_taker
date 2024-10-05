# AI_note_taker: PDF Note Generator

## Description
AI Note Takeris a Flask-based web application that uses AI to generate comprehensive study notes from PDF documents. It leverages the Groq API to process and summarize content, making it easier for students and researchers to digest large amounts of information quickly.

## Features
- PDF text extraction
- AI-powered note generation
- Real-time progress tracking
- Markdown to HTML conversion for easy reading
- Downloadable notes in Markdown format

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/AlirezaKondori/AI_note_taker.git
   cd AI_note_taker
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create an `api_key.txt` file in the root directory and add your Groq API key to it.

## Usage

1. Run the Flask application:
   ```
   python app.py
   ```

2. Open a web browser and go to `http://localhost:5000`.

3. Upload a PDF file and click "Generate Notes".

4. Wait for the notes to be generated. You can track the progress in real-time.

5. Once complete, view the generated notes in the browser or download them as a Markdown file.

## Configuration

- Adjust the `chunk_size` in `app.py` to change how the PDF is processed.
- Modify the AI prompt in `generate_coherent_notes()` function to customize the note-taking style.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is currently under development and not licensed.

## Acknowledgements

- Flask for the web framework
- Groq for the AI API
- PyPDF2 for PDF processing
- Markdown2 for Markdown conversion
