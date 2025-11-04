# scripts/load_data.py
import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import sqlalchemy
from sqlalchemy import text

# Resolve project root and script-relative paths
HERE = Path(__file__).resolve().parent       # .../SwarmDB/scripts
PROJECT_ROOT = HERE.parent                   # .../SwarmDB
SCHEMA_SQL_PATH = PROJECT_ROOT / "scripts" / "schema.sql"
CSV_PATH = PROJECT_ROOT / "data" / "reviews.csv"

load_dotenv(PROJECT_ROOT / ".env")

DB_USER = os.getenv("DB_USER", "swarm_user")
DB_PASS = os.getenv("DB_PASSWORD", "swarm_pass")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "swarm_main")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def create_schema(engine):
    if not SCHEMA_SQL_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_SQL_PATH}")
    with engine.begin() as conn:
        sql = SCHEMA_SQL_PATH.read_text()
        conn.execute(text(sql))
    print("Schema created/verified.")

def load_reviews_csv(engine, csv_path=CSV_PATH):
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found at {csv_path}")
    df = pd.read_csv(csv_path, dtype=str)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['rating'] = df['rating'].astype(int)
    with engine.begin() as conn:
        df.to_sql("tmp_reviews", con=engine, if_exists="replace", index=False)
        conn.execute(text("""
        INSERT INTO reviews (id, created_at, user_id, region, rating, text)
        SELECT id, created_at, user_id, region, rating, text FROM tmp_reviews
        ON CONFLICT (id) DO UPDATE
        SET created_at = EXCLUDED.created_at,
            user_id = EXCLUDED.user_id,
            region = EXCLUDED.region,
            rating = EXCLUDED.rating,
            text = EXCLUDED.text;
        DROP TABLE IF EXISTS tmp_reviews;
        """))
    print("Loaded reviews from", csv_path)

if __name__ == "__main__":
    engine = sqlalchemy.create_engine(DATABASE_URL, future=True)
    create_schema(engine)
    load_reviews_csv(engine)
    print("Done.")