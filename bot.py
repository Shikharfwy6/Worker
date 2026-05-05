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
    return "Bot is Online and Running!"

def run_web():
    # Render automatically provides a PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# --- CONFIGURATION ---
# Render ke Environment Variables se data lega
API_ID = int(os.environ.get("API_ID", "12345")) 
API_HASH = os.environ.get("API_HASH", "your_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")
AROLINKS_API = os.environ.get("AROLINKS_API", "your_arolinks_key")

app = Client("universal_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# User data storage
user_data = {}

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
    await message.reply_text("👋 **Universal Bot Active Hai!**\n\nKaam shuru karne ke liye `/generate` command ka use karein.\nFormat: `/generate 20 25`")

@app.on_message(filters.command("generate") & filters.private)
async def generate_links(client, message):
    try:
        args = message.text.split()
        if len(args) < 3:
            return await message.reply_text("❌ Galat Format! Use: `/generate 20 25`")

        start_val = int(args[1])
        end_val = int(args[2])
        
        status = await message.reply_text("🔗 **Links generate ho rahe hain...**")
        
        links_list = []
        for i in range(start_val, end_val + 1):
            long_url = f"https://t.me/Getvideo81827_bot?start={i}"
            short_url = shorten_link(long_url)
            if short_url:
                links_list.append(short_url)
        
        user_data[message.from_user.id] = {
            "links": links_list,
            "start_num": start_val,
            "step": "awaiting_source"
        }

        await status.edit_text(
            f"✅ **{len(links_list)} Links Taiyaar Hain!**\n\nAb us **Source Channel** ki ID bhejiye jahan se images uthani hain.\nExample: `-1003925609024`"
        )
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")

@app.on_message(filters.private & ~filters.command(["start", "generate"]))
async def collect_inputs(client, message):
    uid = message.from_user.id
    if uid not in user_data:
        return

    state = user_data[uid].get("step")

    if state == "awaiting_source":
        user_data[uid]["source_chat"] = int(message.text)
        user_data[uid]["step"] = "awaiting_target"
        await message.reply_text("✅ Source Chat Save!\n\nAb us **Target Channel** ki ID bhejiye jahan POST karna hai.")

    elif state == "awaiting_target":
        user_data[uid]["target_chat"] = int(message.text)
        user_data[uid]["step"] = "awaiting_msg_id"
        await message.reply_text("✅ Target Chat Save!\n\nAb pehli **Photo (Message ID)** bhejiye jahan se process shuru karna hai.\nExample: `34`")

    elif state == "awaiting_msg_id":
        user_data[uid]["msg_id"] = int(message.text)
        user_data[uid]["step"] = "ready"
        await message.reply_text(
            "🚀 **Sab kuch taiyaar hai!**\n\nNiche diya gaya button dabate hi posting shuru ho jayegi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏁 Start Posting Now", callback_data="start_task")]])
        )

@app.on_callback_query(filters.regex("start_task"))
async def run_task(client, callback_query):
    uid = callback_query.from_user.id
    data = user_data.get(uid)
    
    if not data or data.get("step") != "ready":
        return await callback_query.answer("Session expired! Fir se shuru karein.", show_alert=True)

    await callback_query.message.edit_text("⏳ **Posting Process Shuru Ho Gaya Hai...**")
    
    curr_msg_id = data["msg_id"]
    
    for i, link in enumerate(data["links"]):
        try:
            # 1. Fetch from source
            source_msg = await client.get_messages(data["source_chat"], curr_msg_id)
            
            if source_msg and source_msg.photo:
                # 2. Send to target
                await client.send_photo(
                    chat_id=data["target_chat"],
                    photo=source_msg.photo.file_id,
                    caption=f"✅ Video No: {data['start_num'] + i}\n\n📥 **Download Link:** {link}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download Now", url=link)]])
                )
                curr_msg_id += 1
                await asyncio.sleep(3) # Anti-flood delay
            else:
                await client.send_message(uid, f"⚠️ ID {curr_msg_id} par photo nahi mili. Skipping...")
                curr_msg_id += 1
        except Exception as e:
            await client.send_message(uid, f"❌ Posting Error: {e}")
            break

    await client.send_message(uid, "✨ **Tasks Completed! Saare posts line se ho gaye hain.**")
    user_data.pop(uid) # Clear session

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    keep_alive() # Starts Flask Web Server
    print("Bot is Running...")
    app.run()
