from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, MessageHandler, 
    filters, CallbackQueryHandler
)
from database import SessionLocal, BotSubmission, Bot
import datetime

import html

# Stages
NAME, DESC, FEATURES, CATEGORY, CONFIRM = range(5)

async def start_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for /add or 'Add a Bot' button."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text("🤖 Please enter the <b>Bot Username</b> (e.g., @example_bot):", parse_mode="HTML")
    else:
        await update.message.reply_text("🤖 Please enter the <b>Bot Username</b> (e.g., @example_bot):", parse_mode="HTML")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.startswith("@"):
        await update.message.reply_text("⚠️ Username must start with '@'. Please try again:")
        return NAME
    
    # Check duplicates
    session = SessionLocal()
    if session.query(Bot).filter(Bot.username == text).first():
        await update.message.reply_text("⚠️ This bot is already in our library!")
        session.close()
        return ConversationHandler.END
        
    if session.query(BotSubmission).filter(BotSubmission.bot_username == text, BotSubmission.status == "pending").first():
        await update.message.reply_text("⚠️ This bot is already submitted and pending review.")
        session.close()
        return ConversationHandler.END
    session.close()
    
    context.user_data['bot_username'] = text
    await update.message.reply_text("📝 <b>Description</b>:\nProvide a brief description of your bot:", parse_mode="HTML")
    return DESC

async def get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['bot_desc'] = update.message.text
    await update.message.reply_text("⚙️ <b>Features</b>:\nList the main features of your bot:", parse_mode="HTML")
    return FEATURES

async def get_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['bot_features'] = update.message.text
    
    categories = ["Utility", "Entertainment", "Productivity", "Social", "Gaming", "Other"]
    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in categories
    ]
    await update.message.reply_text("🏷️ Select a <b>Category</b>:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return CATEGORY

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("cat_", "")
    context.user_data['bot_category'] = category
    
    # Confirmation
    data = context.user_data
    # Escape user content!
    safe_user = html.escape(data['bot_username'])
    safe_desc = html.escape(data['bot_desc'])
    safe_feat = html.escape(data['bot_features'])
    
    text = (
        "📋 <b>Submission Confirmation</b>\n\n"
        f"🤖 <b>Bot</b>: {safe_user}\n"
        f"📝 <b>Desc</b>: {safe_desc}\n"
        f"⚙️ <b>Features</b>: {safe_feat}\n"
        f"🏷️ <b>Category</b>: {data['bot_category']}\n\n"
        "Submit this request?"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Submit", callback_data="submit_yes"),
         InlineKeyboardButton("❌ Cancel", callback_data="submit_no")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return CONFIRM

async def submit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "submit_no":
        await query.edit_message_text("❌ Submission cancelled.")
        return ConversationHandler.END
        
    # Save to DB
    data = context.user_data
    session = SessionLocal()
    submission = BotSubmission(
        bot_username=data['bot_username'],
        description=data['bot_desc'],
        features=data['bot_features'],
        category=data['bot_category'],
        submitted_by=update.effective_user.id,
        status="pending"
    )
    session.add(submission)
    session.commit()
    submission_id = submission.id
    session.close() # Close session
    
    await query.edit_message_text("✅ <b>Submitted!</b> Your bot is now under review.", parse_mode="HTML")
    
    # Trigger notification
    from handlers.moderation import notify_new_submission
    context.application.create_task(notify_new_submission(context, submission_id))
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 Operation cancelled.")
    return ConversationHandler.END

submission_handler = ConversationHandler(
    entry_points=[CommandHandler("add", start_submission), CallbackQueryHandler(start_submission, pattern="^add_bot$")],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
        DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_desc)],
        FEATURES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_features)],
        CATEGORY: [CallbackQueryHandler(get_category, pattern="^cat_")],
        CONFIRM: [CallbackQueryHandler(submit_confirm, pattern="^submit_")]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False # Explicitly set to silence warning, as this is user-based conversation
)
