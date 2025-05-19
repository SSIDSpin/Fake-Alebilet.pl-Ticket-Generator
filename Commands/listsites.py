import requests
from datetime import datetime, timedelta
from telegram import Update
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
import asyncssh
from config import REMOTE_HOST , USERNAME , PASSWORD , AUTH_ID


SSH_HOST = REMOTE_HOST
SSH_USER = USERNAME
SSH_PASSWORD = PASSWORD
APACHE_ROOT = '/var/www/html'

async def delete_website_folder(website_name: str) -> bool:
    folder_path = f"{APACHE_ROOT}/{website_name}"
    try:
        async with asyncssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASSWORD) as conn:
            result = await conn.run(f"rm -rf {folder_path}", check=True)
        return True
    except (asyncssh.Error, OSError) as e:
        print(f"SSH error deleting folder {folder_path}: {e}")
        return False

async def weblist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    print(f"User ID: {user_id}")

    if user_id != AUTH_ID:
        if update.message:
            await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    conn = sqlite3.connect('userdata.db')
    cursor = conn.cursor()
    cursor.execute("SELECT websites FROM licenses WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row[0]:
        msg = "No websites found for your account."
        if update.message:
            await update.message.reply_text(msg)
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg)
        return

    websites_str = row[0]


    try:
        websites = json.loads(websites_str)
    except json.JSONDecodeError:
        websites = [w.strip() for w in websites_str.split(",") if w.strip()]


    keyboard = []
    for website in websites:
        button = InlineKeyboardButton(text=website, callback_data=f"website_{website}")
        keyboard.append([button]) 

    reply_markup = InlineKeyboardMarkup(keyboard)


    if update.message:
        await update.message.reply_text("Select a website:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Type in the website you want to delete:", reply_markup=reply_markup)

    context.user_data['expecting_website_selection'] = True



async def handle_website_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != AUTH_ID:
        if update.message:
            await update.message.reply_text("⛔ You are not authorized to use this command.")
        return


    if not context.user_data.get('expecting_website_selection'):
        if update.message:
            await update.message.reply_text("Please use /weblist to see your websites first.")
        return

    if not update.message or not update.message.text:
        return

    website_to_delete = update.message.text.strip()


    conn = sqlite3.connect('userdata.db')
    cursor = conn.cursor()
    cursor.execute("SELECT websites FROM licenses WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row or not row[0]:
        await update.message.reply_text("No websites found for your account.")
        conn.close()
        context.user_data['expecting_website_selection'] = False
        return

    websites_str = row[0]

   
    try:
        websites = json.loads(websites_str)
    except json.JSONDecodeError:
        websites = [w.strip() for w in websites_str.split(",") if w.strip()]

    if website_to_delete not in websites:
        await update.message.reply_text(f"Website '{website_to_delete}' not found in your list.")
        return
    
    ssh_delete_success = await delete_website_folder(website_to_delete)

    if not ssh_delete_success:
        await update.message.reply_text(f"Failed to delete the website folder on the server. Aborting deletion.")
        return

    websites.remove(website_to_delete)

    new_websites_str = json.dumps(websites)
    cursor.execute("UPDATE licenses SET websites = ? WHERE user_id = ?", (new_websites_str, user_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"Website '{website_to_delete}' has been deleted successfully.")
    context.user_data['expecting_website_selection'] = False
