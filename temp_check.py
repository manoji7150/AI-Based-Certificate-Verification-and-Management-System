import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

if not URL or not KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY missing in .env")
    exit(1)

supabase = create_client(URL, KEY)

def check_table(name, columns):
    try:
        res = supabase.table(name).select(",".join(columns)).limit(1).execute()
        print(f"✅ Table '{name}' exists with columns {columns}.")
        return True
    except Exception as e:
        print(f"❌ Table '{name}' error: {e}")
        return False

print("--- Database Diagnostics ---")
check_table("students", ["id", "roll_number", "full_name"])
check_table("certificates", ["id", "student_id", "status"])
