# 💜 Ani - AI Assistant

> A context-aware AI chatbot built to showcase developer projects, handle professional inquiries, and automate portfolio interaction. Powered by Google Gemini 2.5 Flash.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-8E75B2?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-Web-000000?style=for-the-badge&logo=flask)

## ⚡ Key Features

* **🧠 Intelligent Persona:** Actively roleplays as "Ani," an AI assistant created by Cid Kageno.
* **🔄 Smart Key Rotation:** Automatically cycles through multiple API keys (`KEY1`, `KEY2`, etc.) to bypass rate limits and ensure 99.9% uptime.
* **📂 Live GitHub Sync:** Fetches real-time repository data, bio, and contact info via the GitHub API.
* **🚀 Efficient Caching:** Implements a 5-minute caching layer to prevent hitting GitHub API rate limits.
* **🛡️ Fail-Safe Architecture:** Dynamic fallback systems for both AI generation and data fetching.

---

## 🛠️ Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/cid-kageno-dev/ani.git](https://github.com/cid-kageno-dev/ani.git)
    cd ani
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚙️ Configuration

This project uses a **Dynamic Key Loader**. You can add as many API keys as you want in the `.env` file, and the system will automatically detect and rotate them.

1.  Create a `.env` file in the root directory.
2.  Add your configuration:

```ini
# .env file

# --- API KEY ROTATION SYSTEM ---
# Add as many keys as you need. The system reads them sequentially.
GOOGLE_API_KEY1="AIzaSyD-YourFirstKey..."
GOOGLE_API_KEY2="AIzaSyD-YourSecondKey..."
GOOGLE_API_KEY3="AIzaSyD-YourThirdKey..."

# --- GOOGLE SHEETS (Optional) ---
SHEET_NAME="Ani_Logs"
GOOGLE_SHEET_CREDS="credits.json"
