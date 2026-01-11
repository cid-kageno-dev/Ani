import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # This list will hold all found keys
    GOOGLE_API_KEYS = []
    
    # --- DYNAMIC KEY LOADER ---
    # 1. Loop to find GOOGLE_API_KEY1, GOOGLE_API_KEY2, etc.
    i = 1
    while True:
        key = os.getenv(f'GOOGLE_API_KEY{i}')
        if not key:
            break # Stop when we run out of numbered keys
        GOOGLE_API_KEYS.append(key)
        i += 1
        
    # 2. Fallback: If no numbered keys exist, check for the standard GOOGLE_API_KEY
    if not GOOGLE_API_KEYS:
        single_key = os.getenv('GOOGLE_API_KEY')
        if single_key:
            GOOGLE_API_KEYS.append(single_key)

    # --- OTHER CONFIGS ---
    SHEET_NAME = os.getenv('SHEET_NAME')
    SHEET_CREDS = os.getenv('GOOGLE_SHEET_CREDS')

    # Optional: Print how many keys were found for debugging (remove in production)
    # print(f">> Config loaded {len(GOOGLE_API_KEYS)} API keys.")
    
