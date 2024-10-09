import os
import io
from flask import Flask, render_template, request, send_file, Response, jsonify, redirect, url_for, flash, session
from markdown2 import Markdown
from groq import Groq
import PyPDF2
import json
import time
import pdfkit
import tempfile
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')  # Replace with a real secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model definition
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=True)  # Change to nullable=True

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Auth0 configuration
AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
API_IDENTIFIER = os.getenv('API_IDENTIFIER')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

# Initialize the Markdown converter
markdowner = Markdown()  # Ensure this is defined here

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists')
            return redirect(url_for('register'))
        
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    callback_url = url_for("callback", _external=True)
    print(f"Callback URL: {callback_url}")  # Debugging line
    return redirect(f'https://{AUTH0_DOMAIN}/authorize?audience={API_IDENTIFIER}&client_id={CLIENT_ID}&response_type=token&redirect_uri={callback_url}&scope=openid email')

@app.route('/callback')
def callback():
    return render_template('callback.html')  # Render a simple HTML page to handle the token

@app.route('/logout')
@login_required
def logout():
    # Log out from Flask-Login
    logout_user()
    
    # Redirect to Auth0 logout endpoint
    return redirect(f'https://{AUTH0_DOMAIN}/v2/logout?returnTo={url_for("login", _external=True)}&client_id={CLIENT_ID}')

@app.route('/', methods=['GET', 'POST'])
@login_required
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

@login_manager.unauthorized_handler
def unauthorized():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"error": "Authentication required"}), 401
    flash('You must be logged in to access this page.')
    return redirect(url_for('login'))

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
@login_required
def result():
    markdown_notes = app.config.get('CURRENT_NOTES', '')
    if not markdown_notes:
        return jsonify({"error": "No notes available"}), 400
    
    try:
        html_content = markdowner.convert(markdown_notes)
        return jsonify({"content": html_content})
    except Exception as e:
        print(f"Error generating result: {e}")  # Log the error to the console
        return jsonify({"error": "Failed to generate notes"}), 500

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

@app.route('/process_token', methods=['POST'])
def process_token():
    data = request.get_json()
    token = data.get('token')
    if token:
        user_info_response = requests.get(f'https://{AUTH0_DOMAIN}/userinfo', headers={'Authorization': f'Bearer {token}'})
        if user_info_response.status_code != 200:
            print(f"Failed to retrieve user info: {user_info_response.status_code}, {user_info_response.text}")
            return jsonify({'status': 'error', 'message': 'Failed to retrieve user info'}), 400
        
        user_info = user_info_response.json()
        print(f"User Info: {user_info}")  # Debugging line
        
        # Use email as username if nickname is not available
        username = user_info.get('nickname') or user_info.get('email')
        
        if username is None:
            return jsonify({'status': 'error', 'message': 'No valid username found'}), 400
        
        user = User.query.filter_by(username=username).first()
        if not user:
            # Create a new user with a placeholder password hash
            user = User(username=username)
            user.password_hash = generate_password_hash('placeholder')  # Set a placeholder password
            db.session.add(user)
            db.session.commit()
        
        login_user(user)
        return jsonify({'status': 'success'}), 200
    return jsonify({'status': 'error', 'message': 'No token found'}), 400

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Retrieve the user by ID

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
