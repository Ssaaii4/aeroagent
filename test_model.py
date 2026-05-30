from openai import AzureOpenAI
from dotenv import load_dotenv
import os
load_dotenv()

client = AzureOpenAI(
    azure_endpoint=os.environ["AZURE_AI_FOUNDRY_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_KEY"],
    api_version="2024-02-01"
)

r = client.chat.completions.create(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    messages=[{"role": "user", "content": "Say hello in one sentence."}]
)
print(r.choices[0].message.content)