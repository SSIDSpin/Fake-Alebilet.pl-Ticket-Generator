from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, MessageHandler, filters
import logging
from config import AUTH_ID
from Commands.startcommand import load_users 

BROADCAST_MESSAGE = 1
async def broadcast_start(update: Update, context: CallbackContext):
    await update.callback_query.edit_message_text("This Feature Isnt Ready Yet")
    return BROADCAST_MESSAGE