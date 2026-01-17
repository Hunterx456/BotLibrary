import html
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes, InlineQueryHandler
from database import SessionLocal, Bot
from uuid import uuid4

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return

    session = SessionLocal()
    # ILIKE is Postgres, for sqlite use standard like
    if "sqlite" in str(session.bind.url):
        results = session.query(Bot).filter(Bot.username.contains(query) | Bot.description.contains(query)).limit(10).all()
    else:
        results = session.query(Bot).filter(Bot.username.ilike(f"%{query}%") | Bot.description.ilike(f"%{query}%")).limit(10).all()
    
    inline_results = []
    for bot in results:
        safe_user = html.escape(bot.username)
        safe_desc = html.escape(bot.description)
        
        inline_results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"🤖 {bot.username}",
                description=bot.description,
                input_message_content=InputTextMessageContent(
                    f"🔥 Check out <b>{safe_user}</b> on BotLibrary!\n\n"
                    f"📝 {safe_desc}\n"
                    f"⭐ Rating: {bot.rating}/5.0 ({bot.vote_count} votes)",
                    parse_mode="HTML"
                ),
                thumb_url="https://cdn-icons-png.flaticon.com/512/4712/4712035.png", # Placeholder
            )
        )
    
    session.close()
    await update.inline_query.answer(inline_results, cache_time=5)

inline_handler = InlineQueryHandler(inline_query)
