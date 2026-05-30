from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from datetime import datetime, timedelta
from config import SEARCH_ENDPOINT, SEARCH_ADMIN_KEY
import json

sc = SearchClient(
    SEARCH_ENDPOINT,
    "flight-cache",
    AzureKeyCredential(SEARCH_ADMIN_KEY)
)

def cache_get(origin, dest, date, time_pref):
    key = f"{origin}_{dest}_{date}_{time_pref}"
    cutoff = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        results = list(sc.search(
            search_text="*",
            filter=f"cache_key eq '{key}' and cached_at ge {cutoff}",
            top=1
        ))
        if results:
            return json.loads(results[0]["flights_json"])
    except:
        pass
    return None

def cache_set(origin, dest, date, time_pref, flights):
    key = f"{origin}_{dest}_{date}_{time_pref}"
    try:
        sc.upload_documents([{
            "id":           key,
            "cache_key":    key,
            "origin":       origin,
            "destination":  dest,
            "date":         date,
            "time_pref":    time_pref,
            "flights_json": json.dumps(flights),
            "cached_at":    datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        }])
    except Exception as e:
        print(f"Cache write failed: {e}")