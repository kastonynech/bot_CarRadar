import json
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (CallbackQuery, InlineKeyboardButton as Btn, InlineKeyboardMarkup, Message,
                           User as TgUser, WebAppInfo)
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert

from carradar.db.models import (ErrorLog, Favorite, Filter, FilterQuery, HiddenListing, Listing, ParserStatus,
                                SearchQuery, User)
from carradar.db.session import Session
from carradar.monitoring.queries import register_filter
from carradar.notifications.sender import DEFAULT_NOTIFY
from carradar.shared.config import settings
from carradar.shared.filterspec import FilterSpec

router = Router()
LANGS = {"pl", "ru", "uk", "en"}


async def ensure_user(tg: TgUser) -> User:
    lang = (tg.language_code or "en")[:2]
    async with Session() as s:
        await s.execute(insert(User).values(id=tg.id, username=tg.username, lang=lang if lang in LANGS else "en", notify={})
                        .on_conflict_do_update(index_elements=["id"], set_={"username": tg.username}))
        await s.commit()
        return await s.get(User, tg.id)


def app_button():
    url = settings.webapp_url
    if url.startswith("https://"):
        return [[Btn(text="🚀 Открыть CarRadar", web_app=WebAppInfo(url=url))]]
    return []


@router.message(Command("start"))
async def start(m: Message):
    await ensure_user(m.from_user)
    await m.answer(
        "🚗 <b>CarRadar</b> — мониторинг новых объявлений OTOMOTO.\n\n"
        "Я проверяю площадку регулярно (раз в минуту-две, это не мгновенно) и присылаю новые авто, "
        "подходящие под ваши фильтры.\n\n"
        "<b>Первый фильтр:</b> <code>/add bmw seria-3 50000</code>\n"
        "марка, модель (необязательно), максимальная цена (необязательно).\n\n"
        "/filters · /favorites · /settings · /help",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=app_button()) if app_button() else None)


@router.message(Command("help"))
async def help_(m: Message):
    await m.answer("/add <марка> [модель] [макс. цена] — создать фильтр\n/filters — фильтры\n/favorites — избранное\n"
                   "/settings — уведомления\n/id — ваш Telegram ID\n\n"
                   "Марка и модель — как в адресе OTOMOTO, например <code>/add mercedes-benz klasa-c 60000</code>.")


@router.message(Command("id"))
async def my_id(m: Message):
    await m.answer(f"Ваш Telegram ID: <code>{m.from_user.id}</code>")


@router.message(Command("add"))
async def add(m: Message, command: CommandObject):
    await ensure_user(m.from_user)
    parts = (command.args or "").lower().split()
    price = int(parts.pop()) if parts and parts[-1].isdigit() else None
    if not parts:
        return await m.answer("Пример: <code>/add bmw seria-3 50000</code>")
    spec = FilterSpec(make=parts[0], model=parts[1] if len(parts) > 1 else None, price_max=price)
    name = " ".join(p for p in (parts[0].upper(), parts[1] if len(parts) > 1 else "") if p) + (f" до {price:,} zł".replace(",", " ") if price else "")
    async with Session() as s:
        f = Filter(user_id=m.from_user.id, name=name, sources=["otomoto"], params=spec.model_dump())
        s.add(f)
        await s.flush()
        await register_filter(s, f)
        await s.commit()
    await m.answer(f"✅ Фильтр «{escape(name)}» создан. Первая проверка идёт в фоне: уже существующие объявления "
                   "я не присылаю, только новые.")


def filter_kb(fs):
    rows = []
    for f in fs:
        rows.append([Btn(text=f"{'⏸' if f.active else '▶️'} {f.name}", callback_data=f"ft:{f.id}"),
                     Btn(text="🗑", callback_data=f"fd:{f.id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("filters"))
async def filters(m: Message):
    async with Session() as s:
        fs = (await s.execute(select(Filter).where(Filter.user_id == m.from_user.id).order_by(Filter.id))).scalars().all()
    if not fs:
        return await m.answer("Фильтров пока нет. Пример: <code>/add bmw seria-3 50000</code>")
    await m.answer("Ваши фильтры (нажмите, чтобы включить/выключить):", reply_markup=filter_kb(fs))


@router.callback_query(F.data.startswith("ft:"))
async def toggle_filter(c: CallbackQuery):
    fid = int(c.data[3:])
    async with Session() as s:
        await s.execute(update(Filter).where(Filter.id == fid, Filter.user_id == c.from_user.id)
                        .values(active=~Filter.active))
        await s.commit()
        fs = (await s.execute(select(Filter).where(Filter.user_id == c.from_user.id).order_by(Filter.id))).scalars().all()
    await c.message.edit_reply_markup(reply_markup=filter_kb(fs))
    await c.answer("Готово")


@router.callback_query(F.data.startswith("fd:"))
async def delete_filter_ask(c: CallbackQuery):
    fid = c.data[3:]
    await c.message.edit_text("Удалить фильтр?", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
        Btn(text="Да, удалить", callback_data=f"fy:{fid}"), Btn(text="Отмена", callback_data="fn")]]))
    await c.answer()


