"""
Cockpit Immo - API Carto Integration (IGN France)
Free cadastre API for all French parcels
https://apicarto.ign.fr/api/doc/cadastre
"""
import httpx
from typing import List, Dict, Any, Optional
import asyncio

API_CARTO_BASE = "https://apicarto.ign.fr/api/cadastre"


async def search_communes(search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Search communes by name using API Geo"""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            "https://geo.api.gouv.fr/communes",
            params={
                "nom": search_term,
                "fields": "nom,code,codesPostaux,departement,region,population,centre",
                "boost": "population",
                "limit": limit
            }
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_parcelles_by_commune(code_insee: str, section: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all parcelles for a commune
    Warning: Large communes can have thousands of parcels
    """
    async with httpx.AsyncClient(timeout=60) as client:
        params = {"code_insee": code_insee}
        if section:
            params["section"] = section
        
        response = await client.get(
            f"{API_CARTO_BASE}/parcelle",
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        return {"type": "FeatureCollection", "features": []}


async def get_parcelle_by_id(parcelle_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific parcelle by its ID
    ID format: DDDCCCSSSNNNN (dept + commune + section + numero)
    Example: 13055000AI0123
    """
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{API_CARTO_BASE}/parcelle",
            params={"code_arr": parcelle_id[:5], "section": parcelle_id[5:7], "numero": parcelle_id[7:]}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                return data["features"][0]
        return None


async def get_parcelles_by_bbox(
    min_lon: float, 
    min_lat: float, 
    max_lon: float, 
    max_lat: float,
    limit: int = 500
) -> Dict[str, Any]:
    """
    Get parcelles within a bounding box
    Uses POST with GeoJSON geometry for intersection
    """
    bbox_geojson = {
        "type": "Polygon",
        "coordinates": [[
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat]
        ]]
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(
            f"{API_CARTO_BASE}/parcelle",
            params={
                "geom": str(bbox_geojson).replace("'", '"'),
                "_limit": limit
            }
        )
        
        if response.status_code == 200:
            return response.json()
        return {"type": "FeatureCollection", "features": []}


async def get_parcelles_around_point(
    lon: float, 
    lat: float, 
    radius_m: float = 1000,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get parcelles around a point (circular search)
    Approximates circle with bbox then filters
    """
    # Approximate degrees for radius
    # 1 degree lat ≈ 111km, 1 degree lon ≈ 111km * cos(lat)
    import math
    lat_offset = radius_m / 111000
    lon_offset = radius_m / (111000 * math.cos(math.radians(lat)))
    
    return await get_parcelles_by_bbox(
        lon - lon_offset,
        lat - lat_offset,
        lon + lon_offset,
        lat + lat_offset,
        limit
    )


async def get_sections_by_commune(code_insee: str) -> List[Dict[str, Any]]:
    """Get all cadastral sections for a commune"""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{API_CARTO_BASE}/division",
            params={"code_insee": code_insee}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("features", [])
        return []


def parse_parcelle_feature(feature: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse an API Carto parcelle feature into our internal format
    """
    props = feature.get("properties", {})
    geom = feature.get("geometry", {})
    
    # Calculate centroid from geometry
    coords = geom.get("coordinates", [])
    centroid = None
    if geom.get("type") == "Polygon" and coords:
        # Simple centroid approximation (average of vertices)
        all_points = coords[0] if coords else []
        if all_points:
            avg_lon = sum(p[0] for p in all_points) / len(all_points)
            avg_lat = sum(p[1] for p in all_points) / len(all_points)
            centroid = {"type": "Point", "coordinates": [avg_lon, avg_lat]}
    elif geom.get("type") == "MultiPolygon" and coords:
        # Use first polygon
        first_poly = coords[0][0] if coords and coords[0] else []
        if first_poly:
            avg_lon = sum(p[0] for p in first_poly) / len(first_poly)
            avg_lat = sum(p[1] for p in first_poly) / len(first_poly)
            centroid = {"type": "Point", "coordinates": [avg_lon, avg_lat]}
    
    # Calculate approximate surface from geometry
    surface_m2 = props.get("contenance", 0)  # contenance in m²
    
    # Extract commune code
    code_commune = props.get("code_com", "") or props.get("code_insee", "")
    code_dep = props.get("code_dep", "") or (code_commune[:2] if code_commune else "")
    
    return {
        "parcel_id": f"fr_{props.get('id', '')}",
        "ref_cadastrale": props.get("id", ""),
        "code_commune": code_commune,
        "commune": props.get("nom_com", ""),
        "departement": code_dep,
        "region": get_region_from_dept(code_dep),
        
        "geometry": geom,
        "centroid": centroid,
        "surface_m2": surface_m2,
        "surface_ha": surface_m2 / 10000 if surface_m2 else 0,
        "latitude": centroid["coordinates"][1] if centroid else 0,
        "longitude": centroid["coordinates"][0] if centroid else 0,
        
        # Section cadastrale
        "section": props.get("section", ""),
        "numero": props.get("numero", ""),
        "feuille": props.get("feuille", ""),
        
        # Source
        "source": "api_carto_ign",
        "source_date": props.get("date_creation", ""),
    }


def get_region_from_dept(code_dep: str) -> str:
    """Map department code to region name"""
    DEPT_TO_REGION = {
        "75": "IDF", "77": "IDF", "78": "IDF", "91": "IDF", "92": "IDF", "93": "IDF", "94": "IDF", "95": "IDF",
        "13": "PACA", "83": "PACA", "84": "PACA", "04": "PACA", "05": "PACA", "06": "PACA",
        "69": "AuRA", "01": "AuRA", "07": "AuRA", "26": "AuRA", "38": "AuRA", "42": "AuRA", "43": "AuRA", "63": "AuRA", "73": "AuRA", "74": "AuRA",
        "59": "HdF", "60": "HdF", "62": "HdF", "80": "HdF", "02": "HdF",
        "31": "Occitanie", "09": "Occitanie", "11": "Occitanie", "12": "Occitanie", "30": "Occitanie", "32": "Occitanie", "34": "Occitanie", "46": "Occitanie", "48": "Occitanie", "65": "Occitanie", "66": "Occitanie", "81": "Occitanie", "82": "Occitanie",
        "44": "Pays de la Loire", "49": "Pays de la Loire", "53": "Pays de la Loire", "72": "Pays de la Loire", "85": "Pays de la Loire",
        "22": "Bretagne", "29": "Bretagne", "35": "Bretagne", "56": "Bretagne",
        "14": "Normandie", "27": "Normandie", "50": "Normandie", "61": "Normandie", "76": "Normandie",
        "08": "Grand Est", "10": "Grand Est", "51": "Grand Est", "52": "Grand Est", "54": "Grand Est", "55": "Grand Est", "57": "Grand Est", "67": "Grand Est", "68": "Grand Est", "88": "Grand Est",
        "21": "Bourgogne-FC", "25": "Bourgogne-FC", "39": "Bourgogne-FC", "58": "Bourgogne-FC", "70": "Bourgogne-FC", "71": "Bourgogne-FC", "89": "Bourgogne-FC", "90": "Bourgogne-FC",
        "18": "Centre-VdL", "28": "Centre-VdL", "36": "Centre-VdL", "37": "Centre-VdL", "41": "Centre-VdL", "45": "Centre-VdL",
        "16": "Nouvelle-Aquitaine", "17": "Nouvelle-Aquitaine", "19": "Nouvelle-Aquitaine", "23": "Nouvelle-Aquitaine", "24": "Nouvelle-Aquitaine", "33": "Nouvelle-Aquitaine", "40": "Nouvelle-Aquitaine", "47": "Nouvelle-Aquitaine", "64": "Nouvelle-Aquitaine", "79": "Nouvelle-Aquitaine", "86": "Nouvelle-Aquitaine", "87": "Nouvelle-Aquitaine",
        "2A": "Corse", "2B": "Corse",
    }
    return DEPT_TO_REGION.get(code_dep, "France")
