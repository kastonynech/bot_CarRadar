"""REST API for the Mini App. Every route authenticates via verified Telegram initData."""
import asyncio
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert

from carradar.api.auth import current_user
from carradar.db.models import (AppSetting, ErrorLog, Favorite, Filter, FilterQuery, HiddenListing, Listing,
                                ListingImage, Match, Notification, ParserStatus, PriceHistory, SearchHistory,
                                SearchQuery, User)
from carradar.db.session import Session
from carradar.monitoring.queries import register_filter
from carradar.parsers import PARSERS
from carradar.parsers.otomoto import UA, fetch_detail
from carradar.shared.config import settings
from carradar.shared.filterspec import FilterSpec

router = APIRouter(prefix="/api")
LANGS = {"pl", "ru", "uk", "en"}
DEFAULT_NOTIFY = {"enabled": True, "sources": ["otomoto", "olx"], "photos": True, "mode": "instant",
                  "digest_min": 60, "price_alerts": True, "night": {"enabled": False, "from": "23:00", "to": "07:00"}}
MAX_FILTERS = 50

# ---------- auth, rate limit ----------
_hits: dict[int, deque] = defaultdict(deque)


async def user_dep(tg: dict = Depends(current_user)) -> User:
    now = time.monotonic()
    q = _hits[tg["id"]]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= 240:  # per user per minute
        raise HTTPException(429, "Too many requests")
    q.append(now)
    lang = (tg.get("language_code") or "en")[:2]
    async with Session() as s:
        await s.execute(insert(User).values(id=tg["id"], username=tg.get("username"), lang=lang if lang in LANGS else "en", notify={})
                        .on_conflict_do_update(index_elements=["id"], set_={"username": tg.get("username")}))
        await s.commit()
        u = await s.get(User, tg["id"])
    if u.is_blocked:
        raise HTTPException(403, "blocked")
    return u


async def admin_dep(u: User = Depends(user_dep)) -> User:
    if u.id not in settings.admins:
        raise HTTPException(403, "admin only")
    return u


def now():
    return datetime.now(timezone.utc)


def day_start(tz: str) -> datetime:
    try:
        z = ZoneInfo(tz)
    except Exception:
        z = ZoneInfo("Europe/Warsaw")
    return datetime.now(z).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


# ---------- serialization ----------
IMG = select(ListingImage.url).where(ListingImage.listing_id == Listing.id).order_by(ListingImage.pos).limit(1).scalar_subquery()


def card(l: Listing, image: str | None, favs: set[int]) -> dict:
    fresh = l.first_seen_at and (now() - l.first_seen_at) < timedelta(hours=3)
    return {"id": l.id, "source": l.source, "title": l.title, "make": l.make, "model": l.model, "price": l.price,
            "currency": l.currency, "year": l.year, "mileage": l.mileage, "engine_cc": l.engine_cc, "power_hp": l.power_hp,
            "fuel": l.fuel, "gearbox": l.gearbox, "body": l.body, "drive": l.drive, "city": l.city, "region": l.region,
            "seller_type": l.seller_type, "url": l.url, "image": image, "published_at": l.published_at,
            "first_seen_at": l.first_seen_at, "is_active": l.is_active, "is_new": bool(fresh), "is_fav": l.id in favs}


async def fav_ids(s, uid: int) -> set[int]:
    return set((await s.execute(select(Favorite.listing_id).where(Favorite.user_id == uid))).scalars())


# ---------- me / settings ----------
class SettingsIn(BaseModel):
    lang: str | None = None
    theme: str | None = Field(None, pattern="^(dark|light)$")
    tz: str | None = None
    notify: dict | None = None


def merged_notify(u: User) -> dict:
    return {**DEFAULT_NOTIFY, **(u.notify or {})}


@router.get("/me")
async def me(u: User = Depends(user_dep)):
    async with Session() as s:
        filters = await s.scalar(select(func.count()).select_from(Filter).where(Filter.user_id == u.id))
        favs = await s.scalar(select(func.count()).select_from(Favorite).where(Favorite.user_id == u.id))
        found = await s.scalar(select(func.count(func.distinct(Match.listing_id))).select_from(Match)
                               .join(Filter, Filter.id == Match.filter_id).where(Filter.user_id == u.id))
    return {"id": u.id, "username": u.username, "lang": u.lang, "theme": u.theme, "tz": u.tz, "created_at": u.created_at,
            "notify": merged_notify(u), "filters": filters, "favorites": favs, "found": found,
            "is_admin": u.id in settings.admins}


