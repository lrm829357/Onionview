import sqlite3
from pathlib import Path

DB_PATH = Path("tor_map.db")


def relay_type(flags: list[str]) -> str:
    """
    Classify a Tor relay using its flags.
    - Exit: has Exit flag
    - Guard: has Guard flag (and not Exit)
    - Middle: neither Exit nor Guard
    """
    if not flags:
        return "Unknown"
    if "Exit" in flags:
        return "Exit"
    if "Guard" in flags:
        return "Guard"
    return "Middle"


async def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS relays (
        fingerprint TEXT PRIMARY KEY,
        nickname TEXT,
        ip TEXT,
        flags TEXT,
        bandwidth INTEGER,
        last_seen TEXT,
        lat REAL,
        lon REAL,
        country TEXT,
        city TEXT
      )
    """)
    conn.commit()
    conn.close()


async def upsert_relays(relays: list[dict]):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executemany("""
      INSERT INTO relays (fingerprint,nickname,ip,flags,bandwidth,last_seen,lat,lon,country,city)
      VALUES (?,?,?,?,?,?,?,?,?,?)
      ON CONFLICT(fingerprint) DO UPDATE SET
        nickname=excluded.nickname,
        ip=excluded.ip,
        flags=excluded.flags,
        bandwidth=excluded.bandwidth,
        last_seen=excluded.last_seen,
        lat=excluded.lat,
        lon=excluded.lon,
        country=excluded.country,
        city=excluded.city
    """, [
        (
          r["fingerprint"], r.get("nickname"), r.get("ip"),
          ",".join(r.get("flags") or []),
          int(r["bandwidth"]) if r.get("bandwidth") else None,
          r.get("last_seen"),
          r.get("lat"), r.get("lon"),
          r.get("country"), r.get("city")
        )
        for r in relays
    ])
    conn.commit()
    conn.close()


async def query_relays(type: str, country: str | None, limit: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    where = []
    params = []

    if country:
        where.append("country = ?")
        params.append(country)

    if type == "exit":
        where.append("flags LIKE ?")
        params.append("%Exit%")
    elif type == "guard":
        where.append("flags LIKE ?")
        params.append("%Guard%")

    sql = "SELECT * FROM relays"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " LIMIT ?"
    params.append(limit)

    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    # normalize flags back to list + add derived relay type
    for r in rows:
        r["flags"] = r["flags"].split(",") if r.get("flags") else []
        r["type"] = relay_type(r["flags"])

    return rows


# Optional: handy for /api/stats
async def relay_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM relays")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM relays WHERE lat IS NOT NULL AND lon IS NOT NULL")
    mapped = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM relays WHERE flags LIKE '%Exit%'")
    exits = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM relays WHERE flags LIKE '%Guard%'")
    guards = cur.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "mapped": mapped,
        "unmapped": total - mapped,
        "exits": exits,
        "guards": guards,
    }
