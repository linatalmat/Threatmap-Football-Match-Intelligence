import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
db = os.getenv("POSTGRES_DB")
port = os.getenv("POSTGRES_PORT", "5432")

engine = create_engine(f"postgresql+psycopg2://{user}:{password}@127.0.0.1:{port}/{db}")

try:
    with engine.connect() as conn:
        print(conn.execute(text("SELECT version();")).scalar())
except UnicodeDecodeError as e:
    print("Vraie erreur :", e.object.decode("cp1252", errors="replace"))