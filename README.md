# 💜 Ani - AI Assistant

> A context-aware AI chatbot built to showcase developer projects, handle professional inquiries, and automate portfolio interaction. Powered by Google Gemini 2.5 Flash.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-8E75B2?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-Web-000000?style=for-the-badge&logo=flask)
![Tests](https://img.shields.io/github/actions/workflow/status/cid-kageno-dev/Ani/tests.yml?branch=main&style=for-the-badge&label=Tests)

---

## ⚡ Key Features

* **🧠 Intelligent Persona:** Actively roleplays as "Ani," an AI assistant created by Cid Kageno.
* **🔄 Smart Key Rotation:** Automatically cycles through multiple API keys (`KEY1`, `KEY2`, etc.) to bypass rate limits and ensure 99.9% uptime.
* **📂 Live GitHub Sync:** Fetches real-time repository data, bio, and contact info via the GitHub API.
* **🚀 Efficient Caching:** Implements a 5-minute caching layer to prevent hitting GitHub API rate limits.
* **🛡️ Fail-Safe Architecture:** Dynamic fallback systems for both AI generation and data fetching.
* **⚙️ Multi-Database Support:** Firebase Firestore with PostgreSQL fallback.
* **🐳 Containerized:** Full Docker & Docker Compose support for easy deployment.

---

## 🚀 Quick Start (30 seconds)

```bash
# Clone the repository
git clone https://github.com/cid-kageno-dev/Ani.git
cd Ani

# Copy environment template
cp .env.example .env

# Add your Google Gemini API key to .env
echo 'GOOGLE_API_KEY1="your-api-key-here"' >> .env

# Install dependencies
pip install -r requirements.txt

# Run the dev server
python run.py
```

Server starts at `http://localhost:5000` 🎉

---

## 🛠️ Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- (Optional) Docker & Docker Compose
- (Optional) Firebase account for Firestore

### Step-by-Step Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/cid-kageno-dev/Ani.git
   cd Ani
   ```

2. **Create Virtual Environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Linux/Mac:
   source venv/bin/activate
   
   # On Windows:
   venv\\Scripts\\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables** (see Configuration section below)
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Run the Application**
   ```bash
   # Development server with auto-reload
   python run.py
   
   # Production server with Gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
   ```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory with the following:

```ini
# ========================================
# GOOGLE GEMINI AI
# ========================================
# Add as many API keys as needed. System auto-detects and rotates them.
GOOGLE_API_KEY1="AIzaSyD-YourFirstKey..."
GOOGLE_API_KEY2="AIzaSyD-YourSecondKey..."
GOOGLE_API_KEY3="AIzaSyD-YourThirdKey..."

# Model configuration
GEMINI_MODEL="gemini-2.5-flash"
GEMINI_TEMP=0.55              # Temperature (0.0-2.0)
GEMINI_MAX_TOKENS=512         # Max response tokens

# ========================================
# DATABASE
# ========================================
# Auto-detect: Firebase if configured, else PostgreSQL
DATABASE_BACKEND="auto"       # Options: auto, firebase, postgresql

# Firebase Firestore
FIREBASE_CREDENTIALS="firebase-key.json"
FIREBASE_SERVICE_ACCOUNT_JSON=""  # Inline JSON if needed
FIREBASE_PROJECT_ID=""
FIREBASE_DATABASE_URL=""
FIREBASE_COLLECTION="chat_interactions"

# PostgreSQL fallback
DATABASE_URL="postgresql://user:password@localhost:5432/ani_db"

# ========================================
# GITHUB
# ========================================
GITHUB_USERNAME="cid-kageno-dev"
GITHUB_CACHE_TTL=300          # Cache duration in seconds (default: 5 min)

# ========================================
# APPLICATION
# ========================================
FLASK_DEBUG=true              # Set to false in production
LOG_LEVEL="INFO"              # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Optional: Google Sheets logging
SHEET_NAME="Ani_Logs"
GOOGLE_SHEET_CREDS="credits.json"
```

### Firebase Setup

To use Firebase Firestore for chat history:

1. Create a Firebase project at [firebase.google.com](https://firebase.google.com)
2. Generate a service account key: Firebase Console → Project Settings → Service Accounts → Generate New Private Key
3. Save as `firebase-key.json` in the project root, or set `FIREBASE_SERVICE_ACCOUNT_JSON` with the JSON content
4. Enable Firestore Database in your Firebase console

**Firestore Document Structure:**

```
Collection: chat_interactions
├── Document: {auto-generated ID}
│   ├── user_query: string
│   ├── ai_response: string
│   ├── source: string ("AI Response" | "Database")
│   └── created_at: timestamp
```

---

## 💬 Usage Examples

### Web Interface

Access the web UI at `http://localhost:5000`

```
┌─────────────────────────────────┐
│  💜 Chat with Ani               │
├─────────────────────────────────┤
│ Ask me about Cid's projects!    │
│ Type your question...           │
│                                 │
│ [Send]                          │
└─────────────────────────────────┘
```

### API Endpoints

#### 1. **Health Check**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "ai_ready": true,
  "db_ready": true
}
```

#### 2. **Chat with Ani**
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about your creator"
  }'
```

