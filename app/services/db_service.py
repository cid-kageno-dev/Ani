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
        log.debug("Firebase modules already imported — reusing")
        return _firebase_admin, _firebase_creds_mod, _firebase_fs_mod

    log.debug("Importing firebase_admin modules…")
    if importlib.util.find_spec("firebase_admin") is None:
        raise RuntimeError("firebase-admin is not installed")

    _firebase_admin     = importlib.import_module("firebase_admin")
    _firebase_creds_mod = importlib.import_module("firebase_admin.credentials")
    _firebase_fs_mod    = importlib.import_module("firebase_admin.firestore")
    log.debug("Firebase modules imported successfully")
    return _firebase_admin, _firebase_creds_mod, _firebase_fs_mod


def _firebase_configured() -> bool:
    result = bool(
        Config.FIREBASE_CREDENTIALS
        or Config.FIREBASE_SERVICE_ACCOUNT_JSON
        or Config.FIREBASE_PROJECT_ID
    )
    log.debug(f"_firebase_configured() → {result}")
    return result


def _backend() -> str | None:
    requested = Config.DATABASE_BACKEND.lower()
    log.debug(f"_backend()  requested='{requested}'")

    if requested in {"firebase", "firestore"}:
        log.debug("Backend resolved → firebase (explicit)")
        return "firebase"
    if requested in {"postgres", "postgresql"}:
        result = "postgres" if Config.DATABASE_URL else None
        log.debug(f"Backend resolved → {result} (explicit postgres)")
        return result
    if _firebase_configured():
        log.debug("Backend resolved → firebase (auto)")
        return "firebase"
    if Config.DATABASE_URL:
        log.debug("Backend resolved → postgres (auto)")
        return "postgres"
    log.debug("Backend resolved → None (nothing configured)")
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
        log.debug("Firestore client already initialised — reusing")
        return _firestore_client

    log.debug("Initialising Firestore client…")
    if not _firebase_configured():
        raise RuntimeError("Firebase is not configured")

    firebase_admin, credentials, firestore = _firebase_modules()

    if Config.FIREBASE_SERVICE_ACCOUNT_JSON:
        log.debug("Using FIREBASE_SERVICE_ACCOUNT_JSON for credentials")
        sa_info = json.loads(Config.FIREBASE_SERVICE_ACCOUNT_JSON)
        if "private_key" in sa_info:
            sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(sa_info)
    elif Config.FIREBASE_CREDENTIALS:
        log.debug(f"Using credentials file: {Config.FIREBASE_CREDENTIALS}")
        cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS)
    else:
        log.debug("Using ApplicationDefault credentials")
        cred = credentials.ApplicationDefault()

    options: dict = {}
    if Config.FIREBASE_DATABASE_URL:
        options["databaseURL"] = Config.FIREBASE_DATABASE_URL
    if Config.FIREBASE_PROJECT_ID:
        options["projectId"] = Config.FIREBASE_PROJECT_ID

    log.debug(f"Firebase app options: {list(options.keys())}")

    try:
        app = firebase_admin.get_app()
        log.debug("Reusing existing Firebase app")
    except ValueError:
        log.debug("Initialising new Firebase app")
        app = firebase_admin.initialize_app(cred, options or None)

    _firestore_client = firestore.client(app=app)
    _firebase_ready   = True
    log.info(f"Firebase Firestore ready — collection '{Config.FIREBASE_COLLECTION}'")
    return _firestore_client


def _firebase_collection():
    col = _get_firestore().collection(Config.FIREBASE_COLLECTION)
    log.debug(f"Firebase collection ref: '{Config.FIREBASE_COLLECTION}'")
    return col


# ── PostgreSQL helpers ────────────────────────────────────────────────────

def _get_pool() -> pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        if not Config.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not configured")
        log.debug("Creating primary DB connection pool…")
        log.info("Initialising primary DB pool (min=1, max=5)")
        _pool = pool.ThreadedConnectionPool(1, 5, Config.DATABASE_URL)
        log.info("Primary DB pool ready")
        log.debug(f"  host={Config.DATABASE_URL.split('@')[-1].split('?')[0]}")
    else:
        log.debug("Primary DB pool already exists — reusing")
    return _pool


def _get_render_pool() -> pool.ThreadedConnectionPool:
    global _render_pool
    if _render_pool is None:
        if not Config.RENDER_DATABASE_URL:
            raise RuntimeError("RENDER_DATABASE_URL is not configured")
        log_render.debug("Creating Render DB connection pool…")
        log_render.info("Initialising Render DB pool (min=1, max=5)")
        _render_pool = pool.ThreadedConnectionPool(1, 5, Config.RENDER_DATABASE_URL)
        log_render.info("Render DB pool ready")
        log_render.debug(f"  host={Config.RENDER_DATABASE_URL.split('@')[-1].split('?')[0]}")
    else:
        log_render.debug("Render DB pool already exists — reusing")
    return _render_pool


