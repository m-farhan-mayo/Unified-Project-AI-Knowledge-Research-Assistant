# AI Knowledge & Research Assistant frontend

Use Node.js 22 or newer. Run `npm ci`, then `npm run dev`, and open [the app](http://localhost:3000).

The frontend proxies `/api/*` to FastAPI. For local development the backend defaults to `http://127.0.0.1:8000`. Set `BACKEND_URL` before starting development or running `npm run build` to use another backend. Docker builds default to `http://backend:8000`; override the `BACKEND_URL` build argument if needed. Rebuild after changing this value.

Run `npm run lint` and `npm run build` to validate changes.

The API rewrite proxy waits up to five minutes (`experimental.proxyTimeout`) for AI retries and PDF indexing; Next.js defaults to 30 seconds, which can otherwise produce socket hang-ups before the backend responds.
