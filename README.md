# UniHelper Telegram Bot

## Railway Variables
Add these in Railway -> Variables:

BOT_TOKEN=your_telegram_bot_token
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openai/gpt-oss-20b:free

Optional:
ADMIN_ID=your_telegram_user_id

## Start locally
pip install -r requirements.txt
python main.py

## Railway
Railway will run this automatically through Procfile:
worker: python main.py
