import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(URL, KEY)

def get_columns(name):
    print(f"\n--- Checking {name} ---")
    try:
        # We can't easily get schema via JS client without RPC, 
        # but we can try common columns one by one
        common_cols = ["id", "roll_number", "full_name", "email", "department", "gpa", "points", "student_id", "event_name", "status"]
        existing = []
        for col in common_cols:
            try:
                supabase.table(name).select(col).limit(1).execute()
                existing.append(col)
            except:
                pass
        print(f"Existing columns in '{name}': {existing}")
    except Exception as e:
        print(f"Error checking '{name}': {e}")

get_columns("students")
get_columns("certificates")
