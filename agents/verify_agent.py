import random, string, asyncio
from datetime import datetime, timedelta
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os, httpx
load_dotenv()

SEARCH_ENDPOINT  = os.environ["AZURE_SEARCH_ENDPOINT"]
SEARCH_ADMIN_KEY = os.environ["AZURE_SEARCH_ADMIN_KEY"]
FRONTEND_URL     = os.environ.get("FRONTEND_URL", "https://witty-flower-0e99f2c10.7.azurestaticapps.net")
LOGIC_APPS_URL   = os.environ["LOGIC_APPS_TRIGGER_URL"]

sc = SearchClient(SEARCH_ENDPOINT, "approvals", AzureKeyCredential(SEARCH_ADMIN_KEY))

def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=6))

def store_otp(approval_id: str, otp: str, summary: dict, flight: dict):
    expires = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
    sc.upload_documents([{
        "id":           approval_id,
        "status":       "pending",
        "otp":          otp,
        "expires_at":   expires,
        "triggered_at": datetime.utcnow().isoformat(),
        "approved_at":  None,
        "airline":      flight.get("airline", ""),
        "flight_no":    summary.get("flight_no", ""),
        "departs":      summary.get("departs", ""),
        "total":        summary.get("total", ""),
        "seat":         summary.get("seat", "")
    }])

def verify_otp(approval_id: str, otp: str) -> bool:
    try:
        docs = list(sc.search(
            search_text="*",
            filter=f"id eq '{approval_id}'",
            top=1
        ))
        if not docs:
            return False
        doc = docs[0]
        if doc.get("status") == "approved":
            return True
        if doc.get("otp") != otp:
            return False
        expires = doc.get("expires_at", "")
        if expires and datetime.utcnow().isoformat() > expires:
            return False
        sc.merge_or_upload_documents([{
            "id":          approval_id,
            "status":      "approved",
            "approved_at": datetime.utcnow().isoformat()
        }])
        return True
    except:
        return False

def approve_by_link(approval_id: str) -> bool:
    try:
        docs = list(sc.search(
            search_text="*",
            filter=f"id eq '{approval_id}'",
            top=1
        ))
        if not docs:
            return False
        doc = docs[0]
        expires = doc.get("expires_at", "")
        if expires and datetime.utcnow().isoformat() > expires:
            return False
        sc.merge_or_upload_documents([{
            "id":          approval_id,
            "status":      "approved",
            "approved_at": datetime.utcnow().isoformat()
        }])
        return True
    except:
        return False

async def send_verification_email(
    user_email: str,
    approval_id: str,
    otp: str,
    summary: dict,
    flight: dict
):
    BACKEND_URL = "https://aeroagent-api.salmonsand-ae41dd1f.eastus.azurecontainerapps.io"
approve_url = (
    f"{BACKEND_URL}/approve"
    f"?id={approval_id}&token={otp}"
)
    payload = {
        "to_email":    user_email,
        "approval_id": approval_id,
        "otp":         otp,
        "approve_url": approve_url,
        "flight":      summary.get("flight_no", ""),
        "airline":     flight.get("airline", ""),
        "departs":     summary.get("departs", ""),
        "total":       summary.get("total", "")
    }
    async with httpx.AsyncClient() as h:
        await h.post(LOGIC_APPS_URL, json=payload, timeout=15)