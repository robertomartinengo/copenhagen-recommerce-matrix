import os
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from pdf_generator import generate_district_pdf

API_URL = os.getenv("API_URL", "http://localhost:8000")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        "♻️ *Copenhagen Re-Commerce Matrix Bot*\n\n"
        "Ciao! Ti aiuto a trovare la **zona perfetta** a Copenhagen per aprire il tuo "
        "negozio di moda usata, punto di raccolta o pop-up store.\n\n"
        "Seleziona un'opzione qui sotto:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🏆 Qual è la Zona Top?", callback_data="top_zone")],
        [InlineKeyboardButton("📋 Lista Distretti Promettenti", callback_data="list_zones")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
                    f"🟢 *La Zona Migliore in Assoluto è {district_name}!*\n\n"
                    f"📊 *Punteggio CPI:* `{cpi:.1f} / 10`\n"
                    f"👥 *Target Gen Z:* `{gen_z_text}`\n"
                    f"💡 *Perché conviene:* Altissimo afflusso di materiale tessile usabile "
                    f"e un'ampia community di giovani acquirenti.\n\n"
                    f"Vuoi il *Report Executive PDF* completo per la tua banca/investitori?"
                )
                
                keyboard = [
                    [InlineKeyboardButton(f"📄 Scarica Report PDF ({district_name})", callback_data=f"pdf_{district_name}")]
                ]
                await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.edit_message_text(f"⚠️ Impossibile connettersi al backend: {e}")

    elif query.data.startswith("pdf_"):
        district_name = query.data.replace("pdf_", "")
        try:
            res = requests.get(f"{API_URL}/zones", timeout=5)
            if res.status_code == 200:
                zones = [z for z in res.json() if z["name"] == district_name]
                if zones:
                    target_zone = zones[0]
                    pdf_file = f"Executive_Report_{district_name.replace(' ', '_')}.pdf"
                    generate_district_pdf(target_zone, filename=pdf_file)
                    
                    if os.path.exists(pdf_file):
                        await query.message.reply_document(
                            document=open(pdf_file, "rb"),
                            filename=pdf_file,
                            caption=f"📄 Ecco il tuo Report Executive B2B per **{district_name}**!",
                            parse_mode="Markdown"
                        )
                        return
        except Exception as e:
            await query.message.reply_text(f"⚠️ Errore nella generazione del PDF: {e}")


def main() -> None:
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("⚠️ Inserisci un TELEGRAM_BOT_TOKEN valido nel file .env per avviare il Bot Telegram.")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("🤖 Bot Telegram avviato in ascolto...")
    app.run_polling()


if __name__ == "__main__":
    main()