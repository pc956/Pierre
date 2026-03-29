"""
Cockpit Immo — Distance à la route principale la plus proche
Source: Overpass API (OpenStreetMap highways)
"""
import httpx
import math
import logging

logger = logging.getLogger("road_data")

_road_cache: dict = {}


def _haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    p = math.pi / 180
    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    return R * 2 * math.asin(math.sqrt(a))


async def get_nearest_road(lon: float, lat: float, radius_m: int = 5000) -> dict:
    """Find nearest major road (motorway, trunk, primary) via Overpass API"""
    cache_key = f"{round(lon, 3)}_{round(lat, 3)}"
    if cache_key in _road_cache:
        return _road_cache[cache_key]

    result = {"dist_route_m": None, "nom_route": None, "type_route": None}

    try:
        query = f'[out:json][timeout:8];(way["highway"~"motorway|trunk|primary|motorway_link"](around:{radius_m},{lat},{lon}););out center;'
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://overpass-api.de/api/interpreter",
                data={"data": query}
            )
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                min_dist = 999999
                nearest = None
                for el in elements:
                    center = el.get("center", {})
                    el_lat = center.get("lat", el.get("lat"))
                    el_lon = center.get("lon", el.get("lon"))
                    if el_lat and el_lon:
                        dist = _haversine(lon, lat, el_lon, el_lat)
                        if dist < min_dist:
                            min_dist = dist
                            nearest = el
                if nearest and min_dist < 999999:
                    tags = nearest.get("tags", {})
                    hw = tags.get("highway", "")
                    nom = tags.get("name") or tags.get("ref") or "Route principale"
                    type_route = "autoroute" if "motorway" in hw else "nationale" if hw == "trunk" else "départementale"
                    result["dist_route_m"] = round(min_dist)
                    result["nom_route"] = nom
                    result["type_route"] = type_route
    except Exception as e:
        logger.warning(f"Overpass road error: {e}")

    _road_cache[cache_key] = result
    return result