@router.patch("/me")
async def patch_me(body: SettingsIn, u: User = Depends(user_dep)):
    vals = {}
    if body.lang:
        if body.lang not in LANGS:
            raise HTTPException(422, "bad lang")
        vals["lang"] = body.lang
    if body.theme:
        vals["theme"] = body.theme
    if body.tz:
        try:
            ZoneInfo(body.tz)
        except Exception:
            raise HTTPException(422, "bad timezone")
        vals["tz"] = body.tz
    if body.notify is not None:
        cur = merged_notify(u)
        n = body.notify
        if "enabled" in n: cur["enabled"] = bool(n["enabled"])
        if "photos" in n: cur["photos"] = bool(n["photos"])
        if "price_alerts" in n: cur["price_alerts"] = bool(n["price_alerts"])
        if n.get("mode") in ("instant", "digest"): cur["mode"] = n["mode"]
        if "digest_min" in n: cur["digest_min"] = min(max(int(n["digest_min"]), 15), 1440)
        if "sources" in n: cur["sources"] = [x for x in n["sources"] if x in ("otomoto", "olx")]
        if isinstance(n.get("night"), dict):
            ni = n["night"]
            ok = lambda t: isinstance(t, str) and len(t) == 5 and t[2] == ":" and t[:2].isdigit() and t[3:].isdigit()  # noqa: E731
            cur["night"] = {"enabled": bool(ni.get("enabled")), "from": ni["from"] if ok(ni.get("from")) else "23:00",
                            "to": ni["to"] if ok(ni.get("to")) else "07:00"}
        vals["notify"] = cur
    if vals:
        async with Session() as s:
            await s.execute(update(User).where(User.id == u.id).values(**vals))
            await s.commit()
    return {"ok": True}


# ---------- dashboard ----------
@router.get("/dashboard")
async def dashboard(u: User = Depends(user_dep)):
    t0 = day_start(u.tz)
    mine = select(Match.listing_id, Match.created_at).join(Filter, Filter.id == Match.filter_id).where(Filter.user_id == u.id).subquery()

    async def count_since(s, since):
        return await s.scalar(select(func.count(func.distinct(mine.c.listing_id))).where(mine.c.created_at >= since))

    async with Session() as s:
        stats = {"today": await count_since(s, t0), "week": await count_since(s, now() - timedelta(days=7)),
                 "month": await count_since(s, now() - timedelta(days=30))}
        active = await s.scalar(select(func.count()).select_from(Filter).where(Filter.user_id == u.id, Filter.active))
        favs = await s.scalar(select(func.count()).select_from(Favorite).where(Favorite.user_id == u.id))
        favset = await fav_ids(s, u.id)
        hidden = select(HiddenListing.listing_id).where(HiddenListing.user_id == u.id)
        rows = (await s.execute(select(Listing, IMG).where(Listing.id.in_(select(mine.c.listing_id)), Listing.id.not_in(hidden))
                                .order_by(Listing.first_seen_at.desc()).limit(8))).all()
        sts = (await s.execute(select(ParserStatus))).scalars().all()
        iv = await s.get(AppSetting, "poll_interval_sec")
    parsers = {p.source: {"state": p.state, "last_success_at": p.last_success_at, "last_error": p.last_error} for p in sts}
    parsers.setdefault("otomoto", {"state": "unknown", "last_success_at": None, "last_error": None})
    parsers["olx"] = {"state": "unavailable", "last_success_at": None,  # honest: OLX blocks automated access (403)
                      "last_error": "OLX blocks automated access (HTTP 403 from CloudFront); not monitored."}
    last = max((p["last_success_at"] for p in parsers.values() if p["last_success_at"]), default=None)
    return {"stats": stats, "active_filters": active, "favorites": favs, "latest": [card(l, i, favset) for l, i in rows],
            "parsers": parsers, "last_update": last, "interval": int(iv.value["v"]) if iv else settings.poll_interval_sec}


# ---------- filters ----------
class FilterIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    sources: list[str] = ["otomoto"]
    params: dict = {}
    active: bool = True
    notify: bool = True


