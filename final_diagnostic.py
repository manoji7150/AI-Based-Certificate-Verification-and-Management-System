import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

print(f"Connecting to: {URL}")
supabase = create_client(URL, KEY)

print("\n--- Storage Buckets ---")
try:
    buckets = supabase.storage.list_buckets()
    print(f"Found {len(buckets)} buckets:")
    for b in buckets:
        print(f" - {b.name} (Public: {b.public})")
except Exception as e:
    print(f"❌ Error listing buckets: {e}")

print("\n--- 'certificates' Specific Check ---")
try:
    bucket = supabase.storage.get_bucket("certificates")
    print(f"✅ 'certificates' bucket found! Public: {bucket.public}")
except Exception as e:
    print(f"❌ 'certificates' bucket error: {e}")

print("\n--- Database Schema Check ---")
def check_table(name):
    try:
        supabase.table(name).select("id").limit(1).execute()
        print(f"✅ Table '{name}' table is accessible.")
    except Exception as e:
        print(f"❌ Table '{name}' error: {e}")

check_table("students")
check_table("certificates")
