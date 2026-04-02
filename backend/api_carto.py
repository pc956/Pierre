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
    ID format 14 chars: CCCCCPPPSSNNN (code_insee 5 + com_abs 3 + section 2 + numero 4)
    Example: 13039000BS0118 → code_insee=13039, com_abs=000, section=BS, numero=0118
    """
    pid = parcelle_id.strip().upper()

    async with httpx.AsyncClient(timeout=30) as client:
        # Format 14 chars: 5 code_insee + 3 prefix + 2 section + 4 numero
        if len(pid) == 14:
            code_insee = pid[:5]
            section = pid[8:10]
            numero = pid[10:14]
        elif len(pid) >= 9:
            # Try to detect section (2 alpha chars) position
            code_insee = pid[:5]
            rest = pid[5:]
            # Skip numeric prefix (com_abs), find first alpha pair
            i = 0
            while i < len(rest) and rest[i].isdigit():
                i += 1
            if i + 2 <= len(rest):
                section = rest[i:i+2]
                numero = rest[i+2:]
            else:
                section = rest[:2]
                numero = rest[2:]
        else:
            code_insee = pid[:5]
            section = pid[5:7]
            numero = pid[7:]

        response = await client.get(
            f"{API_CARTO_BASE}/parcelle",
            params={"code_insee": code_insee, "section": section, "numero": numero}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("features"):
                return data["features"][0]

        # Fallback: try with code_arr parameter
        if len(pid) >= 9:
            response2 = await client.get(
                f"{API_CARTO_BASE}/parcelle",
                params={"code_arr": code_insee, "section": section, "numero": numero}
            )
            if response2.status_code == 200:
                data2 = response2.json()
                if data2.get("features"):
                    return data2["features"][0]

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


async def get_gpu_zone_urba_for_point(lon: float, lat: float) -> Optional[Dict[str, Any]]:
    """
    Get PLU zone from Géoportail de l'Urbanisme (GPU) for a point
    Returns zone info: typezone (U, AU, A, N), libelle, libelong
    """
    geom = {"type": "Point", "coordinates": [lon, lat]}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://apicarto.ign.fr/api/gpu/zone-urba",
                params={"geom": str(geom).replace("'", '"')}
            )
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                if features:
                    props = features[0].get("properties", {})
                    return {
                        "typezone": props.get("typezone", ""),
                        "libelle": props.get("libelle", ""),
                        "libelong": props.get("libelong", ""),
                        "destdomi": props.get("destdomi", ""),
                    }
    except Exception:
        pass
    return None


async def get_gpu_full_context(lon: float, lat: float) -> Dict[str, Any]:
    """
    Get FULL PLU context from GPU API for dynamic PLU scoring.
    Fetches zone-urba + prescription-surf + info-surf in parallel.
    Returns enriched zone data with prescriptions and risk info.
    """
    geom_str = f'{{"type":"Point","coordinates":[{lon},{lat}]}}'
    result = {
        "zone": None,
        "prescriptions": [],
        "informations": [],
        "raw_features_count": 0,
    }
    
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            # Parallel fetch of zone, prescriptions, and informations
            import asyncio
            zone_req = client.get(
                "https://apicarto.ign.fr/api/gpu/zone-urba",
                params={"geom": geom_str}
            )
            presc_req = client.get(
                "https://apicarto.ign.fr/api/gpu/prescription-surf",
                params={"geom": geom_str}
            )
            info_req = client.get(
                "https://apicarto.ign.fr/api/gpu/info-surf",
                params={"geom": geom_str}
            )
            
            responses = await asyncio.gather(zone_req, presc_req, info_req, return_exceptions=True)
            
            # Parse zone-urba
            if not isinstance(responses[0], Exception) and responses[0].status_code == 200:
                zone_data = responses[0].json()
                features = zone_data.get("features", [])
                if features:
                    props = features[0].get("properties", {})
                    result["zone"] = {
                        "typezone": props.get("typezone", ""),
                        "libelle": props.get("libelle", ""),
                        "libelong": props.get("libelong", ""),
                        "destdomi": props.get("destdomi", ""),
                        "nomfic": props.get("nomfic", ""),
                        "idurba": props.get("idurba", ""),
                        "partition": props.get("partition", ""),
                        "datvalid": props.get("datvalid", ""),
                    }
                    result["raw_features_count"] = len(features)
            
            # Parse prescriptions
            if not isinstance(responses[1], Exception) and responses[1].status_code == 200:
                presc_data = responses[1].json()
                for f in presc_data.get("features", []):
                    p = f.get("properties", {})
                    result["prescriptions"].append({
                        "libelle": p.get("libelle", ""),
                        "txt": p.get("txt", ""),
                        "typepsc": p.get("typepsc", ""),
                        "stypepsc": p.get("stypepsc", ""),
                    })
            
            # Parse informations (risques, servitudes)
            if not isinstance(responses[2], Exception) and responses[2].status_code == 200:
                info_data = responses[2].json()
                for f in info_data.get("features", []):
                    p = f.get("properties", {})
                    result["informations"].append({
                        "libelle": p.get("libelle", ""),
                        "txt": p.get("txt", ""),
                        "typeinf": p.get("typeinf", ""),
                        "stypeinf": p.get("stypeinf", ""),
                    })
    except Exception:
        pass
    
    return result


async def get_gpu_zones_for_bbox(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> List[Dict[str, Any]]:
    """
    Get all PLU zones within a bounding box from GPU
    Returns list of zone features with geometry and properties
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
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://apicarto.ign.fr/api/gpu/zone-urba",
                params={"geom": str(bbox_geojson).replace("'", '"')}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("features", [])
    except Exception:
        pass
    return []


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
    
    # Build unique parcel ID from cadastral reference fields
    # BUG 1 FIX — Reconstruire code_commune complet (5 chiffres = dept + com)
    code_dep = props.get("code_dep", "")
    code_com_raw = props.get("code_com", "")
    code_insee_raw = props.get("code_insee", "")

    if code_insee_raw and len(code_insee_raw) >= 5:
        code_commune = code_insee_raw
        code_dep = code_dep or code_commune[:2]
    elif code_dep and code_com_raw:
        code_commune = code_dep + code_com_raw
    elif code_com_raw and len(code_com_raw) >= 5:
        code_commune = code_com_raw
        code_dep = code_dep or code_commune[:2]
    else:
        code_commune = code_com_raw
        code_dep = code_dep or (code_commune[:2] if len(code_commune) >= 2 else "")

    if not code_dep and code_commune and len(code_commune) >= 2:
        code_dep = code_commune[:2]
    section = props.get("section", "")
    numero = props.get("numero", "")
    feuille = props.get("feuille", "1")
    surface_m2 = props.get("contenance", 0)  # contenance in m²
    
    # IDU (identifiant unique parcelle) from API Carto
    idu = props.get("idu", "") or props.get("id", "")
    
    # Build a truly unique parcel_id
    if idu:
        parcel_id = f"fr_{idu}"
    elif code_commune and section and numero:
        parcel_id = f"fr_{code_commune}_{section}_{numero}_{feuille}"
    else:
        # Fallback: use hash of geometry coordinates
        import hashlib
        geom_str = str(geom.get("coordinates", []))[:200]
        h = hashlib.md5(geom_str.encode()).hexdigest()[:12]
        parcel_id = f"fr_g{h}"
    
    # Référence cadastrale normalisée (14 caractères: commune + prefixe + section + numero)
    com_abs = props.get("com_abs", "000") or "000"
    ref_cadastrale = idu or f"{code_commune}{com_abs}{section}{numero}".strip()

    # URLs externes Pappers Immo
    pappers_immo_url = f"https://immobilier.pappers.fr/?q={ref_cadastrale}" if ref_cadastrale else None
    lat_val = centroid["coordinates"][1] if centroid else 0
    lon_val = centroid["coordinates"][0] if centroid else 0
    pappers_map_url = f"https://immobilier.pappers.fr/#18/{lat_val}/{lon_val}" if lat_val and lon_val else None
    cadastre_gouv_url = "https://www.cadastre.gouv.fr/scpc/rechercherParReferenceCadastrale.do" if ref_cadastrale else None

    return {
        "parcel_id": parcel_id,
        "ref_cadastrale": ref_cadastrale,
        "code_commune": code_commune,
        "commune": props.get("nom_com", ""),
        "departement": code_dep,
        "region": get_region_from_dept(code_dep),
        
        "geometry": geom,
        "centroid": centroid,
        "surface_m2": surface_m2,
        "surface_ha": surface_m2 / 10000 if surface_m2 else 0,
        "latitude": lat_val,
        "longitude": lon_val,
        
        # Section cadastrale
        "section": section,
        "numero": numero,
        "feuille": feuille,
        
        # Liens externes
        "pappers_immo_url": pappers_immo_url,
        "pappers_map_url": pappers_map_url,
        "cadastre_gouv_url": cadastre_gouv_url,
        
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
