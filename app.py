import streamlit as st
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import plotly.express as px
import time
import uuid

# Load environment variables
load_dotenv()

# Supabase configuration
# Attempt to get from st.secrets (Cloud) first, then os.getenv (Local)
try:
    URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    KEY = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
    GEMINI_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
except Exception:
    URL = os.getenv("SUPABASE_URL")
    KEY = os.getenv("SUPABASE_KEY")
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")

@st.cache_resource
def get_supabase_client() -> Client:
    # Improved check to help user differentiate between local and cloud setup
    if not URL or not KEY or URL == "your_supabase_url_here":
        st.error("### ⚠️ Supabase Credentials Missing")
        if "STREAMLIT_RUNTIME_ENV" in os.environ: # Detecting cloud-like env
             st.markdown("""
             To fix this on Streamlit Cloud:
             1. Go to **Manage App** > **Settings** > **Secrets**.
             2. Add the following to the text box:
             ```toml
             SUPABASE_URL = "your_url"
             SUPABASE_KEY = "your_key"
             GEMINI_API_KEY = "your_gemini_key"
             ```
             """)
        else:
             st.error("Please configure SUPABASE_URL and SUPABASE_KEY in your .env file.")
        st.stop()
    return create_client(URL, KEY)

try:
    supabase = get_supabase_client()
    # Attempt to create bucket if it doesn't exist (requires appropriate permissions)
    try:
        supabase.storage.get_bucket("certificates")
    except Exception:
        try:
            supabase.storage.create_bucket("certificates", options={"public": True})
            st.toast("✅ Created 'certificates' storage bucket automatically!")
        except Exception:
            # If it fails, we'll inform the user later during upload or via a persistent warning
            pass
except Exception as e:
    st.error(f"Failed to connect to Supabase: {e}")
    st.stop()

