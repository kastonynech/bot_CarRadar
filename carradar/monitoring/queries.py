from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from carradar.db.models import Filter, FilterQuery, SearchQuery
from carradar.parsers import PARSERS
from carradar.shared.filterspec import FilterSpec, query_hash


async def register_filter(s: AsyncSession, f: Filter) -> None:
    """Bind a filter to deduplicated source queries. Identical queries of different users share one row."""
    spec = FilterSpec(**f.params)
    q = spec.server_query()
    h = query_hash(q)
    await s.execute(delete(FilterQuery).where(FilterQuery.filter_id == f.id))
    for src in f.sources:
        if src not in PARSERS:
            continue
        qid = (await s.execute(
            insert(SearchQuery).values(source=src, query_hash=h, query=q)
            .on_conflict_do_update(index_elements=["source", "query_hash"], set_={"query_hash": h})
            .returning(SearchQuery.id))).scalar_one()
        await s.execute(insert(FilterQuery).values(filter_id=f.id, query_id=qid).on_conflict_do_nothing())
    # ponytail: no backfill of old listings into the new filter; it fills from the next poll on.
