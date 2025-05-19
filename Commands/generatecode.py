import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes
from config import PRODUCT_KEY, API_KEY, AUTH_ID

API_URL = "https://api.cryptolens.io/api/key/CreateKey"

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User ID: {update.effective_user.id}")

    if str(update.effective_user.id) != AUTH_ID:
        if update.message:
            await update.message.reply_text(f"⛔ You are not authorized to use this command.")
        return


    if update.message:
        await update.message.reply_text("How many days should the license be valid for?")
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("How many days should the license be valid for?")

    context.user_data['expecting_days'] = True

async def handle_days_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != AUTH_ID:
        if update.message:
            await update.message.reply_text(f"⛔ You are not authorized to use this command.")
        return

    if context.user_data.get('expecting_days'):
        try:
           
            if update.message:
                days_valid = int(update.message.text)
            elif update.callback_query:
                days_valid = int(update.callback_query.data)

            if not (1 <= days_valid <= 999):
                if update.message:
                    await update.message.reply_text("Please enter a number between 1 and 999.")
                return

            payload = {
                "token": API_KEY,
                "ProductId": PRODUCT_KEY,
                "Period": days_valid,
                "F1": True,  
                "v": 1       
            }

            response = requests.post(API_URL, data=payload)
            data = response.json()

            if data.get("result") == 0:
                key = data.get("key")
                expiration = (datetime.utcnow() + timedelta(days=days_valid)).strftime("%Y-%m-%d")
                if update.message:
                    await update.message.reply_text(
                        f"✅ License key created:\n`{key}`\nValid until: {expiration}",
                        parse_mode="Markdown"
                    )
                elif update.callback_query:
                    await update.callback_query.edit_message_text(
                        f"✅ License key created:\n`{key}`\nValid until: {expiration}",
                        parse_mode="Markdown"
                    )
            else:
                if update.message:
                    await update.message.reply_text(f"❌ Error: {data.get('message', 'Unknown error')}")
                elif update.callback_query:
                    await update.callback_query.edit_message_text(f"❌ Error: {data.get('message', 'Unknown error')}")

        except ValueError:
            if update.message:
                await update.message.reply_text("Please enter a valid number.")
            elif update.callback_query:
                await update.callback_query.edit_message_text("Please enter a valid number.")
        except Exception as e:
            if update.message:
                await update.message.reply_text(f"Unexpected error: {e}")
            elif update.callback_query:
                await update.callback_query.edit_message_text(f"Unexpected error: {e}")

        context.user_data['expecting_days'] = False
