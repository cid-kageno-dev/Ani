import os
import psycopg2
import psycopg2.extras
from thefuzz import process

def _get_connection():
    """Returns a new database connection using DATABASE_URL."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise Exception("DATABASE_URL environment variable not set.")
    return psycopg2.connect(db_url)

def save_interaction(user_query, ai_response, source="AI Response"):
    """Save a chat interaction to the database."""
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_interactions (user_query, ai_response, source) VALUES (%s, %s, %s)",
            (user_query, ai_response, source)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"[DB Service]: Saved interaction for '{user_query}'")
    except Exception as e:
        print(f"[DB Service Save Error]: {e}")

def get_fallback_answer(user_query):
    """
    Fetch past interactions and use fuzzy matching to find the best answer.
    Falls back to a generic message if nothing matches well enough.
    """
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT user_query, ai_response FROM chat_interactions ORDER BY created_at DESC LIMIT 500"
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return "My knowledge base is empty right now. Please try again later."

        past_queries = [row["user_query"] for row in rows]
        best_match, score = process.extractOne(user_query, past_queries)

        print(f"[DB Service]: Best match '{best_match}' with score {score}")

        if score > 75:
            for row in rows:
                if row["user_query"] == best_match:
                    return f"(Fallback) {row['ai_response']}"

        return "I am currently offline and couldn't find a relevant answer in my history."

    except Exception as e:
        print(f"[DB Service Read Error]: {e}")
        return "System Error: Knowledge base unavailable."

def get_recent_interactions(limit=20):
    """Fetch the most recent chat interactions."""
    try:
        conn = _get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT id, user_query, ai_response, source, created_at FROM chat_interactions ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB Service Fetch Error]: {e}")
        return []
