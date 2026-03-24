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
URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

@st.cache_resource
def get_supabase_client() -> Client:
    if not URL or not KEY or URL == "your_supabase_url_here":
        st.error("Please configure SUPABASE_URL and SUPABASE_KEY in the .env file.")
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
        --glass-bg: rgba(255, 255, 255, 0.03);
        --glass-border: rgba(255, 255, 255, 0.1);
        --glass-blur: blur(16px);
        --primary-gradient: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
        --accent-color: #38bdf8;
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at top left, #1e293b, #0f172a);
        background-attachment: fixed;
        color: #f8fafc;
    }

    /* Modern Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0); }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
    
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
        text-shadow: 0 10px 30px rgba(56, 189, 248, 0.2);
    }
    
    /* Reusable Glass Card Component */
    .glass-card {
        background: var(--glass-bg);
        backdrop-filter: var(--glass-blur);
        -webkit-backdrop-filter: var(--glass-blur);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 8px 32px 0 rgba(56, 189, 248, 0.1);
        transform: translateY(-2px);
    }

    /* Metric Styling */
    [data-testid="stMetricValue"] {
        font-weight: 700;
        color: var(--accent-color);
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px 12px 0 0;
        padding: 10px 20px;
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] {
        background: var(--primary-gradient) !important;
        color: white !important;
        border: none !important;
    }
    
    .stButton>button {
        background: var(--primary-gradient);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton>button:hover {
        box-shadow: 0 10px 25px rgba(99, 102, 241, 0.4);
        transform: translateY(-1px);
    }
    
    .status-pending { color: #fbbf24; font-weight: bold; }
    .status-approved { color: #10b981; font-weight: bold; }
    .status-rejected { color: #ef4444; font-weight: bold; }

    /* Login Container Specifics */
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 24px;
        backdrop-filter: var(--glass-blur);
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
st.sidebar.markdown(f"<h2 style='color: #38bdf8;'>👋 Hello, {st.session_state.user_info.get('full_name', 'User')}</h2>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='color: #94a3b8;'>Logged in as {st.session_state.user_role}</p>", unsafe_allow_html=True)

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
