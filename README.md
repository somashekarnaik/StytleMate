# StyleMate

StyleMate helps people discover outfit combinations from clothes they already own. It includes a React frontend, a FastAPI backend, PostgreSQL support, image processing, and an explainable recommendation engine.

## Requirements

- Python 3.11+
- Node.js 20+
- Ollama with the `qwen2.5vl:3b` vision model
- Docker Desktop for local PostgreSQL, or another SQLAlchemy-compatible database

Install the local vision model once:

```powershell
ollama pull qwen2.5vl:3b
```

Keep Ollama running while using photo analysis. By default the backend connects to `http://127.0.0.1:11434`; configure `OLLAMA_HOST`, `OLLAMA_API_KEY`, `OLLAMA_VISION_MODEL`, or `OLLAMA_TIMEOUT_SECONDS` in `.env` if needed.

## Run locally

Start PostgreSQL from the project root:

```powershell
docker compose up -d db
```

In one terminal, start the API:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --app-dir backend --reload
```

In another terminal, start the frontend:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the address printed by Vite, normally `http://localhost:5173`. The development server proxies `/api` requests to the local backend, which can reach your local Ollama service.

## API

- `GET /api/health` — health check
- `POST /api/auth/register` and `POST /api/auth/login` — account registration and sign-in
- `GET /api/clothing` — list wardrobe items
- `POST /api/clothing` — upload a clothing photo and metadata
- `DELETE /api/clothing/{item_id}` — remove an item and stored image
- `GET /api/outfits/recommendations` — generate outfit combinations
- `POST /api/outfits/analyze` — analyze a complete outfit photo

Photos are normalized to WebP before analysis. Garment and outfit analysis require an Ollama server that the API can reach. A Vercel serverless API cannot reach Ollama running on your own computer through `127.0.0.1`.

## Vercel

Deploy the frontend with Vercel using `frontend` as the project Root Directory. Its `vercel.json` proxies `/api/*` requests to the configured backend.

For online photo analysis, use a secure Ollama host. Ollama Cloud uses `OLLAMA_HOST=https://ollama.com`, an `OLLAMA_API_KEY` created in the Ollama account, and a cloud vision model such as `qwen3-vl:235b-cloud`. Do not expose an unauthenticated local Ollama service directly to the public internet.
