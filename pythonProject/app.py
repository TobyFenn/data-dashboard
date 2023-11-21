from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import io
import csv
from flask import Response

cred = credentials.Certificate("celeb-data-a3288-firebase-adminsdk-2ujgb-bfddc51066.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    collections = ['justin bieber', 'paris hilton', 'ice spice']
    data = {}

    if request.method == 'POST':
        for collection in collections:
            item = request.form.get(f'item_{collection}')
            if item:
                db.collection(collection).add({'item': item})

        return redirect(url_for('index'))

    for collection in collections:
        docs = db.collection(collection).stream()
        data[collection] = [doc.to_dict() for doc in docs]

    return render_template('index.html', data=data)

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