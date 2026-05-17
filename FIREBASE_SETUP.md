📋 Firebase Multi-Environment Setup Guide
==========================================

This guide covers Firebase configuration across all deployment environments.

## Quick Start

### 1️⃣ Local Development

```bash
# Copy your Firebase service account key
cp ~/Downloads/firebase-key.json ./

# Create .env file
cp .env.example .env

# Run the app
python run.py
```

**Or use environment variable:**
```bash
export FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
python run.py
```

### 2️⃣ Docker

```bash
# Build and run with docker-compose
docker-compose up --build

# Or manually:
docker build -t ani .
docker run -e FIREBASE_SERVICE_ACCOUNT_JSON='...' ani
```

### 3️⃣ Replit

1. Go to Replit Secrets (lock icon)
2. Add:
   - `GOOGLE_API_KEY1`: Your Gemini API key
   - `FIREBASE_SERVICE_ACCOUNT_JSON`: Your Firebase service account JSON

3. The `.replit` file already includes:
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_DATABASE_URL`

4. Click "Run"

### 4️⃣ GitHub Actions

1. Go to repo Settings → Secrets and Variables → Actions
2. Add these secrets:
   - `GOOGLE_API_KEY1`
   - `FIREBASE_SERVICE_ACCOUNT_JSON`
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_DATABASE_URL`

3. Workflow will auto-detect and use them

### 5️⃣ Production (Cloud Run, Heroku)

**Google Cloud Run:**
```bash
gcloud run deploy ani \
  --set-env-vars GOOGLE_API_KEY1=AIza... \
  --set-env-vars FIREBASE_PROJECT_ID=my-project \
  --set-env-vars FIREBASE_SERVICE_ACCOUNT_JSON='...'
```

**Heroku:**
```bash
heroku config:set GOOGLE_API_KEY1=AIza...
heroku config:set FIREBASE_SERVICE_ACCOUNT_JSON='...'
heroku config:set FIREBASE_PROJECT_ID=my-project
```

---

## Credential Methods (in priority order)

### Method 1: Environment Variable (Recommended for containers)
```bash
export FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
```
✅ Works in: Docker, Replit, Cloud Run, GitHub Actions, Heroku
✅ Secure: Use secrets management
✅ Flexible: No file needed

### Method 2: Local File (Recommended for development)
```bash
# Place firebase-key.json in project root
export FIREBASE_CREDENTIALS="firebase-key.json"
# OR just place it and it auto-detects
```
✅ Works in: Local development
✅ Simple: Just copy and run
⚠️ WARNING: Never commit firebase-key.json to git!

### Method 3: Application Default Credentials (Recommended for GCP)
```bash
export FIREBASE_PROJECT_ID="my-project-id"
# gcloud auth application-default login (local)
# Or service account attached to Cloud Run instance
```
✅ Works in: GCP (Cloud Run, Compute Engine, App Engine)
✅ Seamless: No credentials needed on instance
⚠️ Only for GCP services

---

## Testing Your Setup

**Before deploying, test Firebase locally:**

```bash
# Standalone test (doesn't require full app)
python scripts/test_firebase.py

# Expected output:
# ✓ Firebase is ready for use!
```

**Test in your code:**
```python
from app.services.db_service import _get_firestore

firestore = _get_firestore()  # Raises exception if not configured
print("✓ Firebase connected!")
```

---

## Troubleshooting

### "Firebase is not configured"
- Check you have at least one of:
  - ✓ `firebase-key.json` in project root
  - ✓ `FIREBASE_SERVICE_ACCOUNT_JSON` environment variable
  - ✓ `FIREBASE_PROJECT_ID` environment variable

### "Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON"
- Ensure the JSON is properly escaped as a string
- Docker example:
  ```dockerfile
  ENV FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
  ```

### "Service account key file not found"
- Ensure `firebase-key.json` is in the project root
- Or set `FIREBASE_CREDENTIALS` to the correct path
- Or use `FIREBASE_SERVICE_ACCOUNT_JSON` instead

### "Connection refused" or "Invalid credentials"
- Verify your service account is valid
- Check the key hasn't expired
- Ensure Firebase Firestore is enabled in your Google Cloud project

### "Database not available" in CI/CD
- GitHub Actions may not have network access to Firebase
- This is expected in test environments
- Test script will show: `⚠️ Firebase configured but connection test failed`
- This is OK if you're just testing the config validation

---

## Environment-Specific Configurations

See `scripts/env_examples.py` for complete examples:

| Environment | Credential Method | How to Set |
|-------------|------------------|-----------|
| Local Dev | File (`firebase-key.json`) | Copy file to project root |
| Docker | Env var | `ENV FIREBASE_SERVICE_ACCOUNT_JSON='...'` in Dockerfile |
| Replit | Secrets | Replit UI + `.replit` config |
| GitHub Actions | Secrets | GitHub UI → repo secrets |
| Cloud Run | Service Account | Attached to Cloud Run instance |
| Heroku | Config Vars | `heroku config:set` |

---

## Best Practices

### Security
- 🔒 Never commit `firebase-key.json` to git
- 🔒 Use `.gitignore` to exclude it:
  ```
  firebase-key.json
  ```
- 🔒 Use secrets management (GitHub Secrets, Cloud Secret Manager, etc.)
- 🔒 Rotate service account keys regularly

### Configuration
- ✅ Use environment variables for all credentials
- ✅ Set `FIREBASE_PROJECT_ID` for better debugging
- ✅ Set `FIREBASE_DATABASE_URL` if using Realtime Database
- ✅ Use different service accounts for dev/staging/prod

### Testing
- ✅ Run `python scripts/test_firebase.py` before deploying
- ✅ Test in each environment separately
- ✅ Check startup logs for Firebase status
- ✅ Monitor connection health via `/health` endpoint

---

## API Endpoints for Firebase Info

**Health Check:**
```bash
curl http://localhost:5000/health
```

**Stats:**
```bash
curl http://localhost:5000/stats
```

**History:**
```bash
curl http://localhost:5000/history?limit=10
```

---

## Additional Resources

- [Firebase Admin SDK Documentation](https://firebase.google.com/docs/admin/setup)
- [Firebase Service Account Setup](https://firebase.google.com/docs/admin/setup#initialize_the_sdk)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
- [Docker Security Best Practices](https://docs.docker.com/develop/security/)
- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

## Questions?

Run the diagnostic tool:
```bash
python scripts/test_firebase.py
```

This will show:
- Current environment detected
- Credentials validation status
- Connection test results
- Specific issues and how to fix them
