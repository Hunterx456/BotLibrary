from sqlalchemy import create_engine, text
import config

def enable_unaccent():
    engine = create_engine(config.DB_URL)
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))
            conn.commit()
            print("✅ 'unaccent' extension enabled successfully.")
        except Exception as e:
            print(f"❌ Failed to enable 'unaccent': {e}")
            print("You might need Superuser privileges. If so, contact your DB provider (Neon usually allows this).")

if __name__ == "__main__":
    enable_unaccent()