# --- Page Configuration ---
st.set_page_config(
    page_title="Student Certificate Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for Premium Glassmorphism Look ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    :root {
        --glass-bg: rgba(255, 255, 255, 0.6);
        --glass-border: rgba(255, 255, 255, 0.4);
        --glass-blur: blur(12px);
        --primary-gradient: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
        --accent-color: #0284c7;
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: #ffffff;
        background-attachment: fixed;
        color: #1e293b;
    }

    /* Sidebar Styling for White Theme */
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0;
    }
    
    [data-testid="stSidebarNav"] {
        background-color: #f8fafc !important;
    }

    /* Sidebar text colors */
    [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] p, [data-testid="stSidebar"] h2 {
        color: #1e293b !important;
    }

    /* Modern Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0); }
    ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.2); }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e40af; /* Solid deep blue */
        margin-bottom: 1.5rem;
    }
    
    .stMarkdown h2, .stMarkdown h3 {
        color: #334155;
        font-weight: 600;
    }
    
    /* Reusable Clean Card Component (replacing glass) */
    .glass-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        transition: all 0.2s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(3, 105, 161, 0.3);
        box-shadow: 0 8px 32px 0 rgba(3, 105, 161, 0.1);
        transform: translateY(-2px);
    }

    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-weight: 700;
        color: #3b82f6; /* Blue metrics as in image */
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        color: #475569;
    }

    .stTabs [aria-selected="true"] {
        background: var(--primary-gradient) !important;
        color: white !important;
        border: none !important;
    }
    
    .stButton>button {
        background: #3b82f6 !important; /* Solid Blue */
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        transition: background 0.2s ease !important;
        text-transform: none !important;
        letter-spacing: normal !important;
    }
    
    .stButton>button:hover {
        background: #2563eb !important;
        box-shadow: none !important;
        transform: none !important;
    }
    
    .status-pending { color: #fbbf24; font-weight: bold; }
    .status-approved { color: #10b981; font-weight: bold; }
    .status-rejected { color: #ef4444; font-weight: bold; }

    /* Login Container Specifics */
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Fix Input Fields for Readability */
    div[data-baseweb="input"] {
        background-color: white !important;
        border-radius: 8px !important;
        border: 1px solid #ccc !important;
        padding: 1px !important;
    }
    
    div[data-baseweb="input"] input {
        color: black !important;
        background-color: white !important;
        -webkit-text-fill-color: black !important;
    }
    
    div[aria-label="Email Address"], div[aria-label="Password"], 
    div[aria-label="Staff Email"], div[aria-label="Password"] {
        color: #1e293b !important;
    }

    /* Force all text inside tables and dataframes to be dark */
    .stTable, [data-testid="stTable"], [data-testid="stDataFrame"], [data-testid="stTable"] * {
        color: #1e293b !important;
    }
    
    .stTable td, .stTable th {
        color: #1e293b !important;
        background-color: white !important;
    }

    /* Fix for Selectboxes and other widgets */
    div[data-baseweb="select"] * {
        color: black !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: white !important;
        border: 1px solid #cbd5e1 !important; /* Visible border */
        border-radius: 8px !important;
    }
    
    div[role="listbox"] * {
        color: black !important;
    }

    /* Input Field Border Update */
    div[data-baseweb="input"] {
        background-color: white !important;
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important; /* Consistent border */
        padding: 1px !important;
    }

    /* General text visibility fallback */
    .stMarkdown, .stText, p, span, label, li, td, th {
        color: #1e293b !important;
    }

    /* Placeholder color */
    ::placeholder {
        color: #666666 !important;
        opacity: 1; 
    }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def fetch_student_data(roll_number):
    try:
        response = supabase.table("students").select("*").eq("roll_number", roll_number).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error fetching student: {e}")
        return None

def fetch_certificates(student_id=None):
    try:
        # Avoid join to prevent Relationship Cache errors
        query = supabase.table("certificates").select("*")
        if student_id:
            query = query.eq("student_id", student_id)
        response = query.order("created_at", desc=True).execute()
        
        # Manually enrich if needed (optional here as portals handle their own fetching)
        return response.data
    except Exception as e:
        st.error(f"Error fetching certificates: {e}")
        return []

# --- Authentication Logic ---
def login_screen():
    # Centered Logo Display
    col1, col2, col3 = st.columns([1, 0.8, 1])
    with col2:
        st.image("logo.jpg", use_container_width=True)
    
    st.markdown("<h1 class='main-header' style='text-align: center;'>🎓 Portal Login</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["👨‍🎓 Student login", "👨‍🏫 Staff login"])
    
    with tab1:
        with st.form("student_auth"):
            email = st.text_input("Email Address")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login as Student")
            if submit:
                if email and password:
                    res = supabase.table("students").select("*").eq("email", email).eq("password", password).execute()
                    if res.data:
                        st.session_state.authenticated = True
                        st.session_state.user_role = "Student"
                        st.session_state.user_info = res.data[0]
                        st.success("Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
                else:
                    st.warning("Please fill all fields")

    with tab2:
        with st.form("staff_auth"):
            email = st.text_input("Staff Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login as Staff")
            if submit:
                if email and password:
                    res = supabase.table("staff").select("*").eq("email", email).eq("password", password).execute()
                    if res.data:
                        st.session_state.authenticated = True
                        st.session_state.user_role = "Staff"
                        st.session_state.user_info = res.data[0]
                        st.success("Staff login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid staff credentials")
                else:
                    st.warning("Please fill all fields")

# --- App State Control ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    login_screen()
    st.stop()

# --- Sidebar Navigation (Authenticated) ---
st.sidebar.markdown(f"<h2 style='color: #0369a1;'>👋 Hello, {st.session_state.user_info.get('full_name', 'User')}</h2>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='color: #475569;'>Logged in as {st.session_state.user_role}</p>", unsafe_allow_html=True)

# Build navigation options based on role
nav_options = []
if st.session_state.user_role == "Student":
    nav_options = ["Student Dashboard"]
elif st.session_state.user_role == "Staff":
    nav_options = ["Staff Portal", "System Setup"]

choice = st.sidebar.radio("Navigation", nav_options)

if st.sidebar.button("Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- Route to Pages with Global Error Handling ---
try:
    if choice == "Student Dashboard":
        import student_portal
        student_portal.show_page(supabase)
    elif choice == "Staff Portal":
        import staff_portal
        staff_portal.show_page(supabase)
    elif choice == "System Setup":
        import setup_page
        setup_page.show_page(supabase)
except Exception as e:
    st.error("🚨 An unexpected error occurred.")
    st.exception(e)
    if st.button("🔄 Reload App"):
        st.rerun()
