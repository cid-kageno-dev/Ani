import importlib
import importlib.util
import json
import time
from datetime import datetime, timezone
from threading import RLock

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

# In-memory cache configuration
_cache_lock = RLock()
_cache = {
    "interactions": [],
    "interactions_timestamp": 0,
    "stats": {},
    "stats_timestamp": 0,
}
_CACHE_TTL = 300  # 5 minutes in seconds


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


def _is_cache_valid(cache_key: str) -> bool:
    """Check if cache entry is still valid (not expired).

    NOTE: caller should hold _cache_lock if multiple cache reads must be consistent.
    """
    timestamp_key = f"{cache_key}_timestamp"
    if timestamp_key not in _cache:
        return False
    elapsed = time.time() - _cache[timestamp_key]
    is_valid = elapsed < _CACHE_TTL
    if not is_valid:
        log.debug(f"Cache expired for '{cache_key}' (age: {elapsed:.1f}s)")
    return is_valid


def _get_cached(cache_key: str):
    """Get value from cache if valid."""
    with _cache_lock:
        if _is_cache_valid(cache_key):
            log.debug(f"Cache hit for '{cache_key}'")
            return _cache.get(cache_key)
    return None


def _set_cache(cache_key: str, value):
    """Store value in cache with timestamp."""
    with _cache_lock:
        _cache[cache_key] = value
        _cache[f"{cache_key}_timestamp"] = time.time()
        log.debug(f"Cache updated for '{cache_key}'")


def _clear_cache(cache_key: str = None):
    """Clear specific cache entry or all cache."""
    with _cache_lock:
        if cache_key:
            if cache_key in _cache:
                del _cache[cache_key]
            timestamp_key = f"{cache_key}_timestamp"
            if timestamp_key in _cache:
                del _cache[timestamp_key]
            log.debug(f"Cache cleared for '{cache_key}'")
        else:
            _cache.clear()
            log.debug("All cache cleared")


def _get_firestore():
    global _firestore_client, _firebase_ready
    if _firestore_client is not None:
        return _firestore_client

    if not _firebase_configured():
        raise RuntimeError("Firebase is not configured")

    cred = None
    firebase_admin, credentials, firestore = _firebase_modules()

    if Config.FIREBASE_SERVICE_ACCOUNT_JSON:
        sa_info = json.loads(Config.FIREBASE_SERVICE_ACCOUNT_JSON)
        if "private_key" in sa_info:
            sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(sa_info)
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
    # Invalidate cache so next fetch gets fresh data
    _clear_cache("interactions")
    _clear_cache("stats")


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
        # Invalidate cache so next fetch gets fresh data
        _clear_cache("interactions")
        _clear_cache("stats")
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
        # Use cached interactions if available
        rows = _get_cached("interactions")
        if rows is None:
            rows = _get_firebase_rows(500) if backend == "firebase" else _get_postgres_rows(500)
            _set_cache("interactions", rows)

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
    
    # Check cache first
    cached_rows = _get_cached("interactions")
    if cached_rows is not None:
        log.debug(f"Returning {min(len(cached_rows), limit)} cached interactions")
        return cached_rows[:limit]
    
    if backend == "firebase":
        try:
            rows = _get_firebase_rows(limit)
            _set_cache("interactions", rows)
            log.debug(f"Returned {len(rows)} Firebase interactions")
            return rows
        except Exception as e:
            log.error(f"Failed to fetch Firebase interactions: {e}")
            return []

    rows = _get_postgres_rows(limit)
    _set_cache("interactions", rows)
    log.debug(f"Returned {len(rows)} PostgreSQL interactions")
    return rows


def _get_firebase_stats() -> dict:
    _, _, firestore = _firebase_modules()
    col = _firebase_collection()

    total_res    = col.count().get()
    ai_res       = col.where("source", "==", "AI Response").count().get()
    fallback_res = col.where("source", "==", "Database").count().get()

    total    = total_res[0][0].value
    ai_count = ai_res[0][0].value
    fb_count = fallback_res[0][0].value

    first_docs = col.order_by("created_at", direction=firestore.Query.ASCENDING).limit(1).stream()
    last_docs  = col.order_by("created_at", direction=firestore.Query.DESCENDING).limit(1).stream()

    first_doc = next(iter(first_docs), None)
    last_doc  = next(iter(last_docs), None)

    first_at = _normalize_datetime(first_doc.to_dict().get("created_at") if first_doc else None).isoformat() if first_doc else None
    last_at  = _normalize_datetime(last_doc.to_dict().get("created_at")  if last_doc  else None).isoformat() if last_doc  else None

    return {
        "total": total,
        "ai_responses": ai_count,
        "fallback_responses": fb_count,
        "first_interaction": first_at,
        "last_interaction": last_at,
    }


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

    # Check cache first
    cached_stats = _get_cached("stats")
    if cached_stats is not None:
        return cached_stats

    if backend == "firebase":
        try:
            stats = _get_firebase_stats()
            _set_cache("stats", stats)
            return stats
        except Exception as e:
            log.error(f"Firebase stats query failed: {e}")
            return _empty_stats()

    stats = _get_postgres_stats()
    _set_cache("stats", stats)
    return stats
