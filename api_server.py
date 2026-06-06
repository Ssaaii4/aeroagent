from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from main import run_agent, handle_selection
from agents.verify_agent import verify_otp, approve_by_link
import os

app = FastAPI()
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

sessions: dict = {}

FRONTEND_URL = os.environ.get(
    "FRONTEND_URL",
    "https://witty-flower-0e99f2c10.7.azurestaticapps.net"
)

class ChatReq(BaseModel):
    session_id: str
    message: str

class SelectReq(BaseModel):
    session_id: str
    choice: str

class OtpReq(BaseModel):
    session_id: str
    otp: str

@app.post("/chat")
async def chat(req: ChatReq):
    sess = sessions.setdefault(req.session_id, {})
    replies = []
    async def reply_fn(text): replies.append(text)
    sessions[req.session_id] = await run_agent(
        req.message, reply_fn, sess)
    return {
        "session_id": req.session_id,
        "reply": "\n\n".join(replies),
        "state": sessions[req.session_id].get("state", "clarifying")
    }

@app.post("/select")
async def select(req: SelectReq):
    sess = sessions.get(req.session_id, {})
    replies = []
    async def reply_fn(text): replies.append(text)
    sessions[req.session_id] = await handle_selection(
        req.choice, sess, reply_fn)
    return {
        "session_id": req.session_id,
        "reply": "\n\n".join(replies),
        "state": sessions[req.session_id].get("state"),
        "summary": sessions[req.session_id].get("summary"),
        "approval_id": sessions[req.session_id].get("approval_id")
    }

@app.post("/verify-otp")
async def verify(req: OtpReq):
    sess = sessions.get(req.session_id, {})
    approval_id = sess.get("approval_id")
    if not approval_id:
        return {"success": False, "message": "No pending approval"}
    ok = verify_otp(approval_id, req.otp)
    if ok:
        sess["state"] = "complete"
        replies = []
        async def reply_fn(text): replies.append(text)
        from agents.booking_agent import complete_payment
        from agents.notify_agent import build_confirmation_message
        booking = await complete_payment(
            sess.get("summary", {}).get("page_state", {}),
            sess.get("passenger", {})
        )
        msg = build_confirmation_message(booking, sess.get("flight", {}))
        sess["pnr"] = booking["pnr"]
        return {"success": True, "message": msg, "pnr": booking["pnr"]}
    return {"success": False, "message": "Invalid or expired OTP"}

@app.get("/approve")
async def approve(
    id: str = Query(...),
    token: str = Query(...)
):
    ok = approve_by_link(id)
    if ok:
        return RedirectResponse(
            url=f"{FRONTEND_URL}?approved=true&id={id}"
        )
    return RedirectResponse(
        url=f"{FRONTEND_URL}?approved=false&id={id}"
    )

@app.get("/approval-status")
async def approval_status(session_id: str):
    sess = sessions.get(session_id, {})
    return {"status": sess.get("state", "not_found")}

@app.get("/booking")
async def booking(session_id: str):
    sess = sessions.get(session_id, {})
    if sess.get("state") != "complete":
        return {"status": "not_ready"}
    return {
        "pnr":     sess.get("pnr"),
        "summary": sess.get("summary")
    }

@app.get("/health")
def health():
    return {"status": "ok"}