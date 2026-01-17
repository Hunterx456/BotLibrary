# 🤖 BotLibrary

A community-driven Telegram Bot Directory. Users can submit bots, and moderators can approve/reject them. Approved bots are posted to a channel with a rating system.

## Features
- **Submission System**: Guided conversation to add bots.
- **Moderation**: Admin approval workflow with rejection reasons.
- **Rating**: 1-5 star rating system with real-time updates.
- **Inline Search**: Search bots from any chat (`@BotLibBot query`).
- **Browsing**: Top Rated and Categorized lists.
- **PostGres Database**: Robust data storage.

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/BotLibrary.git
   cd BotLibrary
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Create a `.env` file:
   ```env
   BOT_TOKEN=your_bot_token
   OWNER_ID=your_user_id
   CHANNEL_ID=-1001234567890
   DB_URL=postgresql://user:pass@host/dbname
   ```

4. **Run**
   ```bash
   python main.py
   ```

## Tech Stack
- Python 3.9+
- `python-telegram-bot` (v20+)
- SQLAlchemy + PostgreSQL
