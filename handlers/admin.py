from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from database import SessionLocal, User, Bot, BotSubmission
from handlers.utils import restricted
import config
import html

@restricted
async def add_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.OWNER_ID:
        await update.message.reply_text("⛔ Only the Owner can add Sudo users.")
        return

    try:
        user_id = int(context.args[0])
        config.SUDO_USERS.add(user_id) # Runtime update
        # DB update
        session = SessionLocal()
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.role = "sudo"
        else:
            # If user not in DB, create placeholder? Or assume they exist?
            # Better to create if not exists
            user = User(user_id=user_id, role="sudo")
            session.add(user)
        session.commit()
        session.close()
        
        await update.message.reply_text(f"✅ User {user_id} promoted to SUDO.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /addsudo <user_id>")

@restricted
async def add_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Sudos and Owner can add mods
    try:
        user_id = int(context.args[0])
        session = SessionLocal()
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.role = "mod"
        else:
            user = User(user_id=user_id, role="mod")
            session.add(user)
        session.commit()
        session.close()
        
        await update.message.reply_text(f"✅ User {user_id} promoted to MODERATOR.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /addmod <user_id>")

@restricted
async def remove_sudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.OWNER_ID:
        await update.message.reply_text("⛔ Only the Owner can remove Sudo users.")
        return

    try:
        user_id = int(context.args[0])
        if user_id in config.SUDO_USERS:
             config.SUDO_USERS.remove(user_id)
        
        session = SessionLocal()
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.role = "user"
            session.commit()
            await update.message.reply_text(f"✅ User {user_id} removed from SUDO.")
        else:
            await update.message.reply_text("⚠️ User not found in DB.")
        session.close()
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /removesudo <user_id>")

@restricted
async def remove_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(context.args[0])
        session = SessionLocal()
        user = session.query(User).filter(User.user_id == user_id).first()
        if user and user.role == "mod":
            user.role = "user"
            session.commit()
            await update.message.reply_text(f"✅ User {user_id} removed from MODERATOR.")
        else:
             await update.message.reply_text("⚠️ User not found or not a mod.")
        session.close()
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /removemod <user_id>")

@restricted
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
        
    message = " ".join(context.args)
    # We allow the admin to send Markdown or HTML? Let's assume HTML for safety or just raw text.
    # If admin wants format, they should use it. But for broadcast, usually safest is to just copy text.
    # Let's trust admin input but use HTML for the "ANNOUNCEMENT" header.
    
    session = SessionLocal()
    users = session.query(User).all()
    count = 0
    for user in users:
        try:
            # Using HTML for consistency
            await context.bot.send_message(chat_id=user.user_id, text=f"📢 <b>ANNOUNCEMENT</b>\n\n{html.escape(message)}", parse_mode="HTML")
            count += 1
        except:
            pass # Blocked or deleted
    session.close()
    await update.message.reply_text(f"✅ Broadcast sent to {count} users.")

@restricted
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    total_users = session.query(User).count()
    total_bots = session.query(Bot).count()
    pending_subs = session.query(BotSubmission).filter(BotSubmission.status == "pending").count()
    
    # Category breakdown
    from sqlalchemy import func
    categories = session.query(Bot.category, func.count(Bot.bot_id)).group_by(Bot.category).all()
    cat_text = "\n".join([f"• {c[0]}: {c[1]}" for c in categories])
    
    session.close()
    
    text = (
        "📊 <b>System Statistics</b>\n\n"
        f"👥 Total Users: {total_users}\n"
        f"🤖 Approved Bots: {total_bots}\n"
        f"⏳ Pending Reviews: {pending_subs}\n\n"
        "📂 <b>Categories</b>:\n"
        f"{cat_text}"
    )
    await update.message.reply_text(text, parse_mode="HTML")
    
@restricted
async def delete_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /deletebot <username>")
        return

    username = context.args[0]
    if not username.startswith("@"):
        username = "@" + username

    session = SessionLocal()
    # Find the bot
    bot = session.query(Bot).filter(Bot.username == username).first()
    
    if not bot:
        await update.message.reply_text(f"❌ Bot {username} not found in library.")
        session.close()
        return

    try:
        # 1. Delete Channel Post
        if bot.channel_message_id and config.CHANNEL_ID:
            try:
                await context.bot.delete_message(chat_id=config.CHANNEL_ID, message_id=bot.channel_message_id)
                await update.message.reply_text("✅ Channel post deleted.")
            except Exception as e:
                await update.message.reply_text(f"⚠️ Could not delete channel post: {e}")

        # 2. Delete from DB (Bot and Submission)
        # Note: We should probably delete the submission or mark it deleted?
        # User said "everything is deleted".
        
        # Check for related submission
        sub = session.query(BotSubmission).filter(BotSubmission.id == bot.submission_id).first()
        if sub:
            session.delete(sub)
        
        session.delete(bot)
        session.commit()
        
        await update.message.reply_text(f"✅ Bot {username} has been completely removed from the database.")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error during deletion: {e}")
        
    session.close()

add_sudo_handler = CommandHandler("addsudo", add_sudo)
rem_sudo_handler = CommandHandler("removesudo", remove_sudo)
add_mod_handler = CommandHandler("addmod", add_mod)
rem_mod_handler = CommandHandler("removemod", remove_mod)
broadcast_handler = CommandHandler("broadcast", broadcast)
stats_handler = CommandHandler("stats", stats)
delete_bot_handler = CommandHandler("deletebot", delete_bot)
