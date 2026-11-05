"""OTOMOTO: one GET of the public search page; listings come from the embedded Next.js JSON.
robots.txt allows /osobowe/; we make one request per unique query, no deep crawling."""
import asyncio
import json
import re
from datetime import datetime
from urllib.parse import urlencode

import httpx

from .base import BlockedError, ParsedListing, RateLimitedError, SchemaError, TemporaryError

UA = "Mozilla/5.0 (compatible; CarRadar/0.1; personal listing monitor)"
_NEXT = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
_RANGES = {"price": "price", "year": "year", "mileage": "mileage", "engine": "engine_capacity", "power": "engine_power"}


def build_url(q: dict) -> str:
    path = "/osobowe" + "".join(f"/{q[k]}" for k in ("make", "model") if q.get(k))
    p = {"search[order]": "created_at_first:desc"}
    for ours, theirs in _RANGES.items():
        for side in ("min", "max"):
            v = q.get(f"{ours}_{side}")
            if v is not None:
                p[f"search[filter_float_{theirs}:{'from' if side == 'min' else 'to'}]"] = v
    for ours, theirs in (("fuel", "fuel_type"), ("gearbox", "gearbox"), ("body", "body_type")):
        for i, v in enumerate(q.get(ours, [])):
            p[f"search[filter_enum_{theirs}][{i}]"] = v
    return "https://www.otomoto.pl" + path + "?" + urlencode(p)


def parse_page(html: str) -> list[ParsedListing]:
    m = _NEXT.search(html)
    if not m:
        raise SchemaError("__NEXT_DATA__ not found")
    try:
        state = json.loads(m.group(1))["props"]["pageProps"]["urqlState"]
        edges = None
        for v in state.values():
            data = json.loads(v["data"]) if isinstance(v.get("data"), str) else v.get("data") or {}
            if "advertSearch" in data:
                edges = data["advertSearch"]["edges"]
        if edges is None:
            raise KeyError("advertSearch")
    except (KeyError, TypeError, ValueError) as e:
        raise SchemaError(f"unexpected JSON shape: {e}") from e
    out = [parse_node(e["node"]) for e in edges if e.get("node")]
    if edges and not out:
        raise SchemaError("edges present but no nodes")
    return out


def _int(v) -> int | None:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def parse_node(n: dict) -> ParsedListing:
    params = {p["key"]: p for p in n.get("parameters", [])}
    val = lambda k: params.get(k, {}).get("value")  # noqa: E731
    amount = ((n.get("price") or {}).get("amount") or {})
    loc = n.get("location") or {}
    seller = (n.get("seller") or {}).get("__typename", "")
    thumb = n.get("thumbnail") or {}
    created = n.get("createdAt")
    return ParsedListing(
        source="otomoto", external_id=str(n["id"]), url=n["url"], title=n.get("title", ""),
        description=n.get("shortDescription"),
        price=_int(amount.get("value")), currency=amount.get("currencyCode") or "PLN",
        make=params.get("make", {}).get("displayValue"), model=params.get("model", {}).get("displayValue"),
        model_slug=val("model"), year=_int(val("year")), mileage=_int(val("mileage")),
        engine_cc=_int(val("engine_capacity")), power_hp=_int(val("engine_power")),
        fuel=val("fuel_type"), gearbox=val("gearbox"),
        seller_type="dealer" if seller.startswith("Professional") else "private" if seller.startswith("Private") else None,
        city=((loc.get("city") or {}).get("name")), region=((loc.get("region") or {}).get("name")),
        published_at=datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None,
        images=[u for u in (thumb.get("x2") or thumb.get("x1"),) if u],
        attrs={"display": {k: p.get("displayValue") for k, p in params.items()}},
    )


class OtomotoParser:
    source = "otomoto"

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=15, follow_redirects=True,
                                 headers={"User-Agent": UA, "Accept-Language": "pl,en;q=0.8"})

    async def fetch(self, client: httpx.AsyncClient, query: dict) -> list[ParsedListing]:
        url = build_url(query)
        last: Exception | None = None
        for attempt in range(3):
            try:
                r = await client.get(url)
            except httpx.HTTPError as e:
                last = e
            else:
                if r.status_code == 200:
                    return parse_page(r.text)
                if r.status_code == 429:
                    raise RateLimitedError(int(r.headers.get("Retry-After", 300)))
                if r.status_code in (401, 403):
                    raise BlockedError(f"HTTP {r.status_code}")
                last = TemporaryError(f"HTTP {r.status_code}")
            await asyncio.sleep(2 ** attempt)
        raise TemporaryError(str(last))


def _pv(pd: dict, key: str):
    vals = (pd.get(key) or {}).get("values") or []
    return vals[0] if vals else None


def _text(html: str) -> str:
    html = re.sub(r"<br\s*/?>|</p>", "\n", html)
    return re.sub(r"[ \t]+", " ", re.sub(r"<[^>]+>", "", html)).strip()


def parse_detail(html: str) -> dict:
    """Full ad page -> extra data. Called once per ad, when a user opens it (cached in DB)."""
    m = _NEXT.search(html)
    if not m:
        raise SchemaError("__NEXT_DATA__ not found on ad page")
    try:
        a = json.loads(m.group(1))["props"]["pageProps"]["advert"]
    except (KeyError, TypeError, ValueError) as e:
        raise SchemaError(f"ad page shape: {e}") from e
    pd = a.get("parametersDict") or {}
    g = lambda k: (_pv(pd, k) or {})  # noqa: E731
    det = {d["key"]: d.get("value") for d in a.get("details", [])}
    loc = (a.get("seller") or {}).get("location") or {}
    return {
        "status": a.get("status"),
        "description": _text(a.get("description") or ""),
        "photos": [p["url"] for p in (a.get("images") or {}).get("photos", []) if p.get("url")],
        "vin": det.get("vin"),
        "body": g("body_type").get("label"), "drive": g("transmission").get("label"),
        "doors": g("door_count").get("value"), "seats": g("nr_seats").get("value"), "color": g("color").get("label"),
        "damaged": g("damaged").get("label"), "service_record": g("service_record").get("label"),
        "new_used": g("new_used").get("label"), "imported": g("is_imported_car").get("label"),
        "details": [{"label": d["label"], "value": d.get("value")} for d in a.get("details", []) if d.get("value")],
        "equipment": [{"label": e["label"], "values": [v["label"] for v in e.get("values", [])]} for e in a.get("equipment", [])],
        "seller_name": (a.get("seller") or {}).get("name"),
        "seller_type": "dealer" if (a.get("seller") or {}).get("type") == "PROFESSIONAL" else "private",
        "address": loc.get("address"),
    }


async def fetch_detail(client: httpx.AsyncClient, url: str) -> dict | None:
    """None = ad is gone (404/410). Raises on blocking/rate limit like fetch()."""
    r = await client.get(url)
    if r.status_code in (404, 410):
        return None
    if r.status_code == 429:
        raise RateLimitedError(int(r.headers.get("Retry-After", 300)))
    if r.status_code in (401, 403):
        raise BlockedError(f"HTTP {r.status_code}")
    if r.status_code != 200:
        raise TemporaryError(f"HTTP {r.status_code}")
    return parse_detail(r.text)
