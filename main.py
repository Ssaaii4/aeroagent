import asyncio, json, uuid, os
from openai import AzureOpenAI
from dotenv import load_dotenv
from agents.search_agent  import search_flights
from agents.compare_agent import compare_flights, format_choice_card
from agents.booking_agent import fill_booking_form, complete_payment
from agents.notify_agent  import build_confirmation_message
from agents.logicapps    import poll_approval
from agents.verify_agent import generate_otp, store_otp, send_verification_email
from tools.keyvault_tool  import get_secret

load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_AI_FOUNDRY_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-02-01"
)

INTENT_SYS = """Extract travel intent as JSON only. No prose.
Schema: {"origin":"IATA","destination":"IATA","date":"YYYY-MM-DD",
"time_pref":null,"budget_usd":null,"seat_pref":"any",
"passengers":1,"trip_type":"one-way","user_email":null}
Set missing fields to null.
If you cannot determine origin or destination, set them to null."""

def parse_intent(text: str) -> dict:
    r = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": INTENT_SYS},
            {"role": "user",   "content": text}
        ]
    )
    raw = r.choices[0].message.content
    raw = raw.replace("```json","").replace("```","").strip()
    return json.loads(raw)

def ask_clarification(intent: dict) -> str | None:
    if not intent.get("time_pref"):
        return (
            "When would you prefer to fly?\n"
            "  A) Early morning (before 8am)\n"
            "  B) Morning (8am-12pm)\n"
            "  C) Afternoon (12pm-6pm)\n"
            "  D) Evening (after 6pm)\n"
            "  E) No preference"
        )
    if not intent.get("user_email"):
        return "What email should we send your booking approval to?"
    return None

TIME_MAP = {
    "a": "early",
    "b": "morning",
    "c": "afternoon",
    "d": "evening",
    "e": "any",
    "no preference": "any"
}

def apply_clarification(intent: dict, reply: str) -> dict:
    r = reply.strip().lower()
    if not intent.get("time_pref"):
        intent["time_pref"] = TIME_MAP.get(r, "any")
    elif not intent.get("user_email") and "@" in reply:
        intent["user_email"] = reply.strip()
    return intent

def get_passenger() -> dict:
    return {
        "first":     get_secret("passenger-first"),
        "last":      get_secret("passenger-last"),
        "passport":  get_secret("passenger-passport"),
        "email":     get_secret("passenger-email"),
        "full_name": get_secret("passenger-fullname"),
        "seat_pref": "aisle"
    }

async def run_agent(user_message: str, reply_fn, session: dict = {}):
    if "intent" not in session:
        intent = parse_intent(user_message)

        # validate we got origin and destination
        if not intent.get("origin") or not intent.get("destination"):
            await reply_fn(
                "I need a bit more detail. Try something like:\n"
                "'Find me the cheapest flight from New York to London on August 15th 2026'"
            )
            return session

        session["intent"] = intent
    else:
        intent = apply_clarification(session["intent"], user_message)
        session["intent"] = intent

    clarification = ask_clarification(intent)
    if clarification:
        await reply_fn(clarification)
        return session

    await reply_fn("Searching flights...")
    flights = search_flights(intent)

    if not flights:
        await reply_fn("No flights found for those dates. Try different dates?")
        return session

    await reply_fn("Analysing and ranking options...")
    top3 = compare_flights(flights, intent)
    session["top3"] = top3
    await reply_fn(format_choice_card(top3))
    session["state"] = "selecting"
    return session

async def handle_selection(choice: str, session: dict, reply_fn):
    top3 = session.get("top3", [])
    try:
        idx = int(choice.strip()) - 1
    except:
        await reply_fn("Please reply with 1, 2 or 3.")
        return session

    if idx < 0 or idx >= len(top3):
        await reply_fn("Please reply with 1, 2 or 3.")
        return session

    flight    = top3[idx]
    passenger = get_passenger()
    intent    = session["intent"]

    await reply_fn("Filling booking form...")
    summary = await fill_booking_form(flight, passenger)
    session["summary"]   = summary
    session["flight"]    = flight
    session["passenger"] = passenger

    approval_id = str(uuid.uuid4())
    session["approval_id"] = approval_id

   otp = generate_otp()
   store_otp(approval_id, otp, summary, flight)
   await send_verification_email(
   user_email=intent.get("user_email", "judge@aeroagent.dev"),
   approval_id=approval_id,
   otp=otp,
   summary=summary,
   flight=flight
   )

    await reply_fn(
    f"Booking summary:\n"
    f"  Flight:  {summary['airline']} {summary['flight_no']}\n"
    f"  Departs: {summary['departs']}\n"
    f"  Arrives: {summary['arrives']}\n"
    f"  Seat:    {summary['seat']}\n"
    f"  Total:   {summary['total']}\n\n"
    f"A verification email has been sent to {intent.get('user_email')}.\n"
    f"Click the approval link in the email, or type your 6-digit OTP here."
   )

    session["state"] = "awaiting_approval"

   approved = await poll_approval(approval_id, timeout_seconds=300)

    if not approved:
        await reply_fn("Approval timed out. Booking cancelled for safety.")
        session["state"] = "expired"
        return session

    await reply_fn("Approved! Completing booking...")
    booking = await complete_payment(summary["page_state"], passenger)
    msg = build_confirmation_message(booking, flight)
    await reply_fn(msg)
    session["state"] = "complete"
    session["pnr"]   = booking["pnr"]
    return session


if __name__ == "__main__":
    async def test():
        session = {}
        async def reply(t): print(f"\nAGENT: {t}")

        session = await run_agent(
            "Find cheapest flight from New York to London August 15th 2026",
            reply, session
        )
        session = await run_agent("c", reply, session)
        session = await run_agent("test@example.com", reply, session)
        await handle_selection("1", session, reply)

    asyncio.run(test())