from dataclasses import dataclass, field
from datetime import datetime


class BlockedError(Exception):
    """403 or similar. We never try to bypass it; the source is paused."""


class RateLimitedError(Exception):
    def __init__(self, retry_after: int = 300):
        self.retry_after = retry_after


class SchemaError(Exception):
    """Page layout/JSON changed and we could not find listings."""


class QueryRejected(Exception):
    """The site redirected the query elsewhere (e.g. unknown model slug): results would silently be wrong."""


class TemporaryError(Exception):
    """Network failure / 5xx after retries."""


@dataclass
class ParsedListing:
    source: str
    external_id: str
    url: str
    title: str
    description: str | None = None
    price: int | None = None
    currency: str = "PLN"
    make: str | None = None
    model: str | None = None
    model_slug: str | None = None
    year: int | None = None
    mileage: int | None = None
    engine_cc: int | None = None
    power_hp: int | None = None
    fuel: str | None = None
    gearbox: str | None = None
    seller_type: str | None = None  # private | dealer
    city: str | None = None
    region: str | None = None
    published_at: datetime | None = None
    images: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)  # {"display": {param: human readable}}
