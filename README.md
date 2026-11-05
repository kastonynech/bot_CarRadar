# CarRadar

Telegram bot that monitors new car listings (OTOMOTO now, OLX when accessible) and notifies on matches.
Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Run locally
    cp .env.example .env   # fill BOT_TOKEN, DATABASE_URL (Postgres), ADMIN_IDS
    cd backend && pip install -r requirements.txt && alembic upgrade head && python -m carradar.main
Run only ONE instance per bot token (local and Render polling would conflict).

## Render (free web service)
Root Directory `backend` · Build `pip install -r requirements.txt` · Start `alembic upgrade head && python -m carradar.main`
Health check `/health` (ping it with UptimeRobot so the free instance stays awake).
Env: BOT_TOKEN, DATABASE_URL, ADMIN_IDS, WEBAPP_URL, PYTHON_VERSION=3.12.7

## Tests
    cd backend && python -m pytest tests
