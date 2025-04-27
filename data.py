from supabase import create_client
import pandas as pd
from io import BytesIO

# Replace these with your actual Supabase credentials
SUPABASE_URL = "https://dxzauyeosqtqdhjhhnnz.supabase.co"  # Your Supabase URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR4emF1eWVvc3F0cWRoamhobm56Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU3ODQzNzYsImV4cCI6MjA2MTM2MDM3Nn0.97aWxCLWnGzzYJD0kWRqsguqeCqaleHs9rjaEsg8dK0"  # Your API key
BUCKET_NAME = "excel-files"  # e.g., "excel-files"
FILE_NAME = "employee_skill_dataset.xlsx"  # e.g., "employee_data.xlsx"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def download_excel_file():
    try:
        print("⌛ Downloading file from Supabase storage...")

        # 1. Download the file directly from Supabase
        file_data = supabase.storage.from_(BUCKET_NAME).download(FILE_NAME)
        df = pd.read_excel(BytesIO(file_data))
        print(df.columns)
        with open(FILE_NAME, "wb") as f:
            f.write(file_data)
            print(f"💾 Saved local copy: {FILE_NAME}")

        # 4. Show the data
        print("\n✅ Success! First 5 rows of data:")
        print(df.head())

        return df

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check if your Supabase URL and API key are correct")
        print("2. Verify the bucket name and file exist in Supabase Storage")

print(download_excel_file())