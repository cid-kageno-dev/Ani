import importlib
import importlib.util
import json
import time
from datetime import datetime, timezone

from psycopg2 import pool
import psycopg2.extras
from thefuzz import process

from config import Config
from app.logger import get_logger

log = get_logger("ani.db")

_pool: pool.ThreadedConnectionPool | None = None
_firestore_client = None
_firebase_ready = False
_firebase_admin = None
_firebase_credentials = None
_firebase_firestore = None


def _firebase_modules():
    global _firebase_admin, _firebase_credentials, _firebase_firestore
    if _firebase_admin and _firebase_credentials and _firebase_firestore:
        return _firebase_admin, _firebase_credentials, _firebase_firestore

    if importlib.util.find_spec("firebase_admin") is None:
        raise RuntimeError("firebase-admin is not installed")

    _firebase_admin = importlib.import_module("firebase_admin")
    _firebase_credentials = importlib.import_module("firebase_admin.credentials")
    _firebase_firestore = importlib.import_module("firebase_admin.firestore")
    return _firebase_admin, _firebase_credentials, _firebase_firestore


def _firebase_configured() -> bool:
    return bool(
        Config.FIREBASE_CREDENTIALS
        or Config.FIREBASE_SERVICE_ACCOUNT_JSON
        or Config.FIREBASE_PROJECT_ID
    )


def _backend() -> str | None:
    requested = Config.DATABASE_BACKEND.lower()
    if requested in {"firebase", "firestore"}:
        return "firebase"
    if requested in {"postgres", "postgresql"}:
        return "postgres" if Config.DATABASE_URL else None
    if _firebase_configured():
        return "firebase"
    if Config.DATABASE_URL:
        return "postgres"
    return None


def _empty_stats() -> dict:
    return {
        "total": 0,
        "ai_responses": 0,
        "fallback_responses": 0,
        "first_interaction": None,
        "last_interaction": None,
    }


def _normalize_datetime(value):
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value
    return datetime.now(timezone.utc)


def _doc_to_interaction(doc) -> dict:
    data = doc.to_dict() or {}
    return {
        "id": doc.id,
        "user_query": data.get("user_query", ""),
        "ai_response": data.get("ai_response", ""),
        "source": data.get("source", "AI Response"),
        "created_at": _normalize_datetime(data.get("created_at")),
    }


def _get_firestore():
    global _firestore_client, _firebase_ready
    if _firestore_client is not None:
        return _firestore_client

    if not _firebase_configured():
        raise RuntimeError("Firebase is not configured")

    cred = None
    firebase_admin, credentials, firestore = _firebase_modules()

    if Config.FIREBASE_SERVICE_ACCOUNT_JSON:
        cred = credentials.Certificate(json.loads(Config.FIREBASE_SERVICE_ACCOUNT_JSON))
    elif Config.FIREBASE_CREDENTIALS:
        cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS)
    else:
        cred = credentials.ApplicationDefault()

    options = {}
    if Config.FIREBASE_DATABASE_URL:
        options["databaseURL"] = Config.FIREBASE_DATABASE_URL
    if Config.FIREBASE_PROJECT_ID:
        options["projectId"] = Config.FIREBASE_PROJECT_ID

    try:
        app = firebase_admin.get_app()
    except ValueError:
        app = firebase_admin.initialize_app(cred, options or None)

    _firestore_client = firestore.client(app=app)
    _firebase_ready = True
    log.info(f"Firebase Firestore ready — collection '{Config.FIREBASE_COLLECTION}'")
    return _firestore_client


def _firebase_collection():
    return _get_firestore().collection(Config.FIREBASE_COLLECTION)


def _get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        if not Config.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not configured")
        log.info("Initializing DB connection pool (min=1, max=5)")
        _pool = pool.ThreadedConnectionPool(1, 5, Config.DATABASE_URL)
        log.info("DB connection pool ready")
    return _pool


def _conn():
    return _get_pool().getconn()


def _put(conn):
    if conn and _pool is not None:
        _pool.putconn(conn)


