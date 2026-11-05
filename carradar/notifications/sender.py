"""Outbox worker: sends pending notifications. One message per (user, listing)."""
import asyncio
import logging
from datetime import datetime, timezone
from html import escape

from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardButton as Btn, InlineKeyboardMarkup
from sqlalchemy import or_, select, update

from carradar.bot.instance import bot
from carradar.db.models import Filter, HiddenListing, Listing, ListingImage, Notification, User
from carradar.db.session import Session

log = logging.getLogger("sender")
FUEL = {"petrol": "Benzyna", "diesel": "Diesel", "lpg": "LPG", "petrol-lpg": "Benzyna + LPG", "hybrid": "Hybryda",
        "plug-in-hybrid": "Hybryda Plug-in", "electric": "Elektryczny"}
GEARBOX = {"manual": "Manualna", "automatic": "Automatyczna"}
DEFAULT_NOTIFY = {"enabled": True, "sources": ["otomoto", "olx"], "photos": True}


def money(v: int | None, cur="PLN") -> str:
    return f"{v:,}".replace(",", " ") + (" zł" if cur == "PLN" else f" {cur}") if v is not None else "—"


def render(l: Listing, filter_names: list[str]) -> str:
    d = (l.attrs or {}).get("display", {})
    rows = [("💰 Цена", money(l.price, l.currency)), ("📅 Год", l.year), ("🛣 Пробег", f"{l.mileage:,} km".replace(",", " ") if l.mileage is not None else None),
            ("⚙️ Двигатель", f"{l.engine_cc} cm³" if l.engine_cc else None), ("⛽ Топливо", d.get("fuel_type") or FUEL.get(l.fuel or "")),
            ("🔧 Коробка", d.get("gearbox") or GEARBOX.get(l.gearbox or "")), ("📍 Локация", l.city)]
    body = "\n".join(f"{k}: {escape(str(v))}" for k, v in rows if v not in (None, ""))
    flt = "\n".join(f"• {escape(n)}" for n in filter_names)
    return (f"🚗 <b>Найден новый автомобиль!</b>\n\n<b>{escape(l.title)}</b>\n\n{body}\n\n"
            f"Источник: {l.source.upper()}\n\nФильтр{'ы' if len(filter_names) > 1 else ''}:\n{flt}")


def keyboard(l: Listing) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text="Открыть объявление", url=l.url)],
        [Btn(text="⭐ Добавить в избранное", callback_data=f"fav:{l.id}")],
        [Btn(text="🚫 Больше не показывать", callback_data=f"hide:{l.id}")]])


async def send_one(n: Notification):
    async with Session() as s:
        user = await s.get(User, n.user_id)
        l = await s.get(Listing, n.listing_id)
        photo = (await s.execute(select(ListingImage.url).where(ListingImage.listing_id == l.id)
                                 .order_by(ListingImage.pos).limit(1))).scalar()
        names = (await s.execute(select(Filter.name).where(Filter.id.in_(n.filter_ids)))).scalars().all()
        hidden = await s.get(HiddenListing, (n.user_id, n.listing_id))
        cfg = {**DEFAULT_NOTIFY, **(user.notify or {})}
        skip = hidden or user.is_blocked or not cfg["enabled"] or l.source not in cfg["sources"]
        status = "skipped" if skip else "sent"
        if not skip:
            text, kb = render(l, list(names)), keyboard(l)
            try:
                if photo and cfg["photos"]:
                    try:
                        await bot.send_photo(n.user_id, photo, caption=text, reply_markup=kb)
                    except TelegramForbiddenError:
                        raise
                    except Exception:  # bad/blocked image URL: fall back to text
                        await bot.send_message(n.user_id, text, reply_markup=kb)
                else:
                    await bot.send_message(n.user_id, text, reply_markup=kb)
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
            status=status, **({"sent_at": datetime.now(timezone.utc)} if status == "sent" else {})))
        await s.commit()


async def sender_loop():
    log.info("sender started")
    while True:
        async with Session() as s:
            pending = (await s.execute(
                select(Notification).where(Notification.status == "pending")
                .where(or_(Notification.deliver_after.is_(None), Notification.deliver_after <= datetime.now(timezone.utc)))
                .order_by(Notification.id).limit(20))).scalars().all()
        for n in pending:
            await send_one(n)
            await asyncio.sleep(0.05)  # stay well under Telegram's 30 msg/s
        await asyncio.sleep(1 if pending else 2)
