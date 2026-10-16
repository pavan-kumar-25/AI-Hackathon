# Design Decisions — RideWise Assist

## Top 3 decisions

1. **Streamlit + OpenAI tool-calling (not a heavy agent framework)**  
   Fastest path to a demoable chat UI and multi-step SQL/policy reasoning within 3 hours. LangChain/LlamaIndex were rejected to keep the control flow readable and debuggable for the tech talk.

2. **Entitlement enforcement in `query_db`, not only in the prompt**  
   Customer sessions must include their `customer_id` in SQL touching owned tables; results with a `customer_id` column are post-filtered. Prompt-only RBAC is too easy for the model to ignore under adversarial or confused questions.

3. **BM25 policy index + annexure fallback text**  
   Local keyword retrieval is lightweight (no large embedding model download) and works well on short policy docs. Scanned annexure pages are OCR'd when Tesseract is available; curated annexure text (transcribed from the signed scans) is bundled so refund/grace tables remain searchable offline. Annexure A: only GOLD has a 30-minute late grace; STANDARD and SILVER have none.

## Rejected alternatives

| Idea | Why rejected |
|------|----------------|
| Free-text SQL with no guard | Fails Trust & Safety (15%) |
| Embeddings only (sentence-transformers) | Heavier install; little gain on 5 short PDFs |
| Hard-coded FAQ answers | Forbidden; fails on unseen evaluation questions |
| Full auth / login | Out of scope; role + customer_id at session start is enough |

## Known gaps / failures

- Without Tesseract, annexure OCR may fail and the app relies on curated annexure text in `rag/ingest.py`.
- Complex multi-hop fee calculations depend on the model correctly chaining tools; edge cases may need a clarifying question.
- Rate limits on the NeoStats endpoint surface as a friendly error; no offline LLM fallback (rules forbid other providers).

## Next week

- Add automated entitlement tests and golden Q&A eval set
- Structured calculators for late fee / refund % (deterministic math, LLM only for explanation)
- Proper OCR pipeline in CI and optional hybrid dense+sparse retrieval
