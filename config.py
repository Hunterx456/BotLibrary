import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "5667016949"))
# Channel to post approved bots to
CHANNEL_ID = os.getenv("CHANNEL_ID") 
# Support multiple admins/sudos if needed, parsing comma-separated list
SUDO_USERS = set(int(x) for x in os.getenv("SUDO_USERS", "").split(",") if x)
SUDO_USERS.add(OWNER_ID)

DB_URL = os.getenv("DB_URL", "sqlite:///botlibrary.db")
