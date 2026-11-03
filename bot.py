import os
import asyncio
import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

load_dotenv(override=True)

API_URL = os.getenv("API_URL", "http://localhost:8000")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


async def start_command(update: Update, context) -> None:
    welcome_text = (
        "♻️ *Copenhagen Re-Commerce Matrix Bot*\n\n"
        "Ciao! Ti aiuto a trovare la **zona perfetta** a Copenhagen per aprire il tuo "
        "negozio di moda usata, punto di raccolta o pop-up store.\n\n"
        "Seleziona un'opzione qui sotto:"
    )
    keyboard = [
        [InlineKeyboardButton("🎯 Qual è la Zona Top?", callback_data="top_zone")],
        [InlineKeyboardButton("📋 Lista Distretti Promettenti", callback_data="list_zones")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


async def handle_callback(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "top_zone":
        try:
            res = requests.get(f"{API_URL}/zones", timeout=5)
            if res.status_code == 200 and len(res.json()) > 0:
                top = res.json()[0]
                district_name = top["name"]
                cpi = top["cpi_score"]
                gen_z = top.get("population_gen_z", top.get("gen_z_percentage", 0))
                gen_z_text = f"{gen_z:,.0f} residenti" if gen_z > 100 else f"{gen_z:.1f}%"
                
                msg = (
                    f"🏆 *La Zona Migliore in Assoluto è {district_name}!*\n\n"
                    f"📊 *Punteggio CPI:* `{cpi:.1f} / 10`\n"
                    f"👥 *Target Gen Z:* `{gen_z_text}`\n"
                    f"💡 *Perché conviene:* Altissimo afflusso di materiale tessile usabile "
                    f"e un'ampia community di giovani acquirenti.\n\n"
                    f"Vuoi il *Report Executive PDF* completo per la tua banca/investitori?"
                )
                keyboard = [
                    [InlineKeyboardButton(f"📄 Scarica Report PDF ({district_name})", callback_data=f"pdf_{district_name}")],
                    [InlineKeyboardButton("⬅️ Torna al Menu", callback_data="menu")]
                ]
                await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.edit_message_text(f"⚠️ Impossibile connettersi al backend: {e}")

    elif query.data == "list_zones":
        try:
            res = requests.get(f"{API_URL}/zones", timeout=5)
            if res.status_code == 200:
                zones = res.json()[:5]
                msg = "📋 *Top 5 Distretti per Potenziale Re-Commerce (CPI):*\n\n"
                keyboard = []
                for idx, z in enumerate(zones, start=1):
                    msg += f"*{idx}. {z['name']}* — CPI: `{z['cpi_score']:.1f}`\n"
                    keyboard.append([InlineKeyboardButton(f"📄 PDF {z['name']}", callback_data=f"pdf_{z['name']}")])
                keyboard.append([InlineKeyboardButton("⬅️ Torna al Menu", callback_data="menu")])
                await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.edit_message_text(f"⚠️ Errore nel recupero della lista: {e}")

    elif query.data == "menu":
        welcome_text = "♻️ *Copenhagen Re-Commerce Matrix Bot*\n\nSeleziona un'opzione dal menu principale:"
        keyboard = [
            [InlineKeyboardButton("🎯 Qual è la Zona Top?", callback_data="top_zone")],
            [InlineKeyboardButton("📋 Lista Distretti Promettenti", callback_data="list_zones")]
        ]
        await query.edit_message_text(welcome_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def start_telegram_bot():
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("⚠️ [BOT] TELEGRAM_BOT_TOKEN non trovato tra le variabili d'ambiente!", flush=True)
            return

        print("🤖 [BOT] Inizializzazione Bot Telegram in corso...", flush=True)
        app = Application.builder().token(token).build()
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CallbackQueryHandler(handle_callback))

        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        print("✅ [BOT] Bot Telegram avviato con successo e in ascolto 24/7!", flush=True)
    except Exception as e:
        print(f"❌ [BOT] Errore critico durante l'avvio del bot: {e}", flush=True)