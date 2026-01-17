import logging
import config
from database import init_db
from telegram.ext import ApplicationBuilder

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Initialize Database
    print("Initializing Database...")
    init_db()
    
    # Build Application
    if not config.BOT_TOKEN:
        print("Error: BOT_TOKEN is not set in config.py or environment variables.")
        return

    print("Starting Bot...")
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()
    
    # Register Handlers
    from handlers.start import start_handler, button_handler, help_handler
    from handlers.submission import submission_handler
    from handlers.moderation import moderation_handler
    from handlers.rating import rating_handler
    from handlers.admin import (
        add_sudo_handler, rem_sudo_handler, 
        add_mod_handler, rem_mod_handler, 
        broadcast_handler, stats_handler,
        delete_bot_handler
    )
    from telegram.ext import CallbackQueryHandler
    
    app.add_handler(submission_handler) # High priority for conversation
    app.add_handler(start_handler)
    app.add_handler(help_handler)
    app.add_handler(moderation_handler)
    app.add_handler(rating_handler)
    
    # Admin
    app.add_handler(add_sudo_handler)
    app.add_handler(rem_sudo_handler)
    app.add_handler(add_mod_handler)
    app.add_handler(rem_mod_handler)
    app.add_handler(broadcast_handler)
    app.add_handler(stats_handler)
    app.add_handler(delete_bot_handler)
    
    app.add_handler(CallbackQueryHandler(button_handler)) # Catch-all for other buttons like 'help'
    
    # Extras
    from handlers.inline import inline_handler
    app.add_handler(inline_handler)
    
    # --- Keep Alive for Render ---
    from flask import Flask
    import threading
    import os
    
    flask_app = Flask(__name__)
    
    @flask_app.route('/')
    def health_check():
        return "Bot is Alive!", 200
        
    def run_flask():
        port = int(os.environ.get("PORT", 8080))
        flask_app.run(host='0.0.0.0', port=port)
        
    # Start server in background thread
    threading.Thread(target=run_flask, daemon=True).start()
    print("Web server started for UptimeRobot...")
    # -----------------------------
    
    print("Bot is polling...")
    app.run_polling()

if __name__ == '__main__':
    main()
