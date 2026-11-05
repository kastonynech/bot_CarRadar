"""Canonical filter definition, shared by bot, API, monitor.

Split in two on purpose:
  * server_query()  - coarse part the source site can filter itself. Identical specs of different users
                      collapse into ONE polled query.
  * matches()       - exact local check (exclude words, seller type, ...) run on every new listing.
"""
import hashlib
import json

from pydantic import BaseModel, Field

SERVER_FIELDS = ("make", "model", "price_min", "price_max", "year_min", "year_max", "mileage_min", "mileage_max",
                 "engine_min", "engine_max", "power_min", "power_max", "fuel", "gearbox", "body")


class FilterSpec(BaseModel):
    make: str | None = None  # OTOMOTO slug, e.g. "bmw"
    model: str | None = None  # slug, e.g. "seria-3"
    price_min: int | None = Field(None, ge=0)
    price_max: int | None = Field(None, ge=0)
    year_min: int | None = Field(None, ge=1900, le=2100)
    year_max: int | None = Field(None, ge=1900, le=2100)
    mileage_min: int | None = Field(None, ge=0)
    mileage_max: int | None = Field(None, ge=0)
    engine_min: int | None = Field(None, ge=0)  # cm3
    engine_max: int | None = Field(None, ge=0)
    power_min: int | None = Field(None, ge=0)  # KM
    power_max: int | None = Field(None, ge=0)
    fuel: list[str] = []  # petrol, diesel, lpg, petrol-lpg, hybrid, plug-in-hybrid, electric
    gearbox: list[str] = []  # manual, automatic
    body: list[str] = []  # OTOMOTO body_type slugs: sedan, combi, compact, suv, coupe, cabrio, minivan, ...
    # local-only conditions
    regions: list[str] = []  # voivodeship names as OTOMOTO writes them, e.g. "Mazowieckie"
    cities: list[str] = []
    seller: str = "all"  # all | private | dealer
    with_photo: bool = False
    exclude_words: list[str] = []
    exclude_models: list[str] = []
    exclude_fuel: list[str] = []

    def server_query(self) -> dict:
        d = self.model_dump(include=set(SERVER_FIELDS))
        d = {k: (sorted(v) if isinstance(v, list) else v) for k, v in d.items() if v not in (None, [], "")}
        return d


def query_hash(q: dict) -> str:
    return hashlib.sha256(json.dumps(q, sort_keys=True).encode()).hexdigest()


def _in_range(v, lo, hi) -> bool:
    if lo is None and hi is None:
        return True
    if v is None:  # unknown value never matches an explicit bound (no guessing)
        return False
    return (lo is None or v >= lo) and (hi is None or v <= hi)


def matches(spec: FilterSpec, l) -> bool:
    """`l` is anything with listing attributes (ParsedListing or ORM Listing)."""
    if spec.make and (l.make or "").lower().replace(" ", "-") != spec.make:
        return False
    if spec.model and spec.model not in (getattr(l, "model_slug", None) or (l.model or "").lower().replace(" ", "-")):
        return False
    if not (_in_range(l.price, spec.price_min, spec.price_max) and _in_range(l.year, spec.year_min, spec.year_max)
            and _in_range(l.mileage, spec.mileage_min, spec.mileage_max)
            and _in_range(l.engine_cc, spec.engine_min, spec.engine_max)
            and _in_range(l.power_hp, spec.power_min, spec.power_max)):
        return False
    if spec.regions and (l.region or "").lower() not in {r.lower() for r in spec.regions}:
        return False
    if spec.cities and (l.city or "").lower() not in {c.lower() for c in spec.cities}:
        return False
    if spec.fuel and l.fuel not in spec.fuel:
        return False
    if spec.gearbox and l.gearbox not in spec.gearbox:
        return False
    if l.fuel in spec.exclude_fuel:
        return False
    if spec.seller != "all" and l.seller_type != spec.seller:
        return False
    if spec.with_photo and not _has_photo(l):
        return False
    text = f"{l.title} {l.description or ''}".lower()
    if any(w.lower() in text for w in spec.exclude_words if w.strip()):
        return False
    if any(m.lower() in (l.model or "").lower() for m in spec.exclude_models if m.strip()):
        return False
    return True


def _has_photo(l) -> bool:
    imgs = getattr(l, "images", None)
    return bool(imgs)
