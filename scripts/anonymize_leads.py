"""Anonymize lead records older than the configured retention period.

The script prints only the number of affected rows. It never prints lead data.
"""

import os

from dotenv import load_dotenv
from supabase import create_client


load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise SystemExit("SUPABASE_URL and SUPABASE_KEY must be configured")

client = create_client(supabase_url, supabase_key)
response = client.rpc("anonymize_leads_older_than", {"p_older_than": "12 months"}).execute()
result = getattr(response, "data", 0) or 0
if isinstance(result, list):
    result = result[0] if result else 0
print(f"Anonymized lead rows: {int(result)}")
