from supabase import create_client, Client
import requests,pandas as pd
from io import BytesIO

# Replace with your Supabase URL and API key
url = "https://dxzauyeosqtqdhjhhnnz.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR4emF1eWVvc3F0cWRoamhobm56Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3ODQzNzYsImV4cCI6MjA2MTM2MDM3Nn0.97aWxCLWnGzzYJD0kWRqsguqeCqaleHs9rjaEsg8dK0"
supabase: Client = create_client(url, key)


# Get the public URL of the uploaded file
file_url = supabase.storage.from_("excel-file").get_public_url("employee_skill.xlsx")

print(f"File URL: {file_url}")  # You should see the URL as a string

# Download the file using the URL
response = requests.get(file_url)

# Check if the download was successful
if response.status_code == 200:
    # Use pandas to read the Excel file from the content
    excel_file = BytesIO(response.content)
    df = pd.read_excel(excel_file)

    # Print the first few rows of the dataframe
    print(df.head())
else:
    print("Failed to download the file. HTTP Status Code:", response.status_code)