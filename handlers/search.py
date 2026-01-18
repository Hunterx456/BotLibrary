from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from database import SessionLocal, Bot
from sqlalchemy import or_, func
import html

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = " ".join(context.args)
    if not query_text:
        await update.message.reply_text("🔍 Usage: /search <bot name or description>")
        return

    session = SessionLocal()
    # Use unaccent() to ignore accents (e.g. pokemon matches Pokémon)
    # unaccent(column).ilike('%query%') isn't enough if query has no accent but column does.
    # We should unaccent both sides: unaccent(column) ILIKE unaccent('%query%')
    
    # Try Accent-Insensitive Search (Postgres with unaccent)
    try:
        results = session.query(Bot).filter(
            or_(
                func.unaccent(Bot.username).ilike(func.unaccent(f"%{query_text}%")),
                func.unaccent(Bot.description).ilike(func.unaccent(f"%{query_text}%")),
                func.unaccent(Bot.features).ilike(func.unaccent(f"%{query_text}%"))
            )
        ).order_by(Bot.rating.desc()).limit(5).all()
    except Exception as e:
        print(f"Unaccent search failed (falling back to simple search): {e}")
        session.rollback()
        # Fallback to standard ILIKE (Case-insensitive but accent-sensitive)
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
import config

        # Link to channel post if available
        # Default: Bot Link
        link = f"https://t.me/{bot.username.replace('@', '')}"
        
        if bot.channel_message_id and config.CHANNEL_ID:
             clean_id = str(config.CHANNEL_ID).replace("-100", "")
             # Using private link format which works for members (public too if they are members)
             link = f"https://t.me/c/{clean_id}/{bot.channel_message_id}"
             
        keyboard.append([InlineKeyboardButton(f"🔗 {safe_name} ({bot.rating}⭐)", url=link)])
        
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

search_handler = CommandHandler("search", search_command)
