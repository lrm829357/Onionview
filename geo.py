from geoip2.database import Reader

GEO_DB_PATH = "GeoLite2-City.mmdb"

async def enrich_with_geo(relays: list[dict]) -> list[dict]:
    reader = Reader(GEO_DB_PATH)
    out = []
    for r in relays:
        try:
            res = reader.city(r["ip"])
            r["lat"] = res.location.latitude
            r["lon"] = res.location.longitude
            r["country"] = res.country.iso_code
            r["city"] = res.city.name
        except Exception:
            r["lat"] = r["lon"] = None
            r["country"] = r["city"] = None
        out.append(r)
    reader.close()
    return out
