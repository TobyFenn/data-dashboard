from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, session
import firebase_admin
from firebase_admin import credentials, firestore
import io
import csv
import traceback
import openai
import json
import fitz
import os

# Environment variable loading for development purposes
from dotenv import load_dotenv
load_dotenv()

# Firebase Admin Initialization
cred = credentials.Certificate(os.environ['FIREBASE_CREDENTIALS'])
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Flask App
app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

# Set OpenAI API key
openai.api_key = os.environ['OPENAI_API_KEY']

# Global variable to hold extracted text
extracted_text_global = ""

# Main
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Main route for displaying and handling the dashboard.
    Supports both GET and POST requests.
    GET: Displays the dashboard with data from the selected collection.
    POST: Handles adding new items to the collection.
    """
    # Fetching collection names from Firestore
    collections = [col.id for col in db.collections()]
    selected_collection = request.args.get('collection') or collections[0]

    # Handling form submission
    if request.method == 'POST':
        item = request.form.get('item')
        if item:
            db.collection(selected_collection).add({'item': item})
        # Redirect while preserving the selected collection
        return redirect(url_for('index', collection=selected_collection))

    # Fetching items from the selected collection
    items = db.collection(selected_collection).stream()
    data = [doc.to_dict() for doc in items]

    # Rendering the index template with the fetched data
    return render_template('index.html', collections=collections, selected_collection=selected_collection, items=data)


# processing files
@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    """
    Endpoint to handle the processing of uploaded PDF files.
    Extracts text from the PDF and stores it globally for further processing.
    """
    global extracted_text_global

    # Clearing any previously stored text
    session.pop('extracted_text', None)

    # Handling file upload
    if 'pdfUpload' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['pdfUpload']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        try:
            text = extract_text_from_pdf(file)
            app.logger.info(f"Storing text in global variable: {text[:100]}...")  # Log first 100 characters

            extracted_text_global = text
            return jsonify({'message': 'Successfully processed file', 'text': text}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Streaming endpoint
@app.route('/stream_stuff', methods=['GET'])
def stream_stuff():
    """
    Endpoint for streaming the processing of extracted text using OpenAI API.
    Returns a streaming response.
    """
    global extracted_text_global

    if extracted_text_global:
        truncated_text = extracted_text_global[:6828]  # Truncating text for OpenAI API limits
        try:
            response_stream = call_openai_api(truncated_text)
            if response_stream is None:
                app.logger.error('No response stream generated.')
                return jsonify({'error': 'Internal server error'}), 500
            return Response(response_stream(), content_type='text/event-stream')
        except Exception as e:
            app.logger.error(f'Error in stream_stuff: {e}')
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'message': 'No text extracted from PDF'}), 200

# Route for storing quotes in Firestore
@app.route('/store_quote', methods=['POST'])
def store_quote():
    """
    Endpoint to store extracted quotes into a specific Firestore collection.
    Expects a quote and collection name in the request body.
    """
    try:
        data = request.get_json()
        quote = data['quote']
        collection_name = data['collection']
        if quote:
            db.collection(collection_name).add({'item': quote})
            return jsonify({'message': 'Quote stored successfully'}), 200
        else:
            return jsonify({'error': 'No quote provided'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# call OpenAI API
def call_openai_api(extracted_text):
    """
    Calls the OpenAI API to process the extracted text.
    Generates a stream of responses based on the text.
    """
    try:
        messages = [
            {
                'role': 'system',
                'content' : 'Please read the provided article and identify the celebrity mentioned. Then, locate and list only the direct quotations spoken by the celebrity, excluding any statements or interpretations made by the journalist or others. Specifically, ensure that the quotations are verbatim and are the exact words spoken by the celebrity. Do not include any analysis, paraphrasing, or context from the article – just the celebrity own words.'
            },
            {
                'role': 'user',
                'content': extracted_text
            }
        ]
        stream = openai.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=messages,
            temperature=0,
            stream=True
        )

        def generate():
            for part in stream:
                content = part.choices[0].delta.content or ""
                yield f"data: {json.dumps({'content': content})}\n\n"

        return generate
    except Exception as e:
        app.logger.error(f'Error in call_openai_api: {e}')
        traceback.print_exc()
        return None

# Extractor
def extract_text_from_pdf(file_stream):
    """
    Extracts text from a PDF file stream using PyMuPDF.
    """
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Checks for validity
def allowed_file(filename):
    """
    Checks if the uploaded file is a PDF.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['pdf']


# Route for downloading
@app.route('/download/<collection_name>')
def download_csv(collection_name):
    """
    Endpoint to download the contents of a Firestore collection as a CSV file.
    """
    # Fetch data from Firestore
    docs = db.collection(collection_name).stream()
    data = [doc.to_dict() for doc in docs]

    # Create a CSV in-memory
    proxy = io.StringIO()
    writer = csv.writer(proxy)
    writer.writerow(['Item'])

    for item in data:
        writer.writerow([item['item']])

    # Create a response
    proxy.seek(0)
    response = Response(proxy, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment;filename={collection_name}.csv'

    return response

if __name__ == '__main__':
    app.run(debug=True)