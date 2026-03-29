"""
Cockpit Immo — AI Chat Assistant
Parses natural language queries into DC search API calls and returns structured results.
Now also supports finding EXACT cadastral parcels near substations.
Uses Emergent LLM integration for NLP.
"""
import os
import json
import math
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

from dc_search_api import dc_search, dc_get_site
from api_carto import get_parcelles_around_point, parse_parcelle_feature, get_gpu_zone_urba_for_point
from france_infra_data import get_all_france_infra
from rte_future_line import distance_to_future_line, get_buffer_zone, score_future_400kv
from scoring import compute_full_score
from dvf_data import get_dvf_for_commune
from plu_scoring import score_plu

load_dotenv()
logger = logging.getLogger("chat_assistant")

SYSTEM_PROMPT = """Tu es l'assistant IA de Cockpit Immo, expert en prospection foncière pour data centers en France.

Quand l'utilisateur pose une question sur des terrains ou sites pour data centers, tu dois:
1. Extraire les paramètres de recherche
2. Retourner un JSON avec la clé "action" et les paramètres

ACTIONS POSSIBLES:

1. action: "find_parcels" — TROUVER DES PARCELLES EXACTES (action PRIORITAIRE)
Utilise cette action dès que l'utilisateur cherche des terrains, parcelles, ou sites pour un data center.
Paramètres à extraire:
- mw_target: puissance cible en MW (défaut: 20)
- region: "IDF"|"PACA"|"HdF"|"AuRA"|"BRE"|"GES"|"NOR"|"NAQ"|"OCC"|"PDL" (null si pas spécifié)
- max_delay_months: délai max raccordement (défaut: 36)
- min_surface_ha: surface minimum en hectares (défaut: 1.0)
- max_surface_ha: surface maximum en hectares (null = pas de max)
- max_dist_htb_km: distance max au poste HTB en km (défaut: 5)
- min_tension_kv: tension HTB minimum en kV (null = pas de min, 225 ou 400 si demandé)
- max_dist_future_line_km: distance max à la future ligne 400kV en km (null = pas de filtre)
- plu_zones: liste de zones PLU acceptées (null = toutes). Valeurs: "U" (urbanisé), "AU" (à urbaniser), "AUx", "Ux", "UI" (zone industrielle), "N" (naturelle), "A" (agricole)
- brownfield_only: true si brownfield/industriel uniquement (défaut: false)
- grid_priority: true si réseau dispo souhaité (défaut: false)
- strategy: "speed"|"cost"|"power"|"balanced" (défaut: "balanced")
- nb_parcels: nombre max de parcelles à retourner (défaut: 10, max: 20)
- search_radius_m: rayon de recherche autour des postes HTB en mètres (défaut: 2000, max: 5000)

EXEMPLES DE MAPPING:
- "parcelles en zone UI" ou "zone industrielle" → plu_zones: ["U", "UI", "Ux"]
- "zone à urbaniser" → plu_zones: ["AU", "AUx"]
- "terrain de 5 hectares minimum" → min_surface_ha: 5
- "entre 2 et 10 hectares" → min_surface_ha: 2, max_surface_ha: 10
- "à moins de 3km d'un poste" → max_dist_htb_km: 3
- "à moins de 2km de la future ligne" ou "proche future 400kV" → max_dist_future_line_km: 2
- "poste 400kV uniquement" → min_tension_kv: 400
- "poste 225kV ou plus" → min_tension_kv: 225
- "rayon 3km" ou "cherche dans 3km" → search_radius_m: 3000

2. action: "search" — Recherche de SITES DC (vue macro, sans parcelles exactes)
Utilise seulement si l'utilisateur demande une vue d'ensemble ou des sites, pas des terrains précis.
Paramètres:
- mw_target, mw_min, max_delay_months, region, strategy, grid_priority, brownfield_only, per_page

3. action: "site_detail" — Détail d'un site
- site_id: identifiant du site

4. action: "summary" — Résumé S3REnR régional

5. action: "chat" — Question générale
- response: ta réponse en texte

Mapping linguistique:
- "Paris", "Île-de-France", "IDF" → region: "IDF"
- "Marseille", "PACA", "sud", "Provence", "Fos" → region: "PACA"
- "Nord", "Lille", "Hauts-de-France", "HdF" → region: "HdF"
- "Lyon", "Auvergne" → region: "AuRA"
- "rapide", "vite", "urgent" → strategy: "speed"
- "pas cher", "économique", "coût" → strategy: "cost"
- "puissance", "maximum MW" → strategy: "power"
- "brownfield", "industriel", "friche" → brownfield_only: true
- "réseau dispo", "non saturé" → grid_priority: true
- "parcelle", "terrain", "foncier", "acheter", "trouver un terrain", "propose moi" → action: "find_parcels"
- "1 ha", "2 hectares", "5000 m²" → min_surface_ha (convertir en ha)
- "zone industrielle", "UI", "zone I" → plu_zones: ["U"]
- "zone AU", "à urbaniser" → plu_zones: ["AU"]

RÈGLES IMPORTANTES:
- Dès que l'utilisateur parle de "terrain", "parcelle", "trouver", "proposer" → utilise "find_parcels"
- TOUJOURS répondre en JSON valide uniquement, rien d'autre
- Pour "find_parcels": {"action": "find_parcels", "params": {...}, "intro": "texte court"}
- Pour "search": {"action": "search", "params": {...}, "intro": "texte court"}
- Pour "site_detail": {"action": "site_detail", "site_id": "...", "intro": "texte"}
- Pour "summary": {"action": "summary", "intro": "texte"}
- Pour "chat": {"action": "chat", "response": "ta réponse"}

CONTEXTE:
- IDF est SATURÉ (peu de MW disponible)
- PACA a ~3258 MW de capacité réseau, meilleur potentiel
- HdF a ~2925 MW de capacité réseau
- La future ligne 400kV Fos→Jonquières (PACA) sera un atout majeur
- Les scores vont de 0 à 100
"""


