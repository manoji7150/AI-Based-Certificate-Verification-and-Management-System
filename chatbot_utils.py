import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables just in case
load_dotenv()

# System Prompts
STUDENT_PROMPT = """You are a helpful AI assistant for the Student Certificate Management System.
Your main role is to help students navigate the Student Portal. 
You can guide them on:
1. How to upload certificates (Select event type, enter name, upload PDF/image).
2. How to check certificate status (Go to "My Uploaded Certificates" table).
3. How to view their points (Top right of the dashboard).
4. Information about login and reset process if asked.

Keep your answers concise, friendly, and structured. Do not make up features that don't exist in the UI.
"""

STAFF_PROMPT = """You are a helpful AI assistant for the Staff Portal in the Student Certificate Management System.
Your main role is to help staff members navigate the Staff Portal.
You can guide them on:
1. How to review certificates (Go to "Pending Approvals" tab, expand review cards).
2. How to approve or reject certificates (Use the Approve or Reject buttons, assign points 0-10).
3. How to download certificates (Click "Download Certificate" in the review card).
4. How to view student analytics (Go to the "Department Analytics" tab).

Keep your answers professional, concise, and structured. Do not make up features that don't exist in the UI.
"""

def get_ai_response(prompt, chat_history, role="Student"):
    """
    Get AI response using either OpenAI or Google Gemini depending on available API keys.
    chat_history should be a list of dictionaries like [{"role": "user", "content": "hello"}, ...]
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not openai_key and not gemini_key:
        return "I'm sorry, my AI backend is not configured yet. Please ask the administrator to add an API key."
    
    system_prompt = STUDENT_PROMPT if role == "Student" else STAFF_PROMPT

    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.5-flash') # Model supported by your API key version
            
            # Format history for Gemini
            messages = [{"role": "user", "parts": [system_prompt]}]
            messages.append({"role": "model", "parts": ["Understood. How can I help?"]})
            
            for msg in chat_history:
                gemini_role = "user" if msg["role"] == "user" else "model"
                messages.append({"role": gemini_role, "parts": [msg["content"]]})
                
            messages.append({"role": "user", "parts": [prompt]})
            
            response = model.generate_content(messages)
            return response.text
        except Exception as e:
            return f"Gemini Error: {str(e)}\nPlease make sure `google-generativeai` is installed."
            
    elif openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(chat_history)
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI Error: {str(e)}\nPlease make sure `openai` is installed."
