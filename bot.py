import os
import asyncio
import logging
import requests
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import Message

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)

# --- FLASK WEB SERVER ---
web_app = Flask('')
@web_app.route('/')
def home(): return "Bot is Online!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web); t.start()

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "12345")) 
API_HASH = os.environ.get("API_HASH", "your_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")
AROLINKS_API = os.environ.get("AROLINKS_API", "your_arolinks_key")
TARGET_CHAT = int(os.environ.get("TARGET_CHAT_ID", "-100...")) # Aapka Channel ID

app = Client("universal_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- HELPER FUNCTIONS ---
def shorten_link(long_url):
    api_url = f"https://arolinks.com/api?api={AROLINKS_API}&url={long_url}"
    try:
        res = requests.get(api_url).json()
        if res.get("status") == "success":
            return res["shortenedUrl"]
    except Exception as e:
        logging.error(f"Arolinks Error: {e}")
    return None

# --- BOT HANDLERS ---

@app.on_message(filters.command("g") & filters.private)
async def handle_generate(client, message):
    try:
        # Format: /g [start_msg_id] [end_msg_id] [start_count_number]
        args = message.text.split()
        if len(args) < 4:
            return await message.reply_text("❌ **Format sahi nahi hai!**\n\nExample: `/g 128 130 1` \n(Yaha 128 se 130 tak link banenge aur ginti 1 se shuru hogi)")

        start_id = int(args[1])
        end_id = int(args[2])
        count_num = int(args[3])
        
        status = await message.reply_text("🔗 **Links process ho rahe hain aur Channel par bheje ja rahe hain...**")
        
        posted_count = 0

        for i in range(start_id, end_id + 1):
            raw_url = f"https://t.me/Getvideo81827_bot?start={i}"
            short_url = shorten_link(raw_url)
            
            # Agar shortener fail ho jaye toh original link use karega
            final_link = short_url if short_url else raw_url
            
            # Aapke kahe anusar format: "1. [Click Here](link)"
            # Isse text ke andar link chhup jayega
            caption = f"{count_num}. [Click Here]({final_link})"
            
            try:
                # Target channel par post karna
                await client.send_message(
                    chat_id=TARGET_CHAT, 
                    text=caption, 
                    disable_web_page_preview=True # Preview off taaki saaf dikhe
                )
                
                count_num += 1
                posted_count += 1
                await asyncio.sleep(2) # Flood wait protection
                
            except Exception as send_error:
                logging.error(f"Post error: {send_error}")

        await status.edit_text(f"✅ **Done!**\n\nTotal {posted_count} posts channel par bhej diye gaye hain.")

    except ValueError:
        await message.reply_text("❌ Please numbers use karein. Example: `/g 128 130 1`")
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# --- MAIN ---
if __name__ == "__main__":
    keep_alive()
    app.run()
