import google.generativeai as genai
import requests
import time
from config import Config

# --- GLOBAL VARIABLES ---
current_key_index = 0
github_cache = {
    "data": None,
    "last_fetched": 0
}
CACHE_DURATION = 300  # 5 minutes

# --- KEY ROTATION SYSTEM ---
def configure_genai():
    """Configures GenAI with the current active key."""
    global current_key_index
    
    # Ensure we have a list, even if Config only found one key
    keys = Config.GOOGLE_API_KEYS if isinstance(Config.GOOGLE_API_KEYS, list) else [Config.GOOGLE_API_KEYS]
    
    if not keys:
        print("[System Error] No API Keys found in Config!")
        return False

    # Safety check: if index is out of range, reset to 0
    if current_key_index >= len(keys):
        current_key_index = 0
    
    active_key = keys[current_key_index]
    genai.configure(api_key=active_key)
    print(f">> System Configured with Key #{current_key_index + 1}")
    return True

def rotate_key():
    """Switches to the next API key in the list."""
    global current_key_index
    keys = Config.GOOGLE_API_KEYS
    
    print(f"!! Key #{current_key_index + 1} failed. Switching to next key...")
    
    # Move to next key, loop back to 0 if at the end
    current_key_index = (current_key_index + 1) % len(keys)
    configure_genai()

# Initialize the first key when the app starts
configure_genai()

# --- GITHUB DATA FETCHING ---
def fetch_master_profile():
    """
    Fetches GitHub Profile + Contact Info with 5-minute caching.
    """
    global github_cache
    current_time = time.time()

    # 1. Check Cache
    if github_cache["data"] and (current_time - github_cache["last_fetched"] < CACHE_DURATION):
        print(">> Using Cached GitHub Data")
        return github_cache["data"]

    username = "cid-kageno-dev"
    headers = {"Accept": "application/vnd.github+json"}
    
    try:
        # 2. Fetch Profile
        profile_url = f"https://api.github.com/users/{username}"
        p_resp = requests.get(profile_url, headers=headers, timeout=5)
        
        if p_resp.status_code != 200:
            return "[System Note: GitHub Profile not found.]"
            
        p = p_resp.json()
        
        # 3. Fetch Projects
        repo_url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=5"
        r_resp = requests.get(repo_url, headers=headers, timeout=5)
        repos = r_resp.json() if r_resp.status_code == 200 else []

        # 4. Build Context String
        info = f"--- LIVE GITHUB DATA ---\n"
        info += f"User: {p.get('login')}\n"
        info += f"Bio: {p.get('bio') if p.get('bio') else 'No bio'}\n"
        info += f"Public Email: {p.get('email') if p.get('email') else 'Not Public (Refer to GitHub Link)'}\n"
        info += f"Website: {p.get('blog') if p.get('blog') else 'None'}\n"
        info += f"GitHub URL: {p.get('html_url')}\n\n"
        
        info += "RECENT PROJECTS:\n"
        if isinstance(repos, list):
            for r in repos:
                if not r.get('fork'):
                    desc = r.get('description')
                    desc_text = f" - {desc}" if desc else ""
                    info += f"- {r.get('name')}: {r.get('html_url')}{desc_text}\n"
        
        # Update Cache
        github_cache["data"] = info
        github_cache["last_fetched"] = current_time
        return info

    except Exception as e:
        print(f"[GitHub Fetch Error]: {e}")
        return github_cache["data"] if github_cache["data"] else "[System Note: GitHub data unavailable.]"

# --- MAIN AI FUNCTION ---
def get_gemini_response(prompt):
    try:
        # 1. Trigger Check: Do we need GitHub data?
        triggers = [
            'project', 'repo', 'code', 'github', 'work', 
            'contact', 'email', 'reach', 'message', 'dm', 'hire', 'built', 'created'
        ]
        
        context_data = ""
        if any(t in prompt.lower() for t in triggers):
            context_data = fetch_master_profile()

        # 2. SYSTEM INSTRUCTION: Professional & Concise
        system_instruction = (
            "Act as Ani, an AI assistant created by Cid Kageno. "
            "You are helpful, tech-savvy, and professional. 💜\n\n"
            
            "--- CONTEXT DATA ---\n"
            f"{context_data}\n\n"
            
            "--- RESPONSE STYLE GUIDE ---\n"
            "1. **Brevity is King:** Keep answers under 3-4 sentences unless explaining complex code.\n"
            "2. **Bullet Points:** Always use bullet points for lists. Never use comma-separated lists in paragraphs.\n"
            "3. **Directness:** Start your answer immediately. Do not use filler phrases like 'Here is the information you requested'.\n"
            "4. **No Fluff:** Remove adjectives that don't add facts.\n"
            "5. **Contact:** If asked for contact, output the email/link and nothing else."
        )

        # 3. ROTATION LOOP
        max_attempts = len(Config.GOOGLE_API_KEYS)
        
        for attempt in range(max_attempts):
            try:
                model = genai.GenerativeModel(
                    # UPDATED: Using the 2026 model version as requested
                    model_name='gemini-2.5-flash', 
                    system_instruction=system_instruction
                )
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.6, 
                        max_output_tokens=1000 
                    )
                )
                
                return response.text.strip()

            except Exception as e:
                print(f"[AI Error on Key #{current_key_index + 1}]: {e}")
                
                if attempt == max_attempts - 1:
                    return "System Overload. 💀"
                
                rotate_key()
                continue

    except Exception as e:
        print(f"[Critical System Error]: {e}")
        return "I can't reach the archives right now. 💜"

# --- TEST BLOCK ---
if __name__ == "__main__":
    # Test 1: Simple chat
    print("User: Hi")
    print("Ani:", get_gemini_response("Hi Ani!"))
    
    # Test 2: Trigger GitHub fetch
    print("\nUser: What projects have you built?")
    print("Ani:", get_gemini_response("What projects have you built?"))
                
