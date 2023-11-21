from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin
cred = credentials.Certificate("celeb-data-a3288-firebase-adminsdk-2ujgb-bfddc51066.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Flask App
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        item = request.form['item']
        db.collection('items').add({'item': item})
        return redirect(url_for('index'))

    docs = db.collection('items').stream()
    items = [doc.to_dict() for doc in docs]
    return render_template('index.html', items=items)


if __name__ == '__main__':
    app.run(debug=True)
