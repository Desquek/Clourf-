import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db():
    conn = psycopg2.connect(
        os.environ.get("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )
    return conn