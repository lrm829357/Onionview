import httpx

ONIONOO_URL = "https://onionoo.torproject.org/details?type=relay"

async def fetch_relays() -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(ONIONOO_URL)
        r.raise_for_status()
        data = r.json()

    relays = []
    for item in data.get("relays", []):
        # Prefer IPv4 address if present in "or_addresses"
        ip = None
        for addr in item.get("or_addresses", []):
            # looks like "1.2.3.4:9001" or "[v6]:port"
            if ":" in addr and not addr.startswith("["):
                ip = addr.split(":")[0]
                break

        relays.append({
            "fingerprint": item.get("fingerprint"),
            "nickname": item.get("nickname"),
            "ip": ip,
            "flags": item.get("flags", []),
            "bandwidth": item.get("observed_bandwidth") or item.get("advertised_bandwidth"),
            "last_seen": item.get("last_seen"),
        })
    return [r for r in relays if r["fingerprint"] and r["ip"]]
