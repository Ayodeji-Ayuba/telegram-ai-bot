import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import ContextTypes

from models.models import Message, User
from utils.database import SessionLocal

load_dotenv()
logger = logging.getLogger(__name__)

# Created once at import time, not on every message
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.5-flash-lite"
HISTORY_LIMIT = 10

# Persona / behaviour for the bot
SYSTEM_PROMPT = (
    "You are a friendly, helpful assistant chatting with people on Telegram. "
    "Keep replies concise and conversational."
)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user
    message_text = update.message.text

    db = SessionLocal()
    try:
        # find or create the user
        user = db.query(User).filter(User.telegram_id == tg_user.id).first()
        if not user:
            user = User(telegram_id=tg_user.id, username=tg_user.username)
            db.add(user)
            db.commit()
            db.refresh(user)

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

        contents = [
            {
                "role": "user" if msg.role == "user" else "model",
                "parts": [{"text": msg.content}],
            }
            for msg in history
        ]
        # add the new message in memory only, for now
        contents.append({"role": "user", "parts": [{"text": message_text}]})

        # (4) tell the model who it is talking to
        name = tg_user.first_name or tg_user.username
        system_instruction = SYSTEM_PROMPT
        if name:
            system_instruction += (
                f" The user's name is {name}. Use it occasionally, not in every reply."
            )

        # (2) async client: doesn't block the event loop while waiting
        response = await client.aio.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction),
        )
        reply = response.text
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