def fdict(f: Filter) -> dict:
    return {"id": f.id, "name": f.name, "sources": f.sources, "params": f.params, "active": f.active, "notify": f.notify,
            "found_total": f.found_total, "found_new": f.found_new, "created_at": f.created_at}


def validate_filter(body: FilterIn) -> dict:
    srcs = [x for x in body.sources if x in ("otomoto", "olx")]
    if not srcs:
        raise HTTPException(422, "choose a source")
    if "otomoto" not in srcs:
        raise HTTPException(422, "OLX is unavailable (blocks automated access); choose OTOMOTO")
    try:
        return FilterSpec(**body.params).model_dump()
    except Exception as e:
        raise HTTPException(422, f"invalid filter: {e}")


@router.get("/filters")
async def list_filters(u: User = Depends(user_dep)):
    async with Session() as s:
        fs = (await s.execute(select(Filter).where(Filter.user_id == u.id).order_by(Filter.id))).scalars().all()
    return [fdict(f) for f in fs]


@router.post("/filters")
async def create_filter(body: FilterIn, u: User = Depends(user_dep)):
    params = validate_filter(body)
    async with Session() as s:
        if await s.scalar(select(func.count()).select_from(Filter).where(Filter.user_id == u.id)) >= MAX_FILTERS:
            raise HTTPException(422, "filter limit reached")
        for d in (await s.execute(select(Filter).where(Filter.user_id == u.id))).scalars():
            if d.params == params:  # same preset already saved: client asks whether to replace
                raise HTTPException(409, f"duplicate:{d.id}")
        f = Filter(user_id=u.id, name=body.name.strip(), sources=["otomoto"], params=params, active=body.active, notify=body.notify)
        s.add(f)
        await s.flush()
        await register_filter(s, f)
        await s.commit()
        return fdict(f)


async def own_filter(s, fid: int, uid: int) -> Filter:
    f = await s.get(Filter, fid)
    if not f or f.user_id != uid:
        raise HTTPException(404, "filter not found")
    return f


@router.put("/filters/{fid}")
async def update_filter(fid: int, body: FilterIn, u: User = Depends(user_dep)):
    params = validate_filter(body)
    async with Session() as s:
        f = await own_filter(s, fid, u.id)
        f.name, f.sources, f.params, f.active, f.notify = body.name.strip(), ["otomoto"], params, body.active, body.notify
        await s.flush()
        await register_filter(s, f)
        await s.commit()
        return fdict(f)


class FilterPatch(BaseModel):
    active: bool | None = None
    notify: bool | None = None


@router.patch("/filters/{fid}")
async def patch_filter(fid: int, body: FilterPatch, u: User = Depends(user_dep)):
    async with Session() as s:
        f = await own_filter(s, fid, u.id)
        if body.active is not None:
            f.active = body.active
        if body.notify is not None:
            f.notify = body.notify
        await s.commit()
        return fdict(f)


@router.post("/filters/{fid}/copy")
async def copy_filter(fid: int, u: User = Depends(user_dep)):
    async with Session() as s:
        f = await own_filter(s, fid, u.id)
        c = Filter(user_id=u.id, name=f"{f.name} (copy)"[:120], sources=f.sources, params=f.params, active=False, notify=f.notify)
        s.add(c)
        await s.flush()
        await register_filter(s, c)
        await s.commit()
        return fdict(c)


@router.post("/filters/{fid}/seen")
async def filter_seen(fid: int, u: User = Depends(user_dep)):
    async with Session() as s:
        await own_filter(s, fid, u.id)
        await s.execute(update(Filter).where(Filter.id == fid).values(found_new=0))
        await s.commit()
    return {"ok": True}


@router.delete("/filters/{fid}")
async def delete_filter(fid: int, u: User = Depends(user_dep)):
    async with Session() as s:
        await own_filter(s, fid, u.id)
        await s.execute(delete(Filter).where(Filter.id == fid))
        await s.execute(delete(SearchQuery).where(SearchQuery.id.not_in(select(FilterQuery.query_id))))
        await s.commit()
    return {"ok": True}


# ---------- catalog ----------
SORTS = {"new": [Listing.published_at.desc().nullslast(), Listing.id.desc()],
         "found": [Listing.first_seen_at.desc()],
         "cheap": [Listing.price.asc().nullslast()], "expensive": [Listing.price.desc().nullslast()],
         "year": [Listing.year.desc().nullslast()], "mileage": [Listing.mileage.asc().nullslast()]}


