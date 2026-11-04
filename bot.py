import os
import asyncio
import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from pdf_generator import generate_executive_pdf

load_dotenv(override=True)

API_URL = os.getenv("API_URL", "http://127.0.0.1:10000")


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

    # FIX: "if" al posto di "elif" per evitare SyntaxError
    if query.data == "top_zone":
        keyboard = [
            [InlineKeyboardButton("💎 Vintage Premium & Lusso", callback_data="calc_top:vintage_premium")],
            [InlineKeyboardButton("⚖️ Kilo Sale & Thrift Massivo", callback_data="calc_top:kilo_sale")],
            [InlineKeyboardButton("✂️ Upcycling & Laboratorio", callback_data="calc_top:upcycling")],
            [InlineKeyboardButton("🛍️ Curated Vintage & Pop-Up", callback_data="calc_top:curated_vintage")],
            [InlineKeyboardButton("⬅️ Torna al Menu", callback_data="menu")]
        ]
        text = "🎯 *Seleziona il tuo Modello di Business*\n\nIl punteggio CPI verrà ricalcolato ricalibrando i pesi su misura per la tua attività:"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("calc_top:"):
        b_type = query.data.split(":")[1]
        
        try:
            # FIX: Uso di httpx asincrono anziché requests
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{API_URL}/zones/top?business_type={b_type}", timeout=10.0)
            
            if res.status_code == 200:
                data = res.json()
                name = data.get("name", "N/A")
                cpi = float(data.get("cpi_score", 0))
                gen_z = data.get("population_gen_z", 0)
                profile_label = data.get("business_profile_label", b_type)
                
                text = (
                    f"🏆 *TOP ZONA CONSIGLIATA*\n"
                    f"Per: *{profile_label}*\n\n"
                    f"📍 *Distretto:* {name}\n"
                    f"📊 *CPI Personalizzato:* {cpi:.2f} / 10.0\n"
                    f"👥 *Target Gen Z:* {gen_z:,.0f} residenti\n\n"
                    f"Scarica il report PDF per l'analisi completa:"
                )
                
                keyboard = [
                    [InlineKeyboardButton("📄 Genera Report PDF", callback_data=f"pdf:{name}:{b_type}")],
                    [InlineKeyboardButton("⬅️ Cambia Modello", callback_data="top_zone")],
                    [InlineKeyboardButton("🏠 Menu Principale", callback_data="menu")]
                ]
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.edit_message_text(f"⚠️ Errore nel calcolo del CPI dinamico: {e}")

    elif query.data == "list_zones":
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{API_URL}/zones", timeout=10.0)

            if res.status_code == 200:
                zones = res.json()
                zones_sorted = sorted(zones, key=lambda x: float(x.get("cpi_score", 0)), reverse=True)
                zones = zones_sorted[:5]
                msg = "📋 *Top 5 Distretti per Potenziale Re-Commerce (CPI):*\n\n"
                keyboard = []
                for idx, z in enumerate(zones, start=1):
                    cpi_val = float(z.get('cpi_score', 0))
                    msg += f"*{idx}. {z['name']}* — CPI: `{cpi_val:.1f}`\n"
                    keyboard.append([InlineKeyboardButton(f"📄 PDF {z['name']}", callback_data=f"pdf:{z['name']}:curated_vintage")])
                keyboard.append([InlineKeyboardButton("⬅️ Torna al Menu", callback_data="menu")])
                await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.edit_message_text(f"⚠️ Errore nel recupero della lista: {e}")

    # FIX: Gestore unificato per il download PDF (supporta sia pdf_ che pdf:)
    elif query.data.startswith("pdf:") or query.data.startswith("pdf_"):
        parts = query.data.replace("pdf_", "").replace("pdf:", "").split(":")
        district_name = parts[0]
        b_type = parts[1] if len(parts) > 1 else "curated_vintage"
        
        await query.message.reply_text(f"⏳ Generazione del Report PDF per *{district_name}* in corso...", parse_mode="Markdown")
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{API_URL}/zones?business_type={b_type}", timeout=10.0)
            
            if res.status_code == 200:
                zones = res.json()
                zone_data = next((z for z in zones if z["name"].lower() == district_name.lower()), None)
                if not zone_data:
                    zone_data = zones[0]

                pdf_filename = f"Executive_Report_{district_name.replace(' ', '_')}.pdf"
                generate_executive_pdf(zone_data, filename=pdf_filename)

                with open(pdf_filename, "rb") as doc:
                    await query.message.reply_document(
                        document=doc,
                        filename=pdf_filename,
                        caption=f"📄 *Report Executive B2B:* {district_name}\nPronto per investitori e partner finanziari.",
                        parse_mode="Markdown"
                    )

                if os.path.exists(pdf_filename):
                    os.remove(pdf_filename)
        except Exception as e:
            await query.message.reply_text(f"⚠️ Errore durante la generazione del PDF: {e}")

    elif query.data == "menu":
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

if __name__ == "__main__":
    asyncio.run(start_telegram_bot())