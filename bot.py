import os
import asyncio
import logging
import requests
from flask import Flask
from threading import Thread
from pyrogram import Client, filters

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)

# --- FLASK WEB SERVER (For 24/7 Hosting) ---
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
TARGET_CHAT = int(os.environ.get("TARGET_CHAT_ID", "-100..."))

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
        # Example: /g 100 110 1 (Matalab 100 se 110 tak ke links aur ginti 1 se shuru)
        args = message.text.split()
        if len(args) < 4:
            return await message.reply_text("❌ **Format:** `/g [StartID] [EndID] [StartCount]`\n\nExample: `/g 35 45 1`")

        start_v = int(args[1])
        end_v = int(args[2])
        count_start = int(args[3])
        
        status = await message.reply_text("🔗 **Links generate aur post ho rahe hain...**")
        
        posted_count = 0
        current_count = count_start

        for i in range(start_v, end_v + 1):
            l_url = f"https://t.me/Getvideo81827_bot?start={i}"
            s_url = shorten_link(l_url)
            
            if s_url:
                # Text format: 1. https://link.com
                caption = f"{current_count}. {s_url}"
                
                # Direct channel par post karna
                await client.send_message(chat_id=TARGET_CHAT, text=caption)
                
                current_count += 1
                posted_count += 1
                await asyncio.sleep(1.5) # Flood wait se bachne ke liye

        await status.edit_text(f"✅ **Kaam khatam!**\n\nTotal {posted_count} links Target Channel par post kar diye gaye hain.")

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# --- MAIN ---
if __name__ == "__main__":
    keep_alive()
    app.run()