def _conn():
    log.debug("Checking out connection from primary pool")
    conn = _get_pool().getconn()
    log.debug(f"Connection checked out  id={id(conn)}")
    return conn


def _put(conn) -> None:
    if conn and _pool is not None:
        log.debug(f"Returning connection to primary pool  id={id(conn)}")
        _pool.putconn(conn)


def _render_conn():
    log_render.debug("Checking out connection from Render pool")
    conn = _get_render_pool().getconn()
    log_render.debug(f"Render connection checked out  id={id(conn)}")
    return conn


def _render_put(conn) -> None:
    if conn and _render_pool is not None:
        log_render.debug(f"Returning connection to Render pool  id={id(conn)}")
        _render_pool.putconn(conn)


# ── Schema init ───────────────────────────────────────────────────────────

def _init_postgres_schema(get_conn, put_conn, label: str) -> bool:
    logger = log_render if label == "render" else log
    logger.info(f"Verifying schema ({label})…")
    conn = None
    try:
        conn = get_conn()
        logger.debug(f"  Executing CREATE TABLE IF NOT EXISTS  ({label})")
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
    log.debug(f"ensure_schema()  backend={backend}")

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
    log.debug(f"ensure_render_schema()  RENDER_DATABASE_URL={'set' if Config.RENDER_DATABASE_URL else 'not set'}")
    if not Config.RENDER_DATABASE_URL:
        return False
    return _init_postgres_schema(_render_conn, _render_put, "render")


# ── Save interaction ──────────────────────────────────────────────────────

def _save_firebase(user_query: str, ai_response: str, source: str) -> None:
    log.debug(f"_save_firebase()  source={source}  query_len={len(user_query)}  response_len={len(ai_response)}")
    t0 = time.perf_counter()
    _, _, firestore = _firebase_modules()
    doc = {
        "user_query":  user_query,
        "ai_response": ai_response,
        "source":      source,
        "created_at":  firestore.SERVER_TIMESTAMP,
    }
    log.debug("  Calling Firestore collection.add()…")
    update_time, ref = _firebase_collection().add(doc)
    ms = (time.perf_counter() - t0) * 1000
    log.info(f"Firebase saved  id={ref.id}  source={source}  {ms:.0f}ms")


def _save_postgres(user_query: str, ai_response: str, source: str) -> None:
    log.debug(f"_save_postgres()  source={source}  query_len={len(user_query)}  response_len={len(ai_response)}")
    t0   = time.perf_counter()
    conn = None
    try:
        conn = _conn()
        cur  = conn.cursor()
        log.debug("  Executing INSERT INTO chat_interactions…")
        cur.execute(
            "INSERT INTO chat_interactions (user_query, ai_response, source) VALUES (%s, %s, %s) RETURNING id",
            (user_query, ai_response, source),
        )
        row_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        ms = (time.perf_counter() - t0) * 1000
        log.info(f"Primary PG saved  id=#{row_id}  source={source}  {ms:.1f}ms")
    except Exception as e:
        log.error(f"Primary PG save failed: {e}")
        if conn:
            conn.rollback()
    finally:
        _put(conn)


def _save_render(user_query: str, ai_response: str, source: str) -> None:
    log_render.debug(f"_save_render()  source={source}  query_len={len(user_query)}  response_len={len(ai_response)}")
    t0   = time.perf_counter()
    conn = None
    try:
        conn = _render_conn()
        cur  = conn.cursor()
        log_render.debug("  Executing INSERT INTO chat_interactions (Render)…")
        cur.execute(
            "INSERT INTO chat_interactions (user_query, ai_response, source) VALUES (%s, %s, %s) RETURNING id",
            (user_query, ai_response, source),
        )
        row_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        ms = (time.perf_counter() - t0) * 1000
        log_render.info(f"Render PG mirrored  id=#{row_id}  source={source}  {ms:.1f}ms")
    except Exception as e:
        log_render.error(f"Render PG mirror failed: {e}")
        if conn:
            conn.rollback()
    finally:
        _render_put(conn)


