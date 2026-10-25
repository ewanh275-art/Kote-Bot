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
COOLDOWN = 3600
DAILY_CD = 86400

GIFS = {
    "start": [
        "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Z0ajV3cTV3bThqM2Z3M2Z3M2Z3M2Z3M2Z3M2Z3M2Z3JmY9Z19naWZfYnlfaWQmY3Q9Zw/3oriO0OEd9QIDdllqo/giphy.gif",
        "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif",
        "https://media.giphy.com/media/ICOgUNjpvO0PC/giphy.gif"
    ],
    "kote": [
        "https://media.giphy.com/media/ICOgUNjpvO0PC/giphy.gif",
        "https://media.giphy.com/media/GeimIFW00vOKY/giphy.gif",
        "https://media.giphy.com/media/13CoXPo7CojEDC/giphy.gif"
    ],
    "feed": [
        "https://media.giphy.com/media/ICOgUNjpvO0PC/giphy.gif",
        "https://media.giphy.com/media/GeimIFW00vOKY/giphy.gif",
        "https://media.giphy.com/media/12bjQ7uaduAPcc/giphy.gif"
    ],
    "play": [
        "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif",
        "https://media.giphy.com/media/13CoXPo7CojEDC/giphy.gif",
        "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHpucXB3bXVmNXE2M2Q1MWg0djhyODhxOHpucXB3bXVmNXE2M2Q1MSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/Lq0h93752f6J9tijrh/giphy.gif"
    ],
    "raid": [
        "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcnk0ZWRwYWlueGFnZXJreDN6djV0dG4zMWF0bzVvOXV2OGZsc3QybCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ico3bW6e6dMHe/giphy.gif",
        "https://media.giphy.com/media/Lq0h93752f6J9tijrh/giphy.gif",
        "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif"
    ]
}

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is live!")

def run_server():
    port = int(os.getenv("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()

def get_pet(uid, name):
    if uid not in pet_data:
        pet_data[uid] = {
            "name": name or "Player",
            "hunger": 50,
            "happy": 50,
            "coins": 100,
            "streak": 0,
            "last_login": 0
        }
    return pet_data[uid]

def get_timeLeft(last, duration):
    rem = int(duration - (time.time() - last))
    if rem <= 0:
        return "0"
    return f"{rem // 3600}h {(rem % 3600) // 60}m"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_pet(update.effective_user.id, update.effective_user.first_name)
    msg = "Welcome to Kote Pet Simulator! 🐾\nCommands: /kote /stats /daily /feed /play /raid /leaderboard"
    anim = random.choice(GIFS["start"])
    await update.message.reply_animation(animation=anim, caption=msg)

async def kote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pet = get_pet(update.effective_user.id, update.effective_user.first_name)
    msg = f"🐾 This is {pet['name']}! Keep him active to grow your meme bag."
    anim = random.choice(GIFS["kote"])
    await update.message.reply_animation(animation=anim, caption=msg)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pet = get_pet(update.effective_user.id, update.effective_user.first_name)
    event_str
