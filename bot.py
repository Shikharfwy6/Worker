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

SOURCE_CHAT = int(os.environ.get("SOURCE_CHAT_ID", "-100...")) 
TARGET_CHAT = int(os.environ.get("TARGET_CHAT_ID", "-100..."))

app = Client("universal_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Temporary data storage
user_sessions = {}

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
        args = message.text.split()
        if len(args) < 2:
            return await message.reply_text("❌ Format: `/g 35` (Single) या `/g 35 40` (Multiple)")

        start_v = int(args[1])
        end_v = int(args[2]) if len(args) > 2 else start_v
        
        status = await message.reply_text("🔗 **Links generate ho rahe hain...**")
        
        links = []
        for i in range(start_v, end_v + 1):
            l_url = f"https://t.me/Getvideo81827_bot?start={i}"
            s_url = shorten_link(l_url)
            if s_url:
                links.append({"vid_num": i, "link": s_url})
        
        # Session save karlo image ID ke intezaar mein
        user_sessions[message.from_user.id] = {"links": links}
        
        await status.edit_text(
            f"✅ **{len(links)} Links taiyaar hain!**\n\n"
            f"Ab source channel se **Image (Message ID)** bhejiye.\n"
            f"Agar multiple links hain, to sirf **Pehli Image ki ID** bhejiye, baaki bोट line se utha lega."
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@app.on_message(filters.private & filters.text & ~filters.command(["start", "g"]))
async def handle_image_id(client, message):
    uid = message.from_user.id
    if uid not in user_sessions:
        return # Koi active session nahi hai

    try:
        # User ne jo bheja wo Image Message ID hai
        img_id_args = message.text.split()
        start_img_id = int(img_id_args[0])
        
        data = user_sessions[uid]
        links_list = data["links"]
        
        await message.reply_text(f"🚀 **Posting shuru ho rahi hai...**")
        
        for i, item in enumerate(links_list):
            current_img_id = start_img_id + i
            try:
                # Source channel se image uthao
                source_msg = await client.get_messages(SOURCE_CHAT, current_img_id)
                
                if source_msg and source_msg.photo:
                    await client.send_photo(
                        chat_id=TARGET_CHAT,
                        photo=source_msg.photo.file_id,
                        caption=f"✅ **Video No: {item['vid_num']}**\n\n📥 **Download Link:** {item['link']}",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download Now", url=item['link'])]])
                    )
                    await asyncio.sleep(2) # Speed limit protection
                else:
                    await message.reply_text(f"⚠️ ID {current_img_id} par photo nahi mili. Skipping...")
            except Exception as e:
                await message.reply_text(f"❌ Error at Image ID {current_img_id}: {e}")
        
        await message.reply_text("✨ **Saare posts mukammal ho gaye!**")
        del user_sessions[uid] # Kaam khatam, session clear

    except ValueError:
        await message.reply_text("❌ Please valid Message ID (Number) bhejiye.")

# --- MAIN ---
async def main():
    await app.start()
    from pyrogram import idle
    await idle()
    await app.stop()

if __name__ == "__main__":
    keep_alive()
    asyncio.get_event_loop().run_until_complete(main())
