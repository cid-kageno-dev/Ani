#!/usr/bin/env python3
"""
Firebase Configuration Test Script
Validates Firebase setup without running the full app.

Usage:
    python scripts/test_firebase.py

Shows:
    - Current environment detected
    - Credential configuration status
    - Connection test results
    - Specific errors and recommendations
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.firebase_validator import FirebaseValidator
from config import Config
from app.logger import get_logger

log = get_logger("firebase_test")


def detect_environment() -> str:
    """Detect which environment we're running in."""
    if os.getenv("REPL_ID"):
        return "Replit"
    if os.getenv("GITHUB_ACTIONS"):
        return "GitHub Actions"
    if os.getenv("K_SERVICE"):  # Google Cloud Run
        return "Google Cloud Run"
    if os.getenv("DYNO"):  # Heroku
        return "Heroku"
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return "AWS Lambda"
    if os.path.exists("/.dockerenv"):
        return "Docker"
    return "Local Development"


def print_header():
    """Print script header."""
    print("\n" + "=" * 60)
    print("  Firebase Configuration Validator")
    print("=" * 60 + "\n")


def print_section(title):
    """Print a section header."""
    print(f"\n📋 {title}")
    print("-" * 60)


def print_success(msg):
    """Print a success message."""
    print(f"  ✅ {msg}")


def print_error(msg):
    """Print an error message."""
    print(f"  ❌ {msg}")


def print_warning(msg):
    """Print a warning message."""
    print(f"  ⚠️  {msg}")


def print_info(msg):
    """Print an info message."""
    print(f"  ℹ️  {msg}")


def test_firebase():
    """Run all Firebase tests."""
    print_header()

    environment = detect_environment()
    print_section("Environment Detection")
    print_success(f"Running in: {environment}")

    print_section("Configuration Status")

    # Check each credential source
    has_env_var = bool(Config.FIREBASE_SERVICE_ACCOUNT_JSON)
    has_file = bool(Config.FIREBASE_CREDENTIALS) and os.path.isfile(
        Config.FIREBASE_CREDENTIALS
    )
    has_project_id = bool(Config.FIREBASE_PROJECT_ID)

    if has_env_var:
        print_success(
            "FIREBASE_SERVICE_ACCOUNT_JSON environment variable is set"
        )
    else:
        print_warning("FIREBASE_SERVICE_ACCOUNT_JSON not set")

    if has_file:
        print_success(f"Firebase credentials file found: {Config.FIREBASE_CREDENTIALS}")
    else:
        print_warning("firebase-key.json file not found")

    if has_project_id:
        print_success(f"FIREBASE_PROJECT_ID is set: {Config.FIREBASE_PROJECT_ID}")
    else:
        print_warning("FIREBASE_PROJECT_ID not set")

    if not (has_env_var or has_file or has_project_id):
        print_info("Firebase not configured (optional)")
        print_info("Database will fall back to PostgreSQL if configured")
        return

    # Validate configuration
    print_section("Configuration Validation")

    validator = FirebaseValidator()
    is_valid, result = validator.validate()

    if result["errors"]:
        for error in result["errors"]:
            print_error(error)

    if result["warnings"]:
        for warning in result["warnings"]:
            print_warning(warning)

    if result["config_source"]:
        print_success(f"Using credentials from: {result['config_source']}")

    print_section("Connection Test")

    if is_valid:
        print_success("Firebase connection successful!")
        print_info(
            f"Collection: {Config.FIREBASE_COLLECTION}"
        )
        if Config.FIREBASE_DATABASE_URL:
            print_info(f"Database URL: {Config.FIREBASE_DATABASE_URL}")
    else:
        print_error("Firebase connection failed")
        print_warning("Database will attempt to use PostgreSQL fallback")

    print_section("Next Steps")

    if is_valid:
        if result["is_configured"]:
            print_success("Firebase is ready! You can now:")
            print_info("  • Run the app: python run.py")
            print_info("  • Deploy to Docker: docker-compose up --build")
            print_info("  • Deploy to production")
    else:
        print_warning("Firebase configuration needs attention:")
        if "firebase-admin is not installed" in str(result["errors"]):
            print_info("  • Install firebase-admin: pip install firebase-admin")
        if "invalid json" in str(result["errors"]).lower():
            print_info("  • Check FIREBASE_SERVICE_ACCOUNT_JSON is valid JSON")
            print_info("  • Or place firebase-key.json in project root")
        if "connection failed" in str(result["errors"]).lower():
            print_info("  • Verify Firebase project is active in Google Cloud Console")
            print_info("  • Verify service account has Firestore permissions")
            print_info("  • Check network connectivity")
        if not has_file and not has_env_var:
            print_info("  • Set FIREBASE_CREDENTIALS or FIREBASE_SERVICE_ACCOUNT_JSON")
            print_info("  • Or place firebase-key.json in project root")

    print("\n" + "=" * 60)
    print("  Test Complete")
    print("=" * 60 + "\n")

    return 0 if is_valid or not result["is_configured"] else 1


if __name__ == "__main__":
    exit_code = test_firebase()
    sys.exit(exit_code)
