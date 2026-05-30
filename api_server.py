from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import run_agent, handle_selection
import asyncio

app = FastAPI()
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

sessions: dict = {}

class ChatReq(BaseModel):
    session_id: str
    message: str

class SelectReq(BaseModel):
    session_id: str
    choice: str

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
        "summary": sessions[req.session_id].get("summary")
    }

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