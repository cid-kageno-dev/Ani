import requests
from config import Config

def fetch_master_context():
    """
    Fetches Cid Kageno's GitHub profile and pinned/recent repos.
    Returns a formatted string for the AI system instruction.
    """
    username = "cid-kageno-dev" # Or Config.GITHUB_USERNAME
    headers = {
        "Accept": "application/vnd.github+json",
        # "Authorization": f"Bearer {Config.GITHUB_TOKEN}" # Optional: Uncomment if you hit rate limits
    }

    try:
        # 1. Fetch Profile (Bio, Location, etc.)
        profile_url = f"https://api.github.com/users/{username}"
        p_res = requests.get(profile_url, headers=headers, timeout=5)
        p_data = p_res.json() if p_res.status_code == 200 else {}

        # 2. Fetch Repositories (Sorted by updated)
        repo_url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=5"
        r_res = requests.get(repo_url, headers=headers, timeout=5)
        r_data = r_res.json() if r_res.status_code == 200 else []

        # 3. Format Data for Gemini
        context_str = f"--- MASTER ARCHIVE DATA ---\n"
        context_str += f"Developer: {p_data.get('name', username)}\n"
        context_str += f"Bio: {p_data.get('bio', 'N/A')}\n"
        context_str += f"Public Repos: {p_data.get('public_repos', 0)}\n\n"
        
        context_str += "RECENT PROJECTS:\n"
        for repo in r_data:
            # Skip forks if you only want original work
            if repo.get('fork', False): 
                continue
                
            context_str += f"- Name: {repo.get('name')}\n"
            context_str += f"  Language: {repo.get('language')}\n"
            context_str += f"  Desc: {repo.get('description', 'No description')}\n"
            context_str += f"  Url: {repo.get('html_url')}\n"

        return context_str

    except Exception as e:
        print(f"[GitHub Service Error]: {e}")
        return "Error accessing Shadow Garden archives."
      
