# Firebase Setup Guide

This guide covers configuring Firebase Firestore for Ani across different environments. Firebase is the primary database backend; Replit PostgreSQL is used as a fallback when Firebase is not configured.

---

## Quick Start

### On Replit (recommended)

1. Open the **Secrets** tab (lock icon in the sidebar).
2. Add a secret named `FIREBASE_SERVICE_ACCOUNT_JSON` with the full JSON content of your Firebase service account key (see "Generating a Service Account Key" below).
3. The following are already set as shared environment variables in `.replit`:
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_DATABASE_URL`
4. Click **Run** — the startup logs will show `✓ Firebase validation passed`.

### Local Development

```bash
# Option A: place the key file in the project root
cp ~/Downloads/firebase-key.json ./firebase-key.json
python run.py

# Option B: export as an environment variable
export FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
python run.py
```

### Docker

```bash
# Build
docker build -t ani .

# Run with env var
docker run -p 5000:5000 \
  -e FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}' \
  -e FIREBASE_PROJECT_ID="gen-lang-client-0109922552" \
  ani

# Or with Docker Compose + .env file
docker-compose up --build
```

### GitHub Actions

Add these secrets in **Settings → Secrets and Variables → Actions**:

- `GOOGLE_API_KEY1`
- `FIREBASE_SERVICE_ACCOUNT_JSON`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_DATABASE_URL`

The app auto-detects and uses them from environment variables.

---

## Generating a Service Account Key

1. Go to the [Firebase Console](https://console.firebase.google.com/).
2. Select your project → **Project Settings** → **Service Accounts**.
3. Click **Generate New Private Key** → confirm → download the JSON file.
4. The downloaded file looks like:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-...@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  ...
}
```

5. Store the entire JSON as the `FIREBASE_SERVICE_ACCOUNT_JSON` secret (paste the whole file content as one line).

---

## Credential Priority

The app tries credential sources in this order:

| Priority | Method | When to use |
|----------|--------|-------------|
| 1 | `FIREBASE_SERVICE_ACCOUNT_JSON` env/secret | All environments (Replit, Docker, CI/CD) |
| 2 | `firebase-key.json` file | Local development |
| 3 | Application Default Credentials | GCP services (Cloud Run, etc.) |

---

## Firestore Data Structure

```
chat_interactions (collection)
└── {auto-generated ID} (document)
    ├── user_query   : string   — the user's original message
    ├── ai_response  : string   — Ani's reply
    ├── source       : string   — "AI Response" or "Database"
    └── created_at   : timestamp
```

---

## Testing Your Setup

Run the standalone Firebase test script:

```bash
python scripts/test_firebase.py
```

Expected output when configured correctly:
```
✓ Firebase is ready for use!
```

Or check the app startup logs — the connection status table is printed on every boot:

```
  CONNECTION STATUS
─────────────────────────────────────────────
  ✓  Firebase     collection 'chat_interactions'
  ✓  PostgreSQL   helium/heliumdb
  ✓  DB Schema    active backend: firebase
```

---

## Troubleshooting

### "Firebase is not configured"
Ensure at least one of the following is set:
- `FIREBASE_SERVICE_ACCOUNT_JSON` secret
- `firebase-key.json` file in the project root
- `FIREBASE_PROJECT_ID` environment variable

### "Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON"
The value must be valid JSON. Paste the raw file contents — do not add extra quotes around it.

On Linux/Mac you can convert the file to a single-line string:
```bash
cat firebase-key.json | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)))"
```

### "Service account key file not found"
Either place `firebase-key.json` in the project root, or switch to the `FIREBASE_SERVICE_ACCOUNT_JSON` env var instead.

### "Permission denied" or "403"
- Verify Firestore is **enabled** in your Firebase project (Build → Firestore Database → Create database).
- Check the service account has the **Cloud Datastore User** role in Google Cloud IAM.

### Firebase unavailable in CI/CD
If tests run without network access to Firebase, the connection test will fail gracefully. The app still starts; it just won't save interactions. This is expected in ephemeral test environments.

---

## Security Notes

- Never commit `firebase-key.json` to a public repository. Add it to `.gitignore` if you're working in a fork.
- Use different service accounts for development and production.
- Rotate service account keys periodically via the Firebase Console.
- Replit Secrets are encrypted at rest and never exposed in logs or the UI.

---

## Additional Resources

- [Firebase Admin SDK setup](https://firebase.google.com/docs/admin/setup)
- [Service account documentation](https://firebase.google.com/docs/admin/setup#initialize_the_sdk)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
- [Firestore security rules](https://firebase.google.com/docs/firestore/security/get-started)
