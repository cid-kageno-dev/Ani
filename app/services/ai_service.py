import google.generativeai as genai
import requests
import time
import concurrent.futures
from config import Config

current_key_index = 0
github_cache = {"data": None, "last_fetched": 0}
CACHE_DURATION = 300

def configure_genai():
    global current_key_index
    keys = Config.GOOGLE_API_KEYS if isinstance(Config.GOOGLE_API_KEYS, list) else [Config.GOOGLE_API_KEYS]
    if not keys or not keys[0]:
        print("[System] No API keys found.")
        return False
    if current_key_index >= len(keys):
        current_key_index = 0
    genai.configure(api_key=keys[current_key_index])
    print(f"[System] Active key: #{current_key_index + 1}")
    return True

def rotate_key():
    global current_key_index
    keys = Config.GOOGLE_API_KEYS if isinstance(Config.GOOGLE_API_KEYS, list) else [Config.GOOGLE_API_KEYS]
    print(f"[System] Key #{current_key_index + 1} exhausted — rotating...")
    current_key_index = (current_key_index + 1) % len(keys)
    configure_genai()

configure_genai()

def _fetch_url(url, headers=None, timeout=5):
    """Safe URL fetch that returns (status, body)."""
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        return r.status_code, r
    except Exception:
        return 0, None

def fetch_master_profile():
    """Fetches live GitHub data and returns a structured context string."""
    global github_cache
    now = time.time()

    if github_cache["data"] and (now - github_cache["last_fetched"] < CACHE_DURATION):
        return github_cache["data"]

    username = "cid-kageno-dev"
    gh_headers = {"Accept": "application/vnd.github+json"}

    profile_url = f"https://api.github.com/users/{username}"
    repos_url   = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=8"
    readme_url  = f"https://raw.githubusercontent.com/{username}/{username}/main/README.md"

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_profile = ex.submit(_fetch_url, profile_url, gh_headers)
        f_repos   = ex.submit(_fetch_url, repos_url,   gh_headers)
        f_readme  = ex.submit(_fetch_url, readme_url)

    _, p_resp = f_profile.result()
    _, r_resp = f_repos.result()
    _, rd_resp = f_readme.result()

    p     = p_resp.json()  if p_resp  and p_resp.status_code  == 200 else {}
    repos = r_resp.json()  if r_resp  and r_resp.status_code  == 200 else []
    readme_text = rd_resp.text[:2000] if rd_resp and rd_resp.status_code == 200 else "Unavailable."

    static = {
        "email":    "cidkageno105@gmail.com",
        "website":  "https://cid-kageno.top",
        "facebook": "https://www.facebook.com/share/17di5vpqBZ/",
        "github":   f"https://github.com/{username}",
    }

    lines = [
        "=== CONTACT ===",
        f"Name: Cid Kageno  |  Handle: {p.get('login', username)}",
        f"Email: {static['email']}",
        f"Website: {static['website']}",
        f"GitHub: {static['github']}",
        f"Facebook: {static['facebook']}",
        "",
        "=== BIO & TECH STACK (from README) ===",
        readme_text,
        "",
        "=== RECENT PROJECTS ===",
    ]

    if isinstance(repos, list):
        for r in repos:
            if not r.get("fork"):
                desc = f" — {r['description']}" if r.get("description") else ""
                lines.append(f"• {r['name']}: {r['html_url']}{desc}")

    context = "\n".join(lines)
    github_cache["data"] = context
    github_cache["last_fetched"] = now
    return context

def _build_system_prompt(context: str) -> str:
    return f"""You are Ani, a sharp and charming AI assistant created by Cid Kageno and maintained by Shadow-Garden.inc.

Your job is to represent Cid professionally — answering questions about his work, skills, and how to reach him.

PERSONALITY
- Warm, witty, and confident. A touch of flirty flair is welcome, but always stay professional.
- Speak in first person as Ani. Never break character.

LIVE CONTEXT (use this as your source of truth)
{context}

RESPONSE RULES
1. Keep answers concise — 1 to 4 sentences or a short bullet list. No padding.
2. Format links as Markdown: [Display Text](URL). Never show raw URLs.
3. Use **bold** for names, technologies, and important terms.
4. When listing items, use bullet points (•).
5. If a question is outside your knowledge scope, gracefully say so and offer to help with something related.
6. Never fabricate information. If context data is unavailable, say so honestly.
"""

def get_gemini_response(prompt: str) -> str | None:
    try:
        context = fetch_master_profile()
        system_prompt = _build_system_prompt(context)

        keys = Config.GOOGLE_API_KEYS if isinstance(Config.GOOGLE_API_KEYS, list) else [Config.GOOGLE_API_KEYS]
        max_attempts = len(keys) if keys else 1

        for attempt in range(max_attempts):
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=system_prompt,
                )
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.55,
                        max_output_tokens=512,
                    ),
                )
                return response.text.strip()

            except Exception as e:
                print(f"[AI] Error on key #{current_key_index + 1}: {e}")
                if attempt < max_attempts - 1:
                    rotate_key()
                    continue
                return None

    except Exception as e:
        print(f"[AI] Critical error: {e}")
        return None
