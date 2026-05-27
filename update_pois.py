#!/usr/bin/env python3
"""
Tesla Map — POI GeoJSON Updater v5
Source: OpenStreetMap via Overpass API — no API key required.
"""

import json, time, threading, os, sys
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import urllib.request, urllib.parse, urllib.error

# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────
CATEGORIES = [
    {
        "id":          "bucees",
        "label":       "Buc-ee's",
        "emoji":       "\U0001f426",
        "color":       "#FFD700",
        "icon":        "bucees",
        "wikidata_id": "Q4982335",
        "name_regex":  None,
    },
    {
        "id":          "walmart",
        "label":       "Walmart",
        "emoji":       "\U0001f6d2",
        "color":       "#0071CE",
        "icon":        "walmart",
        "wikidata_id": "Q483551",
        "name_regex":  "^Wal-?Mart|^Walmart",
    },
    {
        "id":          "tesla_supercharger",
        "label":       "Tesla Supercharger",
        "emoji":       "\u26a1",
        "color":       "#E82127",
        "icon":        "tesla",
        "wikidata_id": "Q17089620",
        "name_regex":  None,
    },
    {
        "id":          "mr_carwash",
        "label":       "Mister Car Wash",
        "emoji":       "\U0001f697",
        "color":       "#00AEEF",
        "icon":        "carwash",
        "wikidata_id": "Q113753592",
        "name_regex":  "^M(iste)?r\\.? ?Car ?Wash",
    },
    {
        "id":          "rest_stop",
        "label":       "Rest Stop",
        "emoji":       "\U0001f6e3",
        "color":       "#4CAF50",
        "icon":        "rest_stop",
        "wikidata_id": None,
        "name_regex":  None,
    },
    {
        "id":          "starbucks",
        "label":       "Starbucks",
        "emoji":       "\u2615",
        "color":       "#00704A",
        "icon":        "starbucks",
        "wikidata_id": "Q37158",
        "name_regex":  "^Starbucks",
    },
]

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

REGIONS = {
    "Entire USA":    (24.0, -125.0, 49.5,  -66.0),
    "Southeast":     (24.5,  -92.0, 37.0,  -75.0),
    "South-Central": (25.8, -106.7, 36.5,  -88.0),
    "Northeast":     (38.0,  -82.0, 47.5,  -66.5),
    "Midwest":       (36.0,  -97.0, 49.0,  -80.0),
    "Mountain West": (31.3, -117.0, 49.0, -102.0),
    "Pacific Coast": (32.5, -124.5, 49.0, -114.0),
}


# ─────────────────────────────────────────────────────────────────────────────
# QUERY BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_queries(cat, bbox):
    s, w, n, e = bbox
    bb = f"({s},{w},{n},{e})"
    queries = []

    if cat["id"] == "rest_stop":
        q = (
            "[out:json][timeout:120];\n(\n"
            f"  way[\"highway\"=\"rest_area\"]{bb};\n"
            f"  relation[\"highway\"=\"rest_area\"]{bb};\n"
            f"  way[\"amenity\"=\"rest_area\"]{bb};\n"
            f"  relation[\"amenity\"=\"rest_area\"]{bb};\n"
            ");\nout center tags;"
        )
        queries.append(("rest_area ways+relations", q))

    elif cat["id"] == "tesla_supercharger":
        q = f'[out:json][timeout:120];\nnwr["brand:wikidata"="Q17089620"]{bb};\nout center tags;'
        queries.append(("brand:wikidata", q))

    elif cat["id"] in ("walmart", "starbucks"):
        # High-volume brands — two separate queries to avoid Overpass timeouts
        q1 = f'[out:json][timeout:120];\nnwr["brand:wikidata"="{cat["wikidata_id"]}"]{bb};\nout center tags;'
        queries.append(("brand:wikidata", q1))
        rx = cat["name_regex"]
        q2 = f'[out:json][timeout:120];\nnwr["name"~"{rx}",i]{bb};\nout center tags;'
        queries.append(("name regex", q2))

    else:
        clauses = []
        if cat["wikidata_id"]:
            clauses.append(f'nwr["brand:wikidata"="{cat["wikidata_id"]}"]{bb};')
        if cat.get("name_regex"):
            rx = cat["name_regex"]
            clauses.append(f'nwr["name"~"{rx}",i]{bb};')
            clauses.append(f'nwr["brand"~"{rx}",i]{bb};')
        if clauses:
            body = "\n".join(f"  {cl}" for cl in clauses)
            q = f"[out:json][timeout:120];\n(\n{body}\n);\nout center tags;"
            queries.append(("combined", q))

    return queries


# ─────────────────────────────────────────────────────────────────────────────
# OVERPASS FETCH
# ─────────────────────────────────────────────────────────────────────────────

