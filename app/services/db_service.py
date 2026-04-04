import time
from psycopg2 import pool
import psycopg2.extras
from thefuzz import process
from config import Config
from app.logger import get_logger

log = get_logger("ani.db")

_pool: pool.ThreadedConnectionPool | None = None

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
    _get_pool().putconn(conn)

def ensure_schema():
    log.info("Verifying database schema...")
    conn = _conn()
    try:
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
    except Exception as e:
        log.error(f"Schema init failed: {e}")
        conn.rollback()
    finally:
        _put(conn)

def save_interaction(user_query: str, ai_response: str, source: str = "AI Response"):
    t0 = time.perf_counter()
    conn = _conn()
    try:
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
        conn.rollback()
    finally:
        _put(conn)

def get_fallback_answer(user_query: str) -> str:
    log.info(f"Fallback search for: '{user_query[:60]}'")
    t0 = time.perf_counter()
    conn = _conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT user_query, ai_response FROM chat_interactions ORDER BY created_at DESC LIMIT 500"
        )
        rows = cur.fetchall()
        cur.close()

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
    finally:
        _put(conn)

def get_recent_interactions(limit: int = 20) -> list:
    log.debug(f"Fetching {limit} recent interactions")
    conn = _conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, user_query, ai_response, source, created_at "
            "FROM chat_interactions ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        rows = cur.fetchall()
        cur.close()
        log.debug(f"Returned {len(rows)} interactions")
        return rows
    except Exception as e:
        log.error(f"Failed to fetch interactions: {e}")
        return []
    finally:
        _put(conn)

def get_stats() -> dict:
    conn = _conn()
    try:
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
        return {}
    finally:
        _put(conn)
