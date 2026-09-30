import sqlite3
from pathlib import Path
import json


class Database:
    def __init__(self, path):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self):
        con = sqlite3.connect(self.path)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
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
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS project_estimates(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                inputs_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS calculations(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                project_id INTEGER,
                title TEXT NOT NULL,
                result TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL
            );
            """)

            cols = {r[1] for r in c.execute("PRAGMA table_info(calculations)")}
            if "project_id" not in cols:
                c.execute("ALTER TABLE calculations ADD COLUMN project_id INTEGER")

    def ensure_user(self, user_id, name):
        with self.connect() as c:
            c.execute(
                "INSERT INTO users(user_id,name) VALUES(?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET name=excluded.name",
                (user_id, name),
            )

    def add_project(self, user_id, name):
        with self.connect() as c:
            cur = c.execute(
                "INSERT INTO projects(user_id,name) VALUES(?,?)",
                (user_id, name[:120]),
            )
            return cur.lastrowid

    def projects(self, user_id):
        with self.connect() as c:
            return c.execute(
                "SELECT id,name,status,updated_at FROM projects "
                "WHERE user_id=? ORDER BY updated_at DESC, id DESC LIMIT 50",
                (user_id,),
            ).fetchall()

    def save_estimate(self, user_id, project_id, inputs, result, report):
        with self.connect() as c:
            c.execute(
                "INSERT INTO project_estimates(project_id,inputs_json,result_json) "
                "VALUES(?,?,?)",
                (project_id, json.dumps(inputs, ensure_ascii=False),
                 json.dumps(result, ensure_ascii=False)),
            )
            c.execute(
                "UPDATE projects SET updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",
                (project_id, user_id),
            )
            c.execute(
                "INSERT INTO calculations(user_id,project_id,title,result) VALUES(?,?,?,?)",
                (user_id, project_id, "متره ساختمان بتنی", report),
            )

    def last_estimate(self, user_id):
        with self.connect() as c:
            row = c.execute(
                "SELECT pe.project_id, p.name, pe.inputs_json, pe.result_json "
                "FROM project_estimates pe "
                "JOIN projects p ON p.id=pe.project_id "
                "WHERE p.user_id=? ORDER BY pe.id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "project_id": row[0],
            "project_name": row[1],
            "inputs": json.loads(row[2]),
            "result": json.loads(row[3]),
        }

    def last_calc(self, user_id):
        with self.connect() as c:
            return c.execute(
                "SELECT title,result FROM calculations WHERE user_id=? "
                "ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
