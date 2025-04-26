from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import PyPDF2
import tempfile
import google.generativeai as genai
import json
import re
import pandas as pd
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
import nltk
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Download NLTK data (run once)
nltk.download('punkt')
nltk.download('stopwords')

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload folder exists

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_pdf(filepath):
    """Extract text content from PDF file"""
    try:
        text = ""
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise


def parse_gemini_response(paragraph):
    sentences = sent_tokenize(paragraph)
    words = word_tokenize(paragraph.lower())
    stop_words = set(stopwords.words('english'))
    filtered_words = [word for word in words if word.isalnum() and word not in stop_words]
    freq_dist = FreqDist(filtered_words)
    sentence_scores = {}
    for sentence in sentences:
        sentence_word_tokens = word_tokenize(sentence.lower())
        sentence_word_tokens = [word for word in sentence_word_tokens if word.isalnum()]
        score = sum(freq_dist.get(word, 0) for word in sentence_word_tokens)
        sentence_scores[sentence] = score
    sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)
    key_points = sorted_sentences[:7]
    return key_points


def process_pdf(filepath, excel_path='employee_skill_dataset.xlsx'):
        genai.configure(api_key='AIzaSyBvph-JgoPgpF51Fb-0Q-9ikeVwaaCTE2A')
        model = genai.GenerativeModel('gemini-1.5-flash')
        text = extract_text_from_pdf(filepath)
        if not text.strip():
            raise ValueError("PDF appears to be empty or could not extract text")
        prompt = f"""
        Analyze this job description and extract the following information in JSON format:
        - Category 
        - Sub-Category 
        - Required Skills 
        - Experience Level 

        Job Description:
        {text}

        Return only the JSON output with no additional text.
        """
        logger.debug("Sending prompt to Gemini")
        response = model.generate_content(prompt)
        if not response.text:
            raise ValueError("Empty response from Gemini API")

        job_data = parse_gemini_response(response.text)
        logger.debug(f"Gemini response parsed: {job_data}")

        return job_data


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_document():
    if 'document' not in request.files:
        return jsonify({'error': 'No file uploaded', 'status': 'error'}), 400

    file = request.files['document']

    if file.filename == '':
        return jsonify({'error': 'No selected file', 'status': 'error'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type', 'status': 'error'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    try:
        # Save the file temporarily
        file.save(filepath)
        logger.debug(f"File saved to {filepath}")

        # Process the file
        result = process_pdf(filepath)

        print(result)
    except Exception as e:
        logger.error(f"Error in analyze_document: {str(e)}", exc_info=True)
        # Clean up if file was saved
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            'error': f'Error processing file: {str(e)}',
            'status': 'error'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)