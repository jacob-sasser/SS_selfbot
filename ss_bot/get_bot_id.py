import os
import sqlite3
import json

def get_bot_id_from_firefox_profile(profile_path: str) -> str:
    """
    Reads Discord's user_id_cache from Firefox profile caches.sqlite
    and returns the user ID as a string.
    """
    db_path = os.path.join(
        profile_path, "storage", "default", "https+++discord.com", "ls", "data.sqlite"
    )
    
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Cannot find caches.sqlite at {db_path}")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # List all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]
    
    # Usually it's in webappsstore2 table, but check all tables
    target_tables = [t for t in tables if "data" in t.lower()]
    if not target_tables:
        raise ValueError("No data table found in caches.sqlite")
    
    for table in target_tables:
        try:
            cur.execute(f"SELECT key, value FROM {table} WHERE key='user_id_cache';")
            row = cur.fetchone()
            if row:
                value = row[1]
                # value is usually a JSON string
                try:
                    return json.loads(value)
                except Exception:
                    return value
        except Exception:
            continue
    
    raise ValueError("user_id_cache not found in caches.sqlite")
