from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, CallbackQueryHandler
from database import SessionLocal, BotSubmission, Bot, User
from handlers.utils import is_admin
import config
import datetime
import html

# --- Notifications ---

async def notify_new_submission(context: ContextTypes.DEFAULT_TYPE, submission_id: int):
    """Sends a notification to all sudo users/mods about a new submission."""
    session = SessionLocal()
    sub = session.query(BotSubmission).filter(BotSubmission.id == submission_id).first()
    if not sub:
        session.close()
        return

    safe_user = html.escape(sub.bot_username)
    safe_desc = html.escape(sub.description)
    safe_feat = html.escape(sub.features)

    text = (
        "🆕 <b>NEW BOT SUBMISSION</b>\n\n"
        f"👤 Submitted by: {sub.submitted_by}\n" # improved to show link in future
        f"🤖 Bot: {safe_user}\n\n"
        f"📝 Desc: {safe_desc}\n"
        f"⚙️ Features: {safe_feat}\n"
        f"🏷️ Category: {sub.category}\n\n"
        "Status: ⏳ Awaiting Review"
    )
    
    keyboard = [[InlineKeyboardButton("I Will Check ✋", callback_data=f"mod_claim_{submission_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    for admin_id in config.SUDO_USERS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception as e:
            print(f"Failed to send mod notification to {admin_id}: {e}")
            
    session.close()

# --- Handlers ---

async def mod_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    if not is_admin(user_id):
        await query.answer("⛔ You are not part of the moderation team.", show_alert=True)
        return

    session = SessionLocal()
    
    if data.startswith("mod_claim_"):
        sub_id = int(data.split("_")[2])
        sub = session.query(BotSubmission).filter(BotSubmission.id == sub_id).first()
        
        if sub.claimed_by and sub.claimed_by != user_id:
            await query.answer("⚠️ Already claimed by another mod!", show_alert=True)
            session.close()
            return

        # Update DB
        sub.claimed_by = user_id
        sub.claim_time = datetime.datetime.utcnow()
        session.commit()
        
        # Update Message
        # Note: message.text_html might not be available, need to reconstruct or be careful.
        # It's better to just Append the status line.
        
        # Simple reconstruction for safety:
        safe_user = html.escape(sub.bot_username)
        
        new_text = (
            f"🆕 <b>NEW BOT SUBMISSION</b>\n"
            f"🤖 Bot: {safe_user}\n"
            f"Status: 👨💼 <b>Being reviewed by</b>: @{query.from_user.username}"
        )
        # Assuming original details are visible? Actually `edit_message_text` replaces everything.
        # Let's keep the full text if possible. Since we can't easily get the HTML from the message object reliably (only text), 
        # we might just show a shorter version or re-fetch details.
        # Re-fetching details:
        safe_desc = html.escape(sub.description)
        new_text = (
             "🆕 <b>NEW BOT SUBMISSION</b>\n"
             f"🤖 Bot: {safe_user}\n"
             f"📝 Desc: {safe_desc}\n"
             f"Status: 👨💼 <b>Being reviewed by</b>: @{query.from_user.username}"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Approve", callback_data=f"mod_approve_{sub_id}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"mod_reject_{sub_id}")],
            [InlineKeyboardButton("🔙 Unclaim", callback_data=f"mod_unclaim_{sub_id}")]
        ]
        
        await query.edit_message_text(new_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        await query.answer("✅ You claimed this submission.")
        
    elif data.startswith("mod_unclaim_"):
        sub_id = int(data.split("_")[2])
        sub = session.query(BotSubmission).filter(BotSubmission.id == sub_id).first()
        
        if sub.claimed_by != user_id:
             await query.answer("⚠️ You didn't claim this.", show_alert=True)
             session.close()
             return

        sub.claimed_by = None
        session.commit()
        
        safe_user = html.escape(sub.bot_username)
        # Revert message
        text = (
            "🆕 <b>NEW BOT SUBMISSION</b>\n"
            f"🤖 Bot: {safe_user}\n"
            "Status: ⏳ Awaiting Review"
        )
        keyboard = [[InlineKeyboardButton("I Will Check ✋", callback_data=f"mod_claim_{sub_id}")]]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        await query.answer("Unclaimed.")

    elif data.startswith("mod_approve_"):
        sub_id = int(data.split("_")[2])
        sub = session.query(BotSubmission).filter(BotSubmission.id == sub_id).first()
        
        # 1. Update Submission Status
        sub.status = "approved"
        sub.approved_by = user_id # Logic to track who approved
        
        # 2. Add to actual Bots table
        new_bot = Bot(
            submission_id=sub.id,
            username=sub.bot_username,
            description=sub.description,
            features=sub.features,
            category=sub.category,
            submitted_by=sub.submitted_by,
            approved_by=user_id,
            submission_date=sub.submission_date
        )
        session.add(new_bot)
        session.commit()
        
        safe_user = html.escape(sub.bot_username)
        safe_desc = html.escape(sub.description)
        safe_feat = html.escape(sub.features)
        
        # 3. Post to Channel
        channel_text = (
            f"<b>{safe_user}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>📖 Description</b>\n"
            f"{safe_desc}\n\n"
            f"<b>🚀 Features</b>\n"
            f"{safe_feat}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>📂 Category:</b> #{sub.category}\n"
            f"<b>⭐ Rating:</b> 0.0/5.0 (0 votes)\n"
            f"<b>👤 Submitter:</b> <a href=\"tg://user?id={sub.submitted_by}\">Profile</a>\n" 
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 <a href=\"https://t.me/{sub.bot_username.replace('@', '')}\">Start Bot</a>"
        )
        rating_keyboard = [
            [InlineKeyboardButton("⭐ 1", callback_data=f"rate_{new_bot.bot_id}_1"),
             InlineKeyboardButton("⭐ 2", callback_data=f"rate_{new_bot.bot_id}_2"),
             InlineKeyboardButton("⭐ 3", callback_data=f"rate_{new_bot.bot_id}_3")],
            [InlineKeyboardButton("⭐ 4", callback_data=f"rate_{new_bot.bot_id}_4"),
             InlineKeyboardButton("⭐ 5", callback_data=f"rate_{new_bot.bot_id}_5")]
        ]
        
        if config.CHANNEL_ID:
            try:
                msg = await context.bot.send_message(
                    chat_id=config.CHANNEL_ID, 
                    text=channel_text, 
                    reply_markup=InlineKeyboardMarkup(rating_keyboard),
                    parse_mode="HTML"
                )
                new_bot.channel_message_id = msg.message_id
                session.commit()
            except Exception as e:
                print(f"Channel post failed: {e}")
                await query.message.reply_text(f"⚠️ Approved but failed to post to channel: {e}")

        # 4. Notify User
        try:
            await context.bot.send_message(chat_id=sub.submitted_by, text=f"🎉 Congratulations! Your bot {sub.bot_username} has been approved!")
        except:
            pass # User might have blocked bot
            
        await query.edit_message_text(f"✅ Approved by {query.from_user.username}")
        
    elif data.startswith("mod_reject_"):
        # Format: mod_reject_{sub_id} OR mod_reject_{sub_id}_{reason_code}
        parts = data.split("_")
        sub_id = int(parts[2])
        
        if len(parts) == 3:
            # Step 1: Show reasons
            keyboard = [
                [InlineKeyboardButton("Spam 🗑️", callback_data=f"mod_reject_{sub_id}_spam")],
                [InlineKeyboardButton("Offline 🔌", callback_data=f"mod_reject_{sub_id}_offline")],
                [InlineKeyboardButton("Insufficient Desc 📝", callback_data=f"mod_reject_{sub_id}_desc")],
                [InlineKeyboardButton("Duplicate 📑", callback_data=f"mod_reject_{sub_id}_duplicate")],
                [InlineKeyboardButton("Other (Generic) ❌", callback_data=f"mod_reject_{sub_id}_other")],
                [InlineKeyboardButton("🔙 Back", callback_data=f"mod_claim_{sub_id}")] # Reverts to claim view (which is 'Being reviewed by...')
            ]
            await query.edit_message_text("❓ <b>Select Rejection Reason</b>:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
            session.close()
            return
            
        # Step 2: Process Rejection
        reason_code = parts[3]
        reason_map = {
            "spam": "Identified as spam or malicious.",
            "offline": "Bot appears to be offline or unresponsive.",
            "desc": "Description or features provided are insufficient.",
            "duplicate": "This bot is already in our library.",
            "other": "Does not meet our quality standards."
        }
        reason_text = reason_map.get(reason_code, "Configuration mismatch.")
        
        sub = session.query(BotSubmission).filter(BotSubmission.id == sub_id).first()
        sub.status = "rejected"
        sub.rejection_reason = reason_text
        session.commit()
        
        # Notify User
        try:
            await context.bot.send_message(
                chat_id=sub.submitted_by, 
                text=f"❌ <b>Submission Rejected</b>\n\nYour bot {sub.bot_username} was not approved.\n<b>Reason</b>: {reason_text}",
                parse_mode="HTML"
            )
        except:
            pass
            
        await query.edit_message_text(f"❌ Rejected by {query.from_user.username}\nReason: {reason_code}")
        
    session.close()

moderation_handler = CallbackQueryHandler(mod_actions, pattern="^mod_")
