"""
Cockpit Immo - RTE Future 400kV Line: Fos-sur-Mer (Feuillane) → Jonquières
Tracé approximatif basé sur les corridors haute tension existants et la logique terrain.
Buffers 1km / 3km / 5km pour scoring et visualisation.
"""
import math
from typing import Dict, Any, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════
# TRACÉ APPROXIMATIF — Ligne 400kV Fos-sur-Mer → Jonquières
# Basé sur :
#   - Poste de Feuillane (Fos-sur-Mer) : ~4.94, 43.44
#   - Jonquières-Saint-Vincent : ~4.57, 43.83
#   - Corridors HTB existants (évite zones urbaines denses)
#   - Axes industriels Fos/Étang de Berre/Crau/Alpilles
# ═══════════════════════════════════════════════════════════

# Coordinates [lon, lat] — WGS84
FUTURE_LINE_COORDINATES = [
    [4.9430, 43.4380],   # Poste de Feuillane (Fos-sur-Mer)
    [4.9200, 43.4550],   # Sortie Fos — zone industrialo-portuaire
    [4.8850, 43.4750],   # Plaine de la Crau — corridor industriel
    [4.8500, 43.5000],   # Évitement Istres — passage est étang
    [4.8100, 43.5350],   # Corridor Crau nord
    [4.7700, 43.5700],   # Traversée plaine agricole (Mouriès)
    [4.7300, 43.6100],   # Pied des Alpilles — passage sud
    [4.6900, 43.6500],   # Orgon / contournement Alpilles
    [4.6500, 43.6900],   # Vallée Durance — axe naturel
    [4.6200, 43.7200],   # Châteaurenard — zone ouverte
    [4.5900, 43.7600],   # Approche Avignon sud
    [4.5700, 43.7900],   # Corridor existant 400kV Avignon
    [4.5650, 43.8250],   # Jonquières-Saint-Vincent — arrivée
]

FUTURE_LINE_METADATA = {
    "id": "rte_400kv_future_fos_jonquieres",
    "nom": "Future ligne RTE 400 kV Fos-sur-Mer → Jonquières",
    "projet": "Renforcement réseau PACA — Projet Fos-Jonquières",
    "mise_en_service_estimee": "~2029",
    "tension_kv": 400,
    "statut": "en_projet",
    "description": "Projet RTE de renforcement du réseau 400 kV entre le poste de Feuillane (Fos-sur-Mer) et Jonquières-Saint-Vincent. Ce projet vise à sécuriser l'alimentation électrique de la zone industrialo-portuaire de Fos et à renforcer la capacité d'accueil pour les projets data center et industriels de la région PACA.",
    "source": "Concertation publique RTE / Tracé approximatif",
    "longueur_km_approx": 48,
}

# ═══════════════════════════════════════════════════════════
# FONCTIONS GÉOMÉTRIQUES
# ═══════════════════════════════════════════════════════════

