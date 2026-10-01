from telegram.ext import Application, MessageHandler, CommandHandler, filters
from handlers.message_handler import handle_message
from handlers.command_handler import welcome_user, help, profile
import os
from dotenv import load_dotenv
from handlers.admin_handler import stats, broadcast


load_dotenv()


def main():
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    app.add_handler(CommandHandler("start", welcome_user))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
