import json

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging


USER_FILE = 'users.json'

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

def load_users():
    try:
        with open(USER_FILE, 'r') as f:
            return json.load(f)  # Directly return the list from the file
    except FileNotFoundError:
        logging.error(f"{USER_FILE} not found.")
        return []  # Return an empty list if the file doesn't exist
    except json.JSONDecodeError:
        logging.error("Error decoding JSON from the users file.")
        return []  # Return an empty list if the file is not valid JSON
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users = load_users()

    if user_id not in users:
        users.append(user_id)
        save_users(users)
        await update.message.reply_text("Run /menu To See Options.")
    else:
        await update.message.reply_text("Run /menu To See Options.")
