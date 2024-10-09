# AI Note Taker

## Overview
AI Note Taker is an AI-powered PDF note-taking application that allows users to upload PDF documents and generate coherent notes using the Groq API. The application features real-time progress tracking, user authentication, and a visually appealing UI.

## Key Features
1. **Chunking Strategy**: Efficiently handles large PDF documents.
2. **Real-Time Progress Tracking**: Uses server-sent events and dynamic JavaScript updates.
3. **Modular Codebase**: Optimized API usage and error handling.
4. **User Authentication**: Secure login using Auth0.
5. **Downloadable Notes**: Converts generated notes from Markdown to PDF.
6. **UI/UX Improvements**: Includes a visually appealing progress bar.

## Demo
[Watch the demo](https://youtu.be/7YWfX5P9IVs) by clicking on the link.  

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AI-note-taker.git
   cd AI-note-taler
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r pip-requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add the following:
   ```plaintext
   SECRET_KEY=your_secret_key
   AUTH0_DOMAIN=your_auth0_domain  # Sign up at https://auth0.com/ to create an Auth0 account
   API_IDENTIFIER=your_api_identifier
   CLIENT_ID=your_client_id  # Obtain this from your Auth0 application settings
   CALLBACK_URL=your_callback_url  # Set this to your application's callback URL
   ```
   - To create an Auth0 account, visit [Auth0 Sign Up](https://auth0.com/signup).
   - After signing up, create a new application in the Auth0 dashboard to get your `AUTH0_DOMAIN` and `CLIENT_ID`.
   - In the application settings, set the **Allowed Callback URLs** to your application's callback URL (e.g., `http://127.0.0.1:5000/callback`).

## Usage

1. Run the application:
   ```bash
   python app.py
   ```

2. Open your browser and go to `http://127.0.0.1:5000`.

3. Log in using your Google account.

4. Upload a PDF document and generate notes.

## Configuration
- **Adjust the `chunk_size`** in `app.py` to change how the PDF is processed.
- **Modify the AI prompt** in the `generate_coherent_notes()` function to customize the note-taking style.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## License
This project is under development is not currently licensed.
## Acknowledgments
- **Auth0**: For user authentication.
- **Flask**: For the web framework.
- **Groq API**: For generating notes from PDF content.
