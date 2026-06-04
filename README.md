DocSense
========
Team: Isaiah Mathew, Anthony Mirabal

Project summary
---------------
DocSense is a personal-document intelligence system that combines semantic search, retrieval-augmented generation (RAG), classification, and lightweight knowledge-graph structure to let users search, compare, summarize, and analyze large collections of personal documents while keeping responses grounded with provenance and confidence indicators.

Goals
-----
- Let users ask natural-language questions about their personal documents (bank statements, receipts, emails, notes, reports, etc.).
- Retrieve the most relevant evidence (semantic search + metadata filtering).
- Generate grounded, citation-backed answers using retrieved evidence (RAG).
- Provide multi-label tagging, entity extraction, and optional knowledge-graph linking for cross-document reasoning.
- Offer transparency: show source spans, confidence, and let users correct labels.

Quick start (prototype)
-----------------------
1. Create a Python virtual environment and install dependencies from `requirements.txt`.
2. Add documents under `data/docs/` (plain text for prototype).
3. Run ingestion to build the vector index: `python scripts/ingest.py --dir data/docs --index-path data/index`.
4. Run the API server: `uvicorn app.main:app --reload` and query the `/search` endpoint.

Files in this folder
--------------------
- `scripts/ingest.py` — minimal ingestion and vector index builder (txt files only in prototype).
- `app/main.py` — simple FastAPI app that queries the vector index.
- `requirements.txt` — Python dependencies for the prototype.
- `data/docs/` — place documents to ingest.

License
-------
MIT (suggested for prototype)

Contact
-------
Project leads: Isaiah Mathew, Anthony Mirabal