def _haversine(lon1, lat1, lon2, lat2):
    R = 6371000
    p = math.pi / 180
    a = 0.5 - math.cos((lat2 - lat1) * p) / 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    return R * 2 * math.asin(math.sqrt(a))


async def _find_real_parcels(params: dict) -> dict:
    """
    Find real cadastral parcels near the best matching HTB substations.
    1. Use dc_search to find top substations
    2. For each, call IGN API for nearby parcels
    3. Score and filter each parcel
    4. Return enriched parcel data
    """
    infra = get_all_france_infra()
    
    # Search for best sites to get substation locations
    search_params = {
        "region": params.get("region"),
        "mw_target": params.get("mw_target", 20),
        "mw_min": params.get("mw_target", 20) // 4,
        "max_delay_months": params.get("max_delay_months", 36),
        "strategy": params.get("strategy", "balanced"),
        "grid_priority": params.get("grid_priority", False),
        "brownfield_only": params.get("brownfield_only", False),
        "per_page": 5,
    }
    
    dc_results = dc_search(search_params)
    top_sites = dc_results.get("results", [])[:3]
    
    if not top_sites:
        return {"parcels": [], "sites_searched": 0, "message": "Aucun poste HTB correspondant trouvé."}
    
    search_radius = min(params.get("search_radius_m", 2000), 5000)
    min_surface_ha = params.get("min_surface_ha", 1.0)
    max_surface_ha = params.get("max_surface_ha")
    nb_parcels_max = min(params.get("nb_parcels", 10), 20)
    plu_zones = params.get("plu_zones")
    max_dist_htb_m = params.get("max_dist_htb_km", 5) * 1000
    min_tension_kv = params.get("min_tension_kv")
    max_dist_future_line_m = (params.get("max_dist_future_line_km") or 0) * 1000 if params.get("max_dist_future_line_km") else None
    
    all_parcels = []
    sites_searched = []
    
    for site in top_sites:
        lat = site["location"]["lat"]
        lng = site["location"]["lng"]
        site_name = site["name"]
        site_score = site["score"]["global"]
        
        try:
            data = await get_parcelles_around_point(lng, lat, radius_m=search_radius, limit=80)
            features = data.get("features", [])
        except Exception as e:
            logger.warning(f"IGN API error for {site_name}: {e}")
            continue
        
        sites_searched.append({
            "name": site_name,
            "region": site["location"]["region"],
            "lat": lat, "lng": lng,
            "site_score": site_score,
            "parcels_found": len(features),
            "grid": {
                "voltage": site["grid"]["voltage_level"],
                "mw_dispo": site["grid"]["available_capacity_mw"],
                "saturation": site["grid"]["saturation_level"],
            },
        })
        
        for feature in features:
            parsed = parse_parcelle_feature(feature)
            if not parsed.get("centroid"):
                continue
            
            plon = parsed["longitude"]
            plat = parsed["latitude"]
            surface_ha = parsed.get("surface_ha", 0)
            
            # Filter by min surface
            if surface_ha < min_surface_ha:
                continue
            
            # Filter by max surface
            if max_surface_ha and surface_ha > max_surface_ha:
                continue
            
            # Compute distances
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
            
            min_dist_lp = 999999
            nearest_lp_name = ""
            for lp in infra["landing_points"]:
                lcoords = lp["geometry"]["coordinates"]
                dist = _haversine(plon, plat, lcoords[0], lcoords[1])
                if dist < min_dist_lp:
                    min_dist_lp = dist
                    nearest_lp_name = lp["nom"]
            
            parsed["dist_poste_htb_m"] = int(min_dist_htb)
            parsed["tension_htb_kv"] = nearest_htb_kv
            parsed["nearest_htb_name"] = nearest_htb_name
            parsed["dist_landing_point_km"] = round(min_dist_lp / 1000, 1)
            parsed["landing_point_nom"] = nearest_lp_name
            parsed["dist_backbone_fibre_m"] = 2000
            parsed["nb_operateurs_fibre"] = 2
            
            # Filter by max distance to HTB
            if min_dist_htb > max_dist_htb_m:
                continue
            
            # Filter by min tension
            if min_tension_kv and nearest_htb_kv < min_tension_kv:
                continue
            
            # DVF
            code_dep = parsed.get("departement", "")
            if code_dep:
                dvf = get_dvf_for_commune(code_dep + "000")
                parsed["dvf_prix_median_m2"] = dvf.get("prix_median_m2", 0)
            
            # PLU (attempt quick lookup)
            try:
                plu = await get_gpu_zone_urba_for_point(plon, plat)
                if plu:
                    parsed["plu_zone"] = plu.get("typezone", "inconnu")
                    parsed["plu_libelle"] = plu.get("libelle", "")
                else:
                    parsed["plu_zone"] = "inconnu"
                    parsed["plu_libelle"] = ""
            except Exception:
                parsed["plu_zone"] = "inconnu"
                parsed["plu_libelle"] = ""
            
            # Filter by PLU zones if specified
            if plu_zones and parsed["plu_zone"] not in plu_zones and parsed["plu_zone"] != "inconnu":
                continue
            
            # PLU Scoring for DC compatibility
            plu_scoring_result = score_plu(
                zone_code=parsed["plu_zone"],
                zone_label=parsed.get("plu_libelle", ""),
            )
            parsed["plu_scoring"] = plu_scoring_result
            
            # Auto-exclude parcels with EXCLUDED PLU status
            if plu_scoring_result["plu_status"] == "EXCLUDED":
                continue
            
            # Future 400kV
            dist_future = distance_to_future_line(plon, plat)
            parsed["dist_future_400kv_m"] = round(dist_future)
            parsed["future_400kv_buffer"] = get_buffer_zone(plon, plat)
            parsed["future_400kv_score_bonus"] = score_future_400kv(plon, plat)
            
            # Filter by max distance to future line
            if max_dist_future_line_m and dist_future > max_dist_future_line_m:
                continue
            
            # Compute score
            parsed["zone_saturation"] = "inconnu"
            parsed["landing_point_nb_cables"] = 2
            try:
                score_data = compute_full_score(parsed, "colocation_t3")
                base_score = score_data.get("score_net", 0)
                bonus_400kv = score_future_400kv(plon, plat)
                parsed["score"] = {
                    "score_net": min(100, base_score + bonus_400kv),
                    "verdict": score_data.get("verdict", "CONDITIONNEL"),
                    "power_mw_p50": score_data.get("power_mw_p50", 0),
                }
            except Exception:
                parsed["score"] = {"score_net": 0, "verdict": "CONDITIONNEL"}
            
            parsed["site_origin"] = site_name
            all_parcels.append(parsed)
    
    # Sort by score descending
    all_parcels.sort(key=lambda p: -(p.get("score", {}).get("score_net", 0)))
    
    # Deduplicate by parcel_id
    seen = set()
    unique_parcels = []
    for p in all_parcels:
        pid = p["parcel_id"]
        if pid not in seen:
            seen.add(pid)
            unique_parcels.append(p)
    
    final_parcels = unique_parcels[:nb_parcels_max]
    
    # Clean parcels for JSON response (remove geometry to save bandwidth)
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
            "dist_landing_point_km": p.get("dist_landing_point_km", 0),
            "landing_point_nom": p.get("landing_point_nom", ""),
            "plu_zone": p.get("plu_zone", "inconnu"),
            "plu_libelle": p.get("plu_libelle", ""),
            "plu_scoring": p.get("plu_scoring"),
            "dvf_prix_median_m2": p.get("dvf_prix_median_m2", 0),
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
            "max_surface_ha": max_surface_ha,
            "max_dist_htb_km": max_dist_htb_m / 1000,
            "min_tension_kv": min_tension_kv,
            "max_dist_future_line_km": params.get("max_dist_future_line_km"),
            "plu_zones": plu_zones,
            "search_radius_m": search_radius,
        },
    }


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

        # Send the message directly (session handles history)
        response_text = await chat.send_message(UserMessage(text=message))

        # Parse JSON from response
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
                
                # Compute fly target (center of all parcels)
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
    """Extract JSON from LLM response (handles markdown code blocks)"""
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from code block
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
    # Try finding JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def _get_fly_target(results: list, params: dict) -> dict:
    """Compute map fly target from search results"""
    if not results:
        return {"lat": 46.6, "lng": 2.3, "zoom": 6}

    # If region filter, zoom to first result
    if params.get("region"):
        r = results[0]
        return {
            "lat": r["location"]["lat"],
            "lng": r["location"]["lng"],
            "zoom": 8,
        }

    # Otherwise, fit all results
    lats = [r["location"]["lat"] for r in results[:5]]
    lngs = [r["location"]["lng"] for r in results[:5]]
    return {
        "lat": sum(lats) / len(lats),
        "lng": sum(lngs) / len(lngs),
        "zoom": 7,
    }
