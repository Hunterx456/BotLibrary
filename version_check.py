import sqlalchemy
import telegram
try:
    print(f"SQLAlchemy: {sqlalchemy.__version__}")
except:
    print("SQLAlchemy logic broken checking version")

try:
    print(f"PTB: {telegram.__version__}")
except:
    print("PTB logic broken checking version")
