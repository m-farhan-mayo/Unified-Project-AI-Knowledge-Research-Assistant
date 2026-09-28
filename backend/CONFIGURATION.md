# Gemini availability

The backend uses `OPENAI_API_KEY` for Google's OpenAI-compatible Gemini endpoint.
Optional settings in `backend/.env`:

```dotenv
GEMINI_MODEL=gemini-3.5-flash-lite
# Set to another model available to your Google account if desired:
GEMINI_FALLBACK_MODEL=
```

The SDK retries transient generation failures twice, with a 30-second timeout per attempt. If configured, a distinct fallback model is tried after server or connection errors. Authentication and quota errors do not switch models. Tool actions are not replayed by this retry mechanism.

If the provider remains unavailable, the API returns a readable 503 response (504 for timeouts), rather than an unhandled 500. Failed turns are not saved to history. A successful PDF upload remains selected when its subsequent question fails.

Apply code or environment changes with `docker compose up -d --build backend`. Provider capacity is external: local changes cannot guarantee availability during a Gemini outage.

# Local development

Install Python dependencies from the project root with `pip install -r backend/requirements.txt`. This is the same dependency list used by the backend Docker image.

# API routes and tests

The application exposes `/api/chat`, `/api/upload-pdf`, and `/api/health`, plus the root status page and FastAPI documentation. `/api/health` is a liveness check; it does not verify Gemini, PostgreSQL, or Redis availability. Development-only `*-test` routes have been removed.

Run automated regression tests from the project root:

```bash
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

Google embedding SDK errors are handled separately from chat SDK errors: quota exhaustion returns 429, provider outages return 503, and rejected credentials or requests return 502. This applies to PDF indexing and document questions. A failed embedding operation does not save the uploaded document or a failed chat turn. A 429 can indicate quota exhaustion or temporary rate/capacity limits; the generic provider message does not identify which one.
