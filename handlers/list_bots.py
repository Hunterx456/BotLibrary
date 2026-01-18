from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database import SessionLocal, Bot
import math
import html
import config

BOTS_PER_PAGE = 15

async def list_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check current page
    query = update.callback_query
    page = 0
    
    if query:
        await query.answer()
        data = query.data
        if data.startswith("list_page_"):
            page = int(data.split("_")[2])
    
    session = SessionLocal()
    total_bots = session.query(Bot).count()
    total_pages = math.ceil(total_bots / BOTS_PER_PAGE)
    
    offset = page * BOTS_PER_PAGE
    bots = session.query(Bot).order_by(Bot.rating.desc()).offset(offset).limit(BOTS_PER_PAGE).all()
    session.close()
    
    if not bots:
        text = "📂 <b>Bot Library</b>\n\nNo bots found."
        await send_list_response(update, text, None)
        return

    text = f"📂 <b>Bot Library</b> (Page {page + 1}/{total_pages})\n\n"
    
    for i, bot in enumerate(bots):
        safe_name = html.escape(bot.username)
        # Link to channel post if available (Construction logic similar to search)
        link = f"https://t.me/{bot.username.replace('@', '')}"
        
        if bot.channel_message_id and config.CHANNEL_ID:
            clean_id = str(config.CHANNEL_ID).replace("-100", "")
            # Using private link format which works for members
            link = f"https://t.me/c/{clean_id}/{bot.channel_message_id}"

        text += f"{offset + i + 1}. <a href='{link}'>{safe_name}</a> - ⭐ {bot.rating}\n"

    # Pagination Buttons
    keyboard = []
    nav_row = []
    
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"list_page_{page - 1}"))
    
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"list_page_{page + 1}"))
        
    if nav_row:
        keyboard.append(nav_row)
        
    # Standard "Back to Menu" doesn't exist for a standalone command but we can add one if user came from menu
    # For now just simple navigation
    
    await send_list_response(update, text, InlineKeyboardMarkup(keyboard))

async def send_list_response(update, text, reply_markup):
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML", disable_web_page_preview=True)

list_handler = CommandHandler("list", list_bots)
list_callback_handler = CallbackQueryHandler(list_bots, pattern="^list_page_")
