# Fugro Inventory — Developer README

Internal documentation for the development team. Contains setup instructions, architecture overview, dependency list, and deployment steps.

> ⚠️ **Security Notice:** Credentials listed here are placeholders. Never commit real secrets to version control. Obtain actual credentials from the team lead via a secure channel (password manager, encrypted message, etc.).

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Repository Structure](#repository-structure)
4. [Prerequisites](#prerequisites)
5. [Local Development Setup](#local-development-setup)
6. [Environment Variables](#environment-variables)
7. [Backend Dependencies](#backend-dependencies)
8. [Frontend Dependencies](#frontend-dependencies)
9. [Database Setup (Supabase)](#database-setup-supabase)
10. [Running Locally](#running-locally)
11. [Deployment — Backend (Render)](#deployment--backend-render)
12. [Deployment — Desktop Builds (GitHub Actions)](#deployment--desktop-builds-github-actions)
13. [Credentials Reference](#credentials-reference)
14. [Known Issues & Notes](#known-issues--notes)

---

## Project Overview

Fugro Inventory is a full-stack IT asset inventory management system built for internal use. It consists of:

- A **REST API backend** (FastAPI + PostgreSQL) responsible for all data operations
- A **desktop frontend** (PyQt6) for end-user interaction on Windows and Linux
- A **cloud database** (Supabase/PostgreSQL) as the single source of truth
- An automated **CI/CD pipeline** (GitHub Actions) that builds and publishes distributable executables on every release

Live backend URL: `https://inventory-system-iaub.onrender.com`

---

## Architecture

```
┌─────────────────────┐         HTTPS          ┌──────────────────────┐
│   PyQt6 Desktop App │ ──────────────────────▶ │  FastAPI on Render   │
│  (Windows / Linux)  │                         │                      │
└─────────────────────┘                         └──────────┬───────────┘
                                                           │
                                                     SQLAlchemy ORM
                                                           │
                                                ┌──────────▼───────────┐
                                                │  Supabase PostgreSQL │
                                                │      (Cloud DB)      │
                                                └──────────────────────┘
```

---

## Repository Structure

```
fugro-inventory/
├── backend/
│   ├── main.py                  # FastAPI app entrypoint
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schemas.py               # Pydantic schemas
│   ├── database.py              # DB connection & session
│   ├── routers/                 # Route handlers (assets, categories, imports, etc.)
│   └── requirements.txt         # Backend Python dependencies
│
├── frontend/
│   ├── main.py                  # PyQt6 app entrypoint
│   ├── ui/                      # UI components and windows
│   ├── threads/                 # QThread workers (data loading, auto-save)
│   └── requirements.txt         # Frontend Python dependencies
│
├── .github/
│   └── workflows/
│       ├── build-windows.yml    # PyInstaller .exe build
│       └── build-linux.yml      # AppImage build
│
├── .env.example                 # Template for environment variables
└── README.md
```

---

## Prerequisites

| Tool | Minimum Version | Notes |
|------|----------------|-------|
| Python | 3.10+ | 3.11 recommended |
| pip | Latest | `pip install --upgrade pip` |
| Git | Any recent | For cloning & CI/CD |
| PostgreSQL client (psql) | Optional | For manual DB inspection |

---

## Local Development Setup

```bash
# 1. Clone the repo
git clone https://github.com/<your-org>/fugro-inventory.git
cd fugro-inventory

# 2. Create and activate a virtual environment (do this separately for backend and frontend)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Copy the env template and fill in your values
cp .env.example .env
```

---

## Environment Variables

Create a `.env` file in the project root (never commit this file). The following variables are required:

```env
# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>
# Example (Supabase connection string):
# DATABASE_URL=postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres

# ── API Configuration ─────────────────────────────────────────────────────────
SECRET_KEY=<your-secret-key>          # Used for JWT signing if auth is enabled
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ── Frontend ──────────────────────────────────────────────────────────────────
API_BASE_URL=https://inventory-system-iaub.onrender.com
# Use http://localhost:8000 for local development

# ── Environment flag ──────────────────────────────────────────────────────────
ENV=development                        # Set to "production" on Render
```

---

## Backend Dependencies

Listed in `backend/requirements.txt`:

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.36
psycopg2-binary==2.9.9
pydantic==2.9.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
pandas==2.2.3
openpyxl==3.1.5
PyJWT==2.9.0
bcrypt==4.2.0
```

Install with:
```bash
pip install -r backend/requirements.txt
```

---

## Frontend Dependencies

Listed in `frontend/requirements.txt`:

```
PyQt6==6.7.0
PyQt6-Qt6==6.7.0
PyQt6-sip==13.6.0
matplotlib==3.9.0
requests==2.32.3
charset-normalizer==3.3.2
certifi==2024.6.2
urllib3==2.2.2
idna==3.7
pyinstaller        # Only needed for building executables — not pinned, use latest stable
```

Install with:
```bash
pip install -r frontend/requirements.txt
```

---

## Database Setup (Supabase)

### First-time setup

1. Go to [supabase.com](https://supabase.com) and log in with the team account.
2. Open the **fugro-inventory** project.
3. Navigate to **Settings → Database → Connection String → URI**.
4. Copy the URI and paste it as `DATABASE_URL` in your `.env`.

### Running migrations

The project uses raw SQL (no Alembic). Apply the schema manually:
```bash
psql $DATABASE_URL -f schema.sql
```

Or paste the schema directly into the Supabase dashboard SQL editor.

### Supabase Dashboard Access

- URL: `https://app.supabase.com/project/<project-ref>`
- Login credentials: See [Credentials Reference](#credentials-reference)

---

## Running Locally

### Start the backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: `http://localhost:8000/docs`

### Start the frontend

```bash
cd frontend
python main.py
```

Make sure `API_BASE_URL` in `.env` points to `http://localhost:8000` for local dev.

---

## Deployment — Backend (Render)

### Service details

| Field | Value |
|-------|-------|
| Service type | Web Service |
| Runtime | Python 3 |
| Region | Singapore (or as configured) |
| Build command | `pip install -r backend/requirements.txt` |
| Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Auto-deploy | Yes (on push to `main`) |
| Live URL | `https://inventory-system-iaub.onrender.com` |

### Steps to redeploy or set up from scratch

1. Go to [dashboard.render.com](https://dashboard.render.com) and log in.
2. Click **New → Web Service**.
3. Connect the GitHub repo (`fugro-inventory`).
4. Set **Root Directory** to `backend/`.
5. Fill in build and start commands as above.
6. Under **Environment**, add all variables from the [Environment Variables](#environment-variables) section.
7. Click **Create Web Service**. Render will build and deploy automatically.

### Adding/updating environment variables on Render

1. Open the service on the Render dashboard.
2. Go to **Environment** tab.
3. Add or edit key-value pairs.
4. Click **Save Changes** — this triggers a redeploy.

---

## Deployment — Desktop Builds (GitHub Actions)

The CI/CD pipeline auto-builds distributable executables on every push to `main` (or on a tagged release, depending on workflow config).

### Windows (.exe)

Workflow file: `.github/workflows/build-windows.yml`

- Runs on a `windows-latest` GitHub runner
- Uses **PyInstaller** to package the PyQt6 app into a single `.exe`
- Uploads the artifact to GitHub Releases

### Linux (AppImage)

Workflow file: `.github/workflows/build-linux.yml`

- Runs on an `ubuntu-latest` GitHub runner
- Uses **PyInstaller** + `appimage-builder` (or equivalent)
- Uploads the AppImage to GitHub Releases

### Triggering a build manually

```bash
# Push a new tag to trigger a release build
git tag v1.x.x
git push origin v1.x.x
```

Or trigger manually from **GitHub → Actions → Select workflow → Run workflow**.

### Downloading builds

Go to: `https://github.com/<your-org>/fugro-inventory/releases`

---

## Credentials Reference

> ⚠️ Do NOT store real credentials here. This table shows what you need — obtain actual values from the team lead securely.

| Service | What you need | Where to get it |
|---------|--------------|-----------------|
| Supabase | Project URL, anon key, DB connection string | Supabase dashboard → Settings |
| Render | Account login, service dashboard access | Team lead / shared password manager |
| GitHub | Repo access, Actions secrets (`DATABASE_URL`, etc.) | GitHub org settings → Secrets |
| `.env` file | Fully populated local env file | Team lead |

### GitHub Actions secrets required

These must be set under **GitHub → Repo → Settings → Secrets and variables → Actions**:

| Secret name | Description |
|-------------|-------------|
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `SECRET_KEY` | App secret key for JWT |
| `RENDER_API_KEY` | (Optional) For triggering Render deploys via API |

---

## Known Issues & Notes

- **Render cold starts:** The free tier on Render spins down after inactivity. The first request after idle may take 30–60 seconds. Upgrade to a paid tier to avoid this.
- **Supabase connection pooling:** Use the **pooler connection string** (port `6543`) instead of the direct connection (port `5432`) if you hit connection limit errors under load.
- **PyQt6 on Linux:** Ensure `libxcb` and related Qt dependencies are installed on the target Linux machine if running the AppImage fails.
- **CSV import filenames:** The dashboard category display uses `csv_import_id` to derive category names from the original Excel import filename — do not rename import files after upload as this breaks the display logic.
- **Auto-save debounce:** The frontend uses a `QTimer`-based debounce (300ms default) for auto-save. If you're modifying the threading logic, test carefully to avoid race conditions between the `QThread` worker and the UI thread.