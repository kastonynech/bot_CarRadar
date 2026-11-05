import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from carradar.api.auth import verify_init_data
from carradar.parsers.base import ParsedListing, SchemaError
from carradar.parsers.otomoto import build_url, parse_node, parse_page
from carradar.shared.filterspec import FilterSpec, matches, query_hash

NODE = {"id": "1", "title": "BMW Seria 3 318i", "url": "https://x/1", "createdAt": "2026-11-05T19:18:20Z",
        "shortDescription": "Salon Polska", "location": {"city": {"name": "Łódź"}, "region": {"name": "Łódzkie"}},
        "thumbnail": {"x2": "https://img/2"}, "price": {"amount": {"value": "52900", "currencyCode": "PLN"}},
        "seller": {"__typename": "PrivateSeller"},
        "parameters": [{"key": k, "value": v, "displayValue": v} for k, v in
                       dict(make="bmw", model="seria-3", year="2018", mileage="132000", fuel_type="petrol",
                            gearbox="automatic", engine_capacity="1998", engine_power="156").items()]}


def test_parse_node():
    l = parse_node(NODE)
    assert (l.external_id, l.price, l.year, l.mileage, l.fuel, l.seller_type, l.city) == \
           ("1", 52900, 2018, 132000, "petrol", "private", "Łódź")


def test_schema_error():
    with pytest.raises(SchemaError):
        parse_page("<html>nothing</html>")


def test_same_query_same_hash():  # one poll serves many users
    a = FilterSpec(make="bmw", price_max=5, exclude_words=["x"]).server_query()
    b = FilterSpec(make="bmw", price_max=5, seller="private").server_query()
    assert query_hash(a) == query_hash(b)
    assert "search%5Bfilter_float_price%3Ato%5D=5" in build_url(a)


def test_matches():
    l = parse_node(NODE)
    assert matches(FilterSpec(make="bmw", model="seria-3", price_max=60000, year_min=2015), l)
    assert not matches(FilterSpec(make="audi"), l)
    assert not matches(FilterSpec(price_max=50000), l)
    assert not matches(FilterSpec(exclude_words=["salon"]), l)
    assert not matches(FilterSpec(seller="dealer"), l)
    assert not matches(FilterSpec(year_min=2000), ParsedListing("otomoto", "2", "u", "t"))  # unknown year: no guess


def test_init_data():
    token = "123:ABC"
    data = {"auth_date": str(int(time.time())), "user": json.dumps({"id": 5})}
    check = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    assert verify_init_data(urlencode(data), token)["id"] == 5
    data["user"] = json.dumps({"id": 6})  # tampered
    with pytest.raises(ValueError):
        verify_init_data(urlencode(data), token)


def test_quiet_hours():
    from datetime import datetime, timezone
    from unittest.mock import patch
    from carradar.notifications import sender
    cfg = {"night": {"enabled": True, "from": "23:00", "to": "07:00"}}

    class Fake(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 5, 23, 30, tzinfo=tz or timezone.utc)
    with patch.object(sender, "datetime", Fake):
        end = sender.quiet_until(cfg, "UTC")
        assert end and end.hour == 7 and end.day == 6  # 23:30 is inside 23:00-07:00 -> until next 07:00
        assert sender.quiet_until({"night": {"enabled": False, "from": "23:00", "to": "07:00"}}, "UTC") is None


def test_redirect_is_rejected():
    import asyncio
    import httpx
    from carradar.parsers.base import QueryRejected
    from carradar.parsers.otomoto import OtomotoParser

    def handler(req):
        if req.url.path == "/osobowe/audi/a4":
            return httpx.Response(301, headers={"location": "/osobowe/audi/a4-avant"})
        return httpx.Response(200, text="<html></html>")

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True) as c:
            await OtomotoParser().fetch(c, {"make": "audi", "model": "a4"})
    import pytest
    with pytest.raises(QueryRejected):
        asyncio.run(run())
