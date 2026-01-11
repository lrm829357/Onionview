from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from storage import init_db, upsert_relays, query_relays
from tor_source import fetch_relays
from geo import enrich_with_geo

app = FastAPI(title="Tor Relay Map")

@app.on_event("startup")
async def startup():
    await init_db()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(refresh_data, "interval", minutes=60, max_instances=1)
    scheduler.start()
    await refresh_data()

async def refresh_data():
    relays = await fetch_relays()
    print(f"[collector] fetched {len(relays)} relays")

    relays = await enrich_with_geo(relays)
    mapped = sum(1 for r in relays if r.get("lat") and r.get("lon"))
    print(f"[collector] geolocated {mapped}/{len(relays)} relays")

    await upsert_relays(relays)

@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>Tor Relay Map</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <style>#map{height:95vh;width:100%} body{margin:0;font-family:system-ui}</style>
      </head>
      <body>
        <div id="map"></div>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
          const map = L.map('map').setView([20, 0], 2);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18
          }).addTo(map);

          async function load() {
            const res = await fetch('/api/relays?type=all&limit=2000');
            const data = await res.json();
            data.items.forEach(r => {
              if (r.lat == null || r.lon == null) return;
              const m = L.circleMarker([r.lat, r.lon], { radius: 3 });
              m.bindPopup(`<b>${r.nickname || ''}</b><br/>
                  <b>Country:</b> ${r.country || ''}<br/>
                  <b>IP:</b> ${r.ip || ''}<br/>
                  <b>Type:</b> ${r.type}<br/>
                  <b>Fingerprint:</b> ${r.fingerprint}<br/>
                  <b>Flags:</b> ${(r.flags || []).join(', ')}<br/>
                  <b>Bandwidth:</b> ${r.bandwidth || ''}`);
              m.addTo(map);
            });
          }
          load();
        </script>
      </body>
    </html>
    """

@app.get("/api/relays")
async def api_relays(
    type: str = Query("all", pattern="^(all|exit|guard)$"),
    country: str | None = None,
    limit: int = 5000
):
    items = await query_relays(type=type, country=country, limit=limit)
    return {"items": items}
