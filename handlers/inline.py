import html
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes, InlineQueryHandler
from database import SessionLocal, Bot
from uuid import uuid4

from sqlalchemy import or_, func

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return

    session = SessionLocal()
    
    try:
        # Try accent-insensitive
        # Postgres only
        results = session.query(Bot).filter(
            or_(
                func.unaccent(Bot.username).ilike(func.unaccent(f"%{query}%")),
                func.unaccent(Bot.description).ilike(func.unaccent(f"%{query}%")),
                func.unaccent(Bot.features).ilike(func.unaccent(f"%{query}%"))
            )
        ).limit(10).all()
    except Exception as e:
        session.rollback()
        # Fallback (or SQLite)
        results = session.query(Bot).filter(
             or_(
                Bot.username.ilike(f"%{query}%"),
                Bot.description.ilike(f"%{query}%"),
                Bot.features.ilike(f"%{query}%")
            )
        ).limit(10).all()
    
    inline_results = []
    for bot in results:
        safe_user = html.escape(bot.username)
        safe_desc = html.escape(bot.description)
        
        # Construct Channel Link
        import config
        post_link = f"https://t.me/{bot.username.replace('@', '')}"
        if bot.channel_message_id and config.CHANNEL_ID:
             clean_id = str(config.CHANNEL_ID).replace("-100", "")
             post_link = f"https://t.me/c/{clean_id}/{bot.channel_message_id}"

        inline_results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"🤖 {bot.username}",
                description=bot.description,
                input_message_content=InputTextMessageContent(
                    f"🔥 Check out <b>{safe_user}</b> on BotLibrary!\n\n"
                    f"📝 {safe_desc}\n"
                    f"⭐ Rating: {bot.rating}/5.0 ({bot.vote_count} votes)\n\n"
                    f"🔗 <a href='{post_link}'>View in Channel</a>",
                    parse_mode="HTML"
                ),
                url=post_link, # This makes the title clickable in the result list (on some clients)
                thumb_url="https://cdn-icons-png.flaticon.com/512/4712/4712035.png",
            )
        )
    
    session.close()
    await update.inline_query.answer(inline_results, cache_time=5)

inline_handler = InlineQueryHandler(inline_query)
