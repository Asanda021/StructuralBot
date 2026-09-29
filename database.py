import sqlite3
from contextlib import contextmanager
from typing import Iterator

from config import DATABASE_PATH


# =========================================================
# DATABASE CONNECTION
# =========================================================

@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """
    Create a SQLite database connection.

    The connection is automatically committed on success
    and rolled back if an exception occurs.
    """

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def initialize_database() -> None:
    """
    Create the initial database structure.

    The schema is intentionally separated from calculation
    logic so the database can be migrated or replaced later.
    """

    with get_connection() as connection:

        cursor = connection.cursor()

        # -------------------------------------------------
        # USERS
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT NOT NULL DEFAULT 'fa',
                unit_system TEXT NOT NULL DEFAULT 'SI',
                profession TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # -------------------------------------------------
        # PROJECTS
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                structure_type TEXT,
                design_code TEXT,
                code_edition TEXT,
                unit_system TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # -------------------------------------------------
        # FLOORS
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS floors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                floor_number INTEGER,
                height REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            )
            """
        )

        # -------------------------------------------------
        # MEMBERS
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                floor_id INTEGER,
                member_type TEXT NOT NULL,
                name TEXT,
                geometry_json TEXT,
                material_json TEXT,
                input_json TEXT,
                result_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (floor_id)
                    REFERENCES floors(id)
                    ON DELETE SET NULL
            )
            """
        )

        # -------------------------------------------------
        # CALCULATIONS
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS calculations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                member_id INTEGER,
                calculation_type TEXT NOT NULL,
                code TEXT,
                code_edition TEXT,
                input_json TEXT,
                result_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (member_id)
                    REFERENCES members(id)
                    ON DELETE SET NULL
            )
            """
        )

        # -------------------------------------------------
        # REINFORCEMENT
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reinforcement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                member_id INTEGER,
                bar_mark TEXT,
                bar_type TEXT,
                diameter REAL,
                quantity INTEGER,
                length REAL,
                total_length REAL,
                weight REAL,
                grade TEXT,
                shape_code TEXT,
                shape_data_json TEXT,
                location TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (member_id)
                    REFERENCES members(id)
                    ON DELETE SET NULL
            )
            """
        )

        # -------------------------------------------------
        # SPLICES
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS splices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                member_id INTEGER,
                splice_type TEXT NOT NULL,
                diameter REAL,
                quantity INTEGER,
                length REAL,
                location TEXT,
                data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (member_id)
                    REFERENCES members(id)
                    ON DELETE SET NULL
            )
            """
        )

        # -------------------------------------------------
        # CUT LIST
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cut_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                diameter REAL NOT NULL,
                stock_length REAL NOT NULL DEFAULT 12.0,
                piece_length REAL NOT NULL,
                quantity INTEGER NOT NULL,
                waste REAL DEFAULT 0,
                waste_percentage REAL DEFAULT 0,
                cutting_plan_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            )
            """
        )

        # -------------------------------------------------
        # QUANTITIES
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quantities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                member_id INTEGER,
                material_type TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 0,
                unit TEXT,
                details_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (member_id)
                    REFERENCES members(id)
                    ON DELETE SET NULL
            )
            """
        )

        # -------------------------------------------------
        # CALCULATION HISTORY
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS calculation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                member_id INTEGER,
                action TEXT NOT NULL,
                data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (member_id)
                    REFERENCES members(id)
                    ON DELETE SET NULL
            )
            """
        )

        # -------------------------------------------------
        # INDEXES
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_users_telegram_id
            ON users(telegram_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_projects_user_id
            ON projects(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_floors_project_id
            ON floors(project_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_members_project_id
            ON members(project_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_calculations_project_id
            ON calculations(project_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_reinforcement_project_id
            ON reinforcement(project_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cut_list_project_id
            ON cut_list(project_id)
            """
        )


# =========================================================
# USER HELPERS
# =========================================================

def get_user_by_telegram_id(telegram_id: int):
    """
    Return a user by Telegram ID.
    """

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )

        return cursor.fetchone()


def create_user(
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    language: str = "fa",
    unit_system: str = "SI",
    profession: str | None = None,
):
    """
    Create a new user.
    """

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users (
                telegram_id,
                username,
                first_name,
                last_name,
                language,
                unit_system,
                profession
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                username,
                first_name,
                last_name,
                language,
                unit_system,
                profession,
            )
        )

        return cursor.lastrowid


# =========================================================
# PROJECT HELPERS
# =========================================================

def create_project(
    user_id: int,
    name: str,
    description: str | None = None,
    structure_type: str | None = None,
    design_code: str | None = None,
    code_edition: str | None = None,
    unit_system: str = "SI",
):
    """
    Create a new project.
    """

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO projects (
                user_id,
                name,
                description,
                structure_type,
                design_code,
                code_edition,
                unit_system
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name,
                description,
                structure_type,
                design_code,
                code_edition,
                unit_system,
            )
        )

        return cursor.lastrowid


def get_projects_by_user(user_id: int):
    """
    Return all projects belonging to a user.
    """

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM projects
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,)
        )

        return cursor.fetchall()


# =========================================================
# STARTUP
# =========================================================

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")
