import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Quiet noisy HTTP logs
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Securely pulls token from Koyeb environment settings
TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Kote is alive and running 24/7 on the cloud! 🐾🔥")

def main():
    if not TOKEN:
        raise ValueError("No TOKEN environment variable configured!")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Kote bot is active and listening...")
    app.run_polling(drop_pending_updates=True, timeout=10)

if __name__ == "__main__":
    main()
import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

TOKEN = os.getenv("TOKEN")

# In-memory storage for pets (User ID -> Stats)
# In production later, you can hook this up to a database like SQLite or PostgreSQL
pet_data = {}

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

# --- PET COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_pet(user.id, user.first_name)
    await update.message.reply_text(
        f"Welcome to Kote Pet Simulator, {user.first_name}! 🐾🔥\n\n"
        "Your pet is born and ready on the cloud 24/7.\n"
        "Commands:\n"
        "/stats - Check Kote's status\n"
        "/feed - Feed your pet\n"
        "/play - Play with your pet\n"
        "/raid - Go on a meme coin raid for coins\n"
        "/leaderboard - View top wealthy pets"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    await update.message.reply_text(
        f"📊 **{pet['name']}'s Kote Stats**:\n"
        f"🥩 Hunger: {pet['hunger']}/100\n"
        f"🎾 Happiness: {pet['happiness']}/100\n"
        f"🪙 Coins: {pet['coins']}"
    )

async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    pet['hunger'] = min(100, pet['hunger'] + 20)
    await update.message.reply_text(f"Nom nom! 🥩 You fed Kote. Hunger is now {pet['hunger']}/100!")

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    pet['happiness'] = min(100, pet['happiness'] + 20)
    pet['coins'] += 10
    await update.message.reply_text(f"🎉 You played with Kote! Happiness is {pet['happiness']}/100 and you earned +10 coins!")

async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    earned = 50
    pet['coins'] += earned
    await update.message.reply_text(f"🚀 Kote went on a meme coin raid and successfully hauled in +{earned} coins! Total coins: {pet['coins']}")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not pet_data:
        await update.message.reply_text("No pets on the leaderboard yet!")
        return
    
    # Sort players by coins descending
    sorted_pets = sorted(pet_data.values(), key=lambda x: x['coins'], reverse=True)
    
    text = "🏆 **Kote Wealth Leaderboard** 🏆\n\n"
    for i, p in enumerate(sorted_pets[:10], 1):
        text += f"{i}. {p['name']} — 🪙 {p['coins']} coins\n"
    
    await update.message.reply_text(text)

def main():
    if not TOKEN:
        raise ValueError("No TOKEN environment variable found!")
    
    server_thread = threading.Thread(target=run_health_server, daemon=True)
    server_thread.start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Registering all handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("feed", feed))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("raid", raid))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    
    print("Kote simulator bot is running...")
    app.run_polling(drop_pending_updates=True, timeout=10)

if __name__ == "__main__":
    main()
