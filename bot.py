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

# --- DEDICATED GIFS FOR EACH ACTION ---
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
        "/feed - Open interactive feeding menu 🥩\n"
        "/play - Open interactive play menu 🎾\n"
        "/raid - Go on a meme coin raid 🚀\n"
        "/leaderboard - View top wealthy pets 🏆"
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

# --- INTERACTIVE FEED COMMAND ---
async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🥩 Juicy Steak (+25 Hunger)", callback_data="feed_steak")],
        [InlineKeyboardButton("🐟 Fresh Fish (+15 Hunger)", callback_data="feed_fish")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose what to feed Kote:", reply_markup=reply_markup)

# --- INTERACTIVE PLAY COMMAND ---
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎾 Throw Ball (+15 Happy)", callback_data="play_ball")],
        [InlineKeyboardButton("🧶 Laser Pointer (+20 Happy)", callback_data="play_laser")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose how you want to play with Kote:", reply_markup=reply_markup)

# --- UNIFIED BUTTON HANDLER FOR FEEDING & PLAYING ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    pet = get_pet(user.id, user.first_name)
    
    # Handle Feeding Choices
    if query.data == "feed_steak":
        pet['hunger'] = min(100, pet['hunger'] + 25)
        text = f"🥩 Nom nom! Kote devoured the steak. Hunger is now {pet['hunger']}/100!"
        await query.edit_message_text(text=text)
        await context.bot.send_animation(chat_id=query.message.chat_id, animation=GIFS["feed"])
        
    elif query.data == "feed_fish":
        pet['hunger'] = min(100, pet['hunger'] + 15)
        text = f"🐟 Slurp! Kote enjoyed the fish. Hunger is now {pet['hunger']}/100!"
        await query.edit_message_text(text=text)
        await context.bot.send_animation(chat_id=query.message.chat_id, animation=GIFS["feed"])
        
    # Handle Playing Choices
    elif query.data == "play_ball":
        pet['happiness'] = min(100, pet['happiness'] + 15)
        pet['coins'] += 10
        text = f"🎾 You threw the ball! Happiness: {pet['happiness']}/100, Coins: +10 🪙"
        await query.edit_message_text(text=text)
        await context.bot.send_animation(chat_id=query.message.chat_id, animation=GIFS["play"])
        
    elif query.data == "play_laser":
        pet['happiness'] = min(100, pet['happiness'] + 20)
        pet['coins'] += 15
        text = f"🔴 Laser chaos! Happiness: {pet['happiness']}/100, Coins: +15 🪙"
        await query.edit_message_text(text=text)
        await context.bot.send_animation(chat_id=query.message.chat_id, animation=GIFS["play"])

async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    pet = get_pet(user.id, user.first_name)
    earned = 50
    pet['coins'] += earned
    caption = f"🚀 Kote went on a meme coin raid and hauled in +{earned} coins! Total: {pet['coins']}"
    await update.message.reply_animation(animation=GIFS["raid"], caption=caption)

async def leaderboard(update: Update, context
