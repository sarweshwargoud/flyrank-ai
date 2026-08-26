import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from week4/.env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be configured in .env")

# Initialize the Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
