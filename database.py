import psycopg

from options import DATABASE_URL


def connection():
    return psycopg.connect(DATABASE_URL, autocommit=True)


def init_db():
    with connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                group_num TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)


def get_group(user_id):
    with connection() as conn:
        row = conn.execute("SELECT group_num FROM users WHERE user_id = %s", (user_id,)).fetchone()
    return row[0] if row else None


def save_group(user_id, group_num):
    with connection() as conn:
        conn.execute("""
            INSERT INTO users (user_id, group_num)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET group_num = EXCLUDED.group_num, updated_at = NOW()
        """, (user_id, group_num))


def delete_group(user_id):
    with connection() as conn:
        conn.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
