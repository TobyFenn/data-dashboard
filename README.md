
# Genies Magic Data Dashboard 🌟

A flask-based application designed for extracting and managing quotes from webpage PDF files. This app integrates Firebase for data storage and GPT-3.5 for processing.

## Features 🧞

- **PDF Upload**: Upload PDF files for processing.
- **Quote Extraction**: Utilize OpenAI's GPT-3.5 to extract relevant creator quotes from documents.
- **Firebase Integration**: Store and manage your data in Firebase.
- **Data Export**: Download extracted data in CSV format for offline use.

## Getting Started 🚀

### Prerequisites

- Python 3.x
- Flask 3.0.0
- Firebase Admin SDK 6.2.0
- Other dependencies listed in `requirements.txt`.

### Initial Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/geniesinc/data-dashboard.git
   ```
2. **Navigate to the project directory** and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables Setup 🔐

Follow these steps:

1. **Create a `.env` file** in the root directory of the project.
   
2. **Add the following variables** to the `.env` file:
   ```plaintext
   FIREBASE_CREDENTIALS=path/to/your/firebase_credentials.json
   FLASK_SECRET_KEY=your_unique_flask_secret_key
   OPENAI_API_KEY=your_openai_api_key
   ```
   Replace the placeholders with your actual Firebase credentials file path, Flask secret key, and OpenAI API key.

3. **Ensure `.env` is in `.gitignore`** to prevent pushing sensitive data to version control.

### Running the Application

Execute the following command in the project directory:
```bash
python app.py
```
Your application should now be running on `localhost`.
Gonna hopefully get it hosted somewhere depending on what I'm doing so I'll update this as needed.

## Usage Instructions 📘

- **Upload PDF**: Use the interface to upload PDF files.
- **Extract Quotes**: Process the PDFs to extract quotes.
- **Manage Data**: View and manage the extracted quotes through the dashboard.
- **Export Data**: Download the quotes as CSV files for further use.

## Contributing 

Any contributions you make are greatly appreciated.

## Contact 📬

tfenner@usc.edu
tfenner@genies.team

---

Thx! 🎉
