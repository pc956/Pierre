"""
Cockpit Immo — Distance au cours d'eau le plus proche
Source: Overpass API (OpenStreetMap waterways)
"""
import httpx
import math
import logging

logger = logging.getLogger("water_data")

_water_cache: dict = {}


def _haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    p = math.pi / 180
    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    return R * 2 * math.asin(math.sqrt(a))


async def get_nearest_water(lon: float, lat: float, radius_m: int = 5000) -> dict:
    """Find nearest waterway (river, canal, stream) via Overpass API"""
    cache_key = f"{round(lon, 3)}_{round(lat, 3)}"
    if cache_key in _water_cache:
        return _water_cache[cache_key]

    result = {"dist_cours_eau_m": None, "nom_cours_eau": None}

    try:
        query = f'[out:json][timeout:8];(way["waterway"~"river|canal|stream"](around:{radius_m},{lat},{lon}););out center;'
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": query}
            )
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                min_dist = 999999
                nearest_name = None
                for el in elements:
                    center = el.get("center", {})
                    el_lat = center.get("lat", el.get("lat"))
                    el_lon = center.get("lon", el.get("lon"))
                    if el_lat and el_lon:
                        dist = _haversine(lon, lat, el_lon, el_lat)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_name = el.get("tags", {}).get("name", "Cours d'eau")
                if min_dist < 999999:
                    result["dist_cours_eau_m"] = round(min_dist)
                    result["nom_cours_eau"] = nearest_name
    except Exception as e:
        logger.warning(f"Overpass water error: {e}")

    _water_cache[cache_key] = result
    return result