def fetch_overpass(query, log_fn):
    data = urllib.parse.urlencode({"data": query}).encode()
    req  = urllib.request.Request(
        OVERPASS_URL, data=data,
        headers={"User-Agent": "TeslaMapPOIUpdater/5.0 (personal use)"}
    )
    log_fn("  Sending request to Overpass API...")
    with urllib.request.urlopen(req, timeout=150) as resp:
        raw = resp.read()
    log_fn(f"  Received {len(raw):,} bytes.")
    return json.loads(raw)


# ─────────────────────────────────────────────────────────────────────────────
# ELEMENT → GEOJSON FEATURE
# ─────────────────────────────────────────────────────────────────────────────

def elements_to_features(elements, cat, log_fn=None):
    features    = []
    seen        = set()
    type_counts = {}
    skipped     = 0

    for el in elements:
        etype = el.get("type", "?")
        type_counts[etype] = type_counts.get(etype, 0) + 1

        if etype == "node":
            lat, lon = el.get("lat"), el.get("lon")
        elif "center" in el:
            lat, lon = el["center"]["lat"], el["center"]["lon"]
        else:
            skipped += 1; continue

        if lat is None or lon is None:
            skipped += 1; continue

        tags = el.get("tags", {})
        if not tags:
            skipped += 1; continue

        el_name = tags.get("name", "")
        if any(sub in el_name for sub in [
            "Pharmacy", "Garden Center", "Vision Center",
            "Auto Center", "Tire & Lube", "Deli", "Bakery",
        ]):
            skipped += 1; continue

        key = (round(lat, 2), round(lon, 2))
        if key in seen:
            skipped += 1; continue
        seen.add(key)

        name = (tags.get("name") or tags.get("operator") or
                tags.get("brand") or cat["label"])

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "category": cat["id"],
                "name":     name,
                "color":    cat["color"],
                "icon":     cat["icon"],
                "address":  tags.get("addr:full", ""),
                "city":     tags.get("addr:city", ""),
                "state":    tags.get("addr:state", ""),
                "phone":    tags.get("phone", ""),
                "website":  tags.get("website", ""),
                "osm_id":   el.get("id"),
                "osm_type": etype,
            },
        })

    if log_fn:
        breakdown = ", ".join(f"{k}:{v}" for k, v in sorted(type_counts.items()))
        log_fn(f"  Raw elements: {len(elements):,}  ({breakdown})")
        if skipped:
            log_fn(f"  Skipped {skipped} (no coords, no tags, sub-dept, or dedup)")
        log_fn(f"  Unique locations: {len(features):,}")

    return features


