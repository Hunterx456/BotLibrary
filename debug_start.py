import sys
print("Starting debug...")
try:
    import sqlalchemy
    print(f"SQLAlchemy: {sqlalchemy.__version__}")
    from telegram.ext import ApplicationBuilder
    print("PTB Imported")
    import config
    print("Config Imported")
    from database import init_db
    print("DB Init Function Imported")
    init_db()
    print("DB Initialized")
except Exception as e:
    import traceback
    traceback.print_exc()
