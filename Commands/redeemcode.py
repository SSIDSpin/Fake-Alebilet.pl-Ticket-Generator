import requests
from telegram import Update
from telegram.ext import ContextTypes
from config import API_KEY, PRODUCT_KEY
import sqlite3

VALIDATE_KEY_URL = "https://api.cryptolens.io/api/key/Activate"


def add_license_record(user_id: int, license_key: str, websites: str):
    try:
        conn = sqlite3.connect("userdata.db")
        cursor = conn.cursor()
        
        # Use INSERT OR REPLACE to update if user_id exists, or insert otherwise
        cursor.execute('''
            INSERT INTO licenses (user_id, license_key, websites)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                license_key=excluded.license_key,
                websites=excluded.websites
        ''', (user_id, license_key, websites))
        
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()



async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Ensure that we're replying to the user correctly whether it's a message or callback
        if update.message:
            await update.message.reply_text(f"🔑 Please send the license key to redeem:")
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(f"🔑 Please send the license key to redeem:")

        context.user_data['expecting_license_key'] = True

    except Exception as e:
        # General error handling
        if update.message:
            await update.message.reply_text(f"⚠️ Unexpected error in /redeem: {e}")
        elif update.callback_query:
            await update.callback_query.edit_message_text(f"⚠️ Unexpected error in /redeem: {e}")

async def handle_license_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # If the bot is not expecting a license key, ignore input
    if not context.user_data.get('expecting_license_key'):
        return

    # Ensure the update has a message object
    if not update.message:
        return

    license_key = update.message.text.strip()

    if not license_key:
        await update.message.reply_text("❌ You must provide a license key.")
        return

    payload = {
        "token": API_KEY,
        "ProductId": PRODUCT_KEY,
        "Key": license_key,
        "Sign": True,
        "v": 1
    }

    try:
        # Send request to validate the license key
        response = requests.post(VALIDATE_KEY_URL, data=payload, timeout=10)
        response.raise_for_status()  # Raise exception for invalid HTTP responses (e.g., 4xx, 5xx)

        # Parse the API response
        data = response.json()
        if data.get("result") == 0:  # Success case
            license_info = data.get("licenseKey", {})
            expiration = license_info.get("expires", "Unknown")
            features = license_info.get("f1", False)

            add_license_record(
                user_id=update.effective_user.id,
                license_key=license_key,
                websites=None,
            )

            await update.message.reply_text(
                f"✅ License key valid!\n"
                f"Key: `{license_key}`\n"
                f"Expires: {expiration}\n"
                f"Feature F1 Enabled: {features}",
                parse_mode="Markdown"
            )





        else:  # Invalid key
            await update.message.reply_text(
                f"❌ Invalid key:\n"
                f"Reason: {data.get('message', 'Unknown error')}"
            )

    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ Request timed out. Please try again later.")
    except requests.exceptions.HTTPError as e:
        await update.message.reply_text(f"❌ HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Connection error: {e}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Unexpected error: {e}")
    finally:
        # Ensure 'expecting_license_key' is reset whether or not the request was successful
        context.user_data['expecting_license_key'] = False
