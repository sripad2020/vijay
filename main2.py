from flask import Flask, request, jsonify
import pandas as pd
import google.generativeai as genai

app = Flask(__name__)

# Load the employee skill dataset
employee_skills = pd.read_excel('employee_skill_dataset.xlsx')

# Gemini API configuration
genai.configure(api_key='AIzaSyAM8hWwGWv5B9pTCnf14Q-Ck_gkukWUrN8')
model = genai.GenerativeModel('gemini-1.5-flash')


@app.route('/match_job', methods=['GET','POST'])
def match_job():
    # Extract job description from request
    job_description = request.json.get('job_description', '')

    # Use Gemini to extract domain, category, and sub-category from job description
    prompt = f"""
    Given the following job description, extract the relevant domain, category, and sub-categories (specific skills) that match the columns in the employee skill dataset. 
    The domains are: Data Engineering, DevOps, Cloud Computing.
    The categories are: Practice and Technologies, Tools and Platforms.
    The sub-categories are specific skills like React.js, Node.js, etc.

    Job Description: {job_description}

    Return the output as:
    Domain: <domain>
    Category: <category>
    Sub-Categories: <sub-category1>, <sub-category2>, ...
    """

    response = model.generate_content(prompt)
    generated_text = response.text

    # Parse the response to get domain, category, and sub-categories
    domain = None
    category = None
    sub_categories = []

    for line in generated_text.split('\n'):
        if line.startswith('Domain:'):
            domain = line.split(':')[1].strip()
        elif line.startswith('Category:'):
            category = line.split(':')[1].strip()
        elif line.startswith('Sub-Categories:'):
            sub_categories = [s.strip() for s in line.split(':')[1].split(',')]

    # Filter employees based on domain, category, and sub-categories
    filtered_employees = employee_skills[
        (employee_skills['Domain'] == domain) &
        (employee_skills['Category'] == category) &
        (employee_skills['Sub Category'].isin(sub_categories))
        ]

    # Group by employee and calculate average skill rate
    ranked_employees = filtered_employees.groupby('Name').agg({
        'Skill Rate': 'mean',
        'Interest Rate': 'mean'
    }).reset_index()

    # Sort by Skill Rate (descending) and Interest Rate (descending)
    ranked_employees = ranked_employees.sort_values(
        by=['Skill Rate', 'Interest Rate'],
        ascending=[False, False]
    )

    # Get top 10 employees
    top_10 = ranked_employees.head(10)['Name'].tolist()
    print(top_10)
    return jsonify({
        'domain': domain,
        'category': category,
        'sub_categories': sub_categories,
        'top_10_employees': top_10
    })


if __name__ == '__main__':
    app.run(debug=True)