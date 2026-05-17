#!/usr/bin/env python3
"""
Environment Configuration Examples
Shows Firebase setup for different deployment platforms.

Usage:
    python scripts/env_examples.py all                # Show all environments
    python scripts/env_examples.py local              # Local development
    python scripts/env_examples.py docker             # Docker
    python scripts/env_examples.py replit             # Replit
    python scripts/env_examples.py github_actions     # GitHub Actions
    python scripts/env_examples.py google_cloud_run   # Google Cloud Run
    python scripts/env_examples.py heroku             # Heroku
    python scripts/env_examples.py aws_lambda         # AWS Lambda
"""

import sys


EXAMPLES = {
    "local": {
        "name": "Local Development",
        "setup": """
1. Create .env file:
   cp .env.example .env

2. Get Firebase credentials:
   • Go to Firebase Console → Project Settings → Service Accounts
   • Click "Generate New Private Key"
   • Save as firebase-key.json in project root

3. Set environment variables in .env:
   FIREBASE_CREDENTIALS="firebase-key.json"
   FIREBASE_PROJECT_ID="your-project-id"
   FIREBASE_DATABASE_URL="https://your-project.firebaseio.com"

4. Run app:
   python run.py

   Expected output:
   ✓ Firebase Firestore ready — collection 'chat_interactions'
""",
        "files": {
            ".env": """
GOOGLE_API_KEY1="AIzaSyD-your-key..."
FIREBASE_CREDENTIALS="firebase-key.json"
FIREBASE_PROJECT_ID="my-project"
FIREBASE_DATABASE_URL="https://my-project.firebaseio.com"
GITHUB_USERNAME="cid-kageno-dev"
FLASK_DEBUG=true
LOG_LEVEL="DEBUG"
""",
            "firebase-key.json": "(place your Firebase service account JSON here)"
        }
    },
    "docker": {
        "name": "Docker Container",
        "setup": """
1. Get Firebase credentials (as single-line JSON):
   • Go to Firebase Console → Project Settings → Service Accounts
   • Click "Generate New Private Key"
   • Convert to single-line JSON (remove newlines)

2. Create .env.docker:
   cp .env.docker.example .env.docker

3. Set environment:
   FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
   FIREBASE_PROJECT_ID="my-project"
   FIREBASE_DATABASE_URL="https://my-project.firebaseio.com"

4. Build and run:
   docker build -t ani .
   docker run -e FIREBASE_SERVICE_ACCOUNT_JSON='...' ani

   Or use docker-compose:
   docker-compose up --build

   Expected output:
   ✓ Firebase Firestore ready — collection 'chat_interactions'
""",
        "dockerfile": """
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...","..."}'
ENV FIREBASE_PROJECT_ID="my-project"
ENV GOOGLE_API_KEY1="AIzaSyD-..."

EXPOSE 5000
CMD ["python", "run.py"]
""",
        "docker_compose": """
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
      - FIREBASE_PROJECT_ID=my-project
      - FIREBASE_DATABASE_URL=https://my-project.firebaseio.com
      - GOOGLE_API_KEY1=AIzaSyD-...
      - DATABASE_BACKEND=auto
      - LOG_LEVEL=INFO
    depends_on:
      - postgres

  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: ani_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
"""
    },
    "replit": {
        "name": "Replit",
        "setup": """
1. Click lock icon (Secrets) in Replit sidebar

2. Add secrets:
   • GOOGLE_API_KEY1 = AIzaSyD-your-key...
   • FIREBASE_SERVICE_ACCOUNT_JSON = {"type":"service_account",...}
   
3. The .replit file already includes:
   • FIREBASE_PROJECT_ID
   • FIREBASE_DATABASE_URL

4. Click "Run" button

   Expected output:
   ✓ Firebase Firestore ready — collection 'chat_interactions'

Note: .replit has these shared env vars:
  FIREBASE_PROJECT_ID = "gen-lang-client-0109922552"
  FIREBASE_DATABASE_URL = "https://gen-lang-client-0109922552-default-rtdb.asia-southeast1.firebasedatabase.app"
""",
        "replit_config": """
[userenv]

[userenv.shared]
FIREBASE_PROJECT_ID = "gen-lang-client-0109922552"
FIREBASE_DATABASE_URL = "https://gen-lang-client-0109922552-default-rtdb.asia-southeast1.firebasedatabase.app"
"""
    },
    "github_actions": {
        "name": "GitHub Actions CI/CD",
        "setup": """
1. Go to GitHub repo → Settings → Secrets and variables → Actions

2. Add secrets:
   • GOOGLE_API_KEY1 = AIzaSyD-your-key...
   • FIREBASE_SERVICE_ACCOUNT_JSON = {"type":"service_account",...}
   • FIREBASE_PROJECT_ID = my-project
   • FIREBASE_DATABASE_URL = https://my-project.firebaseio.com

3. Create .github/workflows/test.yml:
   See example below

4. Push to repo - workflow runs automatically

   Expected output in GitHub Actions:
   ✓ Firebase Firestore ready — collection 'chat_interactions'
""",
        "workflow": """
name: Test Firebase

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Test Firebase
        env:
          GOOGLE_API_KEY1: ${{ secrets.GOOGLE_API_KEY1 }}
          FIREBASE_SERVICE_ACCOUNT_JSON: ${{ secrets.FIREBASE_SERVICE_ACCOUNT_JSON }}
          FIREBASE_PROJECT_ID: ${{ secrets.FIREBASE_PROJECT_ID }}
          FIREBASE_DATABASE_URL: ${{ secrets.FIREBASE_DATABASE_URL }}
        run: python scripts/test_firebase.py
      
      - name: Run app tests
        env:
          GOOGLE_API_KEY1: ${{ secrets.GOOGLE_API_KEY1 }}
          FIREBASE_SERVICE_ACCOUNT_JSON: ${{ secrets.FIREBASE_SERVICE_ACCOUNT_JSON }}
          DATABASE_BACKEND: firebase
        run: pytest tests/
"""
    },
    "google_cloud_run": {
        "name": "Google Cloud Run",
        "setup": """
1. Build and push to Google Container Registry:
   gcloud builds submit --tag gcr.io/PROJECT_ID/ani

2. Deploy to Cloud Run:
   gcloud run deploy ani \\
     --image gcr.io/PROJECT_ID/ani \\
     --set-env-vars GOOGLE_API_KEY1=AIzaSyD-... \\
     --set-env-vars FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}' \\
     --set-env-vars FIREBASE_PROJECT_ID=my-project \\
     --set-env-vars DATABASE_BACKEND=firebase \\
     --memory 512Mi \\
     --cpu 1 \\
     --timeout 3600 \\
     --allow-unauthenticated \\
     --region us-central1

3. Or use gcloud CLI config file:
   See example below

4. Access at: https://ani-XXXX.run.app

   Expected output:
   ✓ Firebase Firestore ready — collection 'chat_interactions'
""",
        "cloud_run_config": """
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ani
spec:
  template:
    spec:
      containerConcurrency: 50
      containers:
      - image: gcr.io/PROJECT_ID/ani
        env:
        - name: GOOGLE_API_KEY1
          valueFrom:
            secretKeyRef:
              name: ani-secrets
              key: google-api-key
        - name: FIREBASE_SERVICE_ACCOUNT_JSON
          valueFrom:
            secretKeyRef:
              name: ani-secrets
              key: firebase-json
        - name: FIREBASE_PROJECT_ID
          value: "my-project"
        - name: DATABASE_BACKEND
          value: "firebase"
        ports:
        - containerPort: 5000
        resources:
          limits:
            memory: "512Mi"
            cpu: "1"
"""
    },
    "heroku": {
        "name": "Heroku",
        "setup": """
1. Create Heroku app:
   heroku create ani-app

2. Set environment variables:
   heroku config:set GOOGLE_API_KEY1=AIzaSyD-...
   heroku config:set FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
   heroku config:set FIREBASE_PROJECT_ID=my-project
   heroku config:set FIREBASE_DATABASE_URL=https://my-project.firebaseio.com
   heroku config:set DATABASE_BACKEND=firebase

3. Deploy:
   git push heroku main

4. View logs:
   heroku logs --tail

   Expected output:
   ✓ Firebase Firestore ready — collection 'chat_interactions'
""",
        "procfile": """
web: gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"
"""
    },
    "aws_lambda": {
        "name": "AWS Lambda (with API Gateway)",
        "setup": """
1. Package app:
   pip install -r requirements.txt -t package/
   cp -r app/ package/
   cp config.py package/
   cd package && zip -r ../lambda_function.zip .

2. Create Lambda function:
   aws lambda create-function \\
     --function-name ani \\
     --runtime python3.12 \\
     --role arn:aws:iam::ACCOUNT:role/lambda-role \\
     --handler app:lambda_handler \\
     --zip-file fileb://../lambda_function.zip \\
     --environment Variables={GOOGLE_API_KEY1=AIzaSyD-...,...}

3. Set environment variables:
   aws lambda update-function-configuration \\
     --function-name ani \\
     --environment Variables={
       GOOGLE_API_KEY1=AIzaSyD-...,
       FIREBASE_SERVICE_ACCOUNT_JSON={'type':'service_account',...},
       FIREBASE_PROJECT_ID=my-project,
       DATABASE_BACKEND=firebase
     }

4. Create API Gateway trigger

5. Test with curl

   Expected output:
   ✓ Firebase Firestore ready — collection 'chat_interactions'

Note: Lambda + Firestore has cold start overhead (~2-3 seconds)
""",
        "lambda_handler": """
from app import create_app
import json

app = create_app()

def lambda_handler(event, context):
    # Convert API Gateway event to WSGI environ
    from werkzeug.serving import WSGIRequestHandler
    
    environ = {
        'REQUEST_METHOD': event.get('httpMethod', 'GET'),
        'SCRIPT_NAME': '',
        'PATH_INFO': event.get('path', '/'),
        'QUERY_STRING': event.get('queryStringParameters', {}),
        'wsgi.url_scheme': 'https',
    }
    
    with app.test_client() as client:
        response = client.open(environ['PATH_INFO'])
        return {
            'statusCode': response.status_code,
            'body': response.get_data(as_text=True),
            'headers': dict(response.headers)
        }
"""
    }
}


