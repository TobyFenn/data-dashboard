from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
import firebase_admin
from firebase_admin import credentials, firestore
import io
import csv
import traceback
import openai
import json

# Initialize Firebase Admin
cred = credentials.Certificate("celeb-data-a3288-firebase-adminsdk-2ujgb-bfddc51066.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Flask App
app = Flask(__name__)

# Set your OpenAI API key
openai.api_key = "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"

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

# Function to call OpenAI API
# Function to call OpenAI API with streaming
def call_openai_api():
    try:
        stream = openai.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'system', 'content': "Act as a sea pirate."},
                      {'role': 'user', 'content': 'Do you love the sea?'}],
            temperature=0,
            stream=True
        )

        def generate():
            for part in stream:
                content = part.choices[0].delta.content or ""
                yield f"data: {json.dumps({'content': content})}\n\n"

        return generate
    except Exception as e:
        print("Error in call_openai_api:", e)
        traceback.print_exc()

@app.route('/process_pdf', methods=['GET'])
def process_pdf():
    response_stream = call_openai_api()
    return Response(response_stream(), content_type='text/event-stream')



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