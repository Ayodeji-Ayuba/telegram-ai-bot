import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

from models.models import Message, User
from utils.database import SessionLocal


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != os.getenv("ADMIN_ID"):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        message_count = db.query(Message).count()
        stats_message = (
            f"User Stats:\n"
            f"Number of Users: {user_count}\n"
            f"Number of Messages: {message_count}"
        )
        await update.message.reply_text(stats_message)
    except Exception as e:
        logging.error(f"Error in stats: {e}")
        await update.message.reply_text("An error occurred while fetching your stats.")
    finally:
        db.close()


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != os.getenv("ADMIN_ID"):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("Please provide a message to broadcast.")
        return

    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            try:
                await context.bot.send_message(chat_id=user.telegram_id, text=message_text)
            except Exception as e:
                logging.error(
                    f"Failed to send message to {user.telegram_id}: {e}")
        await update.message.reply_text("Broadcast completed.")
    except Exception as e:
        logging.error(f"Error in broadcast: {e}")
        await update.message.reply_text("An error occurred while broadcasting the message.")
    finally:
        db.close()
