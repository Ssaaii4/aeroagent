from openai import AzureOpenAI
from dotenv import load_dotenv
import os
load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_AI_FOUNDRY_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-02-01"
)

def build_confirmation_message(booking: dict, flight: dict) -> str:
    r = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[{
            "role": "user",
            "content": (
                f"Write a short friendly booking confirmation message.\n"
                f"PNR: {booking['pnr']}\n"
                f"Flight: {flight['airline']} {flight.get('flight_no','')}\n"
                f"Departs: {flight['departure']}\n"
                f"Charged: {booking['charged']}\n"
                f"Status: {booking['status']}"
            )
        }]
    )
    return r.choices[0].message.content