# StyleMate

StyleMate helps people discover outfit combinations from clothes they already own.
This repository contains a runnable starter app with a React frontend, FastAPI
backend, PostgreSQL database, Pillow image processing, and an explainable
rule-based recommendation engine.

## Requirements

- Python 3.11+
- Node.js 20+
- Ollama with the local `qwen2.5vl:3b` vision model
- Docker Desktop (for PostgreSQL), or set `DATABASE_URL` to another SQLAlchemy URL

Install Ollama, then download the vision model once:

```powershell
ollama pull qwen2.5vl:3b
```

Keep the Ollama service running while using StyleMate. Photo analysis is sent
only to the local Ollama service (`http://127.0.0.1:11434` by default); it is
not sent to a cloud AI provider. Configure `OLLAMA_HOST`,
`OLLAMA_VISION_MODEL`, or `OLLAMA_TIMEOUT_SECONDS` in `.env` if needed.

## Start the backend

From the project root, start PostgreSQL:

```powershell
docker compose up -d db
```

Create and activate a virtual environment, then install the backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --app-dir backend --reload
```

The site and API are at `http://localhost:8000`; interactive API docs are at
`http://localhost:8000/docs`.

## Start the frontend

In another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the local address printed by Vite. The development server proxies `/api`
requests to the backend.

## Starter API

- `GET /api/health` — health check
- `POST /api/auth/register` and `POST /api/auth/login` — create an account or sign in (passwords must be at least 12 characters)
- `GET /api/clothing` — list wardrobe items
- `POST /api/clothing` — upload a clothing photo and its metadata
- `DELETE /api/clothing/{item_id}` — remove an item and its stored image
- `GET /api/outfits/recommendations` — generate outfit combinations

Users select one image through the browser's native photo/file picker; a website
cannot silently access the entire device gallery. Selected phone and camera
images are validated/normalized to WebP by Pillow, including HEIC/HEIF photos
via Pillow-Heif. Original upload bytes are not retained. Clothing metadata is stored in PostgreSQL; outfit suggestions are computed from
the current wardrobe on each request. Image files are stored locally in
`storage/clothing` for development. For deployment,
each account's wardrobe and clothing photos are isolated behind a signed,
HTTP-only session cookie. Existing local wardrobe rows created before account
support remain unassigned and are not exposed to new accounts.

On upload, the local vision model identifies the garment, category, main color,
style, audience, and season. These details can be overridden before uploading.
The recommender uses the analyzed wardrobe details and transparent rules to
rank outfit combinations by color harmony and the selected filters. Its preview
is a collage of the user's actual clothing photos, not a generated virtual
try-on. If a full combination is not possible, it still suggests an outfit
using available wardrobe pieces and identifies what's missing. Existing local
database rows are upgraded on API startup with casual/unisex defaults for the
new tags.

## Deploy to Render

The root `render.yaml` defines a Singapore-region web service, private Ollama
service, and PostgreSQL database. Deploy it from the Render dashboard as a
Blueprint after pushing this repository. The web app and Ollama each need
persistent disks; Ollama uses an 8 GB RAM compute plan to load the 3.2 GB
vision model. The model is downloaded onto its private disk on first startup,
which can take several minutes. Do not expose the Ollama port publicly.

Render's documented plan prices make the compute and database approximately
$206/month, before persistent disks, usage extras, and tax. Check the current
Render pricing before deploying; these estimates are not a quote.

For production, the Blueprint sets `APP_ENV=production`,
`AUTH_COOKIE_SECURE=true`, and generates `AUTH_SECRET`. Each account's
wardrobe and images are protected by a signed, HTTP-only session cookie.

For Vercel, set the project's Root Directory to `frontend`. Its
`vercel.json` proxies `/api/*` to `https://stylemate.onrender.com`, the Render
web service defined in the Blueprint, and serves the React SPA for other
paths. The root-level `vercel.json` provides the same routing when Vercel's
Root Directory is the repository root. The proxy works once the Render
Blueprint is deployed and the API health check at
`https://stylemate.onrender.com/api/health` succeeds.
