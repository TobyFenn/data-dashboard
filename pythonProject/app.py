from flask import Flask, render_template, request, redirect, url_for, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
import io
import csv
from flask import Response
import requests
import json

# Your API key
api_key = "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"

# Endpoint URL
endpoint_url = "https://api.openai.com/v1/chat/completions"

# Data payload for the request
data = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Say this is a test!"}],
    "temperature": 0.7
}

# Headers with your API key
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Make the POST request to the API
response = requests.post(endpoint_url, json=data, headers=headers)

# Get the response JSON
response_json = response.json()

# Print the response
print(response_json)

cred = credentials.Certificate("celeb-data-a3288-firebase-adminsdk-2ujgb-bfddc51066.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

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
def call_openai_api():

    # Endpoint URL
    endpoint_url = "https://api.openai.com/v1/chat/completions"

    # Data payload for the request
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Say this is a test!"}],
        "temperature": 0.7
    }

    # Headers with your API key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Make the POST request to the API
    response = requests.post(endpoint_url, json=data, headers=headers)

    # Return the response JSON
    return response.json()

@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    # Call the OpenAI API
    response_json = call_openai_api()

    # Return the response
    return jsonify(response_json)

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