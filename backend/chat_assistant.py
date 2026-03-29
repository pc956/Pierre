"""
Cockpit Immo — AI Chat Assistant v2
Refonte complète: score universel /100, données réelles, recherche par commune,
parallélisation, cache GPU, SYSTEM_PROMPT simplifié.
"""
import os
import json
import math
import asyncio
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

from dc_search_api import dc_search, dc_get_site
from api_carto import (
    get_parcelles_around_point, parse_parcelle_feature,
    get_gpu_full_context, search_communes as api_search_communes
)
from france_infra_data import get_all_france_infra
from rte_future_line import distance_to_future_line, get_buffer_zone, score_future_400kv
from scoring import compute_score_simple
from dvf_data import get_dvf_for_commune
from plu_scoring import score_plu, score_plu_dynamic
from fibre_data import estimate_fibre
from georisques import enrich_georisques

load_dotenv()
logger = logging.getLogger("chat_assistant")

# ═══════════════════════════════════════════════════════════
# GPU CACHE (Étape 4B)
# ═══════════════════════════════════════════════════════════
_gpu_cache: dict = {}


async def get_gpu_full_context_cached(lon: float, lat: float) -> dict:
    key = f"{round(lon, 4)}_{round(lat, 4)}"
    if key in _gpu_cache:
        return _gpu_cache[key]
    result = await get_gpu_full_context(lon, lat)
    _gpu_cache[key] = result
    return result


# ═══════════════════════════════════════════════════════════
# S3REnR LOOKUP (Étape 2A)
# ═══════════════════════════════════════════════════════════

def get_s3renr_for_htb(nearest_htb_name: str, region: str) -> dict:
    """Find S3REnR data for the nearest HTB substation"""
    from s3renr_data import S3RENR_DATA
    region_data = S3RENR_DATA.get(region, {})
    postes = region_data.get("postes", {})

    # Normalize substation name
    norm = nearest_htb_name.upper()
    for prefix in ["POSTE "]:
        norm = norm.replace(prefix, "")
    for suffix in ["225KV", "400KV", "63KV", "150KV", "90KV"]:
        norm = norm.replace(suffix, "").strip()

    # Search for match
    norm_htb = norm.replace("-", " ").replace("'", " ").strip()
    for poste_name, poste_data in postes.items():
        norm_s3 = poste_name.upper().replace("-", " ").replace("'", " ").strip()
        if norm_s3 in norm_htb or norm_htb in norm_s3:
            return {
                "etat": poste_data.get("etat", "inconnu"),
                "mw_dispo": poste_data.get("mw_dispo", 0),
                "renforcement": poste_data.get("renforcement"),
                "score_dc": poste_data.get("score_dc", 5),
            }

    # Fallback région
    status = region_data.get("status_global", "")
    if status == "SATURE":
        return {"etat": "sature", "mw_dispo": 0, "renforcement": None, "score_dc": 1}
    return {"etat": "inconnu", "mw_dispo": 0, "renforcement": None, "score_dc": 5}


# ═══════════════════════════════════════════════════════════
# SYSTEM PROMPT (Étape 7)
# ═══════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Tu es l'assistant IA de Cockpit Immo, expert en prospection foncière pour data centers en France.
Ton rôle est de trouver les meilleurs terrains et d'expliquer POURQUOI ils sont bons ou mauvais.

Quand tu retournes des résultats, utilise le champ 'resume' de chaque parcelle pour expliquer le score.
Mentionne toujours: la distance au poste RTE, les MW disponibles, la zone PLU, et les risques éventuels.

Si aucune parcelle n'a un score > 60, dis-le clairement et suggère d'élargir la recherche.

ACTIONS POSSIBLES:

1. action: "find_parcels" — TROUVER DES PARCELLES (action PRIORITAIRE)
Utilise dès que l'utilisateur cherche des terrains, parcelles, ou sites pour un data center.
Paramètres:
- mw_target: puissance cible en MW (défaut: 20)
- region: code région "IDF"|"PACA"|"HdF"|"AuRA"|"BRE"|"GES"|"NOR"|"NAQ"|"OCC"|"PDL" (null si pas spécifié)
- commune: nom de commune ou code INSEE (null si pas spécifié). PRIORITAIRE sur region.
- min_surface_ha: surface minimum en hectares (défaut: 1.0)
- max_surface_ha: surface maximum en hectares (null = pas de max)
- max_dist_htb_km: distance max au poste HTB en km (défaut: 5)
- plu_zones: liste de zones PLU acceptées (null = toutes). Valeurs: "U", "AU", "AUx", "Ux", "UI", "N", "A"
- nb_parcels: nombre max de parcelles à retourner (défaut: 10, max: 20)
- search_radius_m: rayon de recherche autour des postes HTB en mètres (défaut: 2000, max: 5000)

2. action: "search" — Recherche de SITES DC (vue macro)
Paramètres: mw_target, mw_min, max_delay_months, region, strategy, grid_priority, brownfield_only, per_page

3. action: "site_detail" — Détail d'un site
- site_id: identifiant du site

4. action: "summary" — Résumé S3REnR régional

5. action: "chat" — Question générale
- response: ta réponse en texte

MAPPING LINGUISTIQUE:
- "Paris", "Île-de-France", "IDF" → region: "IDF"
- "Marseille", "PACA", "sud", "Provence", "Fos" → region: "PACA"
- "Nord", "Lille", "Hauts-de-France", "HdF" → region: "HdF"
- "Lyon", "Auvergne" → region: "AuRA"
- "à Fos-sur-Mer", "près de Lyon", "commune de Dunkerque" → commune: "nom_ville"
- "autour de Marseille", "secteur Lille" → commune: "nom_ville"
- "parcelle", "terrain", "foncier", "acheter", "trouver un terrain", "propose moi" → action: "find_parcels"
- "zone industrielle", "UI" → plu_zones: ["UI", "UX", "UE", "I", "IX"]
- "zone AU", "à urbaniser" → plu_zones: ["AU", "AUX", "1AU"]

RÈGLES:
- Dès que l'utilisateur parle de "terrain", "parcelle", "trouver", "proposer" → utilise "find_parcels"
- TOUJOURS répondre en JSON valide uniquement
- Pour "find_parcels": {"action": "find_parcels", "params": {...}, "intro": "texte court"}
- Pour "chat": {"action": "chat", "response": "ta réponse"}

CONTEXTE:
- IDF est SATURÉ (0 MW disponible)
- PACA a ~6400 MW de capacité réseau, meilleur potentiel
- HdF a ~2925 MW de capacité réseau
- La future ligne 400kV Fos→Jonquières (PACA) sera un atout majeur
- Les scores vont de 0 à 100 (GO ≥70, À ÉTUDIER 40-69, DÉFAVORABLE <40)
"""


def _haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    p = math.pi / 180
    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    return R * 2 * math.asin(math.sqrt(a))


# ═══════════════════════════════════════════════════════════
# COMMUNE RESOLUTION (Étape 3)
# ═══════════════════════════════════════════════════════════

async def _resolve_commune(commune_name: str) -> dict:
    """Resolve commune name to INSEE code + coordinates via Geo API"""
    try:
        communes = await api_search_communes(commune_name, limit=1)
        if communes:
            c = communes[0]
            centre = c.get("centre", {}).get("coordinates", [0, 0])
            return {
                "nom": c.get("nom", commune_name),
                "code": c.get("code", ""),
                "departement": c.get("departement", {}).get("code", ""),
                "region": c.get("region", {}).get("nom", ""),
                "lat": centre[1] if len(centre) > 1 else 0,
                "lng": centre[0] if len(centre) > 0 else 0,
            }
    except Exception as e:
        logger.warning(f"Commune resolution error for '{commune_name}': {e}")
    return None


# ═══════════════════════════════════════════════════════════
# ENRICH SINGLE PARCEL (Étape 2 + 4)
# ═══════════════════════════════════════════════════════════

async def _enrich_parcel(parsed: dict, infra: dict, params: dict) -> dict:
    """Enrich a single parcel with real data: S3REnR, fibre, risks, DVF, PLU, 400kV.
    Returns None if parcel should be filtered out."""
    plon = parsed["longitude"]
    plat = parsed["latitude"]
    surface_ha = parsed.get("surface_ha", 0)

    min_surface_ha = params.get("min_surface_ha", 1.0)
    max_surface_ha = params.get("max_surface_ha")
    max_dist_htb_m = params.get("max_dist_htb_km", 5) * 1000
    plu_zones = params.get("plu_zones")

    # Filter min/max surface
    if surface_ha < min_surface_ha:
        return None
    if max_surface_ha and surface_ha > max_surface_ha:
        return None

    # ── Distance postes HTB ──
    min_dist_htb = 999999
    nearest_htb_kv = 0
    nearest_htb_name = ""
    for htb in infra["postes_htb"]:
        hcoords = htb["geometry"]["coordinates"]
        dist = _haversine(plon, plat, hcoords[0], hcoords[1])
        if dist < min_dist_htb:
            min_dist_htb = dist
            nearest_htb_kv = htb["tension_kv"]
            nearest_htb_name = htb.get("nom", "")

    if min_dist_htb > max_dist_htb_m:
        return None

    parsed["dist_poste_htb_m"] = int(min_dist_htb)
    parsed["tension_htb_kv"] = nearest_htb_kv
    parsed["nearest_htb_name"] = nearest_htb_name

    # ── Landing point réel (Étape 2C) ──
    min_dist_lp = 999999
    nearest_lp = None
    for lp in infra["landing_points"]:
        lcoords = lp["geometry"]["coordinates"]
        dist = _haversine(plon, plat, lcoords[0], lcoords[1])
        if dist < min_dist_lp:
            min_dist_lp = dist
            nearest_lp = lp

    parsed["dist_landing_point_km"] = round(min_dist_lp / 1000, 1)
    if nearest_lp:
        parsed["landing_point_nom"] = nearest_lp["nom"]
        parsed["landing_point_nb_cables"] = nearest_lp.get("nb_cables_connectes", 0)
        parsed["landing_point_is_major_hub"] = nearest_lp.get("is_major_hub", False)
    else:
        parsed["landing_point_nom"] = ""
        parsed["landing_point_nb_cables"] = 0

    # ── S3REnR réel (Étape 2A) ──
    region = parsed.get("region", "")
    s3renr = get_s3renr_for_htb(nearest_htb_name, region)
    parsed["zone_saturation"] = s3renr["etat"]
    parsed["mw_dispo"] = s3renr["mw_dispo"]
    parsed["renforcement_prevu"] = s3renr.get("renforcement")

    # ── Fibre réelle (Étape 2B) ──
    code_commune = parsed.get("code_commune", "")
    plu_zone_raw = parsed.get("plu_zone", "")
    if code_commune:
        fibre = await estimate_fibre(code_commune, plu_zone_raw)
        parsed["dist_backbone_fibre_m"] = fibre["dist_backbone_fibre_m"]
        parsed["nb_operateurs_fibre"] = fibre["nb_operateurs_fibre"]
    else:
        parsed["dist_backbone_fibre_m"] = 3000
        parsed["nb_operateurs_fibre"] = 1

    # ── Risques Géorisques (Étape 2D) ──
    if code_commune:
        risques = await enrich_georisques(code_commune)
        if risques.get("ppri_zone"):
            parsed["ppri_zone"] = risques["ppri_zone"]
        parsed["zone_sismique"] = risques.get("zone_sismique", 1)
        parsed["argiles_alea"] = risques.get("argiles_alea", "faible")

    # ── DVF réel (Étape 2E) ──
    code_dep = parsed.get("departement", "")
    if code_commune:
        dvf = get_dvf_for_commune(code_commune)
    elif code_dep:
        dvf = get_dvf_for_commune(code_dep + "000")
    else:
        dvf = {}
    parsed["dvf_prix_median_m2"] = dvf.get("prix_median_m2", 0)

    # ── PLU via GPU (avec cache — Étape 4B) ──
    try:
        gpu_ctx = await get_gpu_full_context_cached(plon, plat)
        if gpu_ctx.get("zone"):
            parsed["plu_zone"] = gpu_ctx["zone"].get("typezone", "inconnu")
            parsed["plu_libelle"] = gpu_ctx["zone"].get("libelle", "")
            parsed["plu_libelong"] = gpu_ctx["zone"].get("libelong", "")
            plu_scoring_result = score_plu_dynamic(gpu_ctx)
        else:
            parsed["plu_zone"] = parsed.get("plu_zone", "inconnu")
            parsed["plu_libelle"] = ""
            plu_scoring_result = score_plu(zone_code=parsed.get("plu_zone", "inconnu"))
            plu_scoring_result["gpu_source"] = "fallback"
    except Exception:
        parsed["plu_zone"] = parsed.get("plu_zone", "inconnu")
        parsed["plu_libelle"] = ""
        plu_scoring_result = score_plu(zone_code=parsed.get("plu_zone", "inconnu"))
        plu_scoring_result["gpu_source"] = "error"

    parsed["plu_scoring"] = plu_scoring_result

    # Filter par zones PLU
    if plu_zones and parsed["plu_zone"] not in plu_zones and parsed["plu_zone"] != "inconnu":
        return None

    # Auto-exclude EXCLUDED PLU
    if plu_scoring_result.get("plu_status") == "EXCLUDED":
        return None

    # ── Future 400kV ──
    dist_future = distance_to_future_line(plon, plat)
    parsed["dist_future_400kv_m"] = round(dist_future)
    parsed["future_400kv_buffer"] = get_buffer_zone(plon, plat)
    parsed["future_400kv_score_bonus"] = score_future_400kv(plon, plat)

    # ── SCORE UNIVERSEL /100 (Étape 1) ──
    score_data = compute_score_simple(parsed)
    bonus_400kv = score_future_400kv(plon, plat)
    score_data["score"] = min(100, score_data["score"] + bonus_400kv)
    # Recalculate resume with adjusted score
    if bonus_400kv > 0:
        score_data["resume"] = score_data["resume"].replace(
            f"Score {score_data['score'] - bonus_400kv}/100",
            f"Score {score_data['score']}/100"
        )
    parsed["score"] = score_data
    parsed["site_origin"] = parsed.get("site_origin", "")

    return parsed


# ═══════════════════════════════════════════════════════════
# FIND REAL PARCELS (Étape 3 + 4A)
# ═══════════════════════════════════════════════════════════

async def _find_real_parcels(params: dict) -> dict:
    """Find real cadastral parcels. Supports commune search (Étape 3)
    and parallel enrichment (Étape 4A)."""
    infra = get_all_france_infra()

    commune_name = params.get("commune")
    search_radius = min(params.get("search_radius_m", 2000), 5000)
    min_surface_ha = params.get("min_surface_ha", 1.0)
    nb_parcels_max = min(params.get("nb_parcels", 10), 20)
    max_dist_htb_m = params.get("max_dist_htb_km", 5) * 1000

    # ── ÉTAPE 3: Recherche par commune ──
    if commune_name:
        commune_info = await _resolve_commune(commune_name)
        if commune_info and commune_info["lat"] and commune_info["lng"]:
            # Find HTB substations near the commune center
            htb_near = []
            for htb in infra["postes_htb"]:
                hcoords = htb["geometry"]["coordinates"]
                dist = _haversine(commune_info["lng"], commune_info["lat"], hcoords[0], hcoords[1])
                if dist <= max_dist_htb_m * 1.5:
                    htb_near.append({"htb": htb, "dist": dist})
            htb_near.sort(key=lambda x: x["dist"])

            if not htb_near:
                # No substations nearby, search around commune center directly
                htb_near = [{"htb": {"geometry": {"coordinates": [commune_info["lng"], commune_info["lat"]]}, "nom": commune_info["nom"], "tension_kv": 0}, "dist": 0}]

            top_sites = []
            for h in htb_near[:5]:
                coords = h["htb"]["geometry"]["coordinates"]
                top_sites.append({
                    "name": h["htb"].get("nom", ""),
                    "location": {"lat": coords[1], "lng": coords[0], "region": commune_info.get("region", "")},
                    "score": {"global": 0},
                    "grid": {
                        "voltage_level": f"{h['htb'].get('tension_kv', 0)}kV",
                        "available_capacity_mw": 0,
                        "saturation_level": "inconnu",
                    },
                })
        else:
            return {"parcels": [], "sites_searched": 0, "message": f"Commune '{commune_name}' non trouvée."}
    else:
        # ── Recherche par région (mode classique) ──
        search_params = {
            "region": params.get("region"),
            "mw_target": params.get("mw_target", 20),
            "mw_min": params.get("mw_target", 20) // 4,
            "max_delay_months": 36,
            "strategy": "balanced",
            "grid_priority": False,
            "brownfield_only": False,
            "per_page": 5,
        }
        dc_results = dc_search(search_params)
        top_sites = dc_results.get("results", [])[:5]

    if not top_sites:
        return {"parcels": [], "sites_searched": 0, "message": "Aucun poste HTB correspondant trouvé."}

    # Auto-expand search radius
    effective_radius = max(search_radius, int(max_dist_htb_m * 1.2), 2500)
    if min_surface_ha >= 3:
        effective_radius = max(effective_radius, 4000)
    effective_radius = min(effective_radius, 5000)

    # ── ÉTAPE 4A: Recherche parallèle des parcelles par site ──
    async def _search_site(site):
        lat = site["location"]["lat"]
        lng = site["location"]["lng"]
        site_name = site.get("name", "")
        try:
            data = await get_parcelles_around_point(lng, lat, radius_m=effective_radius, limit=120)
            features = data.get("features", [])
            return site_name, site, features
        except Exception as e:
            logger.warning(f"IGN API error for {site_name}: {e}")
            return site_name, site, []

    site_results = await asyncio.gather(*[_search_site(s) for s in top_sites])

    all_parcels = []
    sites_searched = []

    for site_name, site, features in site_results:
        sites_searched.append({
            "name": site_name,
            "lat": site["location"]["lat"],
            "lng": site["location"]["lng"],
            "parcels_found": len(features),
        })

        # Parse features and enrich in parallel
        parsed_list = []
        for feature in features:
            p = parse_parcelle_feature(feature)
            if p.get("centroid"):
                p["site_origin"] = site_name
                parsed_list.append(p)

        # Enrich parcels in parallel (batches of 10 to avoid API overload)
        for i in range(0, len(parsed_list), 10):
            batch = parsed_list[i:i+10]
            enriched = await asyncio.gather(
                *[_enrich_parcel(p, infra, params) for p in batch]
            )
            for ep in enriched:
                if ep is not None:
                    all_parcels.append(ep)

    # Sort by score descending
    all_parcels.sort(key=lambda p: -(p.get("score", {}).get("score", 0)))

    # Deduplicate by parcel_id
    seen = set()
    unique_parcels = []
    for p in all_parcels:
        pid = p["parcel_id"]
        if pid not in seen:
            seen.add(pid)
            unique_parcels.append(p)

    final_parcels = unique_parcels[:nb_parcels_max]

    # Clean parcels for JSON response
    clean_parcels = []
    for p in final_parcels:
        clean_parcels.append({
            "parcel_id": p["parcel_id"],
            "ref_cadastrale": p.get("ref_cadastrale", ""),
            "commune": p.get("commune", ""),
            "departement": p.get("departement", ""),
            "region": p.get("region", ""),
            "latitude": p["latitude"],
            "longitude": p["longitude"],
            "surface_m2": p.get("surface_m2", 0),
            "surface_ha": p.get("surface_ha", 0),
            "dist_poste_htb_m": p.get("dist_poste_htb_m", 0),
            "tension_htb_kv": p.get("tension_htb_kv", 0),
            "nearest_htb_name": p.get("nearest_htb_name", ""),
            "zone_saturation": p.get("zone_saturation", "inconnu"),
            "mw_dispo": p.get("mw_dispo", 0),
            "renforcement_prevu": p.get("renforcement_prevu"),
            "dist_landing_point_km": p.get("dist_landing_point_km", 0),
            "landing_point_nom": p.get("landing_point_nom", ""),
            "landing_point_nb_cables": p.get("landing_point_nb_cables", 0),
            "dist_backbone_fibre_m": p.get("dist_backbone_fibre_m", 0),
            "nb_operateurs_fibre": p.get("nb_operateurs_fibre", 0),
            "plu_zone": p.get("plu_zone", "inconnu"),
            "plu_libelle": p.get("plu_libelle", ""),
            "plu_scoring": p.get("plu_scoring"),
            "dvf_prix_median_m2": p.get("dvf_prix_median_m2", 0),
            "ppri_zone": p.get("ppri_zone"),
            "zone_sismique": p.get("zone_sismique", 1),
            "dist_future_400kv_m": p.get("dist_future_400kv_m", 0),
            "future_400kv_buffer": p.get("future_400kv_buffer"),
            "future_400kv_score_bonus": p.get("future_400kv_score_bonus", 0),
            "score": p.get("score", {}),
            "site_origin": p.get("site_origin", ""),
        })

    return {
        "parcels": clean_parcels,
        "sites_searched": sites_searched,
        "total_found": len(unique_parcels),
        "returned": len(clean_parcels),
        "filters_applied": {
            "min_surface_ha": min_surface_ha,
            "max_surface_ha": params.get("max_surface_ha"),
            "max_dist_htb_km": max_dist_htb_m / 1000,
            "plu_zones": params.get("plu_zones"),
            "search_radius_m": effective_radius,
            "commune": commune_name,
        },
    }


# ═══════════════════════════════════════════════════════════
# MAIN CHAT PROCESSOR
# ═══════════════════════════════════════════════════════════

async def process_chat_message(
    message: str,
    session_id: str,
    history: list,
) -> dict:
    """Process a chat message and return structured response"""
    api_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not api_key:
        return {
            "type": "error",
            "text": "Clé LLM non configurée. Contactez l'administrateur.",
        }

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"cockpit_{session_id}",
            system_message=SYSTEM_PROMPT,
        ).with_model("openai", "gpt-4.1-mini")

        response_text = await chat.send_message(UserMessage(text=message))

        parsed = _extract_json(response_text)
        if not parsed:
            return {"type": "text", "text": response_text}

        action = parsed.get("action", "chat")
        intro = parsed.get("intro", "")

        if action == "find_parcels":
            params = parsed.get("params", {})
            try:
                result = await _find_real_parcels(params)
                parcels = result["parcels"]
                if not parcels:
                    return {
                        "type": "text",
                        "text": intro + "\n\nAucune parcelle trouvée avec ces critères. Essayez d'élargir le rayon de recherche ou de réduire la surface minimum.",
                    }

                lats = [p["latitude"] for p in parcels]
                lngs = [p["longitude"] for p in parcels]
                fly_to = {
                    "lat": sum(lats) / len(lats),
                    "lng": sum(lngs) / len(lngs),
                    "zoom": 14,
                }

                return {
                    "type": "parcel_results",
                    "intro": intro,
                    "parcels": parcels,
                    "sites_searched": result["sites_searched"],
                    "total_found": result["total_found"],
                    "returned": result["returned"],
                    "fly_to": fly_to,
                    "params": params,
                    "filters_applied": result.get("filters_applied", {}),
                }
            except Exception as e:
                logger.error(f"find_parcels error: {e}")
                return {"type": "error", "text": f"Erreur lors de la recherche de parcelles: {str(e)}"}

        elif action == "search":
            params = parsed.get("params", {})
            results = dc_search(params)
            return {
                "type": "search_results",
                "intro": intro,
                "results": results["results"][:10],
                "meta": results["meta"],
                "params": params,
                "fly_to": _get_fly_target(results["results"], params),
            }

        elif action == "site_detail":
            site_id = parsed.get("site_id", "")
            site = dc_get_site(site_id)
            if site:
                return {
                    "type": "site_detail",
                    "intro": intro,
                    "site": site,
                    "fly_to": {
                        "lat": site["location"]["lat"],
                        "lng": site["location"]["lng"],
                        "zoom": 12,
                    },
                }
            return {"type": "text", "text": f"Site {site_id} non trouvé."}

        elif action == "summary":
            from s3renr_data import S3RENR_DATA
            summary = []
            for region_key, region_data in S3RENR_DATA.items():
                postes = region_data.get("postes", {})
                summary.append({
                    "region": region_key,
                    "status": region_data.get("status_global"),
                    "mw_total": region_data.get("capacite_globale_mw"),
                    "nb_postes": len(postes),
                })
            return {
                "type": "summary",
                "intro": intro,
                "summary": summary,
            }

        else:
            return {
                "type": "text",
                "text": parsed.get("response", response_text),
            }

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "type": "error",
            "text": f"Erreur: {str(e)}",
        }


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response"""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except json.JSONDecodeError:
                continue
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def _get_fly_target(results: list, params: dict) -> dict:
    if not results:
        return {"lat": 46.6, "lng": 2.3, "zoom": 6}
    if params.get("region"):
        r = results[0]
        return {"lat": r["location"]["lat"], "lng": r["location"]["lng"], "zoom": 8}
    lats = [r["location"]["lat"] for r in results[:5]]
    lngs = [r["location"]["lng"] for r in results[:5]]
    return {"lat": sum(lats) / len(lats), "lng": sum(lngs) / len(lngs), "zoom": 7}