def visible_clause(uid: int, filter_id: int | None, only_fav: bool):
    fav = select(Favorite.listing_id).where(Favorite.user_id == uid)
    if only_fav:
        return Listing.id.in_(fav)
    m = select(Match.listing_id).join(Filter, Filter.id == Match.filter_id).where(Filter.user_id == uid)
    if filter_id:
        m = m.where(Filter.id == filter_id)
        return Listing.id.in_(m)
    return or_(Listing.id.in_(m), Listing.id.in_(fav))


@router.get("/listings")
async def listings(u: User = Depends(user_dep), q: str = "", sort: str = "new", source: str = "", filter_id: int | None = None,
                   fav: bool = False, fuel: str = "", gearbox: str = "", price_min: int | None = None, price_max: int | None = None,
                   year_min: int | None = None, year_max: int | None = None, active: bool | None = None,
                   offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)):
    hidden = select(HiddenListing.listing_id).where(HiddenListing.user_id == u.id)
    cond = [visible_clause(u.id, filter_id, fav), Listing.id.not_in(hidden)]
    if q.strip():
        like = f"%{q.strip()[:60]}%"
        cond.append(or_(Listing.title.ilike(like), Listing.make.ilike(like), Listing.model.ilike(like), Listing.city.ilike(like)))
    if source in ("otomoto", "olx"): cond.append(Listing.source == source)
    if fuel: cond.append(Listing.fuel == fuel)
    if gearbox: cond.append(Listing.gearbox == gearbox)
    if price_min is not None: cond.append(Listing.price >= price_min)
    if price_max is not None: cond.append(Listing.price <= price_max)
    if year_min is not None: cond.append(Listing.year >= year_min)
    if year_max is not None: cond.append(Listing.year <= year_max)
    if active is not None: cond.append(Listing.is_active == active)
    async with Session() as s:
        if len(q.strip()) >= 2 and offset == 0:
            last = await s.scalar(select(SearchHistory.text).where(SearchHistory.user_id == u.id).order_by(SearchHistory.id.desc()).limit(1))
            if last != q.strip()[:200]:
                s.add(SearchHistory(user_id=u.id, text=q.strip()[:200]))
                await s.commit()
        rows = (await s.execute(select(Listing, IMG).where(and_(*cond)).order_by(*SORTS.get(sort, SORTS["new"]))
                                .offset(offset).limit(limit + 1))).all()
        favset = await fav_ids(s, u.id)
    return {"items": [card(l, i, favset) for l, i in rows[:limit]], "has_more": len(rows) > limit}


# ---------- listing detail ----------
_detail_gate = asyncio.Semaphore(2)  # polite: at most 2 ad-page fetches at once


async def enrich(l: Listing) -> None:
    """Fetch the full ad page once (when someone opens the listing) and cache everything in the DB."""
    if (l.attrs or {}).get("detail") or l.source != "otomoto":
        return
    async with _detail_gate:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers={"User-Agent": UA, "Accept-Language": "pl"}) as c:
                d = await fetch_detail(c, l.url)
        except Exception:
            return  # show what we have; try again next open
    async with Session() as s:
        if d is None:
            await s.execute(update(Listing).where(Listing.id == l.id).values(is_active=False, last_checked_at=now()))
        else:
            attrs = {**(l.attrs or {}), "detail": {k: v for k, v in d.items() if k not in ("photos", "description")}}
            vals = dict(attrs=attrs, last_checked_at=now(), is_active=d["status"] == "ACTIVE",
                        description=d["description"] or l.description, vin=d["vin"] or l.vin, body=d["body"] or l.body,
                        drive=d["drive"] or l.drive, seller_name=d["seller_name"] or l.seller_name,
                        seller_type=d["seller_type"] or l.seller_type)
            await s.execute(update(Listing).where(Listing.id == l.id).values(**vals))
            if d["photos"]:
                await s.execute(delete(ListingImage).where(ListingImage.listing_id == l.id))
                s.add_all(ListingImage(listing_id=l.id, pos=i, url=p) for i, p in enumerate(d["photos"][:30]))
        await s.commit()


