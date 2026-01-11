# Onionview
Onionview is a Python-based web application that visualizes public Tor relay nodes on an interactive world map, including exit, guard, and middle relays with real-time metadata and geolocation.

This project is a modern reimplementation of an earlier Onionview service that I originally built in 2015.

## GeoIP Database
Download the latest GeoLite2 City database from: https://github.com/wp-statistics/GeoLite2-City

Extract the following file: GeoLite2-City.mmdb

Place the file in the project root directory, alongside main.py

## Use
```bash
git clone https://github.com/yourusername/Onionview.git
cd Onionview

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload
```
