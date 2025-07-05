import telebot
from telebot import types
import requests
import random
import os
import threading
from flask import Flask

BOT_TOKEN = os.environ.get('BOT_TOKEN')
VOTE_DB = {}
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

@app.route('/healthz')
def healthz():
    return 'OK', 200

@bot.message_handler(commands=['start'])
def start(message):
    caption = (
        "👋 Hello! I’m SPAMEK — the shitcoin hunter patrolling Solana.\n\n"
        "🔍 I scan the blockchain and detect token toxicity before it burns you.\n\n"
        "🛠 Type /help to see what I can do.\n\n"
        "🥫 SCAN ACTIVE."
    )
    try:
        with open("spamek_start.png", "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption=caption)
    except Exception:
        bot.send_message(message.chat.id, caption)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    msg = (
        "📖 *Available Commands:*\n\n"
        "🔍 `/scan [mint address]`\n"
        "🗳 `/voting`\n"
        "🎞 `/gif`\n"
        "🔥 `/topmemes`\n"
        "ℹ️ `/about`\n"
        "🧠 `/features`"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['features'])
def features(message):
    msg = (
        "🧠 *Advanced Features — COMING SOON:*\n\n"
        "📊 `/liquidityprofile` — LP depth & volatility maps\n"
        "🔥 `/heatmap` — Real-time token velocity tracker\n"
        "🧠 `/aisignals` — Predictive AI alerts: pump/dump risk\n"
        "🤖 `/aianalysis` — Neural scan of token ecosystem\n"
        "📡 `/botnetwatch` — Detect suspected trading bots\n"
        "🧬 `/c3dsymmetry` — Adaptive learning module that refines toxicity scoring per token type\n"
        "🎖 `/badge` — Trust Score badge: Green / Yellow / Red\n"
        "☢️ `/alertlevel` — Global market toxicity meter"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

@bot.message_handler(commands=['about'])
def about(message):
    text = (
        "🧠 *ABOUT SPAMEK*\n\n"
        "🎯 Mission: Detect token toxicity across the Solana jungle\n"
        "📡 Powered by DEXScreener API\n"
        "🧬 Version: 3.6 — DEX Intelligence Protocol\n\n"
        "⚙️ *SPAMEK Intelligence Status:*\n"
        "Mode: `Autonomous Scan Patrol`\n"
        "Modules active: `Emotion`, `DexScan`, `Voting`\n"
        "🔜 Coming: `Heatmap`, `AI Signals`, `C3D Symmetry`"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['scan'])
def scan(message):
    parts = message.text.strip().split()
    if len(parts) != 2:
        bot.send_message(message.chat.id, "❗ Usage: /scan [mint address]")
        return

    mint = parts[1]
    url = f"https://api.dexscreener.com/latest/dex/search?q={mint}"

    try:
        res = requests.get(url, timeout=5)
        data = res.json().get("pairs", [])
        if not data:
            bot.send_message(message.chat.id, "🚫 Token not found.")
            return

        pair = data[0]
        name = pair.get("baseToken", {}).get("name", "Unknown")
        symbol = pair.get("baseToken", {}).get("symbol", "N/A")
        price = float(pair.get("priceUsd", 0))
        liquidity = float(pair.get("liquidity", {}).get("usd", 0))
        volume = float(pair.get("volume", {}).get("h24", 0))
        fdv = float(pair.get("fdv", 0))
        url_link = pair.get("url", "https://dexscreener.com")

        score = 0
        if liquidity < 1000: score += 40
        elif liquidity < 5000: score += 25
        if volume > 100000: score += 20
        if fdv > 1_000_000_000: score += 15
        toxicity = min(100, max(5, score))

        if toxicity <= 33:
            img = "spamek_happy.png"
            caption = "😄 CLEAN OK."
        elif toxicity <= 66:
            img = "spamek_neutral.png"
            caption = "😐 SUSPICIOUS ACTIVITY."
        else:
            img = "spamek_angry.png"
            caption = "😡 TOXIC ZONE!"

        msg = (
            "🧪 *SCAN REPORT* — DEXScreener Module 🧪\n\n"
            f"📛 *Name*: {name} ({symbol})\n"
            f"🔗 *Mint*: `{mint}`\n"
            f"💰 *Price*: ${round(price, 8)}\n"
            f"🧃 *Liquidity*: ${int(liquidity):,}\n"
            f"📈 *24h Volume*: ${int(volume):,}\n"
            f"🏷 *FDV*: ${int(fdv):,}\n"
            f"☣️ *Toxicity Score*: {toxicity}%\n\n"
            f"🔍 [View on DEXScreener]({url_link})\n"
            f"🧬 *Emotional Profile*: {caption}"
        )

        bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        if os.path.isfile(img):
            with open(img, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=caption)

        VOTE_DB[mint] = {'yes': 0, 'no': 0}

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Scan error: {e}")

@bot.message_handler(commands=['voting'])
def voting(message):
    if not VOTE_DB:
        bot.send_message(message.chat.id, "ℹ️ You need to scan a token before voting.")
        return
    token = list(VOTE_DB.keys())[-1]
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ BAN", callback_data=f"vote_yes:{token}"),
        types.InlineKeyboardButton("❌ PASS", callback_data=f"vote_no:{token}")
    )
    bot.send_message(message.chat.id, f"🗳 Voting for token: {token}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def handle_vote(call):
    try:
        vote_type, token = call.data.split(":")
        if token not in VOTE_DB:
            return
        choice = vote_type.replace("vote_", "")
        VOTE_DB[token][choice] += 1
        counts = VOTE_DB[token]
        bot.send_message(call.message.chat.id, f"🗳 Results so far:\n✅ BAN: {counts['yes']} | ❌ PASS: {counts['no']}")
    except:
        pass

@bot.message_handler(commands=['gif'])
def gif(message):
    gifs = [f for f in os.listdir() if f.endswith('.gif')]
    if not gifs:
        bot.send_message(message.chat.id, "No GIFs found.")
        return
    file = random.choice(gifs)
    with open(file, 'rb') as gif_file:
        bot.send_animation(message.chat.id, gif_file)

@bot.message_handler(commands=['topmemes'])
def topmemes(message):
    msg = (
        "🔥 *Top Meme Tokens:*\n\n"
        "1. BONK 🚀\n"
        "2. DOGWIFHAT 😎\n"
        "3. MOTHER 💅\n"
        "4. POPCAT 🐱\n"
        "5. SHNURK ❓"
    )
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

def run_bot():
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ BOT ERROR: {e}")

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=10000)

