import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carica le variabili di ambiente dal file .env
load_dotenv()

url: str = os.getenv("SUPABASE_URL", "")
key: str = os.getenv("SUPABASE_KEY", "")

if not url or not key:
    raise ValueError("Credenziali Supabase non trovate nel file .env!")

# Inizializza il client Supabase
supabase: Client = create_client(url, key)