def ensure_schema() -> bool:
    backend = _backend()
    if backend == "firebase":
        try:
            _get_firestore()
            log.info("Firebase uses schemaless collections — schema verification skipped")
            return True
        except Exception as e:
            log.error(f"Firebase initialization failed: {e}")
            return False

    if backend != "postgres":
        log.warning("Skipping schema verification — no database backend is configured")
        return False

    log.info("Verifying database schema...")
    conn = None
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_interactions (
                id         SERIAL PRIMARY KEY,
                user_query TEXT        NOT NULL,
                ai_response TEXT       NOT NULL,
                source     VARCHAR(50) DEFAULT 'AI Response',
                created_at TIMESTAMP   DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_chat_created
                ON chat_interactions(created_at DESC);
        """)
        conn.commit()
        cur.close()
        log.info("Schema OK — table 'chat_interactions' is ready")
        return True
    except Exception as e:
        log.error(f"Schema init failed: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        _put(conn)


def _save_interaction_firebase(user_query: str, ai_response: str, source: str):
    _, _, firestore = _firebase_modules()
    doc = {
        "user_query": user_query,
        "ai_response": ai_response,
        "source": source,
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    update_time, ref = _firebase_collection().add(doc)
    log.info(f"Saved interaction {ref.id} [{source}] to Firebase at {update_time}")


def _save_interaction_postgres(user_query: str, ai_response: str, source: str):
    t0 = time.perf_counter()
    conn = None
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_interactions (user_query, ai_response, source) VALUES (%s, %s, %s) RETURNING id",
            (user_query, ai_response, source),
        )
        row_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        ms = (time.perf_counter() - t0) * 1000
        log.info(f"Saved interaction #{row_id} [{source}] in {ms:.1f}ms")
    except Exception as e:
        log.error(f"Failed to save interaction: {e}")
        if conn:
            conn.rollback()
    finally:
        _put(conn)


def save_interaction(user_query: str, ai_response: str, source: str = "AI Response"):
    backend = _backend()
    if backend == "firebase":
        try:
            _save_interaction_firebase(user_query, ai_response, source)
        except Exception as e:
            log.error(f"Failed to save interaction to Firebase: {e}")
        return

    if backend == "postgres":
        _save_interaction_postgres(user_query, ai_response, source)
        return

    log.debug("Skipping interaction save — no database backend is configured")


def _get_firebase_rows(limit: int = 500) -> list:
    _, _, firestore = _firebase_modules()
    docs = (
        _firebase_collection()
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [_doc_to_interaction(doc) for doc in docs]


def _get_postgres_rows(limit: int = 500) -> list:
    conn = None
    try:
        conn = _conn()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, user_query, ai_response, source, created_at "
            "FROM chat_interactions ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        log.error(f"Failed to fetch interactions: {e}")
        return []
    finally:
        _put(conn)


def get_fallback_answer(user_query: str) -> str:
    backend = _backend()
    if backend is None:
        log.warning("Fallback lookup unavailable — no database backend is configured")
        return "I'm offline right now and don't have a database connection for cached answers. Please try again later."

    log.info(f"Fallback search for: '{user_query[:60]}'")
    t0 = time.perf_counter()
    try:
        rows = _get_firebase_rows(500) if backend == "firebase" else _get_postgres_rows(500)

        if not rows:
            log.warning("Fallback DB is empty — no past interactions to match")
            return "I'm offline right now and don't have any cached answers yet. Please try again later."

        past_queries = [r["user_query"] for r in rows]
        best_match, score = process.extractOne(user_query, past_queries)
        ms = (time.perf_counter() - t0) * 1000

        log.info(f"Fuzzy match: '{best_match[:50]}' score={score} in {ms:.1f}ms")

        if score > 75:
            for row in rows:
                if row["user_query"] == best_match:
                    return row["ai_response"]

        log.warning(f"No match above threshold (score={score}) — returning generic message")
        return "I'm currently offline and couldn't find a relevant cached answer. Please try again later."

    except Exception as e:
        log.error(f"Fallback lookup failed: {e}")
        return "System error — knowledge base temporarily unavailable."


def get_recent_interactions(limit: int = 20) -> list:
    backend = _backend()
    if backend is None:
        log.warning("History unavailable — no database backend is configured")
        return []

    log.debug(f"Fetching {limit} recent interactions from {backend}")
    if backend == "firebase":
        try:
            rows = _get_firebase_rows(limit)
            log.debug(f"Returned {len(rows)} Firebase interactions")
            return rows
        except Exception as e:
            log.error(f"Failed to fetch Firebase interactions: {e}")
            return []

    rows = _get_postgres_rows(limit)
    log.debug(f"Returned {len(rows)} PostgreSQL interactions")
    return rows


def _get_firebase_stats() -> dict:
    stats = _empty_stats()
    docs = _firebase_collection().stream()
    for doc in docs:
        row = _doc_to_interaction(doc)
        stats["total"] += 1
        if row["source"] == "AI Response":
            stats["ai_responses"] += 1
        elif row["source"] == "Database":
            stats["fallback_responses"] += 1

        created_at = row["created_at"]
        first_at = stats["first_interaction"]
        last_at = stats["last_interaction"]
        created_iso = created_at.isoformat()
        if first_at is None or created_iso < first_at:
            stats["first_interaction"] = created_iso
        if last_at is None or created_iso > last_at:
            stats["last_interaction"] = created_iso
    return stats


def _get_postgres_stats() -> dict:
    conn = None
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*)                                            AS total,
                COUNT(*) FILTER (WHERE source = 'AI Response')     AS ai_count,
                COUNT(*) FILTER (WHERE source = 'Database')        AS fallback_count,
                MIN(created_at)                                     AS first_at,
                MAX(created_at)                                     AS last_at
            FROM chat_interactions
        """)
        row = cur.fetchone()
        cur.close()
        return {
            "total": row[0],
            "ai_responses": row[1],
            "fallback_responses": row[2],
            "first_interaction": row[3].isoformat() if row[3] else None,
            "last_interaction": row[4].isoformat() if row[4] else None,
        }
    except Exception as e:
        log.error(f"Stats query failed: {e}")
        return _empty_stats()
    finally:
        _put(conn)


def get_stats() -> dict:
    backend = _backend()
    if backend is None:
        log.warning("Stats unavailable — no database backend is configured")
        return _empty_stats()

    if backend == "firebase":
        try:
            return _get_firebase_stats()
        except Exception as e:
            log.error(f"Firebase stats query failed: {e}")
            return _empty_stats()

    return _get_postgres_stats()
