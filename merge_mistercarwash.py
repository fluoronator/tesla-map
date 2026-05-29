#!/usr/bin/env python3
"""
Mister Car Wash Geocoder + Merger
Reads MrCarwashAddresses.txt, geocodes using the free US Census Geocoder
(no API key, no rate limit), then merges into pois.geojson.

Place this script in the same folder as MrCarwashAddresses.txt and pois.geojson.
Double-click to run. Takes about 2-3 minutes.
"""

import json, csv, time, os, sys, math, io, traceback
import urllib.request, urllib.parse, urllib.error

ADDR_FILE    = "MrCarwashAddresses.txt"
GEOJSON_FILE = "pois.geojson"
# Census batch geocoder — free, no key, handles 1000 addresses per call
CENSUS_URL   = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
# Nominatim as fallback for addresses the Census geocoder misses
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8
    d = math.pi / 180
    a = math.sin((lat2-lat1)*d/2)**2 + math.cos(lat1*d)*math.cos(lat2*d)*math.sin((lon2-lon1)*d/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def census_batch_geocode(addresses):
    """
    Geocode up to 1000 addresses at once using the Census batch API.
    addresses: list of (id, street, city, state) tuples
    Returns dict: id -> (lat, lon)
    """
    # Build CSV content for the batch request
    csv_lines = []
    for addr_id, street, city, state in addresses:
        # Census API format: Unique ID, Street address, City, State, ZIP
        row = f'{addr_id},"{street}","{city}","{state}",'
        csv_lines.append(row)
    csv_content = "\n".join(csv_lines).encode("utf-8")

    data = urllib.parse.urlencode({
        "benchmark": "Public_AR_Current",
        "returntype": "locations",
        "vintage": "Current_Current",
    }).encode()

    # Must use multipart/form-data for the file upload
    boundary = "----CensusBatchBoundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="benchmark"\r\n\r\n'
        f"Public_AR_Current\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="addressFile"; filename="addresses.csv"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
    ).encode() + csv_content + (f"\r\n--{boundary}--\r\n").encode()

    req = urllib.request.Request(
        CENSUS_URL,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "TeslaMapMCW/1.0 (personal project)",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            response_text = r.read().decode("utf-8")
    except Exception as ex:
        print(f"  Census batch error: {ex}")
        return {}

    results = {}
    for line in response_text.strip().split("\n"):
        if not line.strip():
            continue
        try:
            parts = list(csv.reader([line]))[0]
            if len(parts) < 6:
                continue
            addr_id = parts[0].strip()
            match_status = parts[2].strip() if len(parts) > 2 else ""
            if "Match" in match_status and len(parts) >= 9:
                # Coordinates are in column 8: "lon,lat"
                coord_str = parts[8].strip() if len(parts) > 8 else ""
                if "," in coord_str:
                    lon_s, lat_s = coord_str.split(",", 1)
                    lat = float(lat_s.strip())
                    lon = float(lon_s.strip())
                    results[addr_id] = (lat, lon)
        except Exception:
            continue

    return results


def nominatim_geocode(address_str):
    """Single address fallback via Nominatim."""
    params = {
        "q":            address_str + ", USA",
        "format":       "json",
        "limit":        1,
        "countrycodes": "us",
    }
    url = NOMINATIM_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": "TeslaMapMCW/1.0 (personal project)"
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            res = json.loads(r.read())
        if res:
            return float(res[0]["lat"]), float(res[0]["lon"])
    except Exception:
        pass
    return None, None


def parse_address(raw):
    """
    Parse 'street, city, state' into components.
    Returns (street, city, state).
    """
    raw = raw.strip()
    # Split on last two commas: street, city, state
    parts = [p.strip() for p in raw.rsplit(",", 2)]
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return parts[0], parts[1], ""
    return raw, "", ""


def main():
    script_dir   = os.path.dirname(os.path.abspath(sys.argv[0]))
    addr_path    = os.path.join(script_dir, ADDR_FILE)
    geojson_path = os.path.join(script_dir, GEOJSON_FILE)

    print("=" * 60)
    print("Mister Car Wash Geocoder + Merger")
    print("=" * 60)
    print()

    if not os.path.exists(addr_path):
        print(f"ERROR: {ADDR_FILE} not found in {script_dir}")
        return
    if not os.path.exists(geojson_path):
        print(f"ERROR: {GEOJSON_FILE} not found in {script_dir}")
        return

    # Load addresses
    with open(addr_path, encoding="utf-8") as f:
        raw_addresses = [l.strip().strip("\r") for l in f if l.strip()]

    # De-duplicate by text, preserve order
    seen_text = set()
    unique_addresses = []
    for a in raw_addresses:
        if a not in seen_text and a != "Address Not Available":
            seen_text.add(a)
            unique_addresses.append(a)

    print(f"Total addresses:      {len(raw_addresses)}")
    print(f"After dedup/cleanup:  {len(unique_addresses)}")
    print()

    # Parse into components for Census API
    parsed = []
    for i, addr in enumerate(unique_addresses):
        street, city, state = parse_address(addr)
        parsed.append((str(i), street, city, state, addr))

    # ── Census batch geocoding (chunks of 999) ────────────────────
    print("Geocoding with US Census batch API (free, no key needed)...")
    CHUNK = 999
    coord_map = {}  # id -> (lat, lon)

    for start in range(0, len(parsed), CHUNK):
        chunk = parsed[start:start+CHUNK]
        batch_input = [(p[0], p[1], p[2], p[3]) for p in chunk]
        chunk_end = min(start + CHUNK, len(parsed))
        print(f"  Batch {start+1}-{chunk_end} of {len(parsed)}...", end=" ", flush=True)
        results = census_batch_geocode(batch_input)
        coord_map.update(results)
        print(f"{len(results)} matched")
        time.sleep(0.5)

    matched   = sum(1 for i in coord_map)
    unmatched = [p for p in parsed if p[0] not in coord_map]
    print(f"\nCensus matched: {matched}/{len(parsed)}")
    print(f"Unmatched:      {len(unmatched)}")

    # ── Nominatim fallback for unmatched ─────────────────────────
    if unmatched:
        print(f"\nTrying Nominatim for {len(unmatched)} unmatched addresses...")
        nominatim_ok = 0
        for p in unmatched:
            addr_id, street, city, state, raw = p
            lat, lon = nominatim_geocode(raw)
            time.sleep(1.1)
            if lat and lon:
                coord_map[addr_id] = (lat, lon)
                nominatim_ok += 1
                print(f"  OK   {raw}")
            else:
                print(f"  FAIL {raw}")
        print(f"Nominatim added: {nominatim_ok}")

    total_geocoded = len(coord_map)
    print(f"\nTotal geocoded: {total_geocoded}/{len(parsed)}")

    # ── Load pois.geojson ─────────────────────────────────────────
    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson["features"]
    other    = [f for f in features if f["properties"]["category"] != "mr_carwash"]
    old_mcw  = [f for f in features if f["properties"]["category"] == "mr_carwash"]
    print(f"\nExisting Mister Car Wash in pois.geojson: {len(old_mcw)}")

    # ── Build new features, dedup by coordinate (~1.1km) ─────────
    new_mcw    = []
    coord_seen = set()
    dupes      = 0

    for p in parsed:
        addr_id, street, city, state, raw = p
        if addr_id not in coord_map:
            continue
        lat, lon = coord_map[addr_id]
        key = (round(lat, 2), round(lon, 2))
        if key in coord_seen:
            dupes += 1
            continue
        coord_seen.add(key)

        # Build a clean display name
        name = f"Mister Car Wash"
        if street:
            name += f" {street}"

        new_mcw.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "category": "mr_carwash",
                "name":     name,
                "icon":     "carwash",
            }
        })

    print(f"New unique locations: {len(new_mcw)}")
    print(f"Coordinate dupes removed: {dupes}")

    # ── Save ──────────────────────────────────────────────────────
    geojson["features"]  = other + new_mcw
    geojson["generated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))

    from collections import Counter
    cats = Counter(ft["properties"]["category"] for ft in geojson["features"])
    print()
    print("Final POI counts:")
    for k, v in sorted(cats.items()):
        print(f"  {k}: {v:,}")
    print(f"  TOTAL: {len(geojson['features']):,}")
    print()
    print(f"Saved to {geojson_path}")
    print("Upload to your GitHub repo when done.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
    print()
    input("Press Enter to close...")
