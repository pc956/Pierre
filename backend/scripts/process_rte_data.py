"""
Process raw Overpass RTE data into clean, app-ready format.
Filters to France, normalizes tensions, assigns regions, deduplicates.
Outputs two files:
  - rte_postes_map.json (≥225kV for map display)
  - rte_postes_all.json (≥63kV for distance calculations)
"""
import json
import os

# Simplified France metropolitan polygon (excludes neighbors)
FRANCE_POLYGON = [
    (-1.8, 43.3),   # Pyrenees west (Bayonne)
    (0.7, 42.5),    # Pyrenees east (Andorra)
    (3.1, 42.4),    # Mediterranean border
    (3.5, 43.2),    # Narbonne coast
    (5.0, 43.2),    # Marseille coast
    (6.2, 43.1),    # Toulon
    (7.4, 43.7),    # Nice / Monaco border
    (7.7, 44.1),    # Italian border Alps south
    (7.1, 44.7),    # Alps mid
    (7.0, 45.5),    # Alps north (Mont Blanc)
    (6.8, 46.4),    # Geneva area
    (7.6, 47.5),    # Jura / Basel
    (8.2, 48.0),    # Alsace south
    (8.2, 49.0),    # Alsace north (Strasbourg)
    (6.4, 49.5),    # Luxembourg border
    (5.8, 49.6),    # Belgium border east
    (4.2, 50.1),    # Belgium border mid
    (2.6, 51.1),    # Calais/Dunkerque
    (1.6, 51.0),    # Channel coast
    (-1.8, 48.6),   # Brittany north
    (-5.1, 48.4),   # Finistère
    (-4.8, 47.8),   # Brittany south
    (-3.5, 47.3),   # Quimper
    (-2.5, 46.7),   # Vendée coast
    (-1.2, 46.1),   # La Rochelle
    (-1.2, 44.5),   # Bordeaux coast
    (-1.8, 43.3),   # back to start
]

# Corsica bbox (separate)
CORSE_BOX = (8.5, 9.6, 41.3, 43.1)

def _point_in_polygon(lon, lat, polygon):
    """Ray casting algorithm for point-in-polygon test"""
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside

def in_france(lon, lat):
    """Check if point is in France metropolitan or Corsica"""
    if CORSE_BOX[0] <= lon <= CORSE_BOX[1] and CORSE_BOX[2] <= lat <= CORSE_BOX[3]:
        return True
    return _point_in_polygon(lon, lat, FRANCE_POLYGON)

# Regional capitals for nearest-center assignment
import math

REGION_CENTERS = {
    "IDF": (2.35, 48.86),
    "HdF": (2.80, 49.90),
    "NOR": (0.10, 49.20),
    "BRE": (-2.75, 48.10),
    "PDL": (-1.55, 47.22),
    "CVL": (1.75, 47.40),
    "BFC": (5.00, 47.30),
    "GES": (5.70, 48.60),
    "AuRA": (4.80, 45.50),
    "NAQ": (0.00, 45.50),
    "OCC": (2.50, 43.60),
    "PACA": (5.70, 43.50),
    "Corse": (9.10, 42.15),
}

def _dist2(lon1, lat1, lon2, lat2):
    return (lon1 - lon2)**2 + (lat1 - lat2)**2

# Normalize OSM voltages to standard French HTB levels
def normalize_tension(kv):
    if kv >= 380:
        return 400
    if kv >= 200:
        return 225
    if kv >= 140:
        return 150
    if kv >= 80:
        return 90
    return 63

# Estimate MVA from tension
def estimate_mva(tension_kv):
    return {400: 500, 225: 280, 150: 180, 90: 120, 63: 100}.get(tension_kv, 100)

def assign_region(lon, lat):
    best_region = ""
    best_dist = float("inf")
    for region, (clon, clat) in REGION_CENTERS.items():
        d = _dist2(lon, lat, clon, clat)
        if d < best_dist:
            best_dist = d
            best_region = region
    return best_region

def process():
    input_path = os.path.join(os.path.dirname(__file__), "..", "rte_postes_reels.json")
    with open(input_path) as f:
        raw = json.load(f)

    print(f"Raw input: {len(raw)} postes")

    # Step 1: Filter to France polygon
    france = [p for p in raw if in_france(p["lon"], p["lat"])]
    print(f"In France bbox: {len(france)}")

    # Step 2: Normalize tensions, assign regions, format
    processed = []
    for p in france:
        tension_norm = normalize_tension(p["tension_kv"])
        region = assign_region(p["lon"], p["lat"])
        processed.append({
            "nom": p.get("nom", "") or f"Poste {tension_norm}kV",
            "tension_kv": tension_norm,
            "tension_kv_raw": p["tension_kv"],
            "puissance_mva": estimate_mva(tension_norm),
            "lon": p["lon"],
            "lat": p["lat"],
            "region": region,
        })

    # Step 3: Deduplicate by proximity (~200m)
    seen = set()
    unique = []
    for p in processed:
        key = f"{round(p['lon'], 3)}_{round(p['lat'], 3)}"
        if key not in seen:
            seen.add(key)
            unique.append(p)
        else:
            # Keep the one with highest tension
            for i, existing in enumerate(unique):
                ekey = f"{round(existing['lon'], 3)}_{round(existing['lat'], 3)}"
                if ekey == key and p["tension_kv"] > existing["tension_kv"]:
                    unique[i] = p
                    break

    print(f"After dedup: {len(unique)}")

    # Step 4: Format for the app
    all_postes = []
    map_postes = []
    for idx, p in enumerate(unique):
        region_code = p["region"].lower().replace("-", "").replace(" ", "") or "fr"
        entry = {
            "asset_id": f"htb_{region_code}_{idx+1:04d}",
            "nom": p["nom"],
            "type": "poste_htb",
            "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
            "tension_kv": p["tension_kv"],
            "puissance_mva": p["puissance_mva"],
            "region": p["region"],
        }
        all_postes.append(entry)
        if p["tension_kv"] >= 225:
            map_postes.append(entry)

    # Stats
    regions = {}
    tensions = {}
    for p in all_postes:
        r = p["region"] or "Unknown"
        regions[r] = regions.get(r, 0) + 1
        t = p["tension_kv"]
        tensions[t] = tensions.get(t, 0) + 1

    print(f"\nAll postes: {len(all_postes)}")
    print(f"Map postes (≥225kV): {len(map_postes)}")
    print(f"\nBy tension: {dict(sorted(tensions.items()))}")
    print(f"\nBy region: {dict(sorted(regions.items()))}")

    # Save
    out_dir = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(out_dir, "rte_postes_all.json"), "w") as f:
        json.dump(all_postes, f, ensure_ascii=False)
    with open(os.path.join(out_dir, "rte_postes_map.json"), "w") as f:
        json.dump(map_postes, f, ensure_ascii=False)

    print(f"\nSaved rte_postes_all.json ({len(all_postes)} postes)")
    print(f"Saved rte_postes_map.json ({len(map_postes)} postes)")

if __name__ == "__main__":
    process()
