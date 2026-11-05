"""Polling scheduler. State lives in PostgreSQL, so a restart just continues."""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from carradar.db.models import (AppSetting, ErrorLog, Filter, FilterQuery, Listing, ListingImage, Match,
                                Notification, ParserStatus, PriceHistory, SearchQuery)
from carradar.db.session import Session
from carradar.parsers import PARSERS
from carradar.parsers.base import BlockedError, ParsedListing, RateLimitedError, SchemaError
from carradar.shared.config import settings
from carradar.shared.filterspec import FilterSpec, matches

log = logging.getLogger("monitor")
REQUEST_GAP = 2.0  # seconds between requests to the same source (politeness)


def now():
    return datetime.now(timezone.utc)


async def get_interval() -> int:
    async with Session() as s:
        row = await s.get(AppSetting, "poll_interval_sec")
    return int(row.value["v"]) if row else settings.poll_interval_sec


async def _status(source: str, **kw):
    async with Session() as s:
        await s.execute(insert(ParserStatus).values(source=source, **kw)
                        .on_conflict_do_update(index_elements=["source"], set_=kw))
        await s.commit()


async def _bump(source: str, ok: bool):
    col = ParserStatus.requests_total if ok else ParserStatus.errors_total
    async with Session() as s:
        await s.execute(insert(ParserStatus).values(source=source).on_conflict_do_nothing())
        await s.execute(update(ParserStatus).where(ParserStatus.source == source)
                        .values(requests_total=ParserStatus.requests_total + 1,
                                **({} if ok else {"errors_total": ParserStatus.errors_total + 1})))
        await s.commit()


def _listing_values(p: ParsedListing) -> dict:
    return dict(source=p.source, external_id=p.external_id, url=p.url, title=p.title, description=p.description,
                price=p.price, currency=p.currency, make=p.make, model=p.model, year=p.year, mileage=p.mileage,
                engine_cc=p.engine_cc, power_hp=p.power_hp, fuel=p.fuel, gearbox=p.gearbox,
                seller_type=p.seller_type, city=p.city, region=p.region, attrs=p.attrs, published_at=p.published_at)


async def process_results(q: SearchQuery, parsed: list[ParsedListing]) -> int:
    """Store listings, detect price changes, match filters, enqueue notifications. Returns #new listings."""
    new_count = 0
    async with Session() as s:
        ids = [p.external_id for p in parsed]
        known = {r.external_id: r for r in (await s.execute(
            select(Listing.id, Listing.external_id, Listing.price)
            .where(Listing.source == q.source, Listing.external_id.in_(ids)))).all()}
        new: list[tuple[int, ParsedListing]] = []
        for p in parsed:
            k = known.get(p.external_id)
            if k:
                await s.execute(update(Listing).where(Listing.id == k.id).values(last_seen_at=now(), is_active=True))
                if p.price is not None and k.price is not None and p.price != k.price:
                    await s.execute(update(Listing).where(Listing.id == k.id).values(price=p.price))
                    s.add(PriceHistory(listing_id=k.id, price=p.price))
                continue
            lid = (await s.execute(insert(Listing).values(**_listing_values(p))
                                   .on_conflict_do_nothing(index_elements=["source", "external_id"])
                                   .returning(Listing.id))).scalar()
            if lid is None:  # lost a race with another poller
                continue
            for i, u in enumerate(p.images):
                s.add(ListingImage(listing_id=lid, pos=i, url=u))
            if p.price is not None:
                s.add(PriceHistory(listing_id=lid, price=p.price))
            new.append((lid, p))
        new_count = len(new)

        # Match EVERY listing of the result against every filter of this query (a listing may have been
        # stored earlier by a different query). Notify only for new matches published after the filter
        # was created, so a fresh filter never floods the user with old ads.
        filters = (await s.execute(
            select(Filter).join(FilterQuery, FilterQuery.filter_id == Filter.id)
            .where(FilterQuery.query_id == q.id, Filter.active))).scalars().all()
        lids = {p.external_id: k.id for p, k in ((p, known.get(p.external_id)) for p in parsed) if k}
        lids.update({p.external_id: lid for lid, p in new})
        for p in parsed:
            lid = lids.get(p.external_id)
            if lid is None:
                continue
            per_user: dict[int, list[int]] = {}
            for f in filters:
                if not matches(FilterSpec(**f.params), p):
                    continue
                r = await s.execute(insert(Match).values(filter_id=f.id, listing_id=lid).on_conflict_do_nothing())
                if not r.rowcount:
                    continue
                await s.execute(update(Filter).where(Filter.id == f.id).values(
                    found_total=Filter.found_total + 1, found_new=Filter.found_new + 1))
                if f.notify and (p.published_at or now()) >= f.created_at:
                    per_user.setdefault(f.user_id, []).append(f.id)
            for uid, fids in per_user.items():  # one notification per (user, listing)
                ins = insert(Notification).values(user_id=uid, listing_id=lid, filter_ids=fids)
                await s.execute(ins.on_conflict_do_update(  # merge filters into a not-yet-sent message
                    index_elements=["user_id", "listing_id", "kind"],
                    set_={"filter_ids": Notification.filter_ids.op("||")(ins.excluded.filter_ids)},
                    where=Notification.status == "pending"))
        await s.commit()
    return new_count


