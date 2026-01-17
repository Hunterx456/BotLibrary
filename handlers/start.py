from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database import SessionLocal, User, Bot

import html

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Add user to DB if new
    session = SessionLocal()
    db_user = session.query(User).filter(User.user_id == user.id).first()
    if not db_user:
        new_user = User(user_id=user.id, username=user.username)
        session.add(new_user)
        session.commit()
    session.close()

    # Deep Linking
    if context.args and context.args[0].startswith("bot_"):
        pass 
    
    # Check 'html' import availability or standardlib
    safe_name = html.escape(user.first_name)
    text = (
        f"Welcome to <b>BotLibrary</b>, {safe_name}! 🤖\n\n"
        "I am a community-driven bot directory. You can discover amazing bots or submit your own!\n\n"
        "Would you like to add a bot to our library?"
    )
    
    keyboard = [
        [InlineKeyboardButton("➕ Add a Bot", callback_data="add_bot")],
        [InlineKeyboardButton("🔍 Browse Library", callback_data="browse_bots")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        help_text = (
            "🤖 <b>BotLibrary Help</b>\n\n"
            "<b>For Users:</b>\n"
            "/add - Submit a new bot\n"
            "/browse - Browse categories\n"
            "/search &lt;query&gt; - Search for bots\n\n"
            "<b>For Staff:</b>\n"
            "/pending - View pending submissions\n"
            "/stats - View statistics"
        )
        await query.edit_message_text(help_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="start_back")]]))

    elif query.data == "start_back":
        # Re-show start menu
        await start(update, context)

    elif query.data == "browse_bots":
        keyboard = [
            [InlineKeyboardButton("🏆 Top Rated", callback_data="browse_top")],
            [InlineKeyboardButton("📂 Categories", callback_data="browse_cats")],
            [InlineKeyboardButton("🔙 Back", callback_data="start_back")]
        ]
        await query.edit_message_text("🔍 <b>Browse Library</b>\nSelect a filter:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif query.data == "browse_top":
        session = SessionLocal()
        bots = session.query(Bot).order_by(Bot.rating.desc()).limit(10).all()
        session.close()
        
        if not bots:
            await query.edit_message_text("No bots found!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="browse_bots")]]))
            return
            
        text = "🏆 <b>Top Rated Bots</b>\n\n"
        for b in bots:
            safe_user = html.escape(b.username)
            text += f"• {safe_user} - ⭐ {b.rating} ({b.vote_count})\n"
            
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="browse_bots")]]), parse_mode="HTML")

    elif query.data == "browse_cats":
        categories = ["Utility", "Entertainment", "Productivity", "Social", "Gaming", "Other"]
        keyboard = []
        row = []
        for cat in categories:
            row.append(InlineKeyboardButton(cat, callback_data=f"list_cat_{cat}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row: keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="browse_bots")])
        
        await query.edit_message_text("📂 <b>Select Category</b>:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

    elif query.data.startswith("list_cat_"):
        cat = query.data.replace("list_cat_", "")
        session = SessionLocal()
        bots = session.query(Bot).filter(Bot.category == cat).order_by(Bot.rating.desc()).limit(15).all()
        session.close()
        
        if not bots:
            text = f"📂 Category: <b>{cat}</b>\n\nNo bots found."
        else:
            text = f"📂 Category: <b>{cat}</b>\n\n"
            for b in bots:
                safe_user = html.escape(b.username)
                text += f"• {safe_user}\n"
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="browse_cats")]]), parse_mode="HTML")

start_handler = CommandHandler("start", start)
help_handler = CommandHandler("help", lambda u,c: u.message.reply_text("Use /start to access the menu."))
# Note: "add_bot" callback is handled in the ConversationHandler entry point
