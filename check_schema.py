import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(URL, KEY)

def check_columns():
    print("Checking 'certificates' table columns...")
    try:
        # Try to select the column
        res = supabase.table("certificates").select("achievement_level").limit(1).execute()
        print("Success! 'achievement_level' column found.")
    except Exception as e:
        print(f"Error: {e}")
        print("\nThis usually means the column is missing.")

if __name__ == "__main__":
    check_columns()
