"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parent

AZURE_OPENAI_BASE_URL = os.getenv(
    "AZURE_OPENAI_BASE_URL",
    "https://neo-hackathon.services.ai.azure.com/openai/v1/",
)
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "Neo-Hackathon")

DB_PATH = Path(os.getenv("RIDEWISE_DB_PATH", str(ROOT_DIR / "ridewise.db")))
POLICY_DIR = Path(os.getenv("RIDEWISE_POLICY_DIR", str(ROOT_DIR)))
INDEX_DIR = Path(os.getenv("RIDEWISE_INDEX_DIR", str(ROOT_DIR / "rag" / "index")))

POLICY_FILES = [
    "01_Rental_Agreement_and_Terms.pdf",
    "02_Cancellation_and_Refund_Policy_v1.pdf",
    "03_Cancellation_and_Refund_Policy_v2.pdf",
    "04_Late_Return_and_Damage_Penalty_Schedule.pdf",
    "05_EV_User_Guide_and_FAQ.pdf",
]

MAX_SQL_ROWS = 50
MAX_TOOL_ROUNDS = 6


def require_api_key() -> str:
    if not AZURE_OPENAI_API_KEY:
        raise RuntimeError(
            "AZURE_OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return AZURE_OPENAI_API_KEY