@router.get("/listings/{lid}")
async def listing_detail(lid: int, u: User = Depends(user_dep)):
    async with Session() as s:
        l = await s.get(Listing, lid)
    if not l:
        raise HTTPException(404, "listing not found")
    await enrich(l)
    async with Session() as s:
        l = await s.get(Listing, lid)
        imgs = (await s.execute(select(ListingImage.url).where(ListingImage.listing_id == lid).order_by(ListingImage.pos))).scalars().all()
        hist = (await s.execute(select(PriceHistory).where(PriceHistory.listing_id == lid).order_by(PriceHistory.seen_at))).scalars().all()
        favset = await fav_ids(s, u.id)
        names = (await s.execute(select(Filter.name).join(Match, Match.filter_id == Filter.id)
                                 .where(Match.listing_id == lid, Filter.user_id == u.id))).scalars().all()
        sim = select(Listing, IMG).where(Listing.id != lid, Listing.is_active, Listing.make == l.make, Listing.model == l.model)
        if l.price:
            sim = sim.where(Listing.price.between(int(l.price * .75), int(l.price * 1.25)))
            sim = sim.order_by(func.abs(Listing.price - l.price))
        similar = (await s.execute(sim.limit(6))).all()
        dups = []
        if l.make and l.model and l.year and l.price:  # cross-source "possible duplicate" candidates; never auto-merged
            dq = select(Listing, IMG).where(Listing.id != lid, Listing.source != l.source, Listing.make == l.make,
                                            Listing.model == l.model, Listing.year == l.year,
                                            Listing.price.between(int(l.price * .95), int(l.price * 1.05)))
            if l.mileage:
                dq = dq.where(Listing.mileage.between(int(l.mileage * .98), int(l.mileage * 1.02) + 1))
            dups = (await s.execute(dq.limit(3))).all()
    d = card(l, imgs[0] if imgs else None, favset)
    return {**d, "images": imgs, "description": l.description, "vin": l.vin, "seller_name": l.seller_name,
            "detail": (l.attrs or {}).get("detail"), "display": (l.attrs or {}).get("display", {}),
            "price_history": [{"price": h.price, "at": h.seen_at} for h in hist], "filters": list(names),
            "similar": [card(x, i, favset) for x, i in similar], "possible_duplicates": [card(x, i, favset) for x, i in dups],
            "last_checked_at": l.last_checked_at}


# ---------- favorites / hidden / compare ----------
@router.put("/favorites/{lid}")
async def add_fav(lid: int, u: User = Depends(user_dep)):
    async with Session() as s:
        if not await s.get(Listing, lid):
            raise HTTPException(404, "listing not found")
        await s.execute(insert(Favorite).values(user_id=u.id, listing_id=lid).on_conflict_do_nothing())
        await s.commit()
    return {"ok": True}


@router.delete("/favorites/{lid}")
async def del_fav(lid: int, u: User = Depends(user_dep)):
    async with Session() as s:
        await s.execute(delete(Favorite).where(Favorite.user_id == u.id, Favorite.listing_id == lid))
        await s.commit()
    return {"ok": True}


@router.put("/hidden/{lid}")
async def hide(lid: int, u: User = Depends(user_dep)):
    async with Session() as s:
        if not await s.get(Listing, lid):
            raise HTTPException(404, "listing not found")
        await s.execute(insert(HiddenListing).values(user_id=u.id, listing_id=lid).on_conflict_do_nothing())
        await s.commit()
    return {"ok": True}


@router.get("/compare")
async def compare(ids: str, u: User = Depends(user_dep)):
    try:
        want = [int(x) for x in ids.split(",")][:4]
    except ValueError:
        raise HTTPException(422, "bad ids")
    async with Session() as s:
        rows = (await s.execute(select(Listing, IMG).where(Listing.id.in_(want)))).all()
        favset = await fav_ids(s, u.id)
    order = {i: n for n, i in enumerate(want)}
    return [{**card(l, i, favset), "seller_name": l.seller_name} for l, i in sorted(rows, key=lambda r: order[r[0].id])]


