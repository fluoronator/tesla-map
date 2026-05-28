#!/usr/bin/env python3
"""
Buc-ee's Coordinate Fixer v2
- Fetches accurate coordinates from OSM for locations it knows about
- Keeps website-sourced entries for any locations OSM doesn't have
- Result: best available coordinates for every location, nothing deleted
Run this from the same folder as pois.geojson.
"""
import json, time, os, sys, urllib.request, urllib.parse, math

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
GEOJSON_FILE = "pois.geojson"

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8
    d = math.pi / 180
    dlat = (lat2 - lat1) * d
    dlon = (lon2 - lon1) * d
    a = math.sin(dlat/2)**2 + math.cos(lat1*d)*math.cos(lat2*d)*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def main():
    script_dir   = os.path.dirname(os.path.abspath(sys.argv[0]))
    geojson_path = os.path.join(script_dir, GEOJSON_FILE)

    if not os.path.exists(geojson_path):
        print(f"ERROR: Could not find {GEOJSON_FILE} in {script_dir}")
        return

    print("=" * 60)
    print("Buc-ee's Coordinate Fixer v2")
    print("Merges OSM accuracy with website completeness")
    print("=" * 60)
    print()

    # ── 1. Query OSM ──────────────────────────────────────────────
    print("Querying OpenStreetMap for Buc-ee's locations...")
    query = """
[out:json][timeout:60];
nwr["brand:wikidata"="Q4982335"](24.0,-125.0,49.5,-66.0);
out center tags;
"""
    data = urllib.parse.urlencode({"data": query}).encode()
    req  = urllib.request.Request(
        OVERPASS_URL, data=data,
        headers={"User-Agent": "TeslaMapBuceeFixer/2.0 (personal use)"})

    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            result = json.loads(r.read())
    except Exception as ex:
        print(f"ERROR querying Overpass: {ex}")
        return

    elements = result.get("elements", [])

    # Build OSM location list, dedup by 2dp coordinate
    osm_seen = set()
    osm_locs = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue
        if lat is None or lon is None:
            continue
        key = (round(lat, 2), round(lon, 2))
        if key in osm_seen:
            continue
        osm_seen.add(key)
        osm_locs.append({
            "lat":   lat, "lon": lon,
            "city":  tags.get("addr:city", ""),
            "state": tags.get("addr:state", ""),
            "name":  tags.get("name", "Buc-ee's"),
            "matched": False,
        })

    print(f"OSM returned {len(osm_locs)} unique Buc-ee's locations")
    print()

    # ── 2. Load existing pois.geojson ─────────────────────────────
    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    features     = geojson["features"]
    other        = [f for f in features if f["properties"]["category"] != "bucees"]
    old_bucees   = [f for f in features if f["properties"]["category"] == "bucees"]

    print(f"Existing Buc-ee's in pois.geojson: {len(old_bucees)}")
    print()

    # ── 3. Match each existing entry to nearest OSM location ──────
    # If a match is found within 15 miles, replace coords with OSM.
    # If no match, keep the original website coords unchanged.
    MATCH_RADIUS_MILES = 15

    updated   = 0
    kept      = 0
    new_bucees = []

    for feat in old_bucees:
        flon, flat = feat["geometry"]["coordinates"]
        best_dist  = float("inf")
        best_osm   = None

        for osm in osm_locs:
            d = haversine_miles(flat, flon, osm["lat"], osm["lon"])
            if d < best_dist:
                best_dist = d
                best_osm  = osm

        if best_osm and best_dist <= MATCH_RADIUS_MILES:
            # Replace coordinates with accurate OSM value
            old_coords = [flon, flat]
            feat["geometry"]["coordinates"] = [best_osm["lon"], best_osm["lat"]]
            best_osm["matched"] = True
            if best_dist > 0.1:  # only report if actually moved
                print(f"  UPDATED  {feat['properties']['name']}")
                print(f"    Was:  {flat:.5f}, {flon:.5f}")
                print(f"    Now:  {best_osm['lat']:.5f}, {best_osm['lon']:.5f}  ({best_dist:.1f} mi off)")
            updated += 1
        else:
            # No OSM match nearby — keep original website coords
            print(f"  KEPT     {feat['properties']['name']}  (no OSM match within {MATCH_RADIUS_MILES} mi)")
            kept += 1

        new_bucees.append(feat)

    # ── 4. Add any OSM locations not matched to an existing entry ──
    # (new stores that opened after we scraped the website)
    added = 0
    for osm in osm_locs:
        if not osm["matched"]:
            name = f"Buc-ee's {osm['city']}, {osm['state']}" if osm["city"] else "Buc-ee's"
            new_bucees.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [osm["lon"], osm["lat"]]},
                "properties": {"category": "bucees", "name": name, "icon": "bucees"}
            })
            print(f"  ADDED    {name}  (new OSM location not in website list)")
            added += 1

    # ── 5. Save ────────────────────────────────────────────────────
    geojson["features"]  = other + new_bucees
    geojson["generated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))

    print()
    print(f"Summary:")
    print(f"  Coordinates updated from OSM: {updated}")
    print(f"  Kept original (no OSM match): {kept}")
    print(f"  New locations added from OSM: {added}")
    print(f"  Total Buc-ee's:               {len(new_bucees)}")
    print(f"  Total POIs:                   {len(geojson['features']):,}")
    print()
    print("Upload the updated pois.geojson to your GitHub repo.")

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print(f"\nUnexpected error: {ex}")
        import traceback
        traceback.print_exc()
    print()
    input("Press Enter to close...")
