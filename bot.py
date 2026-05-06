import os
import asyncio
import logging
import requests
from flask import Flask
from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)

# --- FLASK WEB SERVER (For Render 24/7) ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is Online!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", "12345")) 
API_HASH = os.environ.get("API_HASH", "your_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")
AROLINKS_API = os.environ.get("AROLINKS_API", "your_arolinks_key")

# Environment Variables for Channels
SOURCE_CHAT = int(os.environ.get("SOURCE_CHAT_ID", "-100...")) 
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

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    await message.reply_text(
        "👋 **Bot Ready Hai!**\n\n"
        "▶️ **Single Post:** `/g 50` (Sirf ek post ke liye)\n"
        "▶️ **Multiple Posts:** `/g 50 60` (Range ke liye)"
    )

@app.on_message(filters.command("g") & filters.private)
async def handle_generate(client, message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply_text("❌ Format: `/g 50` ya `/g 50 60` लिखें।")

        # Range Logic
        if len(args) == 2:
            start_val = end_val = int(args[1])
        else:
            start_val = int(args[1])
            end_val = int(args[2])

        status = await message.reply_text("⏳ **Process shuru ho raha hai...**")
        
        # Current Message ID (Assuming it starts from some base or you send the first ID)
        # Yahan hum maan ke chal rahe hain ki Source Chat mein Message ID wahi hai jo Video No. hai
        # Agar aisa nahi hai, to aap code mein thoda badlav kar sakte hain.

        success_count = 0
        for i in range(start_val, end_val + 1):
            # 1. Generate Link
            long_url = f"https://t.me/Getvideo81827_bot?start={i}"
            short_url = shorten_link(long_url)
            
            if not short_url:
                await message.reply_text(f"⚠️ Link skip hua: {i}")
                continue

            try:
                # 2. Get from Source (Assuming Message ID = Video Number)
                # Note: Agar source message ID alag hai, to yahan offset add karna hoga
                source_msg = await client.get_messages(SOURCE_CHAT, i)
                
                if source_msg and source_msg.photo:
                    # 3. Send to Target
                    await client.send_photo(
                        chat_id=TARGET_CHAT,
                        photo=source_msg.photo.file_id,
                        caption=f"✅ **Video No: {i}**\n\n📥 **Download Link:** {short_url}",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download Now", url=short_url)]])
                    )
                    success_count += 1
                    await asyncio.sleep(3) # Anti-flood
                else:
                    await message.reply_text(f"❌ ID {i} par photo nahi mili.")
            except Exception as e:
                logging.error(f"Error at ID {i}: {e}")

        await status.edit_text(f"✨ **Task Done!**\nTotal {success_count} posts successfully share ho gaye.")

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

# --- MAIN EXECUTION ---
async def main():
    await app.start()
    print("✅ Bot is Online!")
    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == "__main__":
    keep_alive()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
