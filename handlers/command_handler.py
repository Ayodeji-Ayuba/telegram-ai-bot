import logging

from telegram import Update
from telegram.ext import ContextTypes

from models.models import Message
from services.gemini_services import chat_reply
from services.user_service import get_or_create_user
from utils.database import SessionLocal

logger = logging.getLogger(__name__)

HISTORY_LIMIT = 10


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    message_text = update.message.text

    db = SessionLocal()
    try:
        user = get_or_create_user(db, tg_user)

        # fetch PREVIOUS history (the new message isn't saved yet)
        # order by id instead of created_at to avoid timestamp ties
        history = (
            db.query(Message)
            .filter(Message.user_id == user.id)
            .order_by(Message.id.desc())
            .limit(HISTORY_LIMIT)
            .all()
        )
        history.reverse()  # oldest -> newest

        # the Gemini call itself lives in services/gemini_services.py
        name = tg_user.first_name or tg_user.username
        reply = await chat_reply(
            [(msg.role, msg.content) for msg in history],
            message_text,
            name,
        )
        if not reply:  # blocked or empty responses return None
            await update.message.reply_text("Sorry, I couldn't come up with a response. Try rephrasing?")
            return

        # (1) save the user message and reply together, only after Gemini succeeded
        db.add(Message(user_id=user.id, role="user", content=message_text))
        db.add(Message(user_id=user.id, role="assistant", content=reply))
        db.commit()

        await update.message.reply_text(reply)

    except Exception:
        db.rollback()
        logger.exception("Error handling message")
        await update.message.reply_text("An error occurred while processing your message.")

    finally:
        db.close()
