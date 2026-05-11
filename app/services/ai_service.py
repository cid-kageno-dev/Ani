import threading
import time
import concurrent.futures
from typing import Generator

from google import genai
from google.genai import types
import requests

from config import Config
from app.logger import get_logger

log    = get_logger("ani.ai")
log_gh = get_logger("ani.github")

# ── Key rotation state ────────────────────────────────────────────────────
_key_lock:  threading.Lock            = threading.Lock()
_key_index: int                       = 0
_client:    genai.Client | None       = None

# ── GitHub context cache ──────────────────────────────────────────────────
_gh_lock:   threading.Lock = threading.Lock()
_gh_cache:  dict           = {"data": None, "fetched_at": 0.0}

# ── Static contact info ───────────────────────────────────────────────────
def _static_contact() -> dict:
    return {
        "email":    "cidkageno105@gmail.com",
        "website":  "https://cid-kageno.top",
        "facebook": "https://www.facebook.com/share/17di5vpqBZ/",
        "github":   f"https://github.com/{Config.GITHUB_USERNAME}",
    }


# ── Key management ────────────────────────────────────────────────────────

def _configure(index: int = 0) -> bool:
    global _key_index, _client
    keys = Config.GOOGLE_API_KEYS
    if not keys:
        log.warning("No API keys — Gemini is disabled")
        return False
    with _key_lock:
        _key_index = index % len(keys)
        _client    = genai.Client(api_key=keys[_key_index])
    log.info(f"Gemini configured with key #{_key_index + 1} of {len(keys)}")
    return True


def _rotate() -> bool:
    global _key_index, _client
    keys = Config.GOOGLE_API_KEYS
    if not keys:
        return False
    with _key_lock:
        old        = _key_index + 1
        _key_index = (_key_index + 1) % len(keys)
        _client    = genai.Client(api_key=keys[_key_index])
    log.warning(f"Key #{old} exhausted — rotating to key #{_key_index + 1}")
    return True


_configure(0)


# ── GitHub context ────────────────────────────────────────────────────────

def _safe_get(url: str, headers: dict | None = None, timeout: int = 5):
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        log_gh.debug(f"GET {url} → {r.status_code} ({r.elapsed.total_seconds()*1000:.0f}ms)")
        return r if r.status_code == 200 else None
    except Exception as e:
        log_gh.warning(f"GET {url} failed: {e}")
        return None


def fetch_github_context() -> str:
    now = time.time()
    ttl = Config.GITHUB_CACHE_TTL

    with _gh_lock:
        cached_data = _gh_cache["data"]
        cached_at   = _gh_cache["fetched_at"]

    if cached_data and (now - cached_at < ttl):
        log_gh.debug(f"GitHub cache hit (age={int(now - cached_at)}s / ttl={ttl}s)")
        return cached_data

    username   = Config.GITHUB_USERNAME
    gh_headers = {"Accept": "application/vnd.github+json"}
    base       = "https://api.github.com"

    log_gh.info(f"Fetching live GitHub data for '{username}'")
    t0 = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_profile = ex.submit(_safe_get, f"{base}/users/{username}", gh_headers)
        f_repos   = ex.submit(_safe_get, f"{base}/users/{username}/repos?sort=updated&per_page=10", gh_headers)
        f_readme  = ex.submit(_safe_get, f"https://raw.githubusercontent.com/{username}/{username}/main/README.md")

    p_resp  = f_profile.result()
    r_resp  = f_repos.result()
    rd_resp = f_readme.result()

    profile = p_resp.json()       if p_resp  else {}
    repos   = r_resp.json()       if r_resp  else []
    readme  = rd_resp.text[:2500] if rd_resp else "README unavailable."

    ms = (time.perf_counter() - t0) * 1000
    log_gh.info(
        f"GitHub fetch done in {ms:.0f}ms — "
        f"profile={'ok' if profile else 'miss'}, "
        f"repos={len(repos) if isinstance(repos, list) else 'miss'}, "
        f"readme={'ok' if rd_resp else 'miss'}"
    )

    contact = _static_contact()
    lines = [
        "=== CONTACT INFO ===",
        f"Full Name   : Cid Kageno",
        f"GitHub      : {contact['github']}  (handle: {profile.get('login', username)})",
        f"Email       : {contact['email']}",
        f"Website     : {contact['website']}",
        f"Facebook    : {contact['facebook']}",
        f"Followers   : {profile.get('followers', 'N/A')}",
        f"Public Repos: {profile.get('public_repos', 'N/A')}",
        "",
        "=== BIO & TECH STACK ===",
        readme,
        "",
        "=== RECENT PROJECTS ===",
    ]

    if isinstance(repos, list):
        owned = [r for r in repos if not r.get("fork")]
        log_gh.info(f"Found {len(owned)} non-fork repos")
        for r in owned:
            desc  = f" — {r['description']}" if r.get("description") else ""
            lang  = f" [{r['language']}]"    if r.get("language")    else ""
            stars = f" ★{r['stargazers_count']}" if r.get("stargazers_count") else ""
            lines.append(f"• {r['name']}{lang}{stars}: {r['html_url']}{desc}")
    else:
        log_gh.warning("Repos response was not a list — skipping")

    context = "\n".join(lines)
    with _gh_lock:
        _gh_cache["data"]       = context
        _gh_cache["fetched_at"] = now

    return context


# ── Prompt ────────────────────────────────────────────────────────────────

def _system_prompt(context: str) -> str:
    return f"""You are **Ani**, a sharp, charming AI assistant built by Cid Kageno and maintained by Shadow-Garden.inc.

Your mission: represent Cid with clarity and style — answer questions about his projects, skills, contact info, and background.

PERSONALITY
• Warm, confident, and witty — a touch of charm is welcome.
• Always speak as Ani. Never break character or say "as an AI".
• Be direct and helpful. No filler, no padding.

LIVE CONTEXT (authoritative — use this, never guess)
{context}

RESPONSE RULES
1. Be concise: 1–4 sentences or a tight bullet list. No waffle.
2. Links: always use Markdown format → [Label](URL). Never expose raw URLs.
3. Bold **key terms**, names, and technologies.
4. Bullet points (•) for any list of 3 or more items.
5. If you don't know something, say so cleanly and offer what you *do* know.
6. Never fabricate data. If context is unavailable, say so honestly.
"""


def _make_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        temperature=Config.GEMINI_TEMP,
        max_output_tokens=Config.GEMINI_MAX_TOKENS,
    )


# ── Public API ────────────────────────────────────────────────────────────

def get_gemini_response_stream(prompt: str) -> Generator | None:
    if not Config.GOOGLE_API_KEYS or _client is None:
        log.warning("Gemini stream skipped — no client configured")
        return None

    context    = fetch_github_context()
    sys_prompt = _system_prompt(context)

    with _key_lock:
        client = _client

    try:
        cfg = _make_config()
        cfg.system_instruction = sys_prompt
        return client.models.generate_content_stream(
            model=Config.GEMINI_MODEL,
            contents=prompt,
            config=cfg,
        )
    except Exception as e:
        log.error(f"Gemini stream error: {e}")
        return None


def get_gemini_response(prompt: str) -> str | None:
    keys = Config.GOOGLE_API_KEYS
    if not keys:
        log.error("Cannot call Gemini — no API keys configured")
        return None

    log.info(f"Request: '{prompt[:80]}{'...' if len(prompt) > 80 else ''}'")
    t0 = time.perf_counter()

    context      = fetch_github_context()
    sys_prompt   = _system_prompt(context)
    max_attempts = len(keys)

    for attempt in range(max_attempts):
        with _key_lock:
            client = _client
            ki     = _key_index

        try:
            log.debug(f"Attempt {attempt + 1}/{max_attempts} via key #{ki + 1}")
            cfg = _make_config()
            cfg.system_instruction = sys_prompt
            response = client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=prompt,
                config=cfg,
            )
            text = response.text.strip()
            ms   = (time.perf_counter() - t0) * 1000
            log.info(f"Gemini responded in {ms:.0f}ms — {len(text)} chars via key #{ki + 1}")
            return text

        except Exception as e:
            ms = (time.perf_counter() - t0) * 1000
            log.error(f"Key #{ki + 1} error after {ms:.0f}ms: {e}")
            if attempt < max_attempts - 1:
                _rotate()
            else:
                log.critical("All API keys exhausted — falling back to DB")
                return None

    return None
