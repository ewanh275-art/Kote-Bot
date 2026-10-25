import os
import time
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

TOKEN = os.getenv("TOKEN")
pet_data = {}

feed_cooldowns = {}
play_cooldowns = {}
COOLDOWN_TIME = 3600  # 1 hour in seconds

GIFS = {
    "start": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Z0ajV3cTV3bThqM2Z3M2Z3M2Z3M2Z3M2Z3M2Z3M2Z3JmY9Z19naWZfYnlfaWQmY3Q9Zw/3oriO0OEd9QIDdllqo/giphy.gif",
    "feed": "https://media.giphy.com/media/12bjQ7uaduAPcc/giphy.gif",
    "play": "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif",
    "raid": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHpucXB3bXVmNXE2M2Q1MWg0djhyODhxOHpucXB3bXVmNXE2M2Q1MSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/Lq0h93752f6J9tijrh/giphy.gif"
}

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Kote Bot is live 24/7!")

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

def get_pet(user_id, username):
    if user_id not in pet_data:
        pet_data[user_id] = {
            "name": username or "Player",
            "hunger": 50,
            "happiness": 50,
            "coins": 100
        }
    return pet_data[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_pet(user.id, user.first_name)
    caption = "Welcome to Kote Pet Simulator! 🐾\nCommands:\n/stats\n/feed (1h cooldown)\n/play (1h cooldown)\n/raid\n/leaderboard"
    await update.message.reply_animation(animation=GIFS["start"], caption=caption)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    text = f"📊 {pet['name']}'s Stats:\nHunger: {pet['hunger']}/100\nHappiness: {pet['happiness']}/100\nCoins: {pet['coins']}"
    await update.message.reply_text(text)

async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_time = time.time()
    if user_id in feed_cooldowns:
        elapsed = current_time - feed_cooldowns[user_id]
        if elapsed < COOLDOWN_TIME:
            remaining = int((COOLDOWN_TIME - elapsed) / 60)
            await update.message.reply_text(f"⏳ Kote is still full! Feed again in {remaining} minutes.")
            return
    keyboard = [
        [InlineKeyboardButton("🥩 Steak (+25)", callback_data="feed_steak")],
        [InlineKeyboardButton("🐟 Fish (+15)", callback_data="feed_fish")]
    ]
    await update.message.reply_text("Choose food:", reply_markup=InlineKeyboardMarkup(keyboard))

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_time = time.time()
    if user_id in play_cooldowns:
        elapsed = current_time - play_cooldowns[user_id]
        if elapsed < COOLDOWN_TIME:
            remaining = int((COOLDOWN_TIME - elapsed) / 60)
            await update.message.reply_text(f"⏳ Kote is resting! Play again in {remaining} minutes.")
            return
    keyboard = [
        [InlineKeyboardButton("🎾 Ball (+15)", callback_data="play_ball")],
        [InlineKeyboardButton("🔴 Laser (+20)", callback_data="play_laser")]
    ]
    await update.message.reply_text("Choose activity:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    pet = get_pet(user_id, query.from_user.first_name)
    current_time = time.time()
    
    if query.data.startswith("feed_"):
        if user_id in feed_cooldowns and current_time - feed_cooldowns[user_id] < COOLDOWN_TIME:
            await query.edit_message_text(text="⏳ Too soon! Kote is still digesting.")
            return
        feed_cooldowns[user_id] = current_time
        if query.data == "feed_steak":
            pet['hunger'] = min(100, pet['hunger'] + 25)
        elif query.data == "feed_fish":
            pet['hunger'] = min(100, pet['hunger'] + 15)
        await query.edit_message_text(text=f"Nom nom! Hunger: {pet['hunger']}/100")
        await context.bot.send_animation(chat_id=query.message.chat_id, animation=GIFS["feed"])
        
    elif query.data.startswith("play_"):
        if user_id in play_cooldowns and current_time - play_cooldowns[user_id] < COOLDOWN_TIME:
            await query.edit_message_text(text="⏳ Too soon! Kote needs a nap.")
            return
        play_cooldowns[user_id] = current_time
        if query.data == "play_ball":
            pet['happiness'] = min(100, pet['happiness'] + 15)
            pet['coins'] += 10
        elif query.data == "play_laser":
            pet['happiness'] = min(100, pet['happiness'] + 20)
            pet['coins'] += 15
        await query.edit_message_text(text=f"Played! Happiness: {pet['happiness']}/100, Coins: {pet['coins']}")
        await context.bot.send_animation(chat_id=query.message.chat_id, animation=GIFS["play"])

async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    pet['coins'] += 50
    await update.message.reply_animation(animation=GIFS["raid"], caption=f"Raid successful! +50 coins. Total: {pet['coins']}")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not pet_data:
        await update.message.reply_text("No pets yet!")
        return
    text = "🏆 Leaderboard 🏆\n\n"
    for p in pet_data.values():
        text += f"{p['name']} — 🪙 {p['coins']} coins\n"
    await update.message.reply_text(text)

def main():
    if not TOKEN:
        raise ValueError("TOKEN missing")
    threading.Thread(target=run_health_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("feed", feed))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("raid", raid))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling(drop_pending_updates=True, timeout=10)

if __name__ == "__main__":
    main()
