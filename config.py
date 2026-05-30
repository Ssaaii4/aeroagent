from dotenv import load_dotenv
import os
load_dotenv()

FOUNDRY_ENDPOINT       = os.environ["AZURE_AI_FOUNDRY_ENDPOINT"]
OPENAI_DEPLOYMENT      = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
EMBED_DEPLOYMENT       = os.environ.get("AZURE_EMBED_DEPLOYMENT", "text-embedding-3-large")
SEARCH_ENDPOINT        = os.environ["AZURE_SEARCH_ENDPOINT"]
SEARCH_ADMIN_KEY       = os.environ["AZURE_SEARCH_ADMIN_KEY"]
KV_URL                 = os.environ["AZURE_KEYVAULT_URL"]
LOGIC_APPS_TRIGGER_URL = os.environ["LOGIC_APPS_TRIGGER_URL"]
DEMO_MODE              = os.environ.get("DEMO_MODE", "true") == "true"
OPENAI_KEY             = os.environ.get("AZURE_OPENAI_KEY", "")