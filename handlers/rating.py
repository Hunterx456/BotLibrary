from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from database import SessionLocal, Bot
from handlers.utils import restricted
import config
import html

async def rate_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    # data format: rate_{bot_id}_{score}
    parts = query.data.split("_")
    bot_id = int(parts[1])
    score = int(parts[2])
    
    session = SessionLocal()
    bot = session.query(Bot).filter(Bot.bot_id == bot_id).first()
    
    if not bot:
        await query.answer("Bot not found!", show_alert=True)
        session.close()
        return
        
    # Check if user already voted (votes_data is a dictionary)
    votes = dict(bot.votes_data) if bot.votes_data else {}
    
    if str(user_id) in votes:
        previous_score = votes[str(user_id)]
        if previous_score == score:
            await query.answer(f"✅ You already rated {score} stars!", show_alert=False)
            session.close()
            return
        else:
            # Update vote
            votes[str(user_id)] = score
            context_text = f"✅ Rating updated to {score} stars!"
    else:
        # New vote
        votes[str(user_id)] = score
        context_text = f"✅ You rated {score} stars!"
        
    bot.votes_data = votes # Assign updated votes to bot object
    
    # Calculate new rating (average)
    # We should average the VALUES in votes_data
    
    total_score = sum(bot.votes_data.values())
    count = len(bot.votes_data)
    
    bot.rating = round(total_score / count, 1)
    bot.vote_count = count
    session.commit()
    
    # Update Channel Message
    # We need to preserve the message content but update the Rating line.
    
    # Using text_html gives us the current message in HTML.
    # But wait, 'text_html' might not exist in some library versions? It should in recent PTB.
    # If not, we can reconstruct it from DB since we have the bot data! This is SAFER.
    # Reconstructing is 100% safe against "Nested entity" errors because we control the format.
    
    safe_user = html.escape(bot.username)
    safe_desc = html.escape(bot.description)
    safe_feat = html.escape(bot.features)
    
    new_text = (
            f"<b>{safe_user}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>📖 Description</b>\n"
            f"{safe_desc}\n\n"
            f"<b>🚀 Features</b>\n"
            f"{safe_feat}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>📂 Category:</b> #{bot.category}\n"
            f"<b>⭐ Rating:</b> {bot.rating}/5.0 ({bot.vote_count} votes)\n"
            f"<b>👤 Submitter:</b> <a href=\"tg://user?id={bot.submitted_by}\">Profile</a>\n" 
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 <a href=\"https://t.me/{bot.username.replace('@', '')}\">Start Bot</a>"
    )

    try:
        await query.edit_message_text(new_text, reply_markup=query.message.reply_markup, parse_mode="HTML")
        await query.answer(context_text)
    except Exception as e:
        print(f"Rating update failed: {e}")
        await query.answer("⚠️ Failed to update rating display.", show_alert=True)
    
    session.close()

rating_handler = CallbackQueryHandler(rate_bot, pattern="^rate_")
