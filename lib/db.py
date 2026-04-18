import os
from contextlib import contextmanager
import psycopg

POSTGRES_URL = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")


@contextmanager
def connect():
    if not POSTGRES_URL:
        raise RuntimeError("POSTGRES_URL not set")
    conn = psycopg.connect(POSTGRES_URL, autocommit=False)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
