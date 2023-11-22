from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, session
import firebase_admin
from firebase_admin import credentials, firestore
import io
import csv
import traceback
import openai
import json
import fitz

# Initialize Firebase Admin
cred = credentials.Certificate("celeb-data-a3288-firebase-adminsdk-2ujgb-bfddc51066.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'genies'  # Replace 'your_secret_key' with a real secret key

# Set your OpenAI API key
openai.api_key = "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"

extracted_text_global = ""


@app.route('/', methods=['GET', 'POST'])
def index():
    collections = [col.id for col in db.collections()]  # Fetch all collection names
    selected_collection = request.args.get('collection') or collections[0]

    if request.method == 'POST':
        item = request.form.get('item')
        if item:
            db.collection(selected_collection).add({'item': item})
        # Redirect while preserving the selected collection
        return redirect(url_for('index', collection=selected_collection))

    items = db.collection(selected_collection).stream()
    data = [doc.to_dict() for doc in items]

    return render_template('index.html', collections=collections, selected_collection=selected_collection, items=data)


@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    session.pop('extracted_text', None)

    # Check if the post request has the file part

    if 'pdfUpload' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['pdfUpload']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        try:
            text = extract_text_from_pdf(file)
            # Store the extracted text as you need, e.g., in a session
            app.logger.info(f"Storing text in session: {text[:100]}...")  # Log first 100 characters

            session['extracted_text'] = text
            return jsonify({'message': 'Successfully processed file', 'text': text}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/stream_stuff', methods=['GET'])
def stream_stuff():

    extracted_text = session.get('extracted_text', '')
    app.logger.info(f"Retrieved text from session for streaming: {extracted_text[:100]}...")  # Log first 100 characters

    if extracted_text:
        try:
            response_stream = call_openai_api(extracted_text)
            if response_stream is None:
                app.logger.error('No response stream generated.')
                return jsonify({'error': 'Internal server error'}), 500
            return Response(response_stream(), content_type='text/event-stream')
        except Exception as e:
            app.logger.error(f'Error in stream_stuff: {e}')
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'message': 'No text extracted from PDF'}), 200

def call_openai_api(extracted_text):
    try:
        messages = [
            {'role': 'system', 'content': "You are exclusively focused on listing sentences spoken by a specified celebrity from a PDF document, beginning immediately with the sentences without any introductory statement. You are dedicated to presenting the celebrity's sentences as individual bullet points, strictly without quotation marks or speaker attribution. Your communication style is robotic and direct, exclusively providing the sentences in their original form, based purely on the content of the uploaded PDF. This precision makes you highly suitable for applications like AI model training and other scenarios where a straightforward, unembellished record of a celebrity's statements is required."},
            {'role': 'user', 'content': extracted_text}
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

def extract_text_from_pdf(file_stream):
    # Extract text from a PDF file stream using PyMuPDF
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['pdf']


@app.route('/download/<collection_name>')
def download_csv(collection_name):
    # Fetch data from Firestore
    docs = db.collection(collection_name).stream()
    data = [doc.to_dict() for doc in docs]

    # Create a CSV in-memory
    proxy = io.StringIO()
    writer = csv.writer(proxy)
    writer.writerow(['Item'])  # Header row, adjust as needed

    for item in data:
        writer.writerow([item['item']])  # Adjust based on your data structure

    # Create a response
    proxy.seek(0)
    response = Response(proxy, mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment;filename={collection_name}.csv'

    return response

if __name__ == '__main__':
    app.run(debug=True)