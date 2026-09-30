from utils.database import SessionLocal
from models.models import User, Message
from google import genai
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

load_dotenv()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    username = update.effective_user.username
    message_text = update.message.text

    db = SessionLocal()
    try:
        # check if user exists, create if not
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, username=username)
            db.add(user)
            db.commit()
            db.refresh(user)

        user_message = Message(
            user_id=user.id, role="user", content=message_text)
        db.add(user_message)
        db.commit()

        # Generate response using Gemini
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=message_text
        )
        reply = response.text

        assistant_message = Message(
            user_id=user.id,
            role="assistant",
            content=reply
        )
        db.add(assistant_message)
        db.commit()

        await update.message.reply_text(reply)

    finally:
        db.close()
