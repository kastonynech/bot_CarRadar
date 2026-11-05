import asyncio
import logging
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
    tasks = [asyncio.create_task(supervised(n, f)) for n, f in
             (("bot", run_bot), ("monitor", monitor_loop), ("sender", sender_loop))]
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


@app.get("/_probe/otomoto")  # TEMPORARY diagnostic, removed after use
async def probe_otomoto():
    import httpx
    from carradar.parsers.otomoto import UA
    out = {}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers={"User-Agent": UA, "Accept-Language": "pl"}) as c:
        for name, url in (("robots", "https://www.otomoto.pl/robots.txt"), ("search", "https://www.otomoto.pl/osobowe/bmw/seria-3?search%5Border%5D=created_at_first%3Adesc")):
            try:
                r = await c.get(url)
                out[name] = {"status": r.status_code, "len": len(r.text), "server": r.headers.get("server"), "via": r.headers.get("via"),
                             "x-cache": r.headers.get("x-cache"), "head": r.text[:250]}
            except Exception as e:
                out[name] = {"error": repr(e)}
        try:
            out["ip"] = (await c.get("https://api.ipify.org")).text
        except Exception as e:
            out["ip"] = repr(e)
    return out
