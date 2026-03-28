"""
SQLite database layer shared by the organizer and the dashboard.
"""

import sqlite3
import os
from config import DB_PATH, DAYS, POSTS_PER_DAY, MODELS


def get_connection():
    """Return a new SQLite connection with row-factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # safe for concurrent reads
    return conn


def init_db():
    """Create tables and seed the post grid if empty."""
    conn = get_connection()
    cur = conn.cursor()

    # --- file_log: every image the organizer processes ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS file_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT    NOT NULL,
            new_name      TEXT    NOT NULL,
            model         TEXT    NOT NULL,
            confidence    REAL    NOT NULL,
            day           TEXT    NOT NULL,
            post          TEXT    NOT NULL,
            frame         INTEGER NOT NULL,
            dest_path     TEXT    NOT NULL,
            timestamp     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        )
    """)

    # --- posts: the content-tracker grid ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            model       TEXT NOT NULL,
            day         TEXT NOT NULL,
            post        TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'Not Started',
            has_images  INTEGER NOT NULL DEFAULT 0,
            image_count INTEGER NOT NULL DEFAULT 0,
            UNIQUE(model, day, post)
        )
    """)

    # Seed posts grid if the table is empty
    cur.execute("SELECT COUNT(*) FROM posts")
    if cur.fetchone()[0] == 0:
        for model_key in MODELS:
            for day in DAYS:
                for p in range(1, POSTS_PER_DAY + 1):
                    post_label = f"Post{p}"
                    cur.execute(
                        "INSERT INTO posts (model, day, post) VALUES (?, ?, ?)",
                        (model_key, day, post_label),
                    )

    conn.commit()
    conn.close()


def log_file(original_name, new_name, model, confidence, day, post, frame, dest_path):
    """Insert a row into file_log and update the matching post's image count."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO file_log
           (original_name, new_name, model, confidence, day, post, frame, dest_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (original_name, new_name, model, confidence, day, post, frame, dest_path),
    )

    # Update the matching post row
    cur.execute(
        """UPDATE posts
           SET has_images = 1,
               image_count = (
                   SELECT COUNT(*) FROM file_log
                   WHERE model = ? AND day = ? AND post = ?
               )
           WHERE model = ? AND day = ? AND post = ?""",
        (model, day, post, model, day, post),
    )
    conn.commit()
    conn.close()


def get_all_posts():
    """Return every post row as a list of dicts."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM posts ORDER BY model, id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_post_status(post_id, new_status):
    """Set the status column for a single post."""
    conn = get_connection()
    conn.execute("UPDATE posts SET status = ? WHERE id = ?", (new_status, post_id))
    conn.commit()
    conn.close()


def get_file_log():
    """Return the full file log, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM file_log ORDER BY timestamp DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
