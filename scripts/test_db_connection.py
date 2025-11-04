# scripts/test_db_connection.py
import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

conn_info = {
    "host": os.getenv("DB_HOST","localhost"),
    "port": os.getenv("DB_PORT","5432"),
    "dbname": os.getenv("DB_NAME","swarm_main"),
    "user": os.getenv("DB_USER","swarm_user"),
    "password": os.getenv("DB_PASSWORD","swarm_pass")
}

try:
    with psycopg.connect(**conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            print("Connected to:", cur.fetchone()[0])
except Exception as e:
    print("Connection failed:", e)