**Response:**
```json
{
  "user_query": "Tell me about your creator",
  "ai_response": "I'm Ani, an AI assistant created by Cid Kageno...",
  "source": "AI Response",
  "timestamp": "2026-05-17T12:34:56Z"
}
```

#### 3. **Get GitHub Info**
```bash
curl http://localhost:5000/api/github
```

**Response:**
```json
{
  "username": "cid-kageno-dev",
  "bio": "Developer & AI Enthusiast",
  "repositories": 12,
  "followers": 45,
  "public_repos": [
    {
      "name": "Ani",
      "description": "Smart AI Assistant",
      "url": "https://github.com/cid-kageno-dev/Ani",
      "stars": 3
    }
  ],
  "cached": false,
  "cache_expires_in": 300
}
```

#### 4. **Cache Management**
```bash
# Check cache status
curl http://localhost:5000/api/cache/status

# Clear all cache
curl -X POST http://localhost:5000/api/cache/clear

# Clear GitHub cache specifically
curl -X POST http://localhost:5000/api/cache/clear/github
```

#### 5. **Chat History** (if database configured)
```bash
curl http://localhost:5000/api/history?limit=10
```

### Python Integration

```python
import requests

BASE_URL = "http://localhost:5000"

# Send a message
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={"message": "What projects have you worked on?"}
)

data = response.json()
print(f"Ani: {data['ai_response']}")

# Get GitHub stats
github_data = requests.get(f"{BASE_URL}/api/github").json()
print(f"GitHub repos: {github_data['repositories']}")
```

### JavaScript/Fetch

```javascript
// Send a message
const response = await fetch('http://localhost:5000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Tell me about Ani' })
});

const data = await response.json();
console.log('Ani says:', data.ai_response);
```

---

## 🧪 Testing

### Run Tests Locally

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_endpoints.py -v

# Run with verbose output
pytest -v

# Run with markers (only unit tests)
pytest -m "not integration"
```

### Test Coverage

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### What's Tested

- ✅ API endpoints (health, chat, GitHub, cache)
- ✅ Configuration loading
- ✅ Cache operations
- ✅ Error handling
- ✅ Database connectivity
- ✅ AI response generation

---

## 🐳 Docker Deployment

### Docker Build & Run

```bash
# Build the image
docker build -t ani:latest .

# Run container
docker run -p 5000:5000 \
  -e GOOGLE_API_KEY1="your-key" \
  -e GEMINI_MODEL="gemini-2.5-flash" \
  ani:latest
```

### Docker Compose

```bash
# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  ani:
    build: .
    ports:
      - "5000:5000"
    environment:
      - GOOGLE_API_KEY1=${GOOGLE_API_KEY1}
      - DATABASE_BACKEND=postgresql
      - DATABASE_URL=postgresql://ani_user:ani_pass@postgres:5432/ani_db
      - FLASK_DEBUG=false
    depends_on:
      - postgres
    volumes:
      - ./logs:/app/logs

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=ani_user
      - POSTGRES_PASSWORD=ani_pass
      - POSTGRES_DB=ani_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
