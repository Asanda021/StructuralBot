import sqlite3
from pathlib import Path

class Database:
    def __init__(self, path):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        con = sqlite3.connect(self.path)
        con.execute("PRAGMA journal_mode=WAL")
        return con

    def init(self):
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS projects(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS calculations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

    def ensure_user(self, user_id, name):
        with self.connect() as c:
            c.execute("INSERT OR IGNORE INTO users(user_id,name) VALUES(?,?)", (user_id, name))

    def add_project(self, user_id, name):
        with self.connect() as c:
            c.execute("INSERT INTO projects(user_id,name) VALUES(?,?)", (user_id, name[:120]))

    def projects(self, user_id):
        with self.connect() as c:
            return c.execute(
                "SELECT id,name FROM projects WHERE user_id=? ORDER BY id DESC LIMIT 20", (user_id,)
            ).fetchall()

    def save_calc(self, user_id, title, result):
        with self.connect() as c:
            c.execute(
                "INSERT INTO calculations(user_id,title,result) VALUES(?,?,?)",
                (user_id, title, result),
            )

    def last_calc(self, user_id):
        with self.connect() as c:
            return c.execute(
                "SELECT title,result FROM calculations WHERE user_id=? ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
