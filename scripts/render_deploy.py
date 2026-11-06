import os
import sys

def trigger_deploy():
    api_key = os.getenv("RENDER_API_KEY")
    if not api_key:
        print("Errore: RENDER_API_KEY non trovata nel file .env")
        sys.exit(1)
        
    print("Script di verifica Render pronto. API Key presente.")

if __name__ == "__main__":
    trigger_deploy()