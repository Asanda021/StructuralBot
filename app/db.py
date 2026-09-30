import sqlite3
from pathlib import Path
import json

class Database:
    def __init__(self,path):
        self.path=path; Path(path).parent.mkdir(parents=True,exist_ok=True)
    def connect(self):
        con=sqlite3.connect(self.path); con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA foreign_keys=ON"); return con
    def init(self):
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,name TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,name TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS project_estimates(id INTEGER PRIMARY KEY AUTOINCREMENT,project_id INTEGER NOT NULL,inputs_json TEXT NOT NULL,result_json TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS calculations(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,project_id INTEGER,title TEXT NOT NULL,result TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL);
            CREATE TABLE IF NOT EXISTS user_settings(user_id INTEGER PRIMARY KEY,language TEXT NOT NULL DEFAULT "fa",calc_mode TEXT NOT NULL DEFAULT "detailed",unit_system TEXT NOT NULL DEFAULT "metric",concrete_grade TEXT NOT NULL DEFAULT "C25",rebar_grade TEXT NOT NULL DEFAULT "A3",standard TEXT NOT NULL DEFAULT "iran",stock_length_m REAL NOT NULL DEFAULT 12.0);
            """)
            cols={row[1] for row in c.execute("PRAGMA table_info(user_settings)").fetchall()}
            migrations={"unit_system":"TEXT NOT NULL DEFAULT 'metric'","concrete_grade":"TEXT NOT NULL DEFAULT 'C25'","rebar_grade":"TEXT NOT NULL DEFAULT 'A3'","standard":"TEXT NOT NULL DEFAULT 'iran'","stock_length_m":"REAL NOT NULL DEFAULT 12.0"}
            for name,definition in migrations.items():
                if name not in cols: c.execute(f"ALTER TABLE user_settings ADD COLUMN {name} {definition}")
    def ensure_user(self,user_id,name):
        with self.connect() as c: c.execute("INSERT INTO users(user_id,name) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET name=excluded.name",(user_id,name))
    def add_project(self,user_id,name):
        with self.connect() as c:
            cur=c.execute("INSERT INTO projects(user_id,name) VALUES(?,?)",(user_id,name[:120])); return cur.lastrowid
    def projects(self,user_id):
        with self.connect() as c: return c.execute("SELECT id,name,status,updated_at FROM projects WHERE user_id=? ORDER BY updated_at DESC,id DESC LIMIT 50",(user_id,)).fetchall()
    def save_estimate(self,user_id,project_id,inputs,result,report):
        with self.connect() as c:
            c.execute("INSERT INTO project_estimates(project_id,inputs_json,result_json) VALUES(?,?,?)",(project_id,json.dumps(inputs,ensure_ascii=False),json.dumps(result,ensure_ascii=False)))
            c.execute("UPDATE projects SET updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?",(project_id,user_id))
            c.execute("INSERT INTO calculations(user_id,project_id,title,result) VALUES(?,?,?,?)",(user_id,project_id,"متره ساختمان بتنی",report))
    def update_latest_estimate_result(self,user_id,project_id,result):
        with self.connect() as c:
            row=c.execute("SELECT id FROM project_estimates WHERE project_id=? ORDER BY id DESC LIMIT 1",(project_id,)).fetchone()
            if not row:
                return False
            c.execute("UPDATE project_estimates SET result_json=? WHERE id=?",(json.dumps(result,ensure_ascii=False),row[0]))
            return True

    def project_estimate(self,user_id,project_id):
        with self.connect() as c:
            row=c.execute("SELECT pe.project_id,p.name,pe.inputs_json,pe.result_json FROM project_estimates pe JOIN projects p ON p.id=pe.project_id WHERE p.user_id=? AND p.id=? ORDER BY pe.id DESC LIMIT 1",(user_id,project_id)).fetchone()
        if not row:return None
        return {"project_id":row[0],"project_name":row[1],"inputs":json.loads(row[2]),"result":json.loads(row[3])}
    def last_estimate(self,user_id):
        with self.connect() as c:
            row=c.execute("SELECT pe.project_id,p.name,pe.inputs_json,pe.result_json FROM project_estimates pe JOIN projects p ON p.id=pe.project_id WHERE p.user_id=? ORDER BY pe.id DESC LIMIT 1",(user_id,)).fetchone()
        if not row:return None
        return {"project_id":row[0],"project_name":row[1],"inputs":json.loads(row[2]),"result":json.loads(row[3])}
    def set_settings(self,user_id,language=None,calc_mode=None,unit_system=None,concrete_grade=None,rebar_grade=None,standard=None,stock_length_m=None):
        with self.connect() as c:
            row=c.execute("SELECT language,calc_mode,unit_system,concrete_grade,rebar_grade,standard,stock_length_m FROM user_settings WHERE user_id=?",(user_id,)).fetchone()
            vals=list(row) if row else ["fa","detailed","metric","C25","A3","iran",12.0]
            vals[0]=language or vals[0]; vals[1]=calc_mode or vals[1]; vals[2]=unit_system or vals[2]
            vals[3]=concrete_grade or vals[3]; vals[4]=rebar_grade or vals[4]; vals[5]=standard or vals[5]
            vals[6]=float(stock_length_m) if stock_length_m is not None else vals[6]
            c.execute("""INSERT INTO user_settings(user_id,language,calc_mode,unit_system,concrete_grade,rebar_grade,standard,stock_length_m)
                         VALUES(?,?,?,?,?,?,?,?)
                         ON CONFLICT(user_id) DO UPDATE SET language=excluded.language,calc_mode=excluded.calc_mode,
                         unit_system=excluded.unit_system,concrete_grade=excluded.concrete_grade,rebar_grade=excluded.rebar_grade,
                         standard=excluded.standard,stock_length_m=excluded.stock_length_m""",(user_id,*vals))


    def settings(self,user_id):
        with self.connect() as c:
            row=c.execute("SELECT language,calc_mode,unit_system,concrete_grade,rebar_grade,standard,stock_length_m FROM user_settings WHERE user_id=?",(user_id,)).fetchone()
        return {"language":row[0],"calc_mode":row[1],"unit_system":row[2],"concrete_grade":row[3],"rebar_grade":row[4],"standard":row[5],"stock_length_m":row[6]} if row else {"language":"fa","calc_mode":"detailed","unit_system":"metric","concrete_grade":"C25","rebar_grade":"A3","standard":"iran","stock_length_m":12.0}

    def last_calc(self,user_id):
        with self.connect() as c:return c.execute("SELECT title,result FROM calculations WHERE user_id=? ORDER BY id DESC LIMIT 1",(user_id,)).fetchone()
