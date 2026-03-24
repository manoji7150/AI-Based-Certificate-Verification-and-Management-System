import google.generativeai as genai
import os
from dotenv import load_dotenv
import PIL.Image
import io
import requests

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def verify_certificate_with_ai(file_url, student_name, event_name):
    """
    Uses Gemini API to extract info from certificate and verify it.
    Returns: { 'score': int, 'extracted_info': dict, 'reason': str }
    """
    if not GEMINI_API_KEY:
        return {"score": 0, "reason": "Gemini API key not configured"}

    try:
        # Download the file content
        response = requests.get(file_url)
        image_data = response.content
        img = PIL.Image.open(io.BytesIO(image_data))

        # Initialize Gemini Model
        model = genai.GenerativeModel('gemini-1.5-pro') # Using Pro for better logic

        prompt = f"""
        Analyze this image/document and determine if it is a VALID certificate or AWARD based on these rules:

        1. It MUST contain the college name: "ACJ" (or "ACJ College" or "Asian College of Journalism" or similar variations).
        2. It MUST contain the event/topic name: "{event_name}".
        3. It MUST contain at least one of these keywords/phrases: 
           - Certificate, Award, Winner, Participation, Achievement, Presented to, Merit, Recognition.

        Rules for Validation:
        - If ALL THREE conditions above are met, the status is: "VALID CERTIFICATE".
        - If ANY condition is missing, or if the image is a random photo (selfie, screenshot of a chat, unrelated scenery), the status is: "NOT VALID CERTIFICATE".

        Return ONLY a JSON object with this exact structure:
        {{
            "verification_status": "VALID CERTIFICATE" or "NOT VALID CERTIFICATE",
            "extracted_name": "the name found on the cert",
            "extracted_event": "the event found on the cert",
            "reasoning": "short explanation of why it passed or failed"
        }}
        """

        response = model.generate_content([prompt, img])
        
        # Clean the response to get valid JSON
        json_text = response.text.strip()
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
             json_text = json_text.split("```")[1].split("```")[0].strip()

        import json
        result = json.loads(json_text)
        return result

    except Exception as e:
        print(f"Error in AI Verification: {e}")
        return {"verification_status": "NOT VALID CERTIFICATE", "reasoning": f"System error: {str(e)}"}