@router.get("/favorites/history")
async def fav_price_history(u: User = Depends(user_dep)):
    """Price changes of favorited listings (only changes we actually observed)."""
    async with Session() as s:
        rows = (await s.execute(select(PriceHistory.listing_id, PriceHistory.price, PriceHistory.seen_at)
                                .where(PriceHistory.listing_id.in_(select(Favorite.listing_id).where(Favorite.user_id == u.id)))
                                .order_by(PriceHistory.listing_id, PriceHistory.seen_at))).all()
    out: dict[int, list] = {}
    for lid, price, at in rows:
        out.setdefault(lid, []).append({"price": price, "at": at})
    return {k: v for k, v in out.items() if len(v) > 1}


# ---------- admin ----------
@router.get("/admin/overview")
async def admin_overview(_: User = Depends(admin_dep)):
    async with Session() as s:
        cnt = lambda t, *w: s.scalar(select(func.count()).select_from(t).where(*w))  # noqa: E731
        data = {"users": await cnt(User), "blocked": await cnt(User, User.is_blocked), "filters_active": await cnt(Filter, Filter.active),
                "filters_total": await cnt(Filter), "listings": await cnt(Listing), "listings_active": await cnt(Listing, Listing.is_active),
                "notifications_sent": await cnt(Notification, Notification.status == "sent"),
                "notifications_pending": await cnt(Notification, Notification.status == "pending"),
                "notifications_failed": await cnt(Notification, Notification.status == "failed"),
                "queries": await cnt(SearchQuery)}
        per_src = (await s.execute(select(Listing.source, func.count()).group_by(Listing.source))).all()
        sts = (await s.execute(select(ParserStatus))).scalars().all()
        errs = (await s.execute(select(ErrorLog).order_by(ErrorLog.id.desc()).limit(20))).scalars().all()
        iv = await s.get(AppSetting, "poll_interval_sec")
        new_1h = await cnt(Listing, Listing.first_seen_at >= now() - timedelta(hours=1))
        db_ms = None
        t = time.perf_counter()
        await s.execute(select(1))
        db_ms = round((time.perf_counter() - t) * 1000, 1)
    return {**data, "by_source": {k: v for k, v in per_src}, "new_listings_1h": new_1h, "db_ping_ms": db_ms,
            "parsers": [{"source": p.source, "state": p.state, "last_success_at": p.last_success_at, "last_error": p.last_error,
                         "requests": p.requests_total, "errors": p.errors_total, "paused_until": p.paused_until} for p in sts],
            "errors": [{"source": e.source, "message": e.message, "at": e.created_at} for e in errs],
            "interval": int(iv.value["v"]) if iv else settings.poll_interval_sec}


class IntervalIn(BaseModel):
    seconds: int = Field(ge=15, le=3600)


@router.post("/admin/interval")
async def admin_interval(body: IntervalIn, _: User = Depends(admin_dep)):
    async with Session() as s:
        await s.execute(insert(AppSetting).values(key="poll_interval_sec", value={"v": body.seconds})
                        .on_conflict_do_update(index_elements=["key"], set_={"value": {"v": body.seconds}}))
        await s.commit()
    return {"ok": True}


@router.post("/admin/restart/{source}")
async def admin_restart(source: str, _: User = Depends(admin_dep)):
    """Un-pause a parser and poll everything of that source on the next tick."""
    if source not in PARSERS:
        raise HTTPException(404, "unknown source")
    async with Session() as s:
        await s.execute(update(ParserStatus).where(ParserStatus.source == source).values(paused_until=None, state="unknown"))
        await s.execute(update(SearchQuery).where(SearchQuery.source == source).values(next_poll_at=None, fail_count=0))
        await s.commit()
    return {"ok": True}


@router.get("/admin/users")
async def admin_users(_: User = Depends(admin_dep), limit: int = Query(50, le=200)):
    async with Session() as s:
        rows = (await s.execute(select(User, func.count(Filter.id)).outerjoin(Filter, Filter.user_id == User.id)
                                .group_by(User.id).order_by(User.created_at.desc()).limit(limit))).all()
    return [{"id": u.id, "username": u.username, "lang": u.lang, "blocked": u.is_blocked, "created_at": u.created_at, "filters": n}
            for u, n in rows]


@router.post("/admin/users/{uid}/block")
async def admin_block(uid: int, blocked: bool = True, admin: User = Depends(admin_dep)):
    if uid in settings.admins:
        raise HTTPException(422, "cannot block an admin")
    async with Session() as s:
        await s.execute(update(User).where(User.id == uid).values(is_blocked=blocked))
        await s.commit()
    return {"ok": True}
