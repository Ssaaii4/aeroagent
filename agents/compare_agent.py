from openai import AzureOpenAI
from dotenv import load_dotenv
import os, json
load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_AI_FOUNDRY_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-02-01"
)

SCORE_PROMPT = """You are a flight analyst. Score each flight 0-100.
Consider: price, stops (direct = bonus), duration, airline reliability,
departure time vs preference. Return ONLY a JSON array sorted best-first:
[{"rank":1,"score":92,"price_usd":312,"airline":"AA",
  "departure":"08:15","stops":0,"duration":"7h10m",
  "flight_no":"AA100",
  "reason":"Direct, cheapest, good on-time record"}]"""

def compare_flights(flights: list, intent: dict) -> list:
    payload = {"user_request": intent, "flights": flights[:10]}
    r = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": SCORE_PROMPT},
            {"role": "user",   "content": json.dumps(payload)}
        ]
    )
    text = r.choices[0].message.content
    text = text.replace("```json","").replace("```","").strip()
    return json.loads(text)[:3]

def format_choice_card(top3: list) -> str:
    lines = ["Here are your top 3 flights:\n"]
    for f in top3:
        stops = "Direct" if f["stops"] == 0 else f"{f['stops']} stop"
        lines.append(
            f"  {f['rank']}. {f['airline']}  "
            f"${f['price_usd']}  {f['departure']}  "
            f"{stops}  ({f['duration']})\n"
            f"     {f['reason']}\n"
        )
    lines.append("Reply 1, 2 or 3 to select.")
    return "".join(lines)