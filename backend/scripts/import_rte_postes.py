"""
Import des postes électriques RTE depuis l'API ODRÉ + fallback Overpass OSM.
Source: https://odre.opendatasoft.com/explore/dataset/postes-electriques-rte/
Génère un fichier JSON avec les coordonnées GPS réelles.
"""
import httpx
import json
import re
import sys
import asyncio

ODRE_APIS = [
    "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/postes-electriques-rte/records?limit=100&offset={offset}",
    "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/postes-electriques-rte-2022/records?limit=100&offset={offset}",
]
GEOJSON_URL = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/postes-electriques-rte/exports/geojson"
ENCEINTES_URL = "https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/enceintes-de-poste-rte/exports/geojson"

REGION_FROM_DEPT = {
    "01": "AuRA", "02": "HdF", "03": "AuRA", "04": "PACA", "05": "PACA", "06": "PACA", "07": "AuRA", "08": "GES",
    "09": "OCC", "10": "GES", "11": "OCC", "12": "OCC", "13": "PACA", "14": "NOR",
    "15": "AuRA", "16": "NAQ", "17": "NAQ", "18": "CVL", "19": "NAQ",
    "21": "BFC", "22": "BRE", "23": "NAQ", "24": "NAQ", "25": "BFC",
    "26": "AuRA", "27": "NOR", "28": "CVL", "29": "BRE",
    "30": "OCC", "31": "OCC", "32": "OCC", "33": "NAQ", "34": "OCC",
    "35": "BRE", "36": "CVL", "37": "CVL", "38": "AuRA", "39": "BFC",
    "40": "NAQ", "41": "CVL", "42": "AuRA", "43": "AuRA", "44": "PDL",
    "45": "CVL", "46": "OCC", "47": "NAQ", "48": "OCC", "49": "PDL",
    "50": "NOR", "51": "GES", "52": "GES", "53": "PDL", "54": "GES",
    "55": "GES", "56": "BRE", "57": "GES", "58": "BFC", "59": "HdF",
    "60": "HdF", "61": "NOR", "62": "HdF", "63": "AuRA", "64": "NAQ",
    "65": "OCC", "66": "OCC", "67": "GES", "68": "GES", "69": "AuRA",
    "70": "BFC", "71": "BFC", "72": "PDL", "73": "AuRA", "74": "AuRA",
    "75": "IDF", "76": "NOR", "77": "IDF", "78": "IDF", "79": "NAQ",
    "80": "HdF", "81": "OCC", "82": "OCC", "83": "PACA", "84": "PACA",
    "85": "PDL", "86": "NAQ", "87": "NAQ", "88": "GES", "89": "BFC",
    "90": "BFC", "91": "IDF", "92": "IDF", "93": "IDF", "94": "IDF", "95": "IDF",
    "2A": "Corse", "2B": "Corse",
}


def extract_tension(props):
    for key in ["tension_max", "tension", "niv_tension", "niveau_tension"]:
        val = props.get(key)
        if val is not None:
            if isinstance(val, (int, float)):
                return int(val)
            s = str(val)
            m = re.search(r"(\d+)", s)
            if m:
                return int(m.group(1))
    return 0


def compute_centroid(geom):
    gtype = geom.get("type", "")
    coords = geom.get("coordinates", [])
    if gtype == "Point":
        return round(coords[0], 5), round(coords[1], 5)
    if gtype == "Polygon" and coords:
        ring = coords[0]
        lon = sum(c[0] for c in ring) / len(ring)
        lat = sum(c[1] for c in ring) / len(ring)
        return round(lon, 5), round(lat, 5)
    if gtype == "MultiPolygon" and coords:
        all_pts = [c for poly in coords for ring in poly for c in ring]
        if all_pts:
            lon = sum(c[0] for c in all_pts) / len(all_pts)
            lat = sum(c[1] for c in all_pts) / len(all_pts)
            return round(lon, 5), round(lat, 5)
    return None, None


