"""Sample NeoStats Azure OpenAI call — credentials come from environment variables."""

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv(
    "AZURE_OPENAI_BASE_URL",
    "https://neo-hackathon.services.ai.azure.com/openai/v1/",
)
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "Neo-Hackathon")
api_key = os.getenv("AZURE_OPENAI_API_KEY", "")

if not api_key:
    raise SystemExit("Set AZURE_OPENAI_API_KEY in .env (see .env.example)")

client = OpenAI(
    base_url=endpoint,
    api_key=api_key,
)

completion = client.chat.completions.create(
    model=deployment_name,
    messages=[
        {
            "role": "user",
            "content": "What is the capital of France?",
        }
    ],
)

print(completion.choices[0].message)