def show_example(env_key):
    """Show example for specific environment."""
    if env_key not in EXAMPLES:
        print(f"Unknown environment: {env_key}")
        print(f"Available: {', '.join(EXAMPLES.keys())}")
        return False

    example = EXAMPLES[env_key]
    print(f"\n{'=' * 70}")
    print(f"  {example['name']} Configuration")
    print(f"{'=' * 70}")
    print(example['setup'])

    if 'files' in example:
        print("\n📁 Configuration Files:")
        for filename, content in example['files'].items():
            print(f"\n  {filename}:")
            print("  " + "\n  ".join(content.split('\n')))

    if 'dockerfile' in example:
        print("\n📄 Dockerfile:")
        print("```dockerfile")
        print(example['dockerfile'])
        print("```")

    if 'docker_compose' in example:
        print("\n📄 docker-compose.yml:")
        print("```yaml")
        print(example['docker_compose'])
        print("```")

    if 'replit_config' in example:
        print("\n📄 .replit:")
        print("```ini")
        print(example['replit_config'])
        print("```")

    if 'workflow' in example:
        print("\n📄 .github/workflows/test.yml:")
        print("```yaml")
        print(example['workflow'])
        print("```")

    if 'cloud_run_config' in example:
        print("\n📄 cloud-run.yaml:")
        print("```yaml")
        print(example['cloud_run_config'])
        print("```")

    if 'procfile' in example:
        print("\n📄 Procfile:")
        print("```")
        print(example['procfile'])
        print("```")

    if 'lambda_handler' in example:
        print("\n📄 lambda_handler.py:")
        print("```python")
        print(example['lambda_handler'])
        print("```")

    return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2 or sys.argv[1] == "help":
        print(__doc__)
        return

    env_key = sys.argv[1]

    if env_key == "all":
        for key in EXAMPLES.keys():
            show_example(key)
    else:
        show_example(env_key)


if __name__ == "__main__":
    main()
