import os
import asyncio
import logging
import requests
import time
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)

# --- FLASK WEB SERVER (To keep the bot alive) ---
web_app = Flask('')
@web_app.route('/')
def home(): return "Bot is Online!"

def run_web():
    # Render default port 10000 use karega, ya 8080
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web); t.start()

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "12345")) 
API_HASH = os.environ.get("API_HASH", "your_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")
AROLINKS_API = os.environ.get("AROLINKS_API", "your_arolinks_key")
TARGET_CHAT = int(os.environ.get("TARGET_CHAT_ID", "-100...")) # Jaha post karna hai

app = Client("link_generator_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- HELPER FUNCTIONS ---
def shorten_link(long_url):
    """Arolinks se link short karne ke liye"""
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
        args = message.text.split()
        
        # CASE 1: Single Video Format -> /g [video_id] [ch_num]
        if len(args) == 3:
            video_id = args[1]
            ch_num = args[2]
            
            # GetVideo Bot ka URL format (Underscore wala)
            raw_url = f"https://t.me/Getvideo81827_bot?start={video_id}_{ch_num}"
            short_url = shorten_link(raw_url)
            final_link = short_url if short_url else raw_url
            
            caption = f"🎥 **New Video Uploaded**\n\n🆔 ID: {video_id}\n\n👉 [Click Here to Watch]({final_link})"
            
            await client.send_message(
                chat_id=TARGET_CHAT, 
                text=caption, 
                disable_web_page_preview=True
            )
            await message.reply_text(f"✅ Single link post kar diya gaya hai!\nURL: {final_link}")

        # CASE 2: Bulk Series Format -> /g [start_id] [end_id] [ch_num] [batch_size]
        elif len(args) == 5:
            start_id = args[1]
            end_id = args[2]
            ch_num = args[3]
            batch_size = args[4]
            
            # GetVideo Bot ka Bulk URL format
            raw_url = f"https://t.me/Getvideo81827_bot?start={start_id}_{end_id}_{ch_num}_{batch_size}"
            short_url = shorten_link(raw_url)
            final_link = short_url if short_url else raw_url
            
            caption = f"🎬 **Full Series Available**\n\n📦 Part: {start_id} to {end_id}\n\n👉 [Click Here to Watch All]({final_link})"
            
            await client.send_message(
                chat_id=TARGET_CHAT, 
                text=caption, 
                disable_web_page_preview=True
            )
            await message.reply_text(f"✅ Bulk series link post kar diya gaya hai!\nURL: {final_link}")

        else:
            # Help Message agar format galat ho
            help_msg = (
                "❌ **Format Sahi Nahi Hai!**\n\n"
                "**1. Single Video ke liye:**\n"
                "`/g 146 1` (VideoID ChannelNum)\n\n"
                "**2. Bulk Series ke liye:**\n"
                "`/g 820 831 2 3` (StartID EndID ChannelNum BatchSize)"
            )
            await message.reply_text(help_msg)

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.reply_text(f"❌ Kuch error aaya: {e}")

# --- START BOT ---
if __name__ == "__main__":
    keep_alive()
    print("🚀 Link Generator Bot is running...")
    app.run()
