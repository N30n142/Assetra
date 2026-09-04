import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance", "assetra.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def get_db():
    """Return a new sqlite3 connection with row access by column name and FK enforcement on."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(seed=True):
    """Create tables if they don't exist. Optionally seed with starter reference data."""
    conn = get_db()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()

    if seed:
        cur = conn.execute("SELECT COUNT(*) AS c FROM locations")
        if cur.fetchone()["c"] == 0:
            conn.executemany(
                "INSERT INTO locations (name) VALUES (?)",
                [
                    ("RECEPTION",),
                    ("General Work Section",),
                    ("Account Office 1",),
                    ("AGM Office",),
                    ("Account Office 2",),
                    ("Legal/Office",),
                    ("Internal Audit Office",),
                    ("Opt/Tech",),
                    ("MD/Secretary Office",),
                    ("MD Office",),
                    ("Boardroom",),
                    ("Bus/Dev Office",),
                    ("COO Office",),
                    ("CFO Office",),
                    ("Kitchen",),
                    ("GP",),
                ],
            )
        conn.commit()
    conn.close()