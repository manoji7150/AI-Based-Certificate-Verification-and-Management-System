import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

def setup_storage():
    print("🚀 Supabase Storage Diagnostic & Setup")
    print("--------------------------------------")
    
    if not URL:
        print("❌ Error: SUPABASE_URL not found in .env")
        return
    
    # Use Service Key if available, otherwise fallback to Anon Key
    target_key = SERVICE_KEY if SERVICE_KEY else KEY
    if not target_key:
        print("❌ Error: Neither SUPABASE_KEY nor SUPABASE_SERVICE_KEY found in .env")
        return

    supabase = create_client(URL, target_key)
    
    print(f"🔗 Connecting to: {URL}")
    if SERVICE_KEY:
        print("🔑 Using SERVICE_ROLE key (Automated setup enabled)")
    else:
        print("🔑 Using ANON key (Limited permissions)")
    
    # 1. Check/Create Bucket
    try:
        print("\nChecking bucket 'certificates'...")
        try:
            supabase.storage.get_bucket("certificates")
            print("✅ Bucket 'certificates' already exists.")
        except Exception:
            print("⏳ Bucket 'certificates' not found. Attempting to create...")
            supabase.storage.create_bucket("certificates", options={"public": True})
            print("✅ Successfully created 'certificates' bucket!")
            
    except Exception as e:
        print(f"❌ Storage Operation Failed: {e}")
        if not SERVICE_KEY:
            print("\n💡 REASON: Your ANON key doesn't have permission to create buckets.")
            print("👉 ACTION: Go to Supabase Dashboard > Storage and create 'certificates' manually.")
            
    # 2. Checklist for manual steps
    print("\n--- MANDATORY STEPS (Verify in Dashboard) ---")
    print("1. [Storage] Bucket name: 'certificates'")
    print("2. [Storage] Configuration: Public Bucket = ON")
    print("3. [Policies] Add Policy for 'certificates' bucket:")
    print("   - Allowed operations: SELECT, INSERT")
    print("   - Target roles: authenticated, anon")
    print("   - Policy definition: true (allow all)")
    print("--------------------------------------------")

if __name__ == "__main__":
    setup_storage()
