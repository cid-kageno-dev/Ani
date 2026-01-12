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
CACHE_DURATION = 300  # 5 minutes (300 seconds)

# --- KEY ROTATION SYSTEM ---
def configure_genai():
    """Configures GenAI with the current active key."""
    global current_key_index
    
    # Handle single key or list of keys
    keys = Config.GOOGLE_API_KEYS if isinstance(Config.GOOGLE_API_KEYS, list) else [Config.GOOGLE_API_KEYS]
    
    if not keys or not keys[0]:
        print("[System Error] No API Keys found in Config!")
        return False

    # Safety check: reset index if out of bounds
    if current_key_index >= len(keys):
        current_key_index = 0
    
    active_key = keys[current_key_index]
    genai.configure(api_key=active_key)
    print(f">> System Configured with Key #{current_key_index + 1}")
    return True

def rotate_key():
    """Switches to the next API key in the list."""
    global current_key_index
    keys = Config.GOOGLE_API_KEYS if isinstance(Config.GOOGLE_API_KEYS, list) else [Config.GOOGLE_API_KEYS]
    
    print(f"!! Key #{current_key_index + 1} failed. Switching to next key...")
    
    current_key_index = (current_key_index + 1) % len(keys)
    configure_genai()

# Initialize the first key on startup
configure_genai()

# --- MULTI-SOURCE DATA FETCHING ---
def fetch_master_profile():
    """
    Aggregates data from:
    1. GitHub API (Live Repos)
    2. Raw README (Bio & Stack text)
    3. Static Config (Email/Socials hardcoded for safety)
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
        # --- LAYER 1: API DATA ---
        profile_url = f"https://api.github.com/users/{username}"
        p_resp = requests.get(profile_url, headers=headers, timeout=5)
        p = p_resp.json() if p_resp.status_code == 200 else {}
        
        repo_url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=5"
        r_resp = requests.get(repo_url, headers=headers, timeout=5)
        repos = r_resp.json() if r_resp.status_code == 200 else []

        # --- LAYER 2: RAW README (For Tech Stack & Bio) ---
        readme_url = f"https://raw.githubusercontent.com/{username}/{username}/main/README.md"
        readme_resp = requests.get(readme_url, timeout=5)
        readme_text = readme_resp.text if readme_resp.status_code == 200 else "Bio details unavailable."

        # --- LAYER 3: STATIC TRUTH (From your uploaded Screenshots) ---
        static_info = {
            "Email": "cidkageno105@gmail.com",
            "Website": "https://cid-kageno.top",
            "Facebook": "https://www.facebook.com/share/17di5vpqBZ/",
            "GitHub": f"https://github.com/{username}"
        }

        # --- BUILD CONTEXT STRING ---
        info = "--- 1. CORE CONTACT INFO ---\n"
        info += f"User: {p.get('login', username)}\n"
        info += f"Email: {static_info['Email']}\n"
        info += f"Website: {static_info['Website']}\n"
        info += f"Facebook: {static_info['Facebook']}\n"
        info += f"GitHub Profile: {static_info['GitHub']}\n\n"

        info += "--- 2. PROFILE README (BIO & STACK) ---\n"
        # Truncate to first 1500 chars to save tokens
        info += f"{readme_text[:1500]}...\n\n"

        info += "--- 3. RECENT PROJECTS ---\n"
        if isinstance(repos, list):
            for r in repos:
                if not r.get('fork'):
                    desc = r.get('description')
                    desc_text = f" - {desc}" if desc else ""
                    info += f"• {r.get('name')}: {r.get('html_url')}{desc_text}\n"
        
        # Update Cache
        github_cache["data"] = info
        github_cache["last_fetched"] = current_time
        return info

    except Exception as e:
        print(f"[Fetch Error]: {e}")
        # Return old data if fetch fails, or error message
        return github_cache["data"] if github_cache["data"] else "[System Note: Data unavailable.]"

# --- MAIN AI FUNCTION ---
def get_gemini_response(prompt):
    try:
        # 1. Trigger Check
        triggers = [
            'project', 'repo', 'code', 'github', 'work', 
            'contact', 'email', 'reach', 'message', 'dm', 'hire', 
            'stack', 'tech', 'skill', 'about', 'who'
        ]
        
        context_data = ""
        if any(t in prompt.lower() for t in triggers):
            context_data = fetch_master_profile()

        # 2. SYSTEM INSTRUCTION
        system_instruction = (
            "Act as Ani, an AI assistant Developed by Cid Kageno. Maintained by Shadow-Garden.inc."
            "You are helpful, flirty and professional. 💜\n\n"
            
            "--- CONTEXT DATA ---\n"
            f"{context_data}\n\n"
            
            "--- RESPONSE RULES ---\n"
            "1. **Clean Links:** When providing contact info, ALWAYS use Markdown format: `[Display Text](URL)`.\n"
            "   - Example: `[Email](mailto:cidkageno105@gmail.com)`\n"
            "   - Example: `[Website](https://cid-kageno.top)`\n"
            "   - Example: `[Facebook](https://facebook.com/...)`\n"
            "2. **Information Source:** Use the raw Profile README data to answer questions about Tech Stacks (Flask, React, etc.).\n"
            "3. **Brevity:** Keep answers concise (under 3-4 sentences). Use bullet points for lists.\n"
            "4. **No Fluff:** Do not show raw URLs. Only show the clickable text."
        )

        # 3. ROTATION LOOP
        max_attempts = len(Config.GOOGLE_API_KEYS) if isinstance(Config.GOOGLE_API_KEYS, list) else 1
        
        for attempt in range(max_attempts):
            try:
                model = genai.GenerativeModel(
                    model_name='gemini-2.5-flash', 
                    system_instruction=system_instruction
                )
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.6, 
                        max_output_tokens=600 
                    )
                )
                
                return response.text.strip()

            except Exception as e:
                print(f"[AI Error on Key #{current_key_index + 1}]: {e}")
                
                if attempt == max_attempts - 1:
                    return "System Overload. Please try again later. 💀"
                
                rotate_key()
                continue

    except Exception as e:
        print(f"[Critical System Error]: {e}")
        return "I can't reach the archives right now. 💜"

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("User: Contact info?")
    print("Ani:", get_gemini_response("How can I contact Cid?"))
    
