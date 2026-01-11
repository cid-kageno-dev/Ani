import gspread
from oauth2client.service_account import ServiceAccountCredentials
from thefuzz import process
from config import Config
import threading

def _get_sheet_client():
    """Helper to connect to Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(Config.SHEET_CREDS, scope)
    client = gspread.authorize(creds)
    return client.open(Config.SHEET_NAME).sheet1

def save_interaction_background(user_msg, ai_msg):
    """
    Worker function to be run in a thread.
    Saves the Q&A pair to the sheet.
    """
    try:
        sheet = _get_sheet_client()
        sheet.append_row([user_msg, ai_msg])
        print(f"[Sheet Service]: Saved interaction for '{user_msg}'")
    except Exception as e:
        print(f"[Sheet Service Save Error]: {e}")

def get_fallback_answer(user_msg):
    """
    1. Fetches all past Q&A.
    2. Uses fuzzy matching to find a similar past question.
    3. Returns the stored AI answer.
    """
    try:
        sheet = _get_sheet_client()
        # get_all_records returns a list of dicts: [{'User_Query': '...', 'AI_Response': '...'}]
        data = sheet.get_all_records()
        
        if not data:
            return "Database is empty."

        # Extract only the questions for matching
        past_queries = [row['User_Query'] for row in data]
        
        # Find best match (Returns tuple: (string, score))
        best_match, score = process.extractOne(user_msg, past_queries)
        
        print(f"[Sheet Service]: Best match '{best_match}' with score {score}")

        if score > 75: # Confidence threshold
            # Find the row with the matching question
            for row in data:
                if row['User_Query'] == best_match:
                    return f"(Fallback) {row['AI_Response']}"
        
        return "I am currently offline and couldn't find a relevant answer in my history."

    except Exception as e:
        print(f"[Sheet Service Read Error]: {e}")
        return "System Error: Knowledge base unavailable."
      
