"""
Firebase connection validator for all environments.
Runs on app startup to verify Firebase is properly configured and accessible.
"""

import json
import os
from typing import Tuple

from config import Config
from app.logger import get_logger

log = get_logger("ani.firebase_validator")


class FirebaseValidator:
    """Validates Firebase configuration and connectivity."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.config_source = None

    def _check_credentials_env(self) -> bool:
        """Check FIREBASE_SERVICE_ACCOUNT_JSON environment variable."""
        if not Config.FIREBASE_SERVICE_ACCOUNT_JSON:
            return False

        try:
            json_str = Config.FIREBASE_SERVICE_ACCOUNT_JSON
            data = json.loads(json_str)

            required_fields = [
                "type",
                "project_id",
                "private_key_id",
                "private_key",
                "client_email",
                "client_id",
                "auth_uri",
                "token_uri",
                "auth_provider_x509_cert_url",
            ]

            missing = [f for f in required_fields if f not in data]
            if missing:
                self.errors.append(
                    f"FIREBASE_SERVICE_ACCOUNT_JSON missing fields: {missing}"
                )
                return False

            self.config_source = "FIREBASE_SERVICE_ACCOUNT_JSON (env)"
            log.info("✓ FIREBASE_SERVICE_ACCOUNT_JSON is valid JSON with required fields")
            return True

        except json.JSONDecodeError as e:
            self.errors.append(f"FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON: {e}")
            return False

    def _check_credentials_file(self) -> bool:
        """Check firebase-key.json file."""
        if not Config.FIREBASE_CREDENTIALS:
            return False

        file_path = Config.FIREBASE_CREDENTIALS
        if not os.path.isfile(file_path):
            self.warnings.append(f"firebase-key.json file not found at: {file_path}")
            return False

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            required_fields = [
                "type",
                "project_id",
                "private_key_id",
                "private_key",
                "client_email",
            ]
            missing = [f for f in required_fields if f not in data]
            if missing:
                self.errors.append(f"firebase-key.json missing fields: {missing}")
                return False

            self.config_source = f"firebase-key.json file"
            log.info(f"✓ {file_path} is valid with required fields")
            return True

        except json.JSONDecodeError as e:
            self.errors.append(f"firebase-key.json is not valid JSON: {e}")
            return False

    def _check_project_id(self) -> bool:
        """Check FIREBASE_PROJECT_ID environment variable."""
        if not Config.FIREBASE_PROJECT_ID:
            return False

        if not isinstance(Config.FIREBASE_PROJECT_ID, str) or not Config.FIREBASE_PROJECT_ID.strip():
            self.errors.append("FIREBASE_PROJECT_ID is empty or invalid")
            return False

        self.config_source = "FIREBASE_PROJECT_ID (env)"
        log.info(f"✓ FIREBASE_PROJECT_ID is set: {Config.FIREBASE_PROJECT_ID}")
        return True

    def _validate_firebase_admin_installed(self) -> bool:
        """Check if firebase-admin is installed."""
        try:
            import firebase_admin
            log.info("✓ firebase-admin package is installed")
            return True
        except ImportError:
            self.errors.append(
                "firebase-admin is not installed. Run: pip install firebase-admin"
            )
            return False

    def _test_firebase_connection(self) -> bool:
        """Attempt to initialize Firebase and test connection."""
        try:
            from app.services.db_service import _get_firestore

            firestore_client = _get_firestore()

            # Test basic read operation
            collection = firestore_client.collection(Config.FIREBASE_COLLECTION)
            # Just test if we can access collection metadata
            collection.limit(1).stream()

            log.info("✓ Firebase Firestore connection successful")
            return True

        except Exception as e:
            error_msg = str(e)
            self.errors.append(f"Firebase connection failed: {error_msg}")
            log.error(f"Firebase connection error: {error_msg}")
            return False

    def validate(self) -> Tuple[bool, dict]:
        """
        Run all validations.

        Returns:
            Tuple of (is_valid, result_dict)
        """
        log.info("━━━ Firebase Configuration Validator ━━━")

        # Check if Firebase is configured at all
        has_creds_env = bool(Config.FIREBASE_SERVICE_ACCOUNT_JSON)
        has_creds_file = bool(Config.FIREBASE_CREDENTIALS) and os.path.isfile(
            Config.FIREBASE_CREDENTIALS
        )
        has_project_id = bool(Config.FIREBASE_PROJECT_ID)

        if not (has_creds_env or has_creds_file or has_project_id):
            log.warning("Firebase not configured (all optional)")
            return True, {
                "is_configured": False,
                "is_valid": True,
                "errors": [],
                "warnings": [],
                "config_source": None,
            }

        # Check package installation
        if not self._validate_firebase_admin_installed():
            return False, {
                "is_configured": True,
                "is_valid": False,
                "errors": self.errors,
                "warnings": self.warnings,
                "config_source": None,
            }

        # Try each credential source
        cred_valid = (
            self._check_credentials_env()
            or self._check_credentials_file()
            or self._check_project_id()
        )

        if not cred_valid and not has_project_id:
            log.error("✗ No valid Firebase credentials found")
            return False, {
                "is_configured": True,
                "is_valid": False,
                "errors": self.errors,
                "warnings": self.warnings,
                "config_source": None,
            }

        # Test connection
        connection_ok = self._test_firebase_connection()

        result = {
            "is_configured": True,
            "is_valid": connection_ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "config_source": self.config_source,
        }

        return connection_ok, result


def validate_firebase_on_startup() -> dict:
    """
    Validate Firebase on application startup.
    Call this from app/__init__.py during initialization.

    Returns:
        Validation result dictionary
    """
    validator = FirebaseValidator()
    is_valid, result = validator.validate()

    # Log results
    if result["errors"]:
        for error in result["errors"]:
            log.error(f"✗ {error}")

    if result["warnings"]:
        for warning in result["warnings"]:
            log.warning(f"⚠ {warning}")

    if is_valid:
        if result["is_configured"]:
            log.info(f"✓ Firebase validation passed (source: {result['config_source']})")
        else:
            log.info("ℹ Firebase not configured (using fallback database)")

    return result
