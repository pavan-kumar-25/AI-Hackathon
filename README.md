# RideWise Assist

Conversational AI for RideWise Mobility (Bengaluru two-wheeler & EV rental). Answers **customers** and **support agents** using the operational SQLite database and official policy PDFs.

## Features

- Streamlit chat UI with role selection (Customer / Support agent)
- Customer entitlement filtering on database queries
- Policy RAG over RW-POL-01 … RW-POL-05 (BM25 + OCR for scanned annexures)
- NeoStats-hosted Azure OpenAI tool-calling agent
- Transparency panel (tools + policy sources)

## Prerequisites

- Python 3.10+
- NeoStats hackathon API key
- Optional: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) on PATH for live annexure OCR (curated annexure text is bundled as fallback)

## Setup (?10 minutes)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows; use `cp` on macOS/Linux
```

Edit `.env` and set:

```
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_BASE_URL=https://neo-hackathon.services.ai.azure.com/openai/v1/
AZURE_OPENAI_DEPLOYMENT=Neo-Hackathon
```

Build the policy index (also auto-runs on first chat):

```bash
python -m rag.ingest
```

Run the app:

```bash
streamlit run app.py
```

## Architecture

1. **UI** (`app.py`) — session role, `customer_id`, chat history, new conversation, transparency panel
2. **Agent** (`agent/orchestrator.py`) — NeoStats LLM with tool calls
3. **SQL tool** (`tools/sql_tool.py`) — read-only `SELECT` against `ridewise.db` + customer entitlement checks
4. **Policy tool** (`tools/policy_tool.py`) — BM25 search over chunked policy PDFs
5. **Ingest** (`rag/ingest.py`) — PDF text extraction, OCR attempt for scanned pages, chunk index under `rag/index/`

Do **not** modify `ridewise.db` or the policy PDFs. Supporting indexes under `rag/index/` are generated locally.

## LLM configuration

All credentials come from environment variables (see `.env.example`). The client uses the OpenAI SDK with NeoStats `base_url`, matching `sample_open_ai_wrapper.py`.

You must be able to resolve and reach `neo-hackathon.services.ai.azure.com` (event network / internet). If DNS fails, the UI shows a connection error instead of crashing.

## Example questions

- Customer (`CUST0001`): “What are my upcoming bookings?”
- Customer: “What is the security deposit for an EV scooter?”
- Agent: “How many vehicles are in maintenance?”
- Either: “I booked after 1 July 2026 — what is my cancel refund if I cancel 10 hours before pickup?”
- Either: “What is the low-battery return fee for EVs?”

## Project layout

```
app.py                 Streamlit entry
config.py              Env + paths
agent/                 Tool-calling loop
llm/                   Azure OpenAI client
tools/                 query_db, search_policies
rag/                   ingest + BM25 store
prompts/               System prompt
ridewise.db            Provided operational DB (do not edit)
01_…05_*.pdf           Policy pack (do not edit)
```

## Design notes

See [DECISIONS.md](DECISIONS.md).
