import telebot
import requests
from bs4 import BeautifulSoup
from flask import Flask
import threading
import os

# Loeb tokeni pilveserveri seadetest
TOKEN = os.environ.get('TELEGRAM_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Loome väikese veebiserveri, et pilveteenus (Render) rahule jääks
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot on elus ja töötab pilves!"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    tervitus = (
        "Hei! Olen sinu isiklik assistent.\n\n"
        "Kasuta neid käsklusi:\n"
        "⚡ /elekter - Praegune elektri börsihind Soomes\n"
        "⛽ /diisel - Diisli hinnad Hyvinkää tanklates"
    )
    bot.reply_to(message, tervitus)

@bot.message_handler(commands=['elekter'])
def get_elekter(message):
    try:
        url = "https://dashboard.elering.ee/api/nps/price/FI/current"
        res = requests.get(url)
        data = res.json()
        hind_mwh = data['data'][0]['price']
        hind_kwh = (hind_mwh / 10) * 1.255
        bot.reply_to(message, f"⚡ **Praegune elektrihind Soomes:**\n{hind_kwh:.2f} c/kWh (koos 25.5% KM-ga)")
    except Exception as e:
        bot.reply_to(message, "Vabandust, elektrihinna laadimine hetkel ebaõnnestus.")

@bot.message_handler(commands=['diisel'])
def get_diisel(message):
    bot.reply_to(message, "🔍 Otsin Hyvinkää diislihindu, palun oota hetk...")
    try:
        url = "https://polttoaine.net/Hyvink%C3%A4%C3%A4"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        vastus = "⛽ **Diisli hinnad Hyvinkääl:**\n\n"
        leitud = False
        rows = soup.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                nimi = cols[0].text.strip()
                diisel_hind = cols[3].text.strip()
                if any(x in nimi for x in ["ABC", "Neste", "St1", "Teboil", "Shell"]) and diisel_hind:
                    if diisel_hind.replace('.', '', 1).isdigit():
                        vastus += f"📍 {nimi}\n💶 {diisel_hind} €/l\n\n"
                        leitud = True
        if not leitud:
            vastus = "Kahjuks ei suutnud ma praegu värskeid tanklate hindu leida."
        bot.reply_to(message, vastus)
    except Exception as e:
        bot.reply_to(message, "Viga diislihindade laadimisel. Veebilehe struktuur võib olla muutunud.")

# Funktsioon boti jooksutamiseks
def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    # Käivitame Telegrami boti eraldi taustalõimes
    threading.Thread(target=run_bot).start()
    # Käivitame veebiserveri põhilõimes
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)