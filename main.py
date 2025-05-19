import asyncio
import nest_asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, ConversationHandler
from config import BOT_TKN, AUTH_ID
from Commands.generatecode import generate, handle_days_input
from Commands.redeemcode import redeem, handle_license_input
from Commands.startcommand import start
from Commands.dmall import broadcast_start
from Commands.generatealebilet import handle_bilet_input , generatebilet
from Commands.listsites import handle_website_input , weblist
import sqlite3

bot_active = True

async def handle_user_input(update, context):
    if not bot_active:
        return  

    if context.user_data.get("expecting_bilet") is not None:
        await handle_bilet_input(update, context)
    elif context.user_data.get("expecting_days"):
        await handle_days_input(update, context)
    elif context.user_data.get("expecting_license_key"):
        await handle_license_input(update, context)
    elif context.user_data.get("expecting_website_selection"):
        await handle_website_input(update, context)


async def menu(update, context):
    user_id = str(update.effective_user.id)
    print(user_id)
    keyboard = []

    if user_id == AUTH_ID:  
        keyboard.append([InlineKeyboardButton("Generate Code", callback_data='generate'),
                         InlineKeyboardButton(f"Turn Bot Off" if bot_active else "Turn Bot On", callback_data='onoff')])
        keyboard.append([InlineKeyboardButton("DM All Users", callback_data='dmall')])
        keyboard.append([InlineKeyboardButton("----", callback_data='no_action')])
        keyboard.append([InlineKeyboardButton("Redeem Code", callback_data='redeem')])
        keyboard.append([InlineKeyboardButton("Alebilet Link", callback_data='alebilet')])
        keyboard.append([InlineKeyboardButton("List Sites", callback_data='listsites')])  
        keyboard.append([InlineKeyboardButton("Status", callback_data='status')])
    else:
        
        keyboard.append([InlineKeyboardButton("Redeem Code", callback_data='redeem')])
        keyboard.append([InlineKeyboardButton("Alebilet Link", callback_data='alebilet')])
        keyboard.append([InlineKeyboardButton("List Sites", callback_data='listsites')])  
        keyboard.append([InlineKeyboardButton("Status", callback_data='status')])

   
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Please choose an option:', reply_markup=reply_markup)

# Handle button press
async def button(update, context):
    global bot_active
    query = update.callback_query
    await query.answer()  
    choice = query.data  

    if choice == 'generate':
        if not bot_active:
            await query.edit_message_text(text="Bot is OFF. Please use the on/off button to turn on.")
            return
        await generate(update, context)

    elif choice == 'redeem':
        if not bot_active:
            await query.edit_message_text(text="Bot is OFF")
            return
        await redeem(update, context)

    elif choice == 'alebilet':
        if not bot_active:
            await query.edit_message_text(text="Bot is OFF")
            return
        await generatebilet(update, context)
    
    elif choice == 'listsites':
        if not bot_active:
            await query.edit_message_text(text="Bot is OFF")
            return
        await weblist(update, context)


    elif choice == 'status':
        if not bot_active:
            await query.edit_message_text(text="Bot is OFF")
            return
        await query.edit_message_text(text="Bot is ON")

    elif choice == 'onoff':
        bot_active = not bot_active
        status = "ON" if bot_active else "OFF"
        await query.edit_message_text(text=f"Bot is now {status}")

    elif choice == 'dmall':
        if not bot_active:
            await query.edit_message_text(text="Bot is OFF")
            return

        test = await broadcast_start(update, context)
        print(test)



def init_db():
    conn = sqlite3.connect("userdata.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            license_key TEXT,
            websites TEXT
        )
    ''')
    conn.commit()
    conn.close()


async def main():
   
    app = ApplicationBuilder().token(BOT_TKN).build()

    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("start", start))

   
    app.add_handler(CallbackQueryHandler(button))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))

    print("✅ Bot is running...")

    
    await app.run_polling()

if __name__ == "__main__":

    init_db()
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
