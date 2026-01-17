from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from database import SessionLocal, Bot
from sqlalchemy import or_
import html

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = " ".join(context.args)
    if not query_text:
        await update.message.reply_text("🔍 Usage: /search <bot name or description>")
        return

    session = SessionLocal()
    # Basic search: match username or description containing the query (case insensitive)
    # For "percentage matching", complex fuzzy search is hard in standard SQL without extensions.
    # We will use ILIKE/contains and then sort by Rating (Topic 5 rated as requested).
    
    # search_term = f"%{query_text}%"
    # standard SQL 'ilike' equivalent in SQLAlchemy is .ilike()
    
    results = session.query(Bot).filter(
        or_(
            Bot.username.ilike(f"%{query_text}%"),
            Bot.description.ilike(f"%{query_text}%"),
            Bot.features.ilike(f"%{query_text}%")
        )
    ).order_by(Bot.rating.desc()).limit(5).all()
    
    session.close()
    
    if not results:
        await update.message.reply_text(f"❌ No bots found matching '<b>{html.escape(query_text)}</b>'.", parse_mode="HTML")
        return
        
    # Format output
    text = f"🔍 <b>Top matches for '{html.escape(query_text)}':</b>\n\n"
    keyboard = []
    
    for bot in results:
        safe_name = html.escape(bot.username)
        # safe_desc = html.escape(bot.description[:50]) + "..." if len(bot.description) > 50 else html.escape(bot.description)
        
        text += f"🤖 <b>{safe_name}</b>\n⭐ {bot.rating}/5.0 ({bot.vote_count} votes)\n\n"
        
        # Inline Link Button
        # User requested "inline link button". 
        # We can put them all in one keyboard.
        link = f"https://t.me/{bot.username.replace('@', '')}"
        keyboard.append([InlineKeyboardButton(f"🔗 {safe_name} ({bot.rating}⭐)", url=link)])
        
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

search_handler = CommandHandler("search", search_command)
