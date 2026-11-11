import html
import os
import re
import tempfile
from datetime import datetime, timezone
from supabase import create_client, Client
import asyncio
import httpx
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from pdf_generator import generate_executive_pdf, _sanitize_filename
from privacy import PRIVACY_NOTICE_URL, PRIVACY_NOTICE_VERSION

load_dotenv(override=True)


def _md_to_html(text: str) -> str:
    """Converte i semplici marcatori Markdown (*grassetto*, `codice`) in HTML,
    escapando prima tutto il resto per evitare iniezione di tag HTML o
    rottura del rendering quando i contenuti dinamici (nomi utente, distretti,
    email) contengono caratteri come _ * [ ] ( ) etc."""
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    return escaped


API_URL = os.getenv("API_URL", "http://127.0.0.1:10000")

# Stati della conversazione per la Lead Generation
WAITING_CONSENT, WAITING_NAME, WAITING_EMAIL = range(3)

CONSENT_VERSION = PRIVACY_NOTICE_VERSION


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
        await update.message.reply_text(
            _md_to_html(welcome_text), parse_mode="HTML", reply_markup=reply_markup
        )
    return ConversationHandler.END


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "top_zone":
        keyboard = [
            [InlineKeyboardButton("💼 Boutique / Lusso", callback_data="calc_top:vintage_premium")],
            [InlineKeyboardButton("⚖️ Mercatino a Peso", callback_data="calc_top:kilo_sale")],
            [InlineKeyboardButton("✂️ Laboratorio Sartoriale", callback_data="calc_top:upcycling")],
            [InlineKeyboardButton("🛍️ Pop-Up di Quartiere", callback_data="calc_top:curated_vintage")],
            [InlineKeyboardButton("⬅️ Torna al Menu", callback_data="menu")]
        ]
        text = "🎯 *Seleziona il tuo Modello di Business*\n\nIl punteggio CPI verrà ricalcolato ricalibrando i pesi su misura per la tua attività:"
        await query.edit_message_text(
            _md_to_html(text), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

    elif query.data.startswith("calc_top:"):
        b_type = query.data.split(":")[1]
        
        try:
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
                    f"Per scaricare l'Executive Report PDF completo, ti chiederemo un paio di dati aziendali."
                )
                
                keyboard = [
                    [InlineKeyboardButton("📄 Sblocca e Scarica PDF", callback_data=f"lead:{name}:{b_type}")],
                    [InlineKeyboardButton("⬅️ Cambia Modello", callback_data="top_zone")],
                    [InlineKeyboardButton("🏠 Menu Principale", callback_data="menu")]
                ]
                await query.edit_message_text(
                    _md_to_html(text),
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                )
            else:
                await query.edit_message_text(
                    _md_to_html(
                        "⚠️ Errore nel recupero della zona top. Riprova più tardi."
                    ),
                    parse_mode="HTML",
                )
        except Exception as e:
            await query.edit_message_text(f"⚠️ Errore nel calcolo del CPI dinamico: {e}")
        return ConversationHandler.END

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
                    keyboard.append([InlineKeyboardButton(f"📄 PDF {z['name']}", callback_data=f"lead:{z['name']}:curated_vintage")])
                keyboard.append([InlineKeyboardButton("⬅️ Torna al Menu", callback_data="menu")])
                await query.edit_message_text(
                    _md_to_html(msg), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await query.edit_message_text(
                    _md_to_html(
                        "⚠️ Errore nel recupero della lista distretti. Riprova più tardi."
                    ),
                    parse_mode="HTML",
                )
        except Exception as e:
            await query.edit_message_text(f"⚠️ Errore nel recupero della lista: {e}")
        return ConversationHandler.END

    # Avvio del Flusso Lead Generation
    elif query.data.startswith("lead:"):
        parts = query.data.split(":")
        district_name = parts[1]
        b_type = parts[2] if len(parts) > 2 else "curated_vintage"

        # Salva solo i parametri non personali nel contesto dell'utente.
        context.user_data["district"] = district_name
        context.user_data["b_type"] = b_type

        consent_keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Accetto e voglio il report",
                        callback_data="consent:accept",
                    ),
                    InlineKeyboardButton(
                        "❌ Rifiuto",
                        callback_data="consent:decline",
                    ),
                ]
            ]
        )
        await query.message.reply_text(
            _md_to_html(
                "🔒 *Informativa privacy e consenso*\n\n"
                "Per preparare il report raccogliamo nome, email, ID Telegram, username, "
                "modello di business e distretto. I dati sono usati solo per erogare il "
                "report e le comunicazioni richieste, vengono conservati per al massimo "
                "12 mesi e non sono inviati ai modelli AI.\n\n"
                "Puoi chiedere la cancellazione con `/delete_my_data`. "
                f"Informativa completa: {PRIVACY_NOTICE_URL}\n\n"
                "Vuoi procedere con il trattamento dei dati per ricevere il report?"
            ),
            parse_mode="HTML",
            reply_markup=consent_keyboard,
        )
        return WAITING_CONSENT

    elif query.data == "consent:accept":
        context.user_data["consent_version"] = CONSENT_VERSION
        context.user_data["consent_at"] = datetime.now(timezone.utc).isoformat()
        context.user_data["privacy_notice_url"] = PRIVACY_NOTICE_URL
        await query.message.reply_text(
            _md_to_html(
                "👤 *Richiesta Report Executive B2B*\n\n"
                "Inserisci il tuo *Nome e Cognome* (o Nome Azienda) per intestare il report:"
            ),
            parse_mode="HTML",
        )
        return WAITING_NAME

    elif query.data == "consent:decline":
        context.user_data.pop("consent_version", None)
        context.user_data.pop("consent_at", None)
        context.user_data.pop("privacy_notice_url", None)
        await query.message.reply_text(
            _md_to_html(
                "Nessun dato personale verrà salvato. Puoi comunque usare il bot per "
                "consultare le zone raccomandate."
            ),
            parse_mode="HTML",
        )
        return ConversationHandler.END

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
        await query.edit_message_text(
            _md_to_html(welcome_text),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ConversationHandler.END


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    context.user_data["full_name"] = name

    await update.message.reply_text(
        _md_to_html(
            f"Grazie *{name}*!\n\n"
            "✉️ Ora inserisci la tua *Email professionale* a cui inviare aggiornamenti o essere ricontattato:"
        ),
        parse_mode="HTML",
    )
    return WAITING_EMAIL


# Inizializza Supabase direttamente nel bot
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

async def _generate_executive_pdf(zone_data: dict, filename: str) -> str:
    """Generate the PDF outside the event-loop thread.

    PDF rendering also calls the synchronous AI reporter, so the whole operation
    is delegated to a worker thread to keep the API and bot responsive.
    """
    return await asyncio.to_thread(
        generate_executive_pdf,
        zone_data,
        filename=filename,
    )


async def receive_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = update.message.text.strip()
    
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        await update.message.reply_text(
            _md_to_html(
                "⚠️ Formato email non valido. Per favore inserisci un'email valida (es. *nome@azienda.com*):"
            ),
            parse_mode="HTML",
        )
        return WAITING_EMAIL

    context.user_data["email"] = email
    user = update.effective_user

    district_name = context.user_data.get("district", "Nørrebro")
    b_type = context.user_data.get("b_type", "curated_vintage")
    full_name = context.user_data.get("full_name", "Utente B2B")
    consent_version = context.user_data.get("consent_version")
    consent_at = context.user_data.get("consent_at")
    privacy_notice_url = context.user_data.get("privacy_notice_url")

    if not consent_version or not consent_at or not privacy_notice_url:
        await update.message.reply_text(
            _md_to_html(
                "⚠️ Per salvare i dati è necessario il consenso all'informativa privacy. "
                "Richiedi nuovamente il report per continuare."
            ),
            parse_mode="HTML",
        )
        return ConversationHandler.END

    # 1. Salvataggio DIRETTO su Supabase tramite funzione atomica con audit.
    if supabase:
        try:
            supabase.rpc(
                "insert_lead_with_consent",
                {
                    "p_telegram_user_id": user.id,
                    "p_telegram_username": user.username,
                    "p_full_name": full_name,
                    "p_email": email,
                    "p_business_type": b_type,
                    "p_interested_district": district_name,
                    "p_consent_version": consent_version,
                    "p_consent_at": consent_at,
                    "p_privacy_notice_url": privacy_notice_url,
                    "p_actor": "telegram_bot",
                },
            ).execute()
            print("✅ [SUPABASE] Lead salvato con consenso registrato.", flush=True)
        except Exception as e:
            print(f"❌ [SUPABASE ERR] Errore inserimento lead: {e}", flush=True)
    else:
        print("⚠️ [SUPABASE] Client Supabase non configurato nel bot!", flush=True)

    # 2. Generazione ed invio del PDF
    await update.message.reply_text(
        _md_to_html("✅ *Dati registrati con successo!* Generazione del Report PDF B2B in corso..."),
        parse_mode="HTML",
    )

    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{API_URL}/zones?business_type={b_type}", timeout=10.0)

        if res.status_code == 200:
            zones = res.json()
            zone_data = next((z for z in zones if z["name"].lower() == district_name.lower()), None)
            if not zone_data:
                await update.message.reply_text(
                    _md_to_html(
                        f"⚠️ Il distretto *{district_name}* non è stato trovato. "
                        "Il report PDF non è stato generato."
                    ),
                    parse_mode="HTML",
                )
                return ConversationHandler.END

            # Nome sicuro per il file mostrato all'utente (niente slash, spazi, ecc.)
            safe_district = _sanitize_filename(district_name)
            display_filename = f"Executive_Report_{safe_district}.pdf"

            # File temporaneo unico per evitare sovrascritture tra utenti concorrenti
            with tempfile.NamedTemporaryFile(suffix=".pdf", prefix="exec_report_", delete=False) as tmp:
                pdf_path = tmp.name

            await _generate_executive_pdf(zone_data, pdf_path)

            with open(pdf_path, "rb") as doc:
                await update.message.reply_document(
                    document=doc,
                    filename=display_filename,
                    caption=_md_to_html(
                        f"📄 *Executive Report B2B:* {district_name}\n"
                        f"Preparato per: *{full_name}*\n\n"
                        f"Grazie per aver utilizzato Copenhagen Re-Commerce Matrix!"
                    ),
                    parse_mode="HTML",
                )

            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            else:
                await update.message.reply_text(
                    _md_to_html(
                        "⚠️ Errore nel recupero dei dati per il PDF. Riprova più tardi."
                    ),
                    parse_mode="HTML",
                )
    except Exception as e:
        await update.message.reply_text(f"⚠️ Errore durante la generazione del PDF: {e}")

    return ConversationHandler.END


async def delete_my_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Delete all data stored for the requesting Telegram user."""
    user = update.effective_user
    if not supabase:
        await update.message.reply_text(
            _md_to_html("⚠️ Il servizio di cancellazione non è configurato.")
        )
        return ConversationHandler.END

    try:
        response = supabase.rpc(
            "delete_lead_data",
            {
                "p_telegram_user_id": user.id,
                "p_actor": "telegram_user_request",
            },
        ).execute()
        deleted = getattr(response, "data", 0) or 0
        if isinstance(deleted, list):
            deleted = deleted[0] if deleted else 0
        if deleted:
            message = "✅ I tuoi dati personali sono stati cancellati."
        else:
            message = "ℹ️ Non risultano dati personali da cancellare per questo profilo."
    except Exception:
        message = "⚠️ Non è stato possibile completare la cancellazione. Riprova più tardi."

    await update.message.reply_text(_md_to_html(message))
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operazione annullata. Usa /start per tornare al menu.")
    return ConversationHandler.END


def build_conv_handler() -> ConversationHandler:
    """Build the lead-generation conversation handler.

    `/start` is available as a fallback so users can always return to the menu,
    even while waiting for name/email/consent. A 5-minute conversation timeout
    prevents stuck conversations from blocking the bot indefinitely.
    """
    return ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(handle_callback)
        ],
        states={
            WAITING_CONSENT: [
                CallbackQueryHandler(handle_callback, pattern=r"^consent:")
            ],
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            WAITING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_email)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CommandHandler("cancel", cancel),
            CommandHandler("delete_my_data", delete_my_data),
        ],
        conversation_timeout=300,
        per_message=False
    )


async def start_telegram_bot():
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("⚠️ [BOT] TELEGRAM_BOT_TOKEN non trovato tra le variabili d'ambiente!", flush=True)
            return

        print("🤖 [BOT] Inizializzazione Bot Telegram con Lead Funnel in corso...", flush=True)
        app = Application.builder().token(token).build()

        conv_handler = build_conv_handler()

        app.add_handler(conv_handler)

        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        print("✅ [BOT] Bot Telegram avviato con successo e in ascolto 24/7!", flush=True)
    except Exception as e:
        print(f"❌ [BOT] Errore critico durante l'avvio del bot: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(start_telegram_bot())