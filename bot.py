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
    "start": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Z0ajV3cTV3bThqM2Z3M2Z3M2Z3M2Z3M2Z3M2Z3M2Z3JmY9Z19naWZfYnlfaWQmY3Q9Zw/3oriO0OEd9QIDdllqo/giphy.gif",
    "feed": "https://media.giphy.com/media/ICOgUNjpvO0PC/giphy.gif",
    "play": "https://media.giphy.com/media/JIX9t2j0ZTN9S/giphy.gif",
    "raid": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExcnk0ZWRwYWlueGFnZXJreDN6djV0dG4zMWF0bzVvOXV2OGZsc3QybCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ico3bW6e6dMHe/giphy.gif",
    "kote": "https://media.giphy.com/media/ICOgUNjpvO0PC/giphy.gif"
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
    anim = GIFS["start"]
    await update.message.reply_animation(animation=anim, caption=msg)

async def kote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pet = get_pet(update.effective_user.id, update.effective_user.first_name)
    msg = f"🐾 This is {pet['name']}! Keep him active to grow your meme bag."
    anim = GIFS["kote"]
    await update.message.reply_animation(animation=anim, caption=msg)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pet = get_pet(update.effective_user.id, update.effective_user.first_name)
    event_str = ""
    if random.random() < 0.2:
        bonus = random.choice([10, 25, 50])
        pet['coins'] += bonus
        event_str = f"\n\n✨ Event: Found wallet! +{bonus} coins."
    msg = f"📊 Stats for {pet['name']}:\nHunger: {pet['hunger']}/100\nHappiness: {pet['happy']}/100\nStreak: {pet['streak']}d\nScore: {pet['coins']:,}{event_str}"
    await update.message.reply_text(msg)

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pet = get_pet(uid, update.effective_user.first_name)
    now = time.time()
    if uid in daily_cooldowns and now - daily_cooldowns[uid] < DAILY_CD:
        t = get_timeLeft(daily_cooldowns[uid], DAILY_CD)
        await update.message.reply_text(f"⏳ Come back in {t} for daily reward!")
        return
    if pet['last_login'] > 0 and now - pet['last_login'] > (DAILY_CD * 2):
        pet['streak'] = 0
    daily_cooldowns[uid] = now
    pet['last_login'] = now
    pet['streak'] += 1
    reward = 50 * pet['streak']
    pet['coins'] += reward
    msg = f"🎁 Daily Claimed!\nStreak: {pet['streak']} days\nReward: +{reward:,} coins!\nTotal Score: {pet['coins']:,}"
    await update.message.reply_text(msg)

async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in feed_cooldowns and time.time() - feed_cooldowns[uid] < COOLDOWN:
        t = get_timeLeft(feed_cooldowns[uid], COOLDOWN)
        await update.message.reply_text(f"⏳ Full! Feed again in {t}.")
        return
    b1 = InlineKeyboardButton("🥩 Steak", callback_data="feed_steak")
    b2 = InlineKeyboardButton("🐟 Fish", callback_data="feed_fish")
    kb = InlineKeyboardMarkup([[b1, b2]])
    await update.message.reply_text("Choose food:", reply_markup=kb)

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in play_cooldowns and time.time() - play_cooldowns[uid] < COOLDOWN:
        t = get_timeLeft(play_cooldowns[uid], COOLDOWN)
        await update.message.reply_text(f"⏳ Resting! Play again in {t}.")
        return
    b1 = InlineKeyboardButton("🎾 Ball", callback_data="play_ball")
    b2 = InlineKeyboardButton("🔴 Laser", callback_data="play_laser")
    kb = InlineKeyboardMarkup([[b1, b2]])
    await update.message.reply_text("Choose activity:", reply_markup=kb)

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    pet = get_pet(uid, query.from_user.first_name)
    now = time.time()
    chat_id = query.message.chat_id
    
    if query.data.startswith("feed_"):
        if uid in feed_cooldowns and now - feed_cooldowns[uid] < COOLDOWN:
            await query.edit_message_text("⏳ Too soon!")
            return
        feed_cooldowns[uid] = now
        gain = random.randint(10, 30)
        pet['hunger'] += gain
        if pet['hunger'] > 100:
            pet['hunger'] = 100
        await query.edit_message_text(f"🥩 Fed! +{gain} Hunger (Total: {pet['hunger']}/100)")
        anim = GIFS["feed"]
        await context.bot.send_animation(chat_id=chat_id, animation=anim)
        
    elif query.data.startswith("play_"):
        if uid in play_cooldowns and now - play_cooldowns[uid] < COOLDOWN:
            await query.edit_message_text("⏳ Too soon!")
            return
        play_cooldowns[uid] = now
        h_gain = random.randint(10, 25)
        c_gain = random.randint(5, 20)
        pet['happy'] += h_gain
        if pet['happy'] > 100:
            pet['happy'] = 100
        pet['coins'] += c_gain
        await query.edit_message_text(f"🎉 Played! +{h_gain} Happy, +{c_gain} Coins (Score: {pet['coins']:,})")
        anim = GIFS["play"]
        await context.bot.send_animation(chat_id=chat_id, animation=anim)

async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pet = get_pet(update.effective_user.id, update.effective_user.first_name)
    roll = random.random()
    if roll < 0.15:
        loss = random.randint(20, 50)
        pet['coins'] = max(0, pet['coins'] - loss)
        msg = f"⚠️ Rug-pull! Lost -{loss} coins. Score: {pet['coins']:,}"
        await update.message.reply_animation(animation=GIFS["raid"], caption=msg)
    elif roll > 0.85:
        win = random.randint(300, 600)
        pet['coins'] += win
        msg = f"💎 JACKPOT! Won +{win:,} coins! Score: {pet['coins']:,}"
        await update.message.reply_animation(animation=GIFS["raid"], caption=msg)
    else:
        gain = random.randint(50, 200)
        pet['coins'] += gain
        msg = f"🚀 Raid success! +{gain:,} coins. Score: {pet['coins']:,}"
        await update.message.reply_animation(animation=GIFS["raid"], caption=msg)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not pet_data:
        await update.message.reply_text("No pets yet!")
        return
    top = sorted(pet_data.values(), key=lambda x: x['coins'], reverse=True)[:10]
    text = "🏆 **Unlimited Token Leaderboard** 🏆\n\n"
    for i, p in enumerate(top, 1):
        text += f"{i}. {p['name']} — 🪙 {p['coins']:,} (🔥 {p['streak']}d)\n"
    await update.message.reply_text(text)

def main():
    if not TOKEN:
        raise ValueError("TOKEN missing")
    threading.Thread(target=run_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kote", kote))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("feed", feed))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("raid", raid))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(buttons))
    app.run_polling(drop_pending_updates=True, timeout=10)

if __name__ == "__main__":
    main()
