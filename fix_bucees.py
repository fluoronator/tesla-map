#!/usr/bin/env python3
"""
Buc-ee's Coordinate Fixer
Queries OpenStreetMap for all Buc-ee's using the confirmed Wikidata ID,
then replaces the hardcoded coordinates in pois.geojson with accurate OSM data.
Run this from the same folder as pois.geojson.
Window stays open when done.
"""
import json, time, os, sys, urllib.request, urllib.parse

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
GEOJSON_FILE = "pois.geojson"

def main():
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    # Look for pois.geojson next to the script
    geojson_path = os.path.join(script_dir, GEOJSON_FILE)
    if not os.path.exists(geojson_path):
        print(f"ERROR: Could not find {GEOJSON_FILE} in {script_dir}")
        print("Place this script in the same folder as pois.geojson and try again.")
        return

    print("=" * 55)
    print("Buc-ee's Coordinate Fixer")
    print("=" * 55)
    print()
    print("Querying OpenStreetMap for all Buc-ee's locations...")

    query = """
[out:json][timeout:60];
nwr["brand:wikidata"="Q4982335"](24.0,-125.0,49.5,-66.0);
out center tags;
"""
    data = urllib.parse.urlencode({"data": query}).encode()
    req  = urllib.request.Request(
        OVERPASS_URL, data=data,
        headers={"User-Agent": "TeslaMapBuceeFixer/1.0 (personal use)"})

    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            result = json.loads(r.read())
    except Exception as ex:
        print(f"ERROR querying Overpass: {ex}")
        return

    elements = result.get("elements", [])
    print(f"OSM returned {len(elements)} raw elements")

    # Extract unique OSM locations, dedup by 2dp coordinate
    osm_seen = set()
    osm_locations = []
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
        osm_locations.append({
            "lat": lat, "lon": lon,
            "city":  tags.get("addr:city", ""),
            "state": tags.get("addr:state", ""),
            "name":  tags.get("name", "Buc-ee's"),
        })

    print(f"Unique OSM Buc-ee's locations: {len(osm_locations)}")
    print()

    # Load pois.geojson
    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson["features"]

    # Separate out existing Buc-ee's entries
    other_features  = [f for f in features if f["properties"]["category"] != "bucees"]
    old_bucees      = [f for f in features if f["properties"]["category"] == "bucees"]
    print(f"Existing Buc-ee's in pois.geojson: {len(old_bucees)}")

    # Build new features from OSM data
    new_bucees = []
    for loc in osm_locations:
        name = loc["name"]
        if loc["city"] and loc["state"]:
            display = f"Buc-ee's {loc['city']}, {loc['state']}"
        else:
            display = name

        new_bucees.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [loc["lon"], loc["lat"]]
            },
            "properties": {
                "category": "bucees",
                "name":     display,
                "icon":     "bucees",
            }
        })

    print(f"New Buc-ee's from OSM: {len(new_bucees)}")
    print()
    print("Locations found:")
    for loc in sorted(osm_locations, key=lambda x: (x["state"], x["city"])):
        print(f"  {loc['city']:20s} {loc['state']}  {loc['lat']:.5f}, {loc['lon']:.5f}")

    # Rebuild geojson
    geojson["features"]  = other_features + new_bucees
    geojson["generated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Save — overwrite in place
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))

    print()
    print(f"Saved {len(geojson['features']):,} total features to {geojson_path}")
    print(f"Replaced {len(old_bucees)} old entries with {len(new_bucees)} OSM-accurate entries.")
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