# ─────────────────────────────────────────────────────────────────────────────
# GUI
# ─────────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tesla Map — POI Updater v5")
        self.resizable(True, True)
        self.minsize(560, 620)
        self._build_ui()
        self._center_window(620, 700)

    def _center_window(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        PAD = 14

        hdr = tk.Frame(self, bg="#1a1a2e", pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Tesla Map  \u00b7  POI Updater",
                 bg="#1a1a2e", fg="#e8f4ff",
                 font=("Helvetica", 16, "bold")).pack()
        tk.Label(hdr, text="Source: OpenStreetMap via Overpass API — no API key needed",
                 bg="#1a1a2e", fg="#6a8aaa", font=("Helvetica", 9)).pack()

        body = tk.Frame(self, padx=PAD, pady=PAD)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        row = 0

        tk.Label(body, text="Categories to fetch:",
                 font=("Helvetica", 10, "bold")).grid(
                 row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
        row += 1

        self.cat_vars = {}
        for cat in CATEGORIES:
            var = tk.BooleanVar(value=True)
            self.cat_vars[cat["id"]] = var
            tk.Checkbutton(body, text=f"{cat['emoji']}  {cat['label']}",
                           variable=var, font=("Helvetica", 10)).grid(
                           row=row, column=0, columnspan=2,
                           sticky="w", padx=(10, 0))
            row += 1

        ttk.Separator(body, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1

        tk.Label(body, text="Region:",
                 font=("Helvetica", 10, "bold")).grid(
                 row=row, column=0, sticky="w", pady=(0, 4))
        self.region_var = tk.StringVar(value="Southeast")
        ttk.Combobox(body, textvariable=self.region_var,
                     values=list(REGIONS.keys()),
                     state="readonly", width=24).grid(
                     row=row, column=1, sticky="w")
        row += 1

        tk.Label(body, text="Output file:",
                 font=("Helvetica", 10, "bold")).grid(
                 row=row, column=0, sticky="w", pady=(6, 4))
        ff = tk.Frame(body)
        ff.grid(row=row, column=1, sticky="ew", pady=(6, 4))
        self.outpath_var = tk.StringVar(value="pois.geojson")
        tk.Entry(ff, textvariable=self.outpath_var, width=30).pack(
            side="left", fill="x", expand=True)
        tk.Button(ff, text="Browse...", command=self._browse).pack(
            side="left", padx=(4, 0))
        row += 1

        ttk.Separator(body, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1

        self.progress = ttk.Progressbar(body, mode="determinate",
                                        length=400, maximum=100)
        self.progress.grid(row=row, column=0, columnspan=2,
                           sticky="ew", pady=(0, 4))
        row += 1

        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(body, textvariable=self.status_var,
                 font=("Helvetica", 9), fg="#555", anchor="w").grid(
                 row=row, column=0, columnspan=2, sticky="w")
        row += 1

        self.log_box = scrolledtext.ScrolledText(
            body, height=12, font=("Courier", 9),
            state="disabled", bg="#f5f5f5", relief="flat", bd=1)
        self.log_box.grid(row=row, column=0, columnspan=2,
                          sticky="nsew", pady=(8, 0))
        body.rowconfigure(row, weight=1)
        row += 1

        self.run_btn = tk.Button(
            body, text="\u2b07  Fetch & Save POIs",
            font=("Helvetica", 12, "bold"),
            bg="#1e8cff", fg="white", activebackground="#1567cc",
            relief="flat", padx=16, pady=8,
            cursor="hand2", command=self._start)
        self.run_btn.grid(row=row, column=0, columnspan=2,
                          sticky="ew", pady=(12, 4))

    def _browse(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".geojson",
            filetypes=[("GeoJSON", "*.geojson"), ("All files", "*.*")],
            initialfile="pois.geojson")
        if path:
            self.outpath_var.set(path)

    def _log(self, msg):
        def _w():
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.after(0, _w)

    def _set_status(self, msg):
        self.after(0, lambda: self.status_var.set(msg))

    def _set_progress(self, pct):
        self.after(0, lambda: self.progress.config(value=pct))

    def _start(self):
        selected = [c for c in CATEGORIES if self.cat_vars[c["id"]].get()]
        if not selected:
            messagebox.showwarning("Nothing selected",
                                   "Please select at least one category.")
            return
        outpath = self.outpath_var.get().strip()
        if not outpath:
            messagebox.showwarning("No output file", "Please choose an output file.")
            return
        self.run_btn.config(state="disabled", text="Working...")
        self._set_progress(0)
        bbox = REGIONS[self.region_var.get()]
        threading.Thread(target=self._run_fetch,
                         args=(selected, bbox, outpath),
                         daemon=True).start()

    def _run_fetch(self, selected_cats, bbox, outpath):
        try:
            all_features = []
            total = len(selected_cats)

            for i, cat in enumerate(selected_cats):
                self._log(f"\n{'─' * 52}")
                self._log(f"Fetching: {cat['emoji']} {cat['label']}")
                self._set_status(f"Fetching {cat['label']}...")

                queries      = build_queries(cat, bbox)
                cat_elements = []

                for q_label, query in queries:
                    if len(queries) > 1:
                        self._log(f"  Sub-query: {q_label}")
                    try:
                        result   = fetch_overpass(query, self._log)
                        elements = result.get("elements", [])
                        cat_elements.extend(elements)
                        if len(queries) > 1:
                            self._log(f"  Returned {len(elements):,} elements")
                        if queries.index((q_label, query)) < len(queries) - 1:
                            time.sleep(2)
                    except urllib.error.HTTPError as ex:
                        self._log(f"  HTTP {ex.code}: {ex.reason}")
                        if ex.code == 504:
                            self._log("  (Gateway timeout — Overpass busy, try again later)")
                    except urllib.error.URLError as ex:
                        self._log(f"  Network error: {ex.reason}")
                    except Exception as ex:
                        self._log(f"  Error: {ex}")

                features = elements_to_features(cat_elements, cat, self._log)
                all_features.extend(features)
                self._set_progress(int((i + 1) / total * 90))

                if i < total - 1:
                    self._log("  Waiting 3s...")
                    time.sleep(3)

            # Write GeoJSON
            self._log(f"\n{'─' * 52}")
            self._log(f"Writing {len(all_features):,} features to:")
            self._log(f"  {outpath}")

            geojson = {
                "type":      "FeatureCollection",
                "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "features":  all_features,
            }
            with open(outpath, "w", encoding="utf-8") as f:
                json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))

            self._set_progress(100)
            self._log(f"\n\u2705 Done!  {len(all_features):,} POIs saved.\n")
            self._log("Summary:")

            counts = {}
            for feat in all_features:
                cid = feat["properties"]["category"]
                counts[cid] = counts.get(cid, 0) + 1
            for cat in selected_cats:
                n   = counts.get(cat["id"], 0)
                bar = "\u2588" * min(n // 10, 35)
                self._log(f"  {cat['emoji']} {cat['label']:25s}  {n:>6,}  {bar}")

            self._log(f"\n  Upload '{outpath}' to your GitHub repo.")
            self._set_status(f"Done — {len(all_features):,} POIs saved.")

        except Exception as ex:
            self._log(f"\nUnexpected error: {ex}")
            import traceback
            self._log(traceback.format_exc())
            self._set_status("Error — see log.")
        finally:
            self.after(0, lambda: self.run_btn.config(
                state="normal", text="\u2b07  Fetch & Save POIs"))


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()