def save_interaction(user_query: str, ai_response: str, source: str = "AI Response") -> None:
    backend = _backend()
    log.debug(f"save_interaction()  backend={backend}  source={source}")

    if backend == "firebase":
        log.debug("Saving to Firebase…")
        try:
            _save_firebase(user_query, ai_response, source)
        except Exception as e:
            log.error(f"Firebase save failed: {e}")
    elif backend == "postgres":
        log.debug("Saving to primary Postgres…")
        _save_postgres(user_query, ai_response, source)
    else:
        log.debug("No primary backend — skipping primary save")

    if Config.RENDER_DATABASE_URL:
        log_render.debug("Spawning Render mirror thread…")
        threading.Thread(
            target=_save_render,
            args=(user_query, ai_response, source),
            daemon=True,
            name="bg-render-mirror",
        ).start()
        log_render.debug("Render mirror thread started")


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
    log.debug(f"_firebase_rows()  limit={limit}")
    t0 = time.perf_counter()
    _, _, firestore = _firebase_modules()
    docs = (
        _firebase_collection()
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    rows = [_doc_to_interaction(doc) for doc in docs]
    ms = (time.perf_counter() - t0) * 1000
    log.debug(f"_firebase_rows() → {len(rows)} rows  {ms:.0f}ms")
    return rows


def _postgres_rows(limit: int = 500) -> list:
    log.debug(f"_postgres_rows()  limit={limit}")
    t0   = time.perf_counter()
    conn = None
    try:
        conn = _conn()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        log.debug(f"  Executing SELECT … LIMIT {limit}")
        cur.execute(
            "SELECT id, user_query, ai_response, source, created_at "
            "FROM chat_interactions ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        ms = (time.perf_counter() - t0) * 1000
        log.debug(f"_postgres_rows() → {len(rows)} rows  {ms:.0f}ms")
        return rows
    except Exception as e:
        log.error(f"Primary PG fetch failed: {e}")
        return []
    finally:
        _put(conn)


# ── Public query API ──────────────────────────────────────────────────────

def get_fallback_answer(user_query: str) -> str:
    backend = _backend()
    log.debug(f"get_fallback_answer()  backend={backend}  query='{user_query[:50]}'")

    if backend is None:
        log.warning("No backend — cannot serve fallback")
        return "I'm offline and have no database connection for cached answers. Please try again later."

    log.info(f"Fallback search: '{user_query[:60]}'")
    t0 = time.perf_counter()
    try:
        log.debug(f"Fetching up to 500 rows from {backend}…")
        rows = _firebase_rows(500) if backend == "firebase" else _postgres_rows(500)
        log.debug(f"Fetched {len(rows)} rows for fuzzy match")

        if not rows:
            log.warning("DB is empty — no cached answers to match against")
            return "I'm offline and have no cached answers yet. Please try again later."

        past_queries      = [r["user_query"] for r in rows]
        log.debug(f"Running fuzzy match against {len(past_queries)} queries…")
        best_match, score = process.extractOne(user_query, past_queries)
        ms                = (time.perf_counter() - t0) * 1000
        log.info(f"Fuzzy match: '{best_match[:50]}'  score={score}  {ms:.1f}ms")

        if score > 75:
            log.debug(f"Score {score} > 75 — serving cached answer")
            for row in rows:
                if row["user_query"] == best_match:
                    ans = row["ai_response"]
                    log.debug(f"Cached answer found  len={len(ans)}")
                    return ans

        log.warning(f"Score {score} ≤ 75 — no match above threshold")
        return "I'm currently offline and couldn't find a relevant cached answer. Please try again later."

    except Exception as e:
        log.error(f"Fallback lookup failed: {e}")
        return "System error — knowledge base temporarily unavailable."


def get_recent_interactions(limit: int = 20) -> list:
    backend = _backend()
    log.debug(f"get_recent_interactions()  backend={backend}  limit={limit}")

    if backend is None:
        log.warning("History unavailable — no backend configured")
        return []

    if backend == "firebase":
        try:
            rows = _firebase_rows(limit)
            log.debug(f"History: {len(rows)} Firebase rows returned")
            return rows
        except Exception as e:
            log.error(f"Firebase history fetch failed: {e}")
            return []

    rows = _postgres_rows(limit)
    log.debug(f"History: {len(rows)} primary PG rows returned")
    return rows


def get_stats() -> dict:
    backend = _backend()
    log.debug(f"get_stats()  backend={backend}")

    if backend is None:
        log.warning("Stats unavailable — no backend configured")
        return _empty_stats()

    if backend == "firebase":
        try:
            stats = _firebase_stats()
            log.debug(f"Firebase stats → {stats}")
            return stats
        except Exception as e:
            log.error(f"Firebase stats failed: {e}")
            return _empty_stats()

    stats = _postgres_stats()
    log.debug(f"Postgres stats → {stats}")
    return stats


def _firebase_stats() -> dict:
    log.debug("_firebase_stats(): streaming all documents…")
    t0    = time.perf_counter()
    stats = _empty_stats()
    count = 0
    for doc in _firebase_collection().stream():
        row    = _doc_to_interaction(doc)
        count += 1
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

    ms = (time.perf_counter() - t0) * 1000
    log.debug(f"_firebase_stats() scanned {count} docs  {ms:.0f}ms")
    return stats


def _postgres_stats() -> dict:
    log.debug("_postgres_stats(): running aggregate query…")
    t0   = time.perf_counter()
    conn = None
    try:
        conn = _conn()
        cur  = conn.cursor()
        log.debug("  Executing COUNT/MIN/MAX aggregate query")
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
        ms = (time.perf_counter() - t0) * 1000
        log.debug(f"_postgres_stats() → total={row[0]}  {ms:.0f}ms")
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
