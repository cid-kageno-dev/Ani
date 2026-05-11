import importlib
import importlib.util
import json
import threading
import time
from datetime import datetime, timezone
from typing import Any

import psycopg2.extras
from psycopg2 import pool
from thefuzz import process

from config import Config
from app.logger import get_logger

log        = get_logger("ani.db")
log_render = get_logger("ani.render")

# ── Connection pools ──────────────────────────────────────────────────────
_pool:        pool.ThreadedConnectionPool | None = None
_render_pool: pool.ThreadedConnectionPool | None = None

# ── Firebase state ────────────────────────────────────────────────────────
_firestore_client   = None
_firebase_ready     = False
_firebase_admin     = None
_firebase_creds_mod = None
_firebase_fs_mod    = None

# ── Schema SQL ────────────────────────────────────────────────────────────
_SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS chat_interactions (
        id          SERIAL PRIMARY KEY,
        user_query  TEXT         NOT NULL,
        ai_response TEXT         NOT NULL,
        source      VARCHAR(50)  DEFAULT 'AI Response',
        created_at  TIMESTAMP    DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS idx_chat_created
        ON chat_interactions(created_at DESC);
"""


# ── Firebase helpers ──────────────────────────────────────────────────────

def _firebase_modules():
    global _firebase_admin, _firebase_creds_mod, _firebase_fs_mod
    if _firebase_admin and _firebase_creds_mod and _firebase_fs_mod:
        return _firebase_admin, _firebase_creds_mod, _firebase_fs_mod

    if importlib.util.find_spec("firebase_admin") is None:
        raise RuntimeError("firebase-admin is not installed")

    _firebase_admin     = importlib.import_module("firebase_admin")
    _firebase_creds_mod = importlib.import_module("firebase_admin.credentials")
    _firebase_fs_mod    = importlib.import_module("firebase_admin.firestore")
    return _firebase_admin, _firebase_creds_mod, _firebase_fs_mod


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


def _normalize_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.now(timezone.utc)


def _doc_to_interaction(doc) -> dict:
    data = doc.to_dict() or {}
    return {
        "id":          doc.id,
        "user_query":  data.get("user_query", ""),
        "ai_response": data.get("ai_response", ""),
        "source":      data.get("source", "AI Response"),
        "created_at":  _normalize_dt(data.get("created_at")),
    }


def _get_firestore():
    global _firestore_client, _firebase_ready
    if _firestore_client is not None:
        return _firestore_client

    if not _firebase_configured():
        raise RuntimeError("Firebase is not configured")

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

    options: dict = {}
    if Config.FIREBASE_DATABASE_URL:
        options["databaseURL"] = Config.FIREBASE_DATABASE_URL
    if Config.FIREBASE_PROJECT_ID:
        options["projectId"] = Config.FIREBASE_PROJECT_ID

    try:
        app = firebase_admin.get_app()
    except ValueError:
        app = firebase_admin.initialize_app(cred, options or None)

    _firestore_client = firestore.client(app=app)
    _firebase_ready   = True
    log.info(f"Firebase Firestore ready — collection '{Config.FIREBASE_COLLECTION}'")
    return _firestore_client


def _firebase_collection():
    return _get_firestore().collection(Config.FIREBASE_COLLECTION)


# ── PostgreSQL helpers ────────────────────────────────────────────────────

def _get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        if not Config.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not configured")
        log.info("Initializing primary DB pool (min=1, max=5)")
        _pool = pool.ThreadedConnectionPool(1, 5, Config.DATABASE_URL)
        log.info("Primary DB pool ready")
    return _pool


def _get_render_pool() -> pool.ThreadedConnectionPool:
    global _render_pool
    if _render_pool is None:
        if not Config.RENDER_DATABASE_URL:
            raise RuntimeError("RENDER_DATABASE_URL is not configured")
        log_render.info("Initializing Render DB pool (min=1, max=5)")
        _render_pool = pool.ThreadedConnectionPool(1, 5, Config.RENDER_DATABASE_URL)
        log_render.info("Render DB pool ready")
    return _render_pool


def _conn():
    return _get_pool().getconn()


def _put(conn) -> None:
    if conn and _pool is not None:
        _pool.putconn(conn)


def _render_conn():
    return _get_render_pool().getconn()


def _render_put(conn) -> None:
    if conn and _render_pool is not None:
        _render_pool.putconn(conn)


# ── Schema init ───────────────────────────────────────────────────────────

def _init_postgres_schema(get_conn, put_conn, label: str) -> bool:
    logger = log_render if label == "render" else log
    logger.info(f"Verifying schema ({label})…")
    conn = None
    try:
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute(_SCHEMA_SQL)
        conn.commit()
        cur.close()
        logger.info(f"Schema OK — 'chat_interactions' ready ({label})")
        return True
    except Exception as e:
        logger.error(f"Schema init failed ({label}): {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        put_conn(conn)


def ensure_schema() -> bool:
    backend = _backend()

    if backend == "firebase":
        try:
            _get_firestore()
            log.info("Firebase — schemaless, schema check skipped")
            return True
        except Exception as e:
            log.error(f"Firebase init failed: {e}")
            return False

    if backend == "postgres":
        return _init_postgres_schema(_conn, _put, "primary")

    log.warning("No database backend — schema check skipped")
    return False


def ensure_render_schema() -> bool:
    if not Config.RENDER_DATABASE_URL:
        return False
    return _init_postgres_schema(_render_conn, _render_put, "render")


# ── Save interaction ──────────────────────────────────────────────────────

def _save_firebase(user_query: str, ai_response: str, source: str) -> None:
    _, _, firestore = _firebase_modules()
    doc = {
        "user_query":  user_query,
        "ai_response": ai_response,
        "source":      source,
        "created_at":  firestore.SERVER_TIMESTAMP,
    }
    update_time, ref = _firebase_collection().add(doc)
    log.info(f"Firebase saved {ref.id} [{source}] at {update_time}")


def _save_postgres(user_query: str, ai_response: str, source: str) -> None:
    t0   = time.perf_counter()
    conn = None
    try:
        conn = _conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO chat_interactions (user_query, ai_response, source) VALUES (%s, %s, %s) RETURNING id",
            (user_query, ai_response, source),
        )
        row_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        ms = (time.perf_counter() - t0) * 1000
        log.info(f"Primary PG saved #{row_id} [{source}] in {ms:.1f}ms")
    except Exception as e:
        log.error(f"Primary PG save failed: {e}")
        if conn:
            conn.rollback()
    finally:
        _put(conn)


def _save_render(user_query: str, ai_response: str, source: str) -> None:
    t0   = time.perf_counter()
    conn = None
    try:
        conn = _render_conn()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO chat_interactions (user_query, ai_response, source) VALUES (%s, %s, %s) RETURNING id",
            (user_query, ai_response, source),
        )
        row_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        ms = (time.perf_counter() - t0) * 1000
        log_render.info(f"Render PG mirrored #{row_id} [{source}] in {ms:.1f}ms")
    except Exception as e:
        log_render.error(f"Render PG mirror failed: {e}")
        if conn:
            conn.rollback()
    finally:
        _render_put(conn)


def save_interaction(user_query: str, ai_response: str, source: str = "AI Response") -> None:
    backend = _backend()

    if backend == "firebase":
        try:
            _save_firebase(user_query, ai_response, source)
        except Exception as e:
            log.error(f"Firebase save failed: {e}")
    elif backend == "postgres":
        _save_postgres(user_query, ai_response, source)
    else:
        log.debug("No backend configured — skipping save")

    if Config.RENDER_DATABASE_URL:
        # Mirror to Render in a separate thread so Firebase + Render run in parallel.
        threading.Thread(
            target=_save_render,
            args=(user_query, ai_response, source),
            daemon=True,
        ).start()


# ── Fetch rows ────────────────────────────────────────────────────────────

def _empty_stats() -> dict:
    return {
        "total":               0,
        "ai_responses":        0,
        "fallback_responses":  0,
        "first_interaction":   None,
        "last_interaction":    None,
    }


def _firebase_rows(limit: int = 500) -> list:
    _, _, firestore = _firebase_modules()
    docs = (
        _firebase_collection()
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [_doc_to_interaction(doc) for doc in docs]


def _postgres_rows(limit: int = 500) -> list:
    conn = None
    try:
        conn = _conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, user_query, ai_response, source, created_at "
            "FROM chat_interactions ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        log.error(f"Primary PG fetch failed: {e}")
        return []
    finally:
        _put(conn)


# ── Public query API ──────────────────────────────────────────────────────

def get_fallback_answer(user_query: str) -> str:
    backend = _backend()
    if backend is None:
        return "I'm offline and have no database connection for cached answers. Please try again later."

    log.info(f"Fallback search: '{user_query[:60]}'")
    t0 = time.perf_counter()
    try:
        rows = _firebase_rows(500) if backend == "firebase" else _postgres_rows(500)

        if not rows:
            return "I'm offline and have no cached answers yet. Please try again later."

        past_queries        = [r["user_query"] for r in rows]
        best_match, score   = process.extractOne(user_query, past_queries)
        ms                  = (time.perf_counter() - t0) * 1000
        log.info(f"Fuzzy match: '{best_match[:50]}' score={score} in {ms:.1f}ms")

        if score > 75:
            for row in rows:
                if row["user_query"] == best_match:
                    return row["ai_response"]

        log.warning(f"No match above threshold (score={score})")
        return "I'm currently offline and couldn't find a relevant cached answer. Please try again later."

    except Exception as e:
        log.error(f"Fallback lookup failed: {e}")
        return "System error — knowledge base temporarily unavailable."


def get_recent_interactions(limit: int = 20) -> list:
    backend = _backend()
    if backend is None:
        log.warning("History unavailable — no backend configured")
        return []

    log.debug(f"Fetching {limit} recent interactions from {backend}")
    if backend == "firebase":
        try:
            rows = _firebase_rows(limit)
            log.debug(f"Firebase returned {len(rows)} interactions")
            return rows
        except Exception as e:
            log.error(f"Firebase history fetch failed: {e}")
            return []

    rows = _postgres_rows(limit)
    log.debug(f"Primary PG returned {len(rows)} interactions")
    return rows


def get_stats() -> dict:
    backend = _backend()
    if backend is None:
        log.warning("Stats unavailable — no backend configured")
        return _empty_stats()

    if backend == "firebase":
        try:
            return _firebase_stats()
        except Exception as e:
            log.error(f"Firebase stats failed: {e}")
            return _empty_stats()

    return _postgres_stats()


def _firebase_stats() -> dict:
    stats = _empty_stats()
    for doc in _firebase_collection().stream():
        row = _doc_to_interaction(doc)
        stats["total"] += 1
        if row["source"] == "AI Response":
            stats["ai_responses"] += 1
        elif row["source"] == "Database":
            stats["fallback_responses"] += 1

        ts       = row["created_at"].isoformat()
        first_at = stats["first_interaction"]
        last_at  = stats["last_interaction"]
        if first_at is None or ts < first_at:
            stats["first_interaction"] = ts
        if last_at is None or ts > last_at:
            stats["last_interaction"] = ts
    return stats


def _postgres_stats() -> dict:
    conn = None
    try:
        conn = _conn()
        cur  = conn.cursor()
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
            "total":              row[0],
            "ai_responses":       row[1],
            "fallback_responses": row[2],
            "first_interaction":  row[3].isoformat() if row[3] else None,
            "last_interaction":   row[4].isoformat() if row[4] else None,
        }
    except Exception as e:
        log.error(f"Primary PG stats failed: {e}")
        return _empty_stats()
    finally:
        _put(conn)
