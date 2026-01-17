from sqlalchemy import create_engine, text
import config

engine = create_engine(config.DB_URL.replace("sqlite:///", "postgresql+psycopg2://")\
                       if "sqlite" not in config.DB_URL else config.DB_URL)

def run_migration():
    if "sqlite" in config.DB_URL:
        print("Using SQLite, schemas don't enforce integer size strictly in the same way, but recreation is safer.")
        # For simplicity in dev: drop all and recreate (Data loss acceptable as per dev stage)
        # Or just let it run if SQLite accepts big ints (which it does dynamically).
        # But for Production Postgres, we MUST alter.
        pass
    else:
        print("Running Postgres ALTER scripts...")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ALTER COLUMN user_id TYPE BIGINT;"))
            conn.execute(text("ALTER TABLE bots ALTER COLUMN submitted_by TYPE BIGINT;"))
            conn.execute(text("ALTER TABLE bots ALTER COLUMN approved_by TYPE BIGINT;"))
            conn.execute(text("ALTER TABLE submissions ALTER COLUMN submitted_by TYPE BIGINT;"))
            conn.execute(text("ALTER TABLE submissions ALTER COLUMN claimed_by TYPE BIGINT;"))
            conn.commit()
            print("Migration done.")

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"Migration failed (might be already done or table empty): {e}")
