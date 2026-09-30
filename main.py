from telegram.ext import Application, MessageHandler, filters
from handlers.message_handler import handle_message
import os
from dotenv import load_dotenv

load_dotenv()


def main():
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
