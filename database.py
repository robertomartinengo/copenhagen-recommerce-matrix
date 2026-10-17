import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Forziamo il ricaricamento del file .env sovrascrivendo le variabili precedenti
load_dotenv(override=True)

url: str = os.getenv("SUPABASE_URL", "").strip()
key: str = os.getenv("SUPABASE_KEY", "").strip()

print(f"--> [DEBUG] Connessione a Supabase URL: '{url}'")

if not url or not key or "tuo-project-id" in url:
    raise ValueError("L'URL di Supabase nel file .env non è valido o contiene ancora il segnaposto!")

supabase: Client = create_client(url, key)