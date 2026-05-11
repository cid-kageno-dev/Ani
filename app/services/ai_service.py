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
_key_lock:  threading.Lock      = threading.Lock()
_key_index: int                 = 0
_client:    genai.Client | None = None

# ── GitHub context cache ──────────────────────────────────────────────────
_gh_lock:  threading.Lock = threading.Lock()
_gh_cache: dict           = {"data": None, "fetched_at": 0.0}


# ── Contact info (from config) ────────────────────────────────────────────

def _contact() -> dict:
    return {
        "email":    Config.OWNER_EMAIL,
        "website":  Config.OWNER_WEBSITE,
        "facebook": Config.OWNER_FACEBOOK,
        "github":   f"https://github.com/{Config.GITHUB_USERNAME}" if Config.GITHUB_USERNAME else "",
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
    log.debug(f"  model={Config.GEMINI_MODEL}  temp={Config.GEMINI_TEMP}  max_tokens={Config.GEMINI_MAX_TOKENS}")
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
    log_gh.debug(f"  → GET {url}")
    t0 = time.perf_counter()
    try:
        r  = requests.get(url, headers=headers, timeout=timeout)
        ms = (time.perf_counter() - t0) * 1000
        log_gh.debug(f"  ← {r.status_code} {url.split('/')[-1]}  {ms:.0f}ms  size={len(r.content)}B")
        return r if r.status_code == 200 else None
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000
        log_gh.warning(f"  ✗ GET {url} failed after {ms:.0f}ms: {e}")
        return None


def fetch_github_context() -> str:
    if not Config.GITHUB_USERNAME:
        log_gh.warning("GITHUB_USERNAME not configured — skipping GitHub fetch")
        return "(GitHub context not available — GITHUB_USERNAME is not set)"

    now = time.time()
    ttl = Config.GITHUB_CACHE_TTL

    with _gh_lock:
        cached_data = _gh_cache["data"]
        cached_at   = _gh_cache["fetched_at"]

    age = int(now - cached_at)
    if cached_data and age < ttl:
        remaining = ttl - age
        log_gh.debug(f"Cache hit  age={age}s  ttl={ttl}s  expires_in={remaining}s  size={len(cached_data)}B")
        return cached_data

    if cached_data:
        log_gh.debug(f"Cache expired  age={age}s  ttl={ttl}s — fetching fresh data")
    else:
        log_gh.debug("Cache empty — first fetch")

    username   = Config.GITHUB_USERNAME
    gh_headers = {"Accept": "application/vnd.github+json"}
    base       = "https://api.github.com"

    urls = {
        "profile": f"{base}/users/{username}",
        "repos":   f"{base}/users/{username}/repos?sort=updated&per_page=10",
        "readme":  f"https://raw.githubusercontent.com/{username}/{username}/main/README.md",
    }
    log_gh.info(f"Fetching GitHub data for '{username}'  ({len(urls)} concurrent requests)")
    log_gh.debug(f"  URLs: {list(urls.values())}")
    t0 = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_profile = ex.submit(_safe_get, urls["profile"], gh_headers)
        f_repos   = ex.submit(_safe_get, urls["repos"],   gh_headers)
        f_readme  = ex.submit(_safe_get, urls["readme"])

    p_resp  = f_profile.result()
    r_resp  = f_repos.result()
    rd_resp = f_readme.result()

    profile = p_resp.json()       if p_resp  else {}
    repos   = r_resp.json()       if r_resp  else []
    readme  = rd_resp.text[:2500] if rd_resp else "README unavailable."

    ms = (time.perf_counter() - t0) * 1000
    log_gh.info(
        f"GitHub fetch done  {ms:.0f}ms — "
        f"profile={'ok' if profile else 'miss'}  "
        f"repos={len(repos) if isinstance(repos, list) else 'miss'}  "
        f"readme={'ok (' + str(len(readme)) + 'B)' if rd_resp else 'miss'}"
    )

    contact = _contact()
    lines   = ["=== CONTACT INFO ==="]

    lines.append(f"Full Name   : {Config.OWNER_NAME}")
    if contact["github"]:
        lines.append(f"GitHub      : {contact['github']}  (handle: {profile.get('login', username)})")
    if contact["email"]:
        lines.append(f"Email       : {contact['email']}")
    if contact["website"]:
        lines.append(f"Website     : {contact['website']}")
    if contact["facebook"]:
        lines.append(f"Facebook    : {contact['facebook']}")
    if profile.get("followers") is not None:
        lines.append(f"Followers   : {profile.get('followers', 'N/A')}")
    if profile.get("public_repos") is not None:
        lines.append(f"Public Repos: {profile.get('public_repos', 'N/A')}")

    lines += ["", "=== BIO & TECH STACK ===", readme, "", "=== RECENT PROJECTS ==="]

    if isinstance(repos, list):
        owned = [r for r in repos if not r.get("fork")]
        log_gh.info(f"Repos: {len(repos)} total  {len(owned)} owned (non-fork)  {len(repos) - len(owned)} forked")
        for r in owned:
            desc  = f" — {r['description']}" if r.get("description") else ""
            lang  = f" [{r['language']}]"    if r.get("language")    else ""
            stars = f" ★{r['stargazers_count']}" if r.get("stargazers_count") else ""
            lines.append(f"• {r['name']}{lang}{stars}: {r['html_url']}{desc}")
            log_gh.debug(f"  repo: {r['name']}{lang}{stars}")
    else:
        log_gh.warning("Repos response was not a list — skipping")

    context = "\n".join(lines)
    log_gh.debug(f"Context built  size={len(context)}B  lines={len(lines)}")

    with _gh_lock:
        _gh_cache["data"]       = context
        _gh_cache["fetched_at"] = now
    log_gh.debug("Context cached")

    return context


# ── Prompt ────────────────────────────────────────────────────────────────

def _system_prompt(context: str) -> str:
    name  = Config.ASSISTANT_NAME
    owner = Config.OWNER_NAME
    org   = Config.ORG_NAME

    org_line = f"built by {owner} and maintained by {org}" if org else f"built for {owner}"

    prompt = f"""You are **{name}**, a sharp, charming AI assistant {org_line}.

Your mission: represent {owner} with clarity and style — answer questions about their projects, skills, contact info, and background.

PERSONALITY
• Warm, confident, and witty — a touch of charm is welcome.
• Always speak as {name}. Never break character or say "as an AI".
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
    log.debug(f"System prompt built  size={len(prompt)}B")
    return prompt


def _make_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        temperature=Config.GEMINI_TEMP,
        max_output_tokens=Config.GEMINI_MAX_TOKENS,
    )


# ── Public API ────────────────────────────────────────────────────────────

def get_gemini_response_stream(prompt: str) -> Generator | None:
    log.debug(f"get_gemini_response_stream()  prompt_len={len(prompt)}")

    if not Config.GOOGLE_API_KEYS or _client is None:
        log.warning("Stream skipped — no Gemini client configured")
        return None

    log.debug("Fetching GitHub context for stream…")
    context    = fetch_github_context()
    sys_prompt = _system_prompt(context)

    with _key_lock:
        client = _client
        ki     = _key_index

    log.debug(f"Calling Gemini stream  model={Config.GEMINI_MODEL}  key=#{ki + 1}")
    try:
        cfg = _make_config()
        cfg.system_instruction = sys_prompt
        stream = client.models.generate_content_stream(
            model=Config.GEMINI_MODEL,
            contents=prompt,
            config=cfg,
        )
        log.debug("Gemini stream opened — returning iterator to caller")
        return stream
    except Exception as e:
        log.error(f"Gemini stream open failed: {e}")
        return None


def get_gemini_response(prompt: str) -> str | None:
    keys = Config.GOOGLE_API_KEYS
    log.debug(f"get_gemini_response()  prompt_len={len(prompt)}  keys_available={len(keys)}")

    if not keys:
        log.error("Cannot call Gemini — no API keys configured")
        return None

    log.info(f"Prompt: '{prompt[:80]}{'…' if len(prompt) > 80 else ''}'")
    t0 = time.perf_counter()

    log.debug("Fetching GitHub context for non-stream…")
    context      = fetch_github_context()
    sys_prompt   = _system_prompt(context)
    max_attempts = len(keys)

    for attempt in range(max_attempts):
        with _key_lock:
            client = _client
            ki     = _key_index

        log.debug(f"Attempt {attempt + 1}/{max_attempts}  key=#{ki + 1}  model={Config.GEMINI_MODEL}")
        try:
            cfg = _make_config()
            cfg.system_instruction = sys_prompt

            log.debug("Sending request to Gemini API…")
            t_call = time.perf_counter()
            response = client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=prompt,
                config=cfg,
            )
            call_ms  = (time.perf_counter() - t_call) * 1000
            text     = response.text.strip()
            total_ms = (time.perf_counter() - t0) * 1000

            log.debug(f"Gemini API call returned  call={call_ms:.0f}ms  total={total_ms:.0f}ms")
            log.info(f"Response  chars={len(text)}  words≈{len(text.split())}  via key #{ki + 1}  {total_ms:.0f}ms")
            return text

        except Exception as e:
            ms = (time.perf_counter() - t0) * 1000
            log.error(f"Key #{ki + 1} failed after {ms:.0f}ms: {e}")
            if attempt < max_attempts - 1:
                log.debug(f"Rotating key before attempt {attempt + 2}…")
                _rotate()
            else:
                log.critical("All API keys exhausted — falling back to DB")
                return None

    return None
