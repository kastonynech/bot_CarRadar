"""Outbox worker: sends pending notifications. One message per (user, listing, kind).
Respects per-user settings: enabled, sources, photos, quiet hours, instant vs digest, price alerts."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from html import escape
from zoneinfo import ZoneInfo

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton as Btn, InlineKeyboardMarkup
from sqlalchemy import or_, select, update

from carradar.bot.instance import bot
from carradar.db.models import Filter, HiddenListing, Listing, ListingImage, Notification, PriceHistory, User
from carradar.db.session import Session

log = logging.getLogger("sender")
FUEL = {"petrol": "Benzyna", "diesel": "Diesel", "lpg": "LPG", "petrol-lpg": "Benzyna + LPG", "hybrid": "Hybryda",
        "plug-in-hybrid": "Hybryda Plug-in", "electric": "Elektryczny"}
GEARBOX = {"manual": "Manualna", "automatic": "Automatyczna"}
DEFAULT_NOTIFY = {"enabled": True, "sources": ["otomoto", "olx"], "photos": True, "mode": "instant", "digest_min": 60,
                  "price_alerts": True, "night": {"enabled": False, "from": "23:00", "to": "07:00"}}


def now():
    return datetime.now(timezone.utc)


def money(v: int | None, cur="PLN") -> str:
    return f"{v:,}".replace(",", " ") + (" zł" if cur == "PLN" else f" {cur}") if v is not None else "—"


def render(l: Listing, filter_names: list[str], old_price: int | None = None) -> str:
    d = (l.attrs or {}).get("display", {})
    rows = [("💰 Цена", money(l.price, l.currency)), ("📅 Год", l.year),
            ("🛣 Пробег", f"{l.mileage:,} km".replace(",", " ") if l.mileage is not None else None),
            ("⚙️ Двигатель", f"{l.engine_cc} cm³" if l.engine_cc else None), ("⛽ Топливо", d.get("fuel_type") or FUEL.get(l.fuel or "")),
            ("🔧 Коробка", d.get("gearbox") or GEARBOX.get(l.gearbox or "")), ("📍 Локация", l.city)]
    if old_price is not None:
        rows[0] = ("💰 Цена", f"{money(old_price)} → {money(l.price)}")
    body = "\n".join(f"{k}: {escape(str(v))}" for k, v in rows if v not in (None, ""))
    head = "💸 <b>Цена изменилась</b>" if old_price is not None else "🚗 <b>Найден новый автомобиль!</b>"
    flt = "\n".join(f"• {escape(n)}" for n in filter_names)
    tail = f"\n\nФильтр{'ы' if len(filter_names) > 1 else ''}:\n{flt}" if filter_names else ""
    return f"{head}\n\n<b>{escape(l.title)}</b>\n\n{body}\n\nИсточник: {l.source.upper()}{tail}"


def keyboard(l: Listing) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="Открыть объявление", url=l.url)],
        [Btn(text="⭐ Добавить в избранное", callback_data=f"fav:{l.id}")],
        [Btn(text="🚫 Больше не показывать", callback_data=f"hide:{l.id}")]])


def quiet_until(cfg: dict, tz: str) -> datetime | None:
    """If quiet hours are active right now, return when they end (UTC)."""
    n = cfg.get("night") or {}
    if not n.get("enabled"):
        return None
    try:
        z = ZoneInfo(tz)
    except Exception:
        z = ZoneInfo("Europe/Warsaw")
    loc = datetime.now(z)
    fh, fm = map(int, n["from"].split(":"))
    th, tm = map(int, n["to"].split(":"))
    cur, a, b = loc.hour * 60 + loc.minute, fh * 60 + fm, th * 60 + tm
    inside = (a <= cur < b) if a < b else (cur >= a or cur < b)
    if not inside:
        return None
    end = loc.replace(hour=th, minute=tm, second=0, microsecond=0)
    if end <= loc:
        end += timedelta(days=1)
    return end.astimezone(timezone.utc)


async def _deliver(user_id: int, text: str, kb, photo: str | None, photos_on: bool):
    if photo and photos_on:
        try:
            await bot.send_photo(user_id, photo, caption=text, reply_markup=kb)
            return
        except TelegramForbiddenError:
            raise
        except TelegramRetryAfter:
            raise
        except Exception:  # bad/blocked image URL: fall back to text
            pass
    await bot.send_message(user_id, text, reply_markup=kb)


async def send_one(n: Notification):
    async with Session() as s:
        user = await s.get(User, n.user_id)
        l = await s.get(Listing, n.listing_id)
        cfg = {**DEFAULT_NOTIFY, **(user.notify or {})}
        until = quiet_until(cfg, user.tz)
        if until:  # quiet hours: hold until they end
            await s.execute(update(Notification).where(Notification.id == n.id).values(deliver_after=until))
            await s.commit()
            return
        photo = (await s.execute(select(ListingImage.url).where(ListingImage.listing_id == l.id)
                                 .order_by(ListingImage.pos).limit(1))).scalar()
        names = (await s.execute(select(Filter.name).where(Filter.id.in_(n.filter_ids)))).scalars().all()
        hidden = await s.get(HiddenListing, (n.user_id, n.listing_id))
        old = None
        if n.kind == "price":
            prices = (await s.execute(select(PriceHistory.price).where(PriceHistory.listing_id == l.id)
                                      .order_by(PriceHistory.id.desc()).limit(2))).scalars().all()
            old = prices[1] if len(prices) == 2 else None
        skip = (hidden or user.is_blocked or not cfg["enabled"] or l.source not in cfg["sources"]
                or (n.kind == "price" and (not cfg["price_alerts"] or old is None)))
        status = "skipped" if skip else "sent"
        if not skip:
            try:
                await _deliver(n.user_id, render(l, list(names), old), keyboard(l), photo, cfg["photos"])
            except TelegramForbiddenError:
                await s.execute(update(User).where(User.id == n.user_id).values(is_blocked=True))
                status = "failed"
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                return
            except Exception as e:
                log.warning("send failed n=%s: %r", n.id, e)
                status = "failed" if n.attempts >= 2 else "pending"
                await s.execute(update(Notification).where(Notification.id == n.id).values(attempts=n.attempts + 1))
        await s.execute(update(Notification).where(Notification.id == n.id).values(
            status=status, **({"sent_at": now()} if status == "sent" else {})))
        await s.commit()


async def send_digests():
    """Users in digest mode get one summary message every `digest_min` minutes (if anything is pending)."""
    async with Session() as s:
        users = (await s.execute(select(User).where(User.notify["mode"].astext == "digest", ~User.is_blocked))).scalars().all()
    for u in users:
        cfg = {**DEFAULT_NOTIFY, **(u.notify or {})}
        last = datetime.fromisoformat(cfg["last_digest"]) if cfg.get("last_digest") else None
        if (last and now() - last < timedelta(minutes=cfg["digest_min"])) or quiet_until(cfg, u.tz):
            continue
        async with Session() as s:
            rows = (await s.execute(select(Notification, Listing).join(Listing, Listing.id == Notification.listing_id)
                                    .where(Notification.user_id == u.id, Notification.status == "pending", Notification.kind == "new")
                                    .order_by(Notification.id).limit(15))).all()
            hidden = set((await s.execute(select(HiddenListing.listing_id).where(HiddenListing.user_id == u.id))).scalars())
            rows = [(n, l) for n, l in rows if l.id not in hidden and l.source in cfg["sources"]]
            if not rows:
                continue
            lines = [f'• <a href="{l.url}">{escape(l.title)}</a> — {money(l.price)}'
                     f'{", " + str(l.year) if l.year else ""}{", " + escape(l.city) if l.city else ""}' for _, l in rows]
            try:
                await bot.send_message(u.id, f"🚗 <b>Подборка: {len(rows)} новых авто</b>\n\n" + "\n".join(lines), disable_web_page_preview=True)
            except TelegramForbiddenError:
                await s.execute(update(User).where(User.id == u.id).values(is_blocked=True))
                await s.commit()
                continue
            except Exception as e:
                log.warning("digest failed user=%s: %r", u.id, e)
                continue
            ids = [n.id for n, _ in rows]
            await s.execute(update(Notification).where(Notification.id.in_(ids)).values(status="sent", sent_at=now()))
            await s.execute(update(User).where(User.id == u.id).values(notify={**(u.notify or {}), "last_digest": now().isoformat()}))
            await s.commit()


async def sender_loop():
    log.info("sender started")
    tick = 0
    while True:
        async with Session() as s:
            pending = (await s.execute(
                select(Notification).join(User, User.id == Notification.user_id)
                .where(Notification.status == "pending", or_(Notification.deliver_after.is_(None), Notification.deliver_after <= now()))
                .where(or_(User.notify["mode"].astext.is_(None), User.notify["mode"].astext != "digest", Notification.kind == "price"))
                .order_by(Notification.id).limit(20))).scalars().all()
        for n in pending:
            await send_one(n)
            await asyncio.sleep(0.05)  # stay well under Telegram's 30 msg/s
        tick += 1
        if tick % 30 == 0:
            await send_digests()
        await asyncio.sleep(1 if pending else 2)
