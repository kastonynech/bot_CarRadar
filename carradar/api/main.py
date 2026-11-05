import asyncio
import logging
import os
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from carradar.api.routes import router as api_router
from carradar.bot.handlers import router
from carradar.bot.instance import bot, dp
from carradar.monitoring.main import monitor_loop
from carradar.notifications.sender import sender_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("app")


async def supervised(name, fn):
    """Auto-recovery: if a worker dies, log and restart it."""
    while True:
        try:
            await fn()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("%s crashed, restarting in 5s", name)
            await asyncio.sleep(5)


async def run_bot():
    await bot.delete_webhook()
    await dp.start_polling(bot, handle_signals=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    dp.include_router(router)
    workers = [("bot", run_bot), ("sender", sender_loop)]
    # Render's datacenter IP is blocked by the sources (HTTP 403, CloudFront), so there the monitor is off by default;
    # run `python -m carradar.monitoring.main` from an IP the sources accept. RUN_MONITOR=1 forces it on.
    if os.environ.get("RUN_MONITOR", "0" if os.environ.get("RENDER") else "1") == "1":
        workers.append(("monitor", monitor_loop))
    else:
        log.warning("monitor disabled in this process (RENDER=%s)", os.environ.get("RENDER"))
    tasks = [asyncio.create_task(supervised(n, f)) for n, f in workers]
    yield
    for t in tasks:
        t.cancel()
    await bot.session.close()


app = FastAPI(title="CarRadar", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"ok": True}


app.include_router(api_router)

DIST = Path(__file__).resolve().parents[2] / "miniapp" / "dist"
if DIST.exists():  # built Mini App is committed to git, served from the same origin as the API
    app.mount("/", StaticFiles(directory=DIST, html=True), name="miniapp")

