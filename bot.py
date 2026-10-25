import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

TOKEN = os.getenv("TOKEN")
pet_data = {}

GIFS = {
    "start": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Z0ajV3cTV3bThqM2Z3M2Z3M2Z3M2Z3M2Z3M2Z3M2Z3JmY9Z19naWZfYnlfaWQmY3Q9Zw/3oriO0OEd9QIDdllqo/giphy.gif",
    "feed": "https://media.giphy.com/media/GeimIFW00vOKY/giphy.gif",
    "play": "https://media.giphy.com/media/13CoXPo7CojEDC/giphy.gif",
    "raid": "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif"
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

# --- COMMAND FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_pet(user.id, user.first_name)
    caption = (
        f"Welcome to Kote Pet Simulator, {user.first_name}! 🐾🔥\n\n"
        "Commands:\n"
        "/stats - Check Kote's status\n"
        "/feed - Feed your pet\n"
        "/play - Open interactive play menu\n"
        "/raid - Go on a meme coin raid\n"
        "/leaderboard - View top wealthy pets"
    )
    await update.message.reply_animation(animation=GIFS["start"], caption=caption)

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
    caption = f"Nom nom! 🥩 You fed Kote. Hunger is now {pet['hunger']}/100!"
    await update.message.reply_animation(animation=GIFS["feed"], caption=caption)

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎾 Throw Ball", callback_data="play_ball")],
        [InlineKeyboardButton("🧶 Laser Pointer", callback_data="play_laser")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose how you want to interact with Kote:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    pet = get_pet(user.id, user.first_name)
    
    if query.data == "play_ball":
        pet['happiness'] = min(100, pet['happiness'] + 15)
        pet['coins'] += 10
        text = f"🎾 You threw the ball and Kote sprinted after it! Happiness: {pet['happiness']}/100, Coins: +10 🪙"
    elif query.data == "play_laser":
        pet['happiness'] = min(100, pet['happiness'] + 20)
        pet['coins'] += 15
        text = f"🔴 You flashed the laser pointer. Kote went wild! Happiness: {pet['happiness']}/100, Coins: +15 🪙"
    else:
        text = "Kote got distracted!"

    await query.edit_message_text(text=text)

async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    earned = 50
    pet['coins'] += earned
    caption = f"🚀 Kote went on a meme coin raid and hauled in +{earned} coins! Total: {pet['coins']}"
    await update.message.reply_animation(animation=GIFS["raid"], caption=caption)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not pet_data:
        await update.message.reply_text("No pets on the leaderboard yet!")
        return
    
    sorted_pets = sorted(pet_data.values(), key=lambda x: x['coins'], reverse=True)
    text = "🏆 **Kote Wealth Leaderboard** 🏆\n\n"
    for i, p in enumerate(sorted_pets[:10], 1):
        text += f"{i}. {p['name']} — 🪙 {p['coins']} coins\n"
    
    await update.message.reply_text(text)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(msg="Exception while handling an update:", exc_info=context.error)

def main():
    if not TOKEN:
        raise ValueError("No TOKEN environment variable found!")
    
    server_thread = threading.Thread(target=run_health_server, daemon=True)
    server_thread.start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("feed", feed))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("raid", raid))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    app.add_error_handler(error_handler)
    
    print("Kote simulator bot is running...")
    app.run_polling(drop_pending_updates=True, timeout=10)

if __name__ == "__main__":
    main()