def _haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Distance en mètres entre deux points GPS (WGS84)."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _point_to_segment_distance(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
    """Distance minimale (mètres) d'un point (px, py) à un segment [A, B] en coordonnées GPS."""
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return _haversine(px, py, ax, ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return _haversine(px, py, proj_x, proj_y)


def distance_to_future_line(lon: float, lat: float) -> float:
    """Distance minimale (mètres) d'un point à la future ligne 400kV."""
    coords = FUTURE_LINE_COORDINATES
    min_dist = float('inf')
    for i in range(len(coords) - 1):
        d = _point_to_segment_distance(
            lon, lat,
            coords[i][0], coords[i][1],
            coords[i + 1][0], coords[i + 1][1],
        )
        min_dist = min(min_dist, d)
    return min_dist


def get_buffer_zone(lon: float, lat: float) -> Optional[str]:
    """Retourne la zone buffer : '1km', '3km', '5km' ou None."""
    dist = distance_to_future_line(lon, lat)
    if dist <= 1000:
        return "1km"
    elif dist <= 3000:
        return "3km"
    elif dist <= 5000:
        return "5km"
    return None


def score_future_400kv(lon: float, lat: float) -> int:
    """Score bonus basé sur la distance à la future ligne 400kV."""
    dist = distance_to_future_line(lon, lat)
    if dist < 1000:
        return 30
    elif dist < 3000:
        return 20
    elif dist < 5000:
        return 10
    return 0


def compute_future_grid_potential(
    lon: float, lat: float,
    dist_poste_htb_m: float = 50000,
    s3renr_mw_dispo: float = 0,
    s3renr_etat: str = "inconnu",
) -> Dict[str, Any]:
    """
    Indicateur composite 'future_grid_potential_score' (0-100).
    Combine : distance ligne 400kV + distance poste source + données S3REnR.
    """
    # Score ligne future (0-40)
    dist_line = distance_to_future_line(lon, lat)
    if dist_line < 1000:
        s_line = 40
    elif dist_line < 3000:
        s_line = 30
    elif dist_line < 5000:
        s_line = 20
    elif dist_line < 10000:
        s_line = 10
    else:
        s_line = 0

    # Score poste source (0-30)
    if dist_poste_htb_m < 2000:
        s_poste = 30
    elif dist_poste_htb_m < 5000:
        s_poste = 22
    elif dist_poste_htb_m < 10000:
        s_poste = 15
    elif dist_poste_htb_m < 20000:
        s_poste = 8
    else:
        s_poste = 0

    # Score S3REnR (0-30)
    if s3renr_etat == "disponible" and s3renr_mw_dispo >= 50:
        s_s3renr = 30
    elif s3renr_etat == "disponible" and s3renr_mw_dispo >= 20:
        s_s3renr = 22
    elif s3renr_etat == "contraint":
        s_s3renr = 12
    elif s3renr_etat == "sature":
        s_s3renr = 5
    else:
        s_s3renr = 8

    total = s_line + s_poste + s_s3renr

    # Catégorie
    if total >= 80:
        cat = "excellent"
    elif total >= 60:
        cat = "tres_bon"
    elif total >= 40:
        cat = "bon"
    elif total >= 20:
        cat = "moyen"
    else:
        cat = "faible"

    return {
        "future_grid_potential_score": total,
        "future_grid_category": cat,
        "detail": {
            "score_ligne_400kv": s_line,
            "score_poste_source": s_poste,
            "score_s3renr": s_s3renr,
            "distance_ligne_m": round(dist_line),
            "buffer_zone": get_buffer_zone(lon, lat),
        },
    }


# ═══════════════════════════════════════════════════════════
# GÉNÉRATION DES BUFFERS (polygones approximatifs)
# ═══════════════════════════════════════════════════════════

def _offset_point(lon: float, lat: float, bearing_rad: float, distance_m: float) -> Tuple[float, float]:
    """Déplace un point GPS d'une distance donnée dans une direction."""
    R = 6371000
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    d = distance_m / R

    new_lat = math.asin(
        math.sin(lat_r) * math.cos(d) + math.cos(lat_r) * math.sin(d) * math.cos(bearing_rad)
    )
    new_lon = lon_r + math.atan2(
        math.sin(bearing_rad) * math.sin(d) * math.cos(lat_r),
        math.cos(d) - math.sin(lat_r) * math.sin(new_lat),
    )
    return (math.degrees(new_lon), math.degrees(new_lat))


def _generate_buffer_polygon(coords: List[List[float]], distance_m: float, points_per_cap: int = 8) -> List[List[float]]:
    """
    Génère un polygone buffer autour d'une polyligne.
    Approche : offset gauche + offset droite + caps aux extrémités.
    """
    if len(coords) < 2:
        return []

    left_side = []
    right_side = []

    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i + 1]

        # Direction du segment
        bearing = math.atan2(
            math.radians(lon2 - lon1) * math.cos(math.radians(lat2)),
            math.radians(lat2 - lat1),
        )

        # Perpendiculaire gauche et droite
        perp_left = bearing - math.pi / 2
        perp_right = bearing + math.pi / 2

        left_side.append(_offset_point(lon1, lat1, perp_left, distance_m))
        right_side.append(_offset_point(lon1, lat1, perp_right, distance_m))

        if i == len(coords) - 2:
            left_side.append(_offset_point(lon2, lat2, perp_left, distance_m))
            right_side.append(_offset_point(lon2, lat2, perp_right, distance_m))

    # Cap de fin (demi-cercle)
    last = coords[-1]
    bearing_last = math.atan2(
        math.radians(coords[-1][0] - coords[-2][0]) * math.cos(math.radians(coords[-1][1])),
        math.radians(coords[-1][1] - coords[-2][1]),
    )
    end_cap = []
    for j in range(points_per_cap + 1):
        angle = bearing_last - math.pi / 2 + math.pi * j / points_per_cap
        end_cap.append(_offset_point(last[0], last[1], angle, distance_m))

    # Cap de début (demi-cercle)
    first = coords[0]
    bearing_first = math.atan2(
        math.radians(coords[1][0] - coords[0][0]) * math.cos(math.radians(coords[1][1])),
        math.radians(coords[1][1] - coords[0][1]),
    )
    start_cap = []
    for j in range(points_per_cap + 1):
        angle = bearing_first + math.pi / 2 + math.pi * j / points_per_cap
        start_cap.append(_offset_point(first[0], first[1], angle, distance_m))

    # Assemblage : left → end_cap → right (inversé) → start_cap
    polygon = left_side + end_cap + list(reversed(right_side)) + start_cap
    # Fermer le polygone
    if polygon:
        polygon.append(polygon[0])

    return [list(p) for p in polygon]


def get_future_line_geojson() -> Dict[str, Any]:
    """Retourne la ligne + buffers en format GeoJSON-like pour l'API."""
    line_coords = FUTURE_LINE_COORDINATES
    buffer_1km = _generate_buffer_polygon(line_coords, 1000)
    buffer_3km = _generate_buffer_polygon(line_coords, 3000)
    buffer_5km = _generate_buffer_polygon(line_coords, 5000)

    return {
        "line": {
            "type": "LineString",
            "coordinates": line_coords,
        },
        "buffers": {
            "1km": {
                "type": "Polygon",
                "coordinates": [buffer_1km],
                "style": {"color": "#ff4757", "fillOpacity": 0.25, "label": "Zone chaude (1 km)"},
            },
            "3km": {
                "type": "Polygon",
                "coordinates": [buffer_3km],
                "style": {"color": "#ffa502", "fillOpacity": 0.15, "label": "Zone stratégique (3 km)"},
            },
            "5km": {
                "type": "Polygon",
                "coordinates": [buffer_5km],
                "style": {"color": "#ffd32a", "fillOpacity": 0.10, "label": "Zone opportunité (5 km)"},
            },
        },
        "metadata": FUTURE_LINE_METADATA,
        "scoring": {
            "rules": [
                {"zone": "<1km", "bonus": 30},
                {"zone": "1-3km", "bonus": 20},
                {"zone": "3-5km", "bonus": 10},
                {"zone": ">5km", "bonus": 0},
            ],
        },
    }
