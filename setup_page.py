import streamlit as st
import os

def show_page(supabase):
    st.markdown("<h1 class='main-header'>System Configuration & Diagnostics</h1>", unsafe_allow_html=True)
    
    st.info("Use this page to verify your Supabase setup and fix common storage issues.")
    
    # --- 1. Connection Check ---
    st.subheader("🔗 Connection Status")
    try:
        # Check if we can reach the students table
        supabase.table("students").select("id").limit(1).execute()
        st.success("✅ Supabase Connection: Active")
    except Exception as e:
        st.error(f"❌ Supabase Connection Failed: {e}")
        st.stop()
        
    # --- 2. Storage Bucket Check ---
    st.subheader("📦 Storage Diagnostics")
    
    bucket_name = "certificates"
    bucket_ready = False
    
    try:
        bucket = supabase.storage.get_bucket(bucket_name)
        bucket_ready = True
        st.success(f"✅ Bucket '{bucket_name}' found.")
        
        # Check if public
        if bucket.public:
            st.success("✅ Bucket is Public.")
        else:
            st.warning("⚠️ Bucket is NOT Public. Students won't be able to view their certificates.")
            st.markdown("👉 **Fix:** Go to Supabase Dashboard > Storage > 'certificates' > Edit Bucket > Toggle 'Public Bucket' to ON.")
            
    except Exception:
        st.error(f"❌ Bucket '{bucket_name}' NOT found.")
        st.markdown(f"""
        ### 🛠️ How to fix:
        1. **Option A: Auto-Fix (Recommended)**
           Add `SUPABASE_SERVICE_KEY` to your `.env` file and restart.
        
        2. **Option B: Manual Setup**
           - Go to **Supabase Dashboard** > **Storage**.
           - Click **New Bucket** and name it `{bucket_name}`.
           - Toggle **Public Bucket** to **ON**.
           - Go to **Policies** for this bucket.
           - Create a NEW policy:
             - **Allowed operations**: `INSERT` and `SELECT`.
             - **Target roles**: `anon` and `authenticated`.
             - **Policy Definition**: `true`.
        """)
        
    # --- 3. Table Check ---
    st.subheader("📊 Database Tables")
    tables = ["students", "certificates"]
    
    for table in tables:
        try:
            supabase.table(table).select("id").limit(1).execute()
            st.success(f"✅ Table '{table}' is ready.")
        except Exception:
            st.error(f"❌ Table '{table}' not found or inaccessible.")
            
    # --- 4. Environment Check ---
    st.subheader("🔑 Environment Variables")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**SUPABASE_URL:**", "✅ Set" if os.getenv("SUPABASE_URL") else "❌ Missing")
        st.write("**SUPABASE_KEY (Anon):**", "✅ Set" if os.getenv("SUPABASE_KEY") else "❌ Missing")
    with col2:
        st.write("**SUPABASE_SERVICE_KEY:**", "✅ Set (Auto-fix enabled)" if os.getenv("SUPABASE_SERVICE_KEY") else "ℹ️ Not Set (Manual setup only)")

    if bucket_ready:
        st.balloons()
        st.success("🎉 Your system is fully configured and ready for uploads!")
    else:
        st.warning("⚠️ Action required: Follow the instructions above to complete the setup.")