async def poll_one(parser, client, q: SearchQuery, interval: int):
    src = q.source
    try:
        parsed = await parser.fetch(client, q.query)
        n = await process_results(q, parsed)
        await _bump(src, True)
        await _status(src, state="ok", last_success_at=now(), last_error=None, last_http_status=200, paused_until=None)
        upd = dict(last_polled_at=now(), next_poll_at=now() + timedelta(seconds=interval), fail_count=0)
        log.info("polled %s q=%s listings=%d new=%d", src, q.id, len(parsed), n)
    except RateLimitedError as e:
        await _bump(src, False)
        await _status(src, state="degraded", last_http_status=429, last_error="rate limited",
                      paused_until=now() + timedelta(seconds=e.retry_after))
        upd = dict(next_poll_at=now() + timedelta(seconds=e.retry_after))
    except BlockedError as e:
        await _bump(src, False)
        await _status(src, state="blocked", last_error=str(e), last_http_status=403,
                      paused_until=now() + timedelta(minutes=30))
        await _log_error(src, f"blocked: {e}")
        upd = dict(next_poll_at=now() + timedelta(minutes=30))
    except SchemaError as e:
        await _bump(src, False)
        await _status(src, state="schema_changed", last_error=str(e))
        await _log_error(src, f"schema: {e}")
        upd = dict(next_poll_at=now() + timedelta(minutes=10), fail_count=q.fail_count + 1)
    except Exception as e:  # network, DB, anything else: back off, keep running
        await _bump(src, False)
        await _status(src, state="degraded", last_error=repr(e)[:500])
        await _log_error(src, repr(e)[:500])
        upd = dict(next_poll_at=now() + timedelta(seconds=min(interval * 2 ** min(q.fail_count, 5), 1800)),
                   fail_count=q.fail_count + 1)
    async with Session() as s:
        await s.execute(update(SearchQuery).where(SearchQuery.id == q.id).values(**upd))
        await s.commit()


async def _log_error(source: str, msg: str):
    log.warning("%s: %s", source, msg)
    async with Session() as s:
        s.add(ErrorLog(source=source, message=msg))
        await s.commit()


async def poll_source(src: str, interval: int):
    parser = PARSERS[src]
    async with Session() as s:
        st = await s.get(ParserStatus, src)
        if st and st.paused_until and st.paused_until > now():
            return
        # only queries that still have an active filter
        qs = (await s.execute(
            select(SearchQuery).where(SearchQuery.source == src)
            .where((SearchQuery.next_poll_at.is_(None)) | (SearchQuery.next_poll_at <= now()))
            .where(SearchQuery.id.in_(select(FilterQuery.query_id).join(Filter, Filter.id == FilterQuery.filter_id)
                                      .where(Filter.active)))
            .order_by(SearchQuery.next_poll_at.asc().nullsfirst()).limit(20))).scalars().all()
    if not qs:
        return
    async with parser.client() as client:
        for q in qs:
            await poll_one(parser, client, q, interval)
            await asyncio.sleep(REQUEST_GAP)


async def monitor_loop():
    log.info("monitor started")
    while True:
        interval = await get_interval()
        await asyncio.gather(*(poll_source(src, interval) for src in PARSERS))
        await asyncio.sleep(5)
