"""All tables. Source of truth for monitoring state (nothing important lives in process memory)."""
from datetime import datetime

from sqlalchemy import (BigInteger, Boolean, DateTime, ForeignKey, Index, Integer,
                        String, Text, UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def ts():
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    username: Mapped[str | None] = mapped_column(String(64))
    lang: Mapped[str] = mapped_column(String(5), default="en")  # pl|ru|uk|en
    theme: Mapped[str] = mapped_column(String(10), default="dark")
    tz: Mapped[str] = mapped_column(String(40), default="Europe/Warsaw")
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    # enabled, sources[], night{from,to}, photos, mode(instant|digest), digest_min, price_alerts
    notify: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = ts()


class Filter(Base):
    __tablename__ = "filters"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    sources: Mapped[list] = mapped_column(JSONB)  # ["otomoto","olx"]
    params: Mapped[dict] = mapped_column(JSONB)  # "filter parameters": canonical FilterSpec
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notify: Mapped[bool] = mapped_column(Boolean, default=True)
    found_total: Mapped[int] = mapped_column(Integer, default=0)
    found_new: Mapped[int] = mapped_column(Integer, default=0)  # unseen in the app
    created_at: Mapped[datetime] = ts()


class SearchQuery(Base):
    """Deduplicated source-specific query. Many filters (of many users) share one row => one poll."""
    __tablename__ = "search_queries"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(16))
    query_hash: Mapped[str] = mapped_column(String(64))
    query: Mapped[dict] = mapped_column(JSONB)  # coarse server-side query (make/model/price/year...)
    last_seen_id: Mapped[str | None] = mapped_column(String(64))  # newest listing id processed
    last_polled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_poll_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (UniqueConstraint("source", "query_hash"), Index("ix_sq_next", "next_poll_at"))


class FilterQuery(Base):
    __tablename__ = "filter_queries"
    filter_id: Mapped[int] = mapped_column(ForeignKey("filters.id", ondelete="CASCADE"), primary_key=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("search_queries.id", ondelete="CASCADE"), primary_key=True)


class Listing(Base):
    __tablename__ = "listings"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(16))
    external_id: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="PLN")
    make: Mapped[str | None] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(64))
    year: Mapped[int | None] = mapped_column(Integer)
    mileage: Mapped[int | None] = mapped_column(Integer)
    engine_cc: Mapped[int | None] = mapped_column(Integer)
    power_hp: Mapped[int | None] = mapped_column(Integer)
    fuel: Mapped[str | None] = mapped_column(String(32))
    gearbox: Mapped[str | None] = mapped_column(String(32))
    body: Mapped[str | None] = mapped_column(String(32))
    drive: Mapped[str | None] = mapped_column(String(16))
    vin: Mapped[str | None] = mapped_column(String(17))
    city: Mapped[str | None] = mapped_column(String(80))
    region: Mapped[str | None] = mapped_column(String(80))
    seller_type: Mapped[str | None] = mapped_column(String(16))  # private|dealer
    seller_name: Mapped[str | None] = mapped_column(String(120))
    attrs: Mapped[dict] = mapped_column(JSONB, default=dict)  # all other parsed parameters, verbatim
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = ts()
    last_seen_at: Mapped[datetime] = ts()
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # false = gone from source, history kept
    dup_group: Mapped[int | None] = mapped_column(Integer, index=True)  # "possible duplicate" cluster
    images: Mapped[list["ListingImage"]] = relationship(order_by="ListingImage.pos", cascade="all, delete-orphan")
    __table_args__ = (
        UniqueConstraint("source", "external_id"),
        Index("ix_l_first_seen", "first_seen_at"),
        Index("ix_l_search", "make", "model", "year"),
        Index("ix_l_price", "price"),
        Index("ix_l_vin", "vin"),
    )


class ListingImage(Base):
    __tablename__ = "listing_images"
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    pos: Mapped[int] = mapped_column(Integer, default=0)
    url: Mapped[str] = mapped_column(Text)


class PriceHistory(Base):
    __tablename__ = "price_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    price: Mapped[int] = mapped_column(Integer)
    seen_at: Mapped[datetime] = ts()


class Match(Base):
    """Listing matched a filter. Drives the catalog and 'new' counters."""
    __tablename__ = "matches"
    filter_id: Mapped[int] = mapped_column(ForeignKey("filters.id", ondelete="CASCADE"), primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = ts()
    __table_args__ = (Index("ix_m_listing", "listing_id"),)


class Favorite(Base):
    __tablename__ = "favorites"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = ts()


class HiddenListing(Base):
    __tablename__ = "hidden_listings"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True)


class Notification(Base):
    """Outbox + dedupe: UNIQUE(user, listing, kind) => one message per user per listing."""
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16), default="new")  # new|price
    filter_ids: Mapped[list] = mapped_column(JSONB)  # all matching filters, shown in one message
    status: Mapped[str] = mapped_column(String(12), default="pending")  # pending|sent|failed|skipped
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    deliver_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # night mode / digest
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = ts()
    __table_args__ = (UniqueConstraint("user_id", "listing_id", "kind"),
                      Index("ix_n_pending", "status", "deliver_after"))


class ParserStatus(Base):
    __tablename__ = "parser_status"
    source: Mapped[str] = mapped_column(String(16), primary_key=True)
    state: Mapped[str] = mapped_column(String(16), default="unknown")  # ok|degraded|blocked|schema_changed
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    last_http_status: Mapped[int | None] = mapped_column(Integer)
    requests_total: Mapped[int] = mapped_column(Integer, default=0)
    errors_total: Mapped[int] = mapped_column(Integer, default=0)
    paused_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SearchHistory(Base):
    __tablename__ = "search_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = ts()


class AppSetting(Base):
    """Global runtime settings (e.g. poll_interval_sec), editable by admin without redeploy."""
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB)


class ErrorLog(Base):
    __tablename__ = "error_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = ts()