EOF

# Start services
docker-compose up -d

# View logs
docker-compose logs -f ani
```

---

## ☁️ Cloud Deployment

### Railway

1. Push to GitHub
2. Connect GitHub repo to Railway
3. Add environment variables in Railway dashboard
4. Deploy!

```bash
# Railway CLI
railway login
railway init
railway up
```

### Render

1. Connect GitHub repository
2. Create new Web Service
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"`
5. Add environment variables
6. Deploy!

### Heroku

```bash
# Create app
heroku create ani-app

# Add buildpack
heroku buildpacks:add heroku/python

# Set environment variables
heroku config:set GOOGLE_API_KEY1="your-key"
heroku config:set DATABASE_BACKEND="postgresql"

# Deploy
git push heroku main
```

---

## 🔧 Troubleshooting

### Issue: "No API keys found"
**Solution:** Ensure `GOOGLE_API_KEY1` is set in `.env` or environment variables
```bash
echo "GOOGLE_API_KEY1=your_key" >> .env
```

### Issue: "Firebase not configured"
**Solution:** Either:
- Set `FIREBASE_CREDENTIALS` to path of service account JSON
- Or set `FIREBASE_SERVICE_ACCOUNT_JSON` with inline JSON
- Or set `FIREBASE_PROJECT_ID` for application-default credentials

### Issue: Database connection failed
**Solution:** Check `DATABASE_URL` format and ensure database server is running
```bash
# Test connection
psql postgresql://user:password@localhost:5432/ani_db
```

### Issue: Port 5000 already in use
**Solution:** Use different port
```bash
# Linux/Mac
PORT=8080 python run.py

# Windows
set PORT=8080 && python run.py
```

### Issue: CORS errors in browser
**Solution:** Ensure Flask-CORS is installed and configured
```bash
pip install flask-cors
```

---

## ⚡ Performance Tips

### 1. **Enable Caching**
- GitHub cache TTL: Set `GITHUB_CACHE_TTL` to 300-600 seconds
- Reduces API rate limiting

### 2. **Multiple API Keys**
- Configure `GOOGLE_API_KEY1`, `GOOGLE_API_KEY2`, etc.
- System auto-rotates on rate limits

### 3. **Use PostgreSQL**
- More efficient than file-based storage
- Better for production use

### 4. **Production Mode**
```bash
# Use Gunicorn with multiple workers
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 30 "app:create_app()"
```

### 5. **Monitor Logs**
```bash
# Tail logs
tail -f logs/app.log

# Filter by level
grep "ERROR" logs/app.log
```

---

## 📊 CI/CD Pipeline

Automated testing and deployment with GitHub Actions:

- ✅ Tests run on every push & PR (Python 3.10, 3.11, 3.12)
- ✅ Code quality checks (Black, Flake8, mypy)
- ✅ Security scanning (Bandit)
- ✅ Docker image build validation
- ✅ Docker image push on main branch
- ✅ Coverage reports to Codecov

Check `.github/workflows/` for workflow configs.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick Start for Contributors:**
```bash
# Clone and setup
git clone https://github.com/cid-kageno-dev/Ani.git
cd Ani
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
pytest
black .
flake8 .

# Push and create PR
git push origin feature/your-feature
```

---

## 📋 Roadmap

- [ ] Web UI improvements
- [ ] Voice chat support
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Real-time notifications
- [ ] Integration with more AI models

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Cid Kageno** - [GitHub](https://github.com/cid-kageno-dev) | [Portfolio](https://cid-kageno.dev)

Meet **Ani** - Your smart portfolio AI assistant! 💜

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/cid-kageno-dev/Ani/issues)
- **Discussions:** [GitHub Discussions](https://github.com/cid-kageno-dev/Ani/discussions)
- **Email:** Contact via GitHub profile

---

**Last Updated:** May 17, 2026
