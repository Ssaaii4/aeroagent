import httpx, asyncio, json
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from datetime import datetime
from config import SEARCH_ENDPOINT, SEARCH_ADMIN_KEY, LOGIC_APPS_TRIGGER_URL

sc = SearchClient(
    SEARCH_ENDPOINT,
    "approvals",
    AzureKeyCredential(SEARCH_ADMIN_KEY)
)

async def trigger_approval(approval_id: str, user_email: str,
                            summary: dict, flight: dict) -> str:
    payload = {
        "approval_id": approval_id,
        "to_email":    user_email,
        "subject":     f"Approve flight booking — {flight['airline']}",
        "body": {
            "airline":  flight["airline"],
            "flight":   summary["flight_no"],
            "departs":  summary["departs"],
            "arrives":  summary["arrives"],
            "seat":     summary["seat"],
            "total":    summary["total"],
        }
    }
    async with httpx.AsyncClient() as h:
        r = await h.post(LOGIC_APPS_TRIGGER_URL, json=payload, timeout=15)

    sc.upload_documents([{
        "id":           approval_id,
        "status":       "pending",
        "triggered_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "approved_at":  None
    }])
    return approval_id

async def poll_approval(approval_id: str,
                         timeout_seconds: int = 300) -> bool:
    deadline = asyncio.get_event_loop().time() + timeout_seconds
    while asyncio.get_event_loop().time() < deadline:
        try:
            docs = list(sc.search(
                search_text="*",
                filter=f"id eq '{approval_id}'",
                top=1
            ))
            if docs:
                status = docs[0].get("status")
                if status == "approved":
                    return True
                if status == "rejected":
                    return False
        except:
            pass
        await asyncio.sleep(5)
    return False