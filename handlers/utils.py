from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import config

def restricted(func):
    """Restrict usage of func to allowed users only (Sudos/Owner)."""
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in config.SUDO_USERS:
            await update.message.reply_text("⛔ You are not authorized to use this command.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def is_admin(user_id: int) -> bool:
    return user_id in config.SUDO_USERS