def fetch_all_postes():
    postes = []

    # Method 1: GeoJSON export
    print("Trying ODRÉ GeoJSON export...")
    try:
        resp = httpx.get(GEOJSON_URL, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            features = data.get("features", [])
            for f in features:
                props = f.get("properties", {})
                geom = f.get("geometry")
                if not geom:
                    continue
                lon, lat = compute_centroid(geom)
                if lon is None:
                    continue
                postes.append({
                    "nom": props.get("nom_poste", props.get("nom", "")),
                    "code_poste": props.get("code_poste", ""),
                    "tension_max": extract_tension(props),
                    "departement": props.get("code_departement", props.get("departement", "")),
                    "type_poste": props.get("type_ouvrage", props.get("type_poste", "")),
                    "lon": lon,
                    "lat": lat,
                })
            if postes:
                print(f"  GeoJSON: {len(postes)} postes found")
                return postes
    except Exception as e:
        print(f"  GeoJSON failed: {e}")

    # Method 2: Paginated API
    for api_url in ODRE_APIS:
        print(f"Trying paginated API: {api_url[:80]}...")
        postes = []
        offset = 0
        try:
            while True:
                resp = httpx.get(api_url.format(offset=offset), timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                records = data.get("results", data.get("records", []))
                if not records:
                    break
                for r in records:
                    fields = r.get("fields", r)
                    geo = fields.get("geo_point_2d") or fields.get("geo_point")
                    if not geo:
                        continue
                    if isinstance(geo, dict):
                        lat = geo.get("lat", geo.get("latitude"))
                        lon = geo.get("lon", geo.get("longitude"))
                    elif isinstance(geo, list) and len(geo) >= 2:
                        lat, lon = geo[0], geo[1]
                    else:
                        continue
                    if not lat or not lon:
                        continue
                    postes.append({
                        "nom": fields.get("nom_poste", fields.get("nom", "")),
                        "code_poste": fields.get("code_poste", ""),
                        "tension_max": extract_tension(fields),
                        "departement": fields.get("code_departement", fields.get("departement", "")),
                        "type_poste": fields.get("type_ouvrage", fields.get("type_poste", "")),
                        "lon": round(float(lon), 5),
                        "lat": round(float(lat), 5),
                    })
                offset += 100
                if len(records) < 100:
                    break
            if postes:
                print(f"  Paginated: {len(postes)} postes found")
                return postes
        except Exception as e:
            print(f"  Paginated API failed: {e}")

    # Method 3: Enceintes (polygons → centroids)
    print("Trying enceintes (polygon centroids)...")
    try:
        resp = httpx.get(ENCEINTES_URL, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            for f in data.get("features", []):
                props = f.get("properties", {})
                geom = f.get("geometry")
                if not geom:
                    continue
                lon, lat = compute_centroid(geom)
                if lon is None:
                    continue
                postes.append({
                    "nom": props.get("nom_poste", props.get("nom", "")),
                    "code_poste": props.get("code_poste", ""),
                    "tension_max": extract_tension(props),
                    "departement": props.get("code_departement", ""),
                    "type_poste": props.get("type_ouvrage", ""),
                    "lon": lon,
                    "lat": lat,
                })
            if postes:
                print(f"  Enceintes: {len(postes)} postes found")
                return postes
    except Exception as e:
        print(f"  Enceintes failed: {e}")

    return postes


def fetch_from_overpass():
    """Fallback: fetch HTB substations from OpenStreetMap Overpass API"""
    print("Trying Overpass API (OSM fallback)...")
    query = '[out:json][timeout:60];area["ISO3166-1"="FR"]->.france;(node["power"="substation"]["voltage"~"[0-9]{5,}"](area.france);way["power"="substation"]["voltage"~"[0-9]{5,}"](area.france););out center;'
    try:
        resp = httpx.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=90)
        if resp.status_code == 200:
            data = resp.json()
            postes = []
            for el in data.get("elements", []):
                tags = el.get("tags", {})
                voltage_str = tags.get("voltage", "0")
                voltages = [int(v) for v in voltage_str.replace(" ", "").split(";") if v.isdigit()]
                max_voltage = max(voltages) if voltages else 0
                kv = max_voltage // 1000
                if kv < 63:
                    continue
                lat = el.get("lat") or el.get("center", {}).get("lat")
                lon = el.get("lon") or el.get("center", {}).get("lon")
                if not lat or not lon:
                    continue
                name = tags.get("name", "")
                postes.append({
                    "nom": name,
                    "code_poste": "",
                    "tension_max": kv,
                    "departement": "",
                    "type_poste": "",
                    "lon": round(float(lon), 5),
                    "lat": round(float(lat), 5),
                })
            print(f"  Overpass: {len(postes)} postes found")
            return postes
    except Exception as e:
        print(f"  Overpass failed: {e}")
    return []


def generate_france_infra_update(postes):
    filtered = []
    for p in postes:
        if not p["lon"] or not p["lat"]:
            continue
        if 0 < p["tension_max"] < 63:
            continue
        tp = (p.get("type_poste") or "").lower()
        if "piquage" in tp:
            continue
        dept = str(p.get("departement", ""))[:2]
        region = REGION_FROM_DEPT.get(dept, "")
        filtered.append({
            "nom": p["nom"],
            "code_poste": p.get("code_poste", ""),
            "tension_max": p["tension_max"],
            "lon": p["lon"],
            "lat": p["lat"],
            "region": region,
            "departement": dept,
        })

    # Deduplicate by coordinates (within ~100m)
    seen = set()
    unique = []
    for p in filtered:
        key = f"{round(p['lon'], 3)}_{round(p['lat'], 3)}"
        if key not in seen:
            seen.add(key)
            unique.append(p)

    print(f"\nFiltered: {len(unique)} postes (from {len(postes)} raw)")

    # Regional distribution
    regions = {}
    for p in unique:
        r = p["region"] or "Unknown"
        regions[r] = regions.get(r, 0) + 1
    for r, c in sorted(regions.items()):
        print(f"  {r}: {c} postes")

    with open("rte_postes_reels.json", "w") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to rte_postes_reels.json")
    return unique


if __name__ == "__main__":
    postes = fetch_all_postes()
    if not postes:
        print("ODRÉ failed. Trying Overpass fallback...")
        postes = fetch_from_overpass()
    if not postes:
        print("ERROR: No data from any source")
        sys.exit(1)
    print(f"\nTotal raw postes: {len(postes)}")
    generate_france_infra_update(postes)
