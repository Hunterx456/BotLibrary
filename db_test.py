import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DB_URL").replace("postgresql+psycopg2://", "postgres://")

print(f"Testing URL: {url.split('@')[1] if '@' in url else 'INVALID'}")

try:
    conn = psycopg2.connect(url, sslmode="require")
    print("Connected successfully!")
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print(cur.fetchone())
    conn.close()
except Exception as e:
    print("Connection failed:")
    print(e)
