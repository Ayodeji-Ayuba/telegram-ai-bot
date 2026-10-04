import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
logger = logging.getLogger(__name__)

# Created once at import time, not on every request
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.5-flash-lite"

# Persona / behaviour for the bot
SYSTEM_PROMPT = (
    "You are a friendly, helpful assistant chatting with people on Telegram. "
    "Keep replies concise and conversational."
)

SUMMARIZE_PROMPT = (
    "Summarize the following text concisely, keeping the main idea and "
    "important information. Do not add extra information:\n\n"
)


async def chat_reply(history, message_text, user_name=None):
    """Return Gemini's reply to message_text, or None if nothing came back.

    history is a list of (role, content) pairs, oldest first, where role is
    "user" or "assistant". Nothing in this file knows about Telegram or the
    database, so any part of the bot can reuse it.
    """
    contents = [
        {
            "role": "user" if role == "user" else "model",
            "parts": [{"text": content}],
        }
        for role, content in history
    ]
    contents.append({"role": "user", "parts": [{"text": message_text}]})

    # tell the model who it is talking to
    system_instruction = SYSTEM_PROMPT
    if user_name:
        system_instruction += (
            f" The user's name is {user_name}. Use it occasionally, not in every reply."
        )

    # async client: doesn't block the event loop while waiting
    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction),
    )
    return response.text  # None if the response was blocked or empty


async def summarize_text(text):
    """Return a short summary of text, or None if nothing came back."""
    response = await client.aio.models.generate_content(
        model=MODEL,
        contents=SUMMARIZE_PROMPT + text,
    )
    return response.text  # None if the response was blocked or empty
