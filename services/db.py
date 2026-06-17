import os
import sqlite3
from flask import g, current_app, has_request_context

try:
    import psycopg2
    from psycopg2.extras import DictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

class PostgresRowWrapper:
    """Mimics sqlite3.Row for dict-like and index-like access."""
    def __init__(self, row_data, description):
        self._row = row_data
        self._keys = [col[0] for col in description]
        self._dict = {col[0]: val for col, val in zip(description, row_data)}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._row[key]
        return self._dict[key]

    def keys(self):
        return self._keys

    def __iter__(self):
        return iter(self._row)

    def __len__(self):
        return len(self._row)

    def items(self):
        return self._dict.items()

    def __repr__(self):
        return repr(self._dict)


class PostgresCursorWrapper:
    """Wraps psycopg2 cursor to mimic sqlite3.Cursor behavior."""
    def __init__(self, pg_cursor):
        self._cursor = pg_cursor
        self.lastrowid = None

    def execute(self, query, args=None):
        # Translate SQLite '?' placeholders to PostgreSQL '%s'
        pg_query = query.replace('?', '%s')
        
        # Handle lastrowid for INSERT statements
        is_insert = pg_query.strip().upper().startswith("INSERT")
        if is_insert and "RETURNING" not in pg_query.upper():
            pg_query = pg_query.rstrip('; \t\n') + " RETURNING id"
            
        if args is None:
            self._cursor.execute(pg_query)
        else:
            if not isinstance(args, (tuple, list)):
                args = (args,)
            self._cursor.execute(pg_query, args)
            
        if is_insert:
            try:
                row = self._cursor.fetchone()
                if row:
                    self.lastrowid = row[0]
            except Exception:
                self.lastrowid = None
                
        return self

    def fetchone(self):
        try:
            row = self._cursor.fetchone()
            if row is None:
                return None
            # If cursor has returned returning id previously, we might get just (id,)
            # but we want the row representation.
            return PostgresRowWrapper(row, self._cursor.description)
        except Exception:
            return None

    def fetchall(self):
        try:
            rows = self._cursor.fetchall()
            desc = self._cursor.description
            return [PostgresRowWrapper(row, desc) for row in rows]
        except Exception:
            return []

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        self._cursor.close()


class PostgresConnectionWrapper:
    """Wraps psycopg2 connection to mimic sqlite3.Connection behavior."""
    def __init__(self, pg_conn):
        self._conn = pg_conn

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor())

    def execute(self, query, args=None):
        cursor = self.cursor()
        cursor.execute(query, args)
        return cursor

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def is_postgres_configured():
    """Checks if a PostgreSQL DATABASE_URL environment variable is set."""
    return bool(os.getenv("DATABASE_URL"))


def get_db():
    """Fetches a database connection, fallback to SQLite locally."""
    if not has_request_context():
        # Out of request context (e.g. migration scripting), create standalone connection
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            if not HAS_PSYCOPG2:
                raise ImportError("DATABASE_URL is set but psycopg2 is not installed.")
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            conn = psycopg2.connect(db_url)
            return PostgresConnectionWrapper(conn)
        else:
            db_path = current_app.config.get("DATABASE") if current_app else "database/finance.db"
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn

    db = getattr(g, "_database", None)
    if db is None:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            if not HAS_PSYCOPG2:
                raise ImportError("DATABASE_URL is set but psycopg2 is not installed.")
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            conn = psycopg2.connect(db_url)
            db = g._database = PostgresConnectionWrapper(conn)
        else:
            db_path = current_app.config["DATABASE"]
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            db = g._database = conn
    return db


def query_db(query, args=(), one=False):
    """Executes a query and returns results."""
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv
