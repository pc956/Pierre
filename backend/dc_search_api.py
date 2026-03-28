"""
Cockpit Immo - DC Search API for AI Agents
POST /api/dc/search — Main search endpoint
GET /api/dc/site/:id — Detailed site view
Designed for conversational AI consumption (ChatGPT, Claude, etc.)
"""
import math
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from france_infra_data import get_all_france_infra
from s3renr_data import S3RENR_DATA

logger = logging.getLogger("dc_search")

# ═══════════════════════════════════════════════════════════
# REGION MAPPING
# ═══════════════════════════════════════════════════════════
REGION_ALIASES = {
    "IDF": "IDF", "ile-de-france": "IDF", "île-de-france": "IDF", "paris": "IDF",
    "PACA": "PACA", "provence": "PACA", "marseille": "PACA", "sud-est": "PACA",
    "HDF": "HdF", "HdF": "HdF", "hauts-de-france": "HdF", "nord": "HdF", "lille": "HdF",
    "AURA": "AuRA", "AuRA": "AuRA", "auvergne": "AuRA", "lyon": "AuRA",
    "BFC": "BFC", "bourgogne": "BFC",
    "BRE": "BRE", "bretagne": "BRE",
    "CVL": "CVL", "centre": "CVL",
    "GES": "GES", "grand-est": "GES", "strasbourg": "GES",
    "NOR": "NOR", "normandie": "NOR",
    "NAQ": "NAQ", "nouvelle-aquitaine": "NAQ", "bordeaux": "NAQ",
    "OCC": "OCC", "occitanie": "OCC", "toulouse": "OCC",
    "PDL": "PDL", "pays-de-la-loire": "PDL", "nantes": "PDL",
    "COR": "COR", "corse": "COR",
}

DVF_PRICE_EUR_M2 = {
    "IDF": 120, "PACA": 95, "AuRA": 70, "HdF": 55,
    "BFC": 45, "BRE": 50, "CVL": 40, "GES": 55,
    "NOR": 50, "NAQ": 55, "OCC": 60, "PDL": 55, "COR": 80,
}

# Estimated delays based on grid situation
DELAY_ESTIMATES = {
    "disponible": {"base": (6, 18), "label": "Raccordement possible"},
    "contraint": {"base": (18, 36), "label": "Raccordement sous conditions"},
    "sature": {"base": (36, 60), "label": "Raccordement très incertain"},
    "inconnu": {"base": (12, 30), "label": "Délai à confirmer"},
}

# Strategy weights: each strategy emphasizes different scoring dimensions
STRATEGY_WEIGHTS = {
    "power":    {"power": 0.45, "speed": 0.15, "cost": 0.15, "risk": 0.25},
    "speed":    {"power": 0.20, "speed": 0.45, "cost": 0.10, "risk": 0.25},
    "cost":     {"power": 0.20, "speed": 0.15, "cost": 0.45, "risk": 0.20},
    "balanced": {"power": 0.30, "speed": 0.25, "cost": 0.20, "risk": 0.25},
}


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════
def _haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    p = math.pi / 180
    a = (
        0.5 - math.cos((lat2 - lat1) * p) / 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def _resolve_region(raw: str) -> Optional[str]:
    if not raw:
        return None
    key = raw.strip().lower()
    return REGION_ALIASES.get(key) or REGION_ALIASES.get(raw.strip())


def _voltage_label(kv: int) -> str:
    if kv >= 400:
        return "400kV"
    elif kv >= 225:
        return "225kV"
    elif kv >= 63:
        return "63kV"
    return f"{kv}kV"


def _saturation_level(etat: str) -> str:
    if etat == "disponible":
        return "low"
    elif etat in ("contraint", "inconnu"):
        return "medium"
    return "high"


def _permitting_risk(plu_compatible: bool, etat: str) -> str:
    if not plu_compatible:
        return "high"
    if etat == "sature":
        return "high"
    if etat == "contraint":
        return "medium"
    return "low"


# ═══════════════════════════════════════════════════════════
# SITE BUILDER — Generates candidate sites from infra data
# ═══════════════════════════════════════════════════════════
def _build_all_sites() -> List[Dict[str, Any]]:
    """Build site candidates from HTB substations + S3REnR data"""
    infra = get_all_france_infra()
    sites = []

    # Build S3REnR lookup: normalized_name -> data
    s3renr_lookup = {}
    for region_key, region_data in S3RENR_DATA.items():
        for poste_name, poste_data in region_data.get("postes", {}).items():
            norm = poste_name.upper().replace("-", " ").replace("'", " ").strip()
            s3renr_lookup[(region_key, norm)] = poste_data

    for poste in infra["postes_htb"]:
        coords = poste["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]
        region = poste.get("region", "France")
        tension = poste.get("tension_kv", 63)
        nom = poste.get("nom", "")
        asset_id = poste.get("asset_id", "")

        # Try to find S3REnR match
        s3renr_region = region
        s3renr_match = None

        # Try direct match
        for poste_name, poste_data in S3RENR_DATA.get(region, {}).get("postes", {}).items():
            norm_s3 = poste_name.upper().replace("-", " ").replace("'", " ").strip()
            norm_htb = nom.upper().replace("POSTE ", "").replace("-", " ").replace("'", " ").strip()
            # Remove voltage suffix
            for suffix in ["225KV", "400KV", "63KV"]:
                norm_htb = norm_htb.replace(suffix, "").strip()
            if norm_s3 in norm_htb or norm_htb in norm_s3:
                s3renr_match = poste_data
                break

        # Compute grid data
        mw_capacity = poste.get("puissance_mva", 200) * 0.8  # 80% of MVA
        mw_dispo = 0
        etat = "inconnu"
        renforcement = None
        score_dc_s3renr = 5

        if s3renr_match:
            mw_dispo = s3renr_match.get("mw_dispo", 0)
            etat = s3renr_match.get("etat", "inconnu")
            renforcement = s3renr_match.get("renforcement")
            score_dc_s3renr = s3renr_match.get("score_dc", 5)
        elif region in S3RENR_DATA:
            # Region covered but no match => use region status
            status = S3RENR_DATA[region].get("status_global", "")
            if status == "SATURE":
                etat = "sature"
                mw_dispo = 0
            else:
                # Unknown poste in active region — estimate conservatively
                etat = "inconnu"
                mw_dispo = max(0, mw_capacity * 0.2)

        # Estimated surface available near substation (5-20 ha typical)
        surface_ha = 5.0 if region == "IDF" else 10.0

        # Price per m2 from DVF benchmarks
        price_m2 = DVF_PRICE_EUR_M2.get(region, 65)

        # Land type — brownfield more likely in industrial areas
        land_type = "brownfield" if tension >= 225 else "greenfield"

        # Delay estimate
        delay_info = DELAY_ESTIMATES.get(etat, DELAY_ESTIMATES["inconnu"])
        delay_min, delay_max = delay_info["base"]
        avg_delay = (delay_min + delay_max) / 2
        if renforcement:
            avg_delay = max(delay_min, avg_delay - 6)  # Bonus for planned reinforcement

        # PLU compatibility — substations are typically in compatible zones
        plu_zone = "UI" if tension >= 225 else "U"
        plu_compatible = True

        # Nearest landing point
        min_dist_lp = 999999
        nearest_lp = ""
        for lp in infra["landing_points"]:
            lcoords = lp["geometry"]["coordinates"]
            d = _haversine(lon, lat, lcoords[0], lcoords[1]) / 1000
            if d < min_dist_lp:
                min_dist_lp = d
                nearest_lp = lp.get("nom", "")

        # Nearest existing DC
        min_dist_dc = 999999
        for dc in infra["dc_existants"]:
            dcoords = dc["geometry"]["coordinates"]
            d = _haversine(lon, lat, dcoords[0], dcoords[1]) / 1000
            if d < min_dist_dc:
                min_dist_dc = d

        # City name from poste name
        city = nom.replace("Poste ", "").split(" ")[0]

        sites.append({
            "site_id": f"dc_{asset_id}",
            "name": f"Site {city} — {_voltage_label(tension)}",
            "htb_asset_id": asset_id,
            "location": {
                "city": city,
                "region": region,
                "lat": lat,
                "lng": lon,
            },
            "land": {
                "surface_ha": surface_ha,
                "price_per_m2": price_m2,
                "type": land_type,
            },
            "grid": {
                "distance_to_substation_km": 0.5,  # Site adjacent to substation
                "voltage_level": _voltage_label(tension),
                "estimated_capacity_mw": round(mw_capacity, 0),
                "available_capacity_mw": round(mw_dispo, 0),
                "saturation_level": _saturation_level(etat),
                "reinforcement_planned": renforcement is not None,
                "reinforcement_detail": renforcement,
                "etat_s3renr": etat,
            },
            "timeline": {
                "estimated_connection_delay_months": round(avg_delay),
                "delay_range_months": [delay_min, delay_max],
                "permitting_risk": _permitting_risk(plu_compatible, etat),
            },
            "urbanism": {
                "plu_zone": plu_zone,
                "data_center_compatible": plu_compatible,
            },
            "connectivity": {
                "nearest_landing_point_km": round(min_dist_lp, 1),
                "nearest_landing_point": nearest_lp,
                "nearest_dc_km": round(min_dist_dc, 1),
            },
            "_raw": {
                "tension_kv": tension,
                "puissance_mva": poste.get("puissance_mva", 0),
                "score_dc_s3renr": score_dc_s3renr,
                "region": region,
                "etat": etat,
            },
        })

    return sites


# Cache sites (computed once at import)
_ALL_SITES = None

def _get_all_sites():
    global _ALL_SITES
    if _ALL_SITES is None:
        _ALL_SITES = _build_all_sites()
    return _ALL_SITES


# ═══════════════════════════════════════════════════════════
# SCORING ENGINE (AI-optimized)
# ═══════════════════════════════════════════════════════════
def _score_site(site: Dict, params: Dict) -> Dict[str, Any]:
    """Compute multi-criteria score for a site based on search parameters"""
    strategy = params.get("strategy", "balanced")
    weights = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS["balanced"])

    grid = site["grid"]
    timeline = site["timeline"]
    land = site["land"]

    mw_target = params.get("mw_target", 20)
    mw_min = params.get("mw_min", 5)
    max_delay = params.get("max_delay_months", 36)

    # ── POWER SCORE (0-100) ──
    mw_available = grid["available_capacity_mw"]
    if mw_available >= mw_target:
        power_score = 100
    elif mw_available >= mw_min:
        power_score = 50 + 50 * (mw_available - mw_min) / max(1, mw_target - mw_min)
    elif mw_available > 0:
        power_score = 50 * mw_available / max(1, mw_min)
    else:
        power_score = 0

    # Bonus for high voltage
    tension = site["_raw"]["tension_kv"]
    if tension >= 400:
        power_score = min(100, power_score + 15)
    elif tension >= 225:
        power_score = min(100, power_score + 10)

    # Bonus for reinforcement planned
    if grid["reinforcement_planned"] and mw_available < mw_target:
        power_score = min(100, power_score + 10)

    # ── SPEED SCORE (0-100) ──
    delay = timeline["estimated_connection_delay_months"]
    if delay <= max_delay:
        speed_score = 100 - (delay / max_delay) * 40
    else:
        overshoot = (delay - max_delay) / max_delay
        speed_score = max(0, 60 - overshoot * 80)

    if grid["saturation_level"] == "low":
        speed_score = min(100, speed_score + 10)

    # ── COST SCORE (0-100) ──
    price = land["price_per_m2"]
    # Cheaper is better. Reference: 65 €/m2 = 80 points
    if price <= 40:
        cost_score = 100
    elif price <= 65:
        cost_score = 80 + 20 * (65 - price) / 25
    elif price <= 120:
        cost_score = 40 + 40 * (120 - price) / 55
    else:
        cost_score = max(0, 40 - (price - 120) * 0.3)

    # Brownfield bonus (lower construction cost)
    if land["type"] == "brownfield":
        cost_score = min(100, cost_score + 5)

    # ── RISK SCORE (0-100, higher = lower risk) ──
    risk_score = 100
    if timeline["permitting_risk"] == "high":
        risk_score -= 40
    elif timeline["permitting_risk"] == "medium":
        risk_score -= 20

    if grid["saturation_level"] == "high":
        risk_score -= 30
    elif grid["saturation_level"] == "medium":
        risk_score -= 15

    if not site["urbanism"]["data_center_compatible"]:
        risk_score -= 30

    risk_score = max(0, risk_score)

    # ── GLOBAL SCORE ──
    global_score = (
        weights["power"] * power_score
        + weights["speed"] * speed_score
        + weights["cost"] * cost_score
        + weights["risk"] * risk_score
    )

    return {
        "global": round(global_score, 1),
        "power": round(power_score, 1),
        "speed": round(speed_score, 1),
        "cost": round(cost_score, 1),
        "risk": round(risk_score, 1),
    }


# ═══════════════════════════════════════════════════════════
# COMMENT GENERATOR (for AI interpretation)
# ═══════════════════════════════════════════════════════════
def _generate_comment(site: Dict, score: Dict, params: Dict) -> str:
    """Generate a concise natural-language comment for AI consumption"""
    parts = []
    grid = site["grid"]
    mw_target = params.get("mw_target", 20)

    # Capacity assessment
    mw = grid["available_capacity_mw"]
    if mw >= mw_target:
        parts.append(f"Capacité suffisante ({mw} MW dispo pour {mw_target} MW visés)")
    elif mw > 0:
        parts.append(f"Capacité partielle ({mw} MW dispo sur {mw_target} MW visés)")
    else:
        parts.append(f"Aucune capacité disponible (réseau saturé)")

    # Grid status
    if grid["etat_s3renr"] == "disponible":
        parts.append("Réseau disponible S3REnR")
    elif grid["etat_s3renr"] == "contraint":
        parts.append("Réseau contraint — raccordement sous conditions")
    elif grid["etat_s3renr"] == "sature":
        parts.append("ATTENTION: Réseau saturé")

    # Reinforcement
    if grid["reinforcement_planned"]:
        parts.append(f"Renforcement prévu: {grid['reinforcement_detail']}")

    # Speed
    delay = site["timeline"]["estimated_connection_delay_months"]
    max_delay = params.get("max_delay_months", 36)
    if delay <= max_delay:
        parts.append(f"Délai raccordement ~{delay} mois (objectif: {max_delay})")
    else:
        parts.append(f"Délai raccordement ~{delay} mois > objectif {max_delay} mois")

    # Risk
    if score["risk"] < 50:
        parts.append("Risque administratif élevé")

    return ". ".join(parts) + "."


# ═══════════════════════════════════════════════════════════
# TAGS GENERATOR
# ═══════════════════════════════════════════════════════════
def _generate_tags(site: Dict, score: Dict, params: Dict) -> List[str]:
    tags = []
    grid = site["grid"]
    mw_target = params.get("mw_target", 20)

    if grid["available_capacity_mw"] >= mw_target:
        tags.append("capacite_ok")
    if grid["voltage_level"] in ("400kV", "225kV"):
        tags.append("haute_tension")
    if grid["reinforcement_planned"]:
        tags.append("renforcement_prevu")
    if grid["saturation_level"] == "low":
        tags.append("reseau_disponible")
    elif grid["saturation_level"] == "high":
        tags.append("reseau_sature")
    if site["land"]["type"] == "brownfield":
        tags.append("brownfield")
    if site["urbanism"]["data_center_compatible"]:
        tags.append("plu_compatible")
    if score["global"] >= 80:
        tags.append("top_site")
    elif score["global"] >= 60:
        tags.append("site_interessant")
    if site["timeline"]["estimated_connection_delay_months"] <= 12:
        tags.append("raccordement_rapide")
    if site["connectivity"]["nearest_dc_km"] < 20:
        tags.append("cluster_dc")

    return tags


# ═══════════════════════════════════════════════════════════
# MAIN SEARCH FUNCTION
# ═══════════════════════════════════════════════════════════
def dc_search(params: Dict) -> Dict[str, Any]:
    """
    Main search function for AI agents.
    Filters, scores, and ranks DC sites based on input criteria.
    """
    start_time = time.time()
    sites = _get_all_sites()

    # ── FILTERS ──
    region_filter = _resolve_region(params.get("region", ""))
    mw_min = params.get("mw_min", 0)
    mw_target = params.get("mw_target", 20)
    max_delay = params.get("max_delay_months", 60)
    surface_min = params.get("surface_min_ha", 0)
    max_dist_sub = params.get("max_distance_substation_km", 100)
    grid_priority = params.get("grid_priority", False)
    brownfield_only = params.get("brownfield_only", False)

    filtered = []
    for site in sites:
        # Region filter
        if region_filter and site["location"]["region"] != region_filter:
            continue

        # Brownfield filter
        if brownfield_only and site["land"]["type"] != "brownfield":
            continue

        # Surface filter
        if site["land"]["surface_ha"] < surface_min:
            continue

        # Distance to substation
        if site["grid"]["distance_to_substation_km"] > max_dist_sub:
            continue

        # Grid priority: skip saturated sites
        if grid_priority and site["grid"]["saturation_level"] == "high":
            continue

        filtered.append(site)

    # ── SCORE ──
    scored = []
    for site in filtered:
        score = _score_site(site, params)
        comment = _generate_comment(site, score, params)
        tags = _generate_tags(site, score, params)

        result = {
            "site_id": site["site_id"],
            "name": site["name"],
            "location": site["location"],
            "land": site["land"],
            "grid": {
                "distance_to_substation_km": site["grid"]["distance_to_substation_km"],
                "voltage_level": site["grid"]["voltage_level"],
                "estimated_capacity_mw": site["grid"]["estimated_capacity_mw"],
                "available_capacity_mw": site["grid"]["available_capacity_mw"],
                "saturation_level": site["grid"]["saturation_level"],
                "reinforcement_planned": site["grid"]["reinforcement_planned"],
            },
            "timeline": {
                "estimated_connection_delay_months": site["timeline"]["estimated_connection_delay_months"],
                "permitting_risk": site["timeline"]["permitting_risk"],
            },
            "urbanism": site["urbanism"],
            "score": score,
            "tags": tags,
            "comment": comment,
        }
        scored.append(result)

    # ── SORT by global score descending ──
    scored.sort(key=lambda x: -x["score"]["global"])

    # ── PAGINATION ──
    page = max(1, params.get("page", 1))
    per_page = min(50, max(1, params.get("per_page", 10)))
    total = len(scored)
    start = (page - 1) * per_page
    end = start + per_page
    results = scored[start:end]

    elapsed_ms = round((time.time() - start_time) * 1000)

    return {
        "results": results,
        "meta": {
            "total_results": total,
            "page": page,
            "per_page": per_page,
            "total_pages": math.ceil(total / per_page) if per_page > 0 else 1,
            "search_time_ms": elapsed_ms,
            "strategy": params.get("strategy", "balanced"),
            "region_filter": region_filter,
        },
    }


def dc_get_site(site_id: str) -> Optional[Dict[str, Any]]:
    """Get a single site by ID with full details"""
    sites = _get_all_sites()
    for site in sites:
        if site["site_id"] == site_id:
            # Return enriched version
            return {
                "site_id": site["site_id"],
                "name": site["name"],
                "location": site["location"],
                "land": site["land"],
                "grid": {
                    "distance_to_substation_km": site["grid"]["distance_to_substation_km"],
                    "voltage_level": site["grid"]["voltage_level"],
                    "estimated_capacity_mw": site["grid"]["estimated_capacity_mw"],
                    "available_capacity_mw": site["grid"]["available_capacity_mw"],
                    "saturation_level": site["grid"]["saturation_level"],
                    "reinforcement_planned": site["grid"]["reinforcement_planned"],
                    "reinforcement_detail": site["grid"].get("reinforcement_detail"),
                    "etat_s3renr": site["grid"]["etat_s3renr"],
                },
                "timeline": {
                    "estimated_connection_delay_months": site["timeline"]["estimated_connection_delay_months"],
                    "delay_range_months": site["timeline"]["delay_range_months"],
                    "permitting_risk": site["timeline"]["permitting_risk"],
                },
                "urbanism": site["urbanism"],
                "connectivity": site["connectivity"],
                "score": _score_site(site, {"strategy": "balanced", "mw_target": 20}),
                "tags": _generate_tags(
                    site,
                    _score_site(site, {"strategy": "balanced", "mw_target": 20}),
                    {"mw_target": 20}
                ),
                "comment": _generate_comment(
                    site,
                    _score_site(site, {"strategy": "balanced", "mw_target": 20}),
                    {"mw_target": 20}
                ),
            }
    return None