@router.callback_query(F.data == "fn")
async def delete_cancel(c: CallbackQuery):
    await c.message.edit_text("Отменено. /filters")
    await c.answer()


@router.callback_query(F.data.startswith("fy:"))
async def delete_filter(c: CallbackQuery):
    async with Session() as s:
        await s.execute(delete(Filter).where(Filter.id == int(c.data[3:]), Filter.user_id == c.from_user.id))
        # drop queries nobody uses any more
        await s.execute(delete(SearchQuery).where(~SearchQuery.id.in_(select(FilterQuery.query_id))))
        await s.commit()
    await c.message.edit_text("Фильтр удалён. /filters")
    await c.answer()


@router.callback_query(F.data.startswith("fav:"))
async def fav(c: CallbackQuery):
    await ensure_user(c.from_user)
    async with Session() as s:
        await s.execute(insert(Favorite).values(user_id=c.from_user.id, listing_id=int(c.data[4:])).on_conflict_do_nothing())
        await s.commit()
    await c.answer("⭐ Добавлено в избранное")


@router.callback_query(F.data.startswith("hide:"))
async def hide(c: CallbackQuery):
    async with Session() as s:
        await s.execute(insert(HiddenListing).values(user_id=c.from_user.id, listing_id=int(c.data[5:])).on_conflict_do_nothing())
        await s.commit()
    await c.message.edit_reply_markup(reply_markup=None)
    await c.answer("Скрыто. Фильтр остаётся активным.")


@router.message(Command("favorites"))
async def favorites(m: Message):
    async with Session() as s:
        ls = (await s.execute(select(Listing).join(Favorite, Favorite.listing_id == Listing.id)
                              .where(Favorite.user_id == m.from_user.id).order_by(Favorite.created_at.desc()).limit(20))).scalars().all()
    if not ls:
        return await m.answer("Избранное пусто. Нажмите ⭐ под уведомлением.")
    await m.answer("\n".join(f'⭐ <a href="{l.url}">{escape(l.title)}</a> — {l.price or "—"} zł, {l.year or "—"}'
                             for l in ls), disable_web_page_preview=True)


def settings_kb(cfg):
    on = lambda b: "✅" if b else "❌"  # noqa: E731
    return InlineKeyboardMarkup(inline_keyboard=[
        [Btn(text=f"{on(cfg['enabled'])} Уведомления", callback_data="set:enabled")],
        [Btn(text=f"{on(cfg['photos'])} Фото", callback_data="set:photos")],
        [Btn(text=f"{on('otomoto' in cfg['sources'])} OTOMOTO", callback_data="set:src_otomoto"),
         Btn(text=f"{on('olx' in cfg['sources'])} OLX", callback_data="set:src_olx")]])


@router.message(Command("settings"))
async def settings_(m: Message):
    u = await ensure_user(m.from_user)
    await m.answer("⚙️ Настройки уведомлений:", reply_markup=settings_kb({**DEFAULT_NOTIFY, **(u.notify or {})}))


@router.callback_query(F.data.startswith("set:"))
async def set_(c: CallbackQuery):
    key = c.data[4:]
    async with Session() as s:
        u = await s.get(User, c.from_user.id)
        cfg = {**DEFAULT_NOTIFY, **(u.notify or {})}
        if key.startswith("src_"):
            src = key[4:]
            cfg["sources"] = [x for x in cfg["sources"] if x != src] if src in cfg["sources"] else cfg["sources"] + [src]
        else:
            cfg[key] = not cfg[key]
        u.notify = cfg
        await s.commit()
    await c.message.edit_reply_markup(reply_markup=settings_kb(cfg))
    await c.answer()


@router.message(Command("status"))
async def status(m: Message):
    if m.from_user.id not in settings.admins:
        return
    async with Session() as s:
        users = await s.scalar(select(func.count()).select_from(User))
        fl = await s.scalar(select(func.count()).select_from(Filter).where(Filter.active))
        ls = await s.scalar(select(func.count()).select_from(Listing))
        ps = (await s.execute(select(ParserStatus))).scalars().all()
        errs = (await s.execute(select(ErrorLog).order_by(ErrorLog.id.desc()).limit(3))).scalars().all()
    txt = f"users {users} · active filters {fl} · listings {ls}\n" + "\n".join(
        f"{p.source}: {p.state}, ok {p.last_success_at:%H:%M:%S}, req {p.requests_total}/err {p.errors_total}" if p.last_success_at
        else f"{p.source}: {p.state}, err {p.errors_total}" for p in ps)
    await m.answer(txt + "\n\n" + "\n".join(escape(e.message[:150]) for e in errs))
