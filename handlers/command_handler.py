import os
from google import genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

from models.models import Message, User
from utils.database import SessionLocal

logger = logging.getLogger(__name__)


async def welcome_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user

    db = SessionLocal()
    try:
        # find or create the user
        user = db.query(User).filter(User.telegram_id == tg_user.id).first()
        if not user:
            user = User(telegram_id=tg_user.id, username=tg_user.username)
            db.add(user)
            db.commit()
            db.refresh(user)

        welcome_message = (
            f"Hello {tg_user.first_name}! Welcome to the Telegram AI Bot. "
            "Feel free to ask me anything or have a chat!"
        )
        await update.effective_message.reply_text(welcome_message)
    except Exception as e:
        logger.error(f"Error in welcome_user: {e}")
    finally:
        db.close()


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_message = (
        "Here are some commands you can use:\n"
        "/start - Start the bot and receive a welcome message\n"
        "/help - Show this help message\n"
        "/profile - View your user profile and stats\n"
        "/stats - View the number of users and messages (admin only)\n"
        "/broadcast - Send a message to all users (admin only)\n"
        "/menu - Show the main menu\n"
        "/summary - Get a summary of your messages\n"
        "Just type any message to chat with the AI!"
    )
    await update.effective_message.reply_text(help_message)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == tg_user.id).first()
        if user:
            profile_message = (
                f"User Profile:\n"
                f"Username: {user.username}\n"
                f"Telegram ID: {user.telegram_id}\n"
                f"Joined At: {user.joined_at}\n"
                f"Number of Messages: {db.query(Message).filter(Message.user_id == user.id).count()}"
            )
        else:
            profile_message = "You are not registered yet. Please send a message to register."
        await update.effective_message.reply_text(profile_message)
    except Exception as e:
        logger.error(f"Error in profile: {e}")
    finally:
        db.close()


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Profile", callback_data='profile')],
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("Summary", callback_data='summary')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text('Please choose an option:', reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # tells Telegram "got it" so the button stops showing a loading spinner
    await query.answer()

    if query.data == "profile":
        await profile(update, context)
    elif query.data == "help":
        await help(update, context)


async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)

    if not text:
        await update.effective_message.reply_text(
            "Please provide text to summarize.\nExample: /summarize Your long text here..."
        )
        return

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=f"Summarize the following text concisely, keeping the main idea and important information. Do not add extra information:\n\n{text}"
    )

    await update.effective_message.reply_text(response.text)
