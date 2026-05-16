import os
import asyncio
import logging
import requests
import time
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import Message

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)

# --- FLASK WEB SERVER (To keep the bot alive on Render) ---
web_app = Flask('')
@web_app.route('/')
def home(): return "Link Generator Bot is Online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web); t.start()

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "12345")) 
API_HASH = os.environ.get("API_HASH", "your_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")
AROLINKS_API = os.environ.get("AROLINKS_API", "your_arolinks_key")
TARGET_CHAT = int(os.environ.get("TARGET_CHAT_ID", "-100...")) 

app = Client("link_generator_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- HELPER FUNCTIONS ---
def shorten_link(long_url):
    """Arolinks API integration for link shortening"""
    api_url = f"https://arolinks.com/api?api={AROLINKS_API}&url={long_url}"
    try:
        res = requests.get(api_url).json()
        if res.get("status") == "success":
            return res["shortenedUrl"]
    except Exception as e:
        logging.error(f"Arolinks Error: {e}")
    return None

# --- BOT HANDLERS ---

# 1. Command /g: For Single or Bulk URL (One post in channel)
@app.on_message(filters.command("g") & filters.private)
async def handle_generate(client, message):
    try:
        args = message.text.split()
        
        # Case: Single Video Link -> /g 146 1
        if len(args) == 3:
            video_id, ch_num = args[1], args[2]
            raw_url = f"https://t.me/Getvideo81827_bot?start={video_id}_{ch_num}"
            final_link = shorten_link(raw_url) or raw_url
            caption = f"🎥 **New Video**\n\n👉 [Click Here to Watch]({final_link})"
            await client.send_message(TARGET_CHAT, caption, disable_web_page_preview=True)
            await message.reply_text("✅ Single link channel par post ho gaya.")

        # Case: Bulk/Batch Link -> /g 253 268 2 3 v Ya i
        elif len(args) >= 5:
            s_id, e_id, ch_n, b_size = args[1], args[2], args[3], args[4]
            
            # Total count calculate karne ke liye
            total_count = (int(e_id) - int(s_id)) + 1
            
            # Check image 'i' or video 'v'
            media_type = "video" # Default video rahega
            if len(args) == 6:
                flag = args[5].lower()
                if flag == 'i':
                    media_type = "image"
                elif flag == 'v':
                    media_type = "video"

            raw_url = f"https://t.me/Getvideo81827_bot?start={s_id}_{e_id}_{ch_n}_{b_size}"
            final_link = shorten_link(raw_url) or raw_url
            
            # Naya Post Format
            caption = (
                f"🎬 **Full Series ({s_id}-{e_id})**\n\n"
                f"Total {total_count} {media_type}\n\n"
                f"👉 [Click Here to Watch All]({final_link})"
            )
            
            await client.send_message(TARGET_CHAT, caption, disable_web_page_preview=True)
            await message.reply_text(f"✅ Bulk {media_type} series link post ho gaya.")
        
        else:
            await message.reply_text("❌ Format:\nSingle: `/g 146 1`\nBulk: `/g 253 268 2 3 v` ya `/g 253 268 2 3 i`")

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# 2. Command /single: For Looping Individual Posts -> /single 50 70 1 1
@app.on_message(filters.command("single") & filters.private)
async def handle_single_loop(client, message):
    try:
        args = message.text.split()
        if len(args) != 5:
            return await message.reply_text("❌ Format: `/single [StartID] [EndID] [ChNum] [CountStart]`")

        start_id = int(args[1])
        end_id = int(args[2])
        ch_num = args[3]
        count = int(args[4])

        status = await message.reply_text(f"⏳ Processing {start_id} to {end_id}...")

        for i in range(start_id, end_id + 1):
            raw_url = f"https://t.me/Getvideo81827_bot?start={i}_{ch_num}"
            final_link = shorten_link(raw_url) or raw_url
            caption = f"{count}. [Click Here]({final_link})"
            
            try:
                await client.send_message(TARGET_CHAT, caption, disable_web_page_preview=True)
                count += 1
                await asyncio.sleep(2) 
            except Exception as post_err:
                logging.error(f"Post error at ID {i}: {post_err}")
        
        await status.edit_text("✅ Sabhi individual links post ho gaye!")

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# --- START ---
if __name__ == "__main__":
    keep_alive()
    print("🚀 Bot is running with updated /g and /single commands...")
    app.run()
