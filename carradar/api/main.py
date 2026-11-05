import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import func, select

from carradar.api.auth import current_user
from carradar.bot.handlers import router
from carradar.bot.instance import bot, dp
from carradar.db.models import Favorite, Filter, User
from carradar.db.session import Session
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


@app.get("/api/me")
async def me(tg: dict = Depends(current_user)):
    async with Session() as s:
        u = await s.get(User, tg["id"])
        if not u:
            return {"id": tg["id"], "registered": False}
        filters = await s.scalar(select(func.count()).select_from(Filter).where(Filter.user_id == u.id))
        favs = await s.scalar(select(func.count()).select_from(Favorite).where(Favorite.user_id == u.id))
    return {"id": u.id, "registered": True, "lang": u.lang, "created_at": u.created_at, "filters": filters, "favorites": favs}


@app.get("/_probe/olx")  # TEMPORARY diagnostic: how does OLX answer from this server's IP? removed after use
async def probe_olx():
    import httpx
    out = {}
    async with httpx.AsyncClient(timeout=15, follow_redirects=True,
                                 headers={"User-Agent": "Mozilla/5.0 (compatible; CarRadar/0.1; personal listing monitor)"}) as c:
        for name, url in (("robots", "https://www.olx.pl/robots.txt"),
                          ("api", "https://www.olx.pl/api/v1/offers/?offset=0&limit=3&category_id=84&sort_by=created_at:desc"),
                          ("html", "https://www.olx.pl/motoryzacja/samochody/?search%5Border%5D=created_at:desc")):
            try:
                r = await c.get(url)
                out[name] = {"status": r.status_code, "len": len(r.text), "head": r.text[:200]}
            except Exception as e:
                out[name] = {"error": repr(e)}
    return out
