import os
import pandas as pd
import google.generativeai as genai
import pdfplumber
from fuzzywuzzy import fuzz
from flask import Flask, render_template, request, redirect, url_for

# --- Gemini setup ---
genai.configure(api_key='AIzaSyBvph-JgoPgpF51Fb-0Q-9ikeVwaaCTE2A')  # <-- Change your API key here
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Flask App setup ---
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- Helper Functions (Same as before) ---
def read_pdf_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def convert_paragraph_to_points(paragraph):
    return [point.strip() for point in paragraph.split('.') if point.strip()]

def clean_text(text):
    return text.replace('\n', ' ').strip()

def extract_domain_category_subcategory(text):
    content = model.generate_content(
        f"Give me the Domain, Category, and Sub Category separately for the following job description: {text}"
    )
    extracted_text = content.text
    points = convert_paragraph_to_points(extracted_text)
    points = [clean_text(p) for p in points]
    domain = points[0] if len(points) > 0 else None
    category = points[1] if len(points) > 1 else None
    sub_category = points[2] if len(points) > 2 else None
    return domain, category, sub_category

def is_similar(a, b, threshold=80):
    if pd.isna(a) or pd.isna(b):
        return False
    return fuzz.token_sort_ratio(str(a).lower(), str(b).lower()) >= threshold

def fuzzy_match_employees(df, domain, category, sub_category):
    filtered_df = df[
        df.apply(lambda row: (
                is_similar(row['Domain'], domain) and
                is_similar(row['Category'], category) and
                is_similar(row['Sub Category'], sub_category)
        ), axis=1)
    ]
    return filtered_df

def get_related_technologies(domain, category):
    content = model.generate_content(
        f"Suggest 5 technologies or skills related to domain '{domain}' and category '{category}' in a comma-separated format."    )
    suggestions = content.text
    suggestions = [clean_text(skill) for skill in suggestions.split(',')]
    return suggestions


def match_employees_with_related_skills(df, suggestions):
    filtered_df = df[
        df.apply(lambda row: any(
            is_similar(row[col], suggestion)
            for col in ['Domain', 'Category', 'Sub Category']
            for suggestion in suggestions
        ), axis=1)
    ]
    return filtered_df

def find_matched_skill(row, domain, category, sub_category, suggestions=[]):
    if is_similar(row['Domain'], domain):
        return row['Domain']
    elif is_similar(row['Category'], category):
        return row['Category']
    elif is_similar(row['Sub Category'], sub_category):
        return row['Sub Category']
    else:
        for suggestion in suggestions:
            if is_similar(row['Domain'], suggestion):
                return row['Domain']
            elif is_similar(row['Category'], suggestion):
                return row['Category']
            elif is_similar(row['Sub Category'], suggestion):
                return row['Sub Category']
    return "No direct match"

# --- Main route ---
@app.route('/',methods=['GET','POST'])
def home():
    return render_template('index.html')

@app.route("/predict", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pdf_file = request.files['pdf_file']
        excel_file = request.files['excel_file']
        if pdf_file and excel_file:
            pdf_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
            excel_path = os.path.join(UPLOAD_FOLDER, excel_file.filename)
            pdf_file.save(pdf_path)
            excel_file.save(excel_path)
            job_description_text = read_pdf_text(pdf_path)
            domain, category, sub_category = extract_domain_category_subcategory(job_description_text)
            df = pd.read_excel(excel_path)
            matched_employees = fuzzy_match_employees(df, domain, category, sub_category)
            suggestions = []
            if len(matched_employees) < 10:
                suggestions = get_related_technologies(domain, category)
                matched_employees = match_employees_with_related_skills(df, suggestions)
            top_employees = matched_employees.sort_values(by='Skill Rate', ascending=False).head(10)
            if not top_employees.empty:
                final_df = pd.DataFrame({
                    'Name': top_employees['Name'],
                    'Matched Skill': top_employees.apply(
                        lambda row: find_matched_skill(row, domain, category, sub_category, suggestions), axis=1),
                    'Skill Rate': top_employees['Skill Rate']
                })
                output_csv_path = os.path.join(OUTPUT_FOLDER, 'top_10_matched_employees.csv')
                final_df.to_csv(output_csv_path, index=False)
                results = final_df.to_dict(orient='records')
                return render_template("index.html", results=results)
            else:
                return render_template("index.html", results=[], message="No matching employees found.")
    return render_template("index.html", results=None)


if __name__ == "__main__":
    app.run(debug=True)