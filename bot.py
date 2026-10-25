import os
import time
import random
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
daily_cooldowns = {}
COOLDOWN_TIME = 3600  # 1 hour in seconds
DAILY_COOLDOWN = 86400  # 24 hours in seconds

GIFS = {
    "start": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Z0ajV3cTV3bThqM2Z3M2Z3M2Z3M2Z3M2Z3M2Z3M2Z3JmY9Z19naWZfYnlfaWQmY3Q9Zw/3oriO0OEd9QIDdllqo/giphy.gif",
    "feed": "https://media.giphy.com/media/ICOgUNjpvO0PC/giphy.gif",
    "play": "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif",
    "raid": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcnk0ZWRwYWlueGFnZXJreDN6djV0dG4zMWF0bzVvOXV2OGZsc3QybCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ico3bW6e6dMHe/giphy.gif",
    "kote": "https://media.giphy.com/media/ICOgUNjpvO0PC/giphy.gif"
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
            "coins": 100,
            "streak": 0,
            "last_login": 0
        }
    return pet_data[user_id]

def get_time_remaining(last_time, total_time=COOLDOWN_TIME):
    elapsed = time.time() - last_time
    remaining = int(total_time - elapsed)
    if remaining <= 0:
        return "0 minutes"
    hours = remaining // 3600
    mins = (remaining % 3600) // 60
    secs = remaining % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    if mins > 0:
        return f"{mins} min {secs} sec"
    return f"{secs} sec"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_pet(user.id, user.first_name)
    caption = (
        "Welcome to Kote Pet Simulator! 🐾🔥\n\n"
        "Commands:\n"
        "/kote - Look at Kote\n"
        "/stats - Check pet stats & events\n"
        "/daily - Claim daily login streak bonus 🎁\n"
        "/feed - Feed pet (1h cooldown)\n"
        "/play - Play with pet (1h cooldown)\n"
        "/raid - Meme coin raid 🚀\n"
        "/leaderboard - Top token holders 🏆"
    )
    await update.message.reply_animation(animation=GIFS["start"], caption=caption)

async def kote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    caption = f"🐾 Here is your meme coin mascot, {pet['name']}! Keep him active to maximize your token bag. 🪙"
    await update.message.reply_animation(animation=GIFS["kote"], caption=caption)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    
    # 20% chance for a random status event when checking stats
    event_text = ""
    if random.random() < 0.2:
        event = random.choice([
            ("💡 Kote stared into the matrix and sniffed out a hidden airdrop! +25 bonus coins.", 25),
            ("😴 Kote took a long nap and dreamed about bull markets. Peaceful vibes!", 0),
            ("🔍 Kote inspected your portfolio and found loose change down the couch cushions! +10 coins.", 10)
        ])
        pet['coins'] += event[1]
        event_text = f"\n\n✨ **Random Event**: {event[0]}"

    text = (
        f"📊 **{pet['name']}'s Stats**:\n"
        f"🥩 Hunger: {pet['hunger']}/100\n"
        f"🎾 Happiness: {pet['happiness']}/100\n"
        f"🔥 Daily Streak: {pet['streak']} days\n"
        f"🪙 Total Token Score: {pet['coins']:,}{event_text}"
    )
    await update.message.reply_text(text)

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    current_time = time.time()
    
    last_login = pet['last_login']
    # If more than 48 hours passed, reset streak
    if last_login > 0 and (current_time - last_login) > (DAILY_COOLDOWN * 2):
        pet['streak'] = 0

    if user.id in daily_cooldowns:
        elapsed = current_time - daily_cooldowns[user.id]
        if elapsed < DAILY_COOLDOWN:
            timeLeft = get_time_remaining(daily_cooldowns[user.id], DAILY_COOLDOWN)
            await update.message.reply_text(f"⏳ You already claimed your daily bonus! Come back in {timeLeft}.")
            return

    daily_cooldowns[user.id] = current_time
    pet['last_login'] = current_time
    pet['streak'] += 1
    
    reward = 50 * pet['streak']
    pet['coins'] += reward
    
    await update.message.reply_text(
        f"🎁 **Daily Streak Claim
