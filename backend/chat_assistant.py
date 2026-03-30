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
import unicodedata
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

from dc_search_api import dc_search, dc_get_site
from api_carto import (
    get_parcelles_around_point, parse_parcelle_feature,
    get_gpu_full_context, search_communes as api_search_communes,
    get_parcelle_by_id,
)
from france_infra_data import get_all_france_infra
from rte_future_line import distance_to_future_line, get_buffer_zone, score_future_400kv
from scoring import compute_score_simple
from dvf_data import get_real_dvf_price
from plu_scoring import score_plu, score_plu_dynamic
from fibre_data import estimate_fibre
from georisques import enrich_georisques
from water_data import get_nearest_water
from road_data import get_nearest_road

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
# S3REnR LOOKUP — Matching amélioré avec aliases (BUG 2 FIX)
# ═══════════════════════════════════════════════════════════

HTB_TO_S3RENR_ALIASES = {
    # PACA — Étang de Berre / Marseille
    "MARIGNANE": ["REALTOR", "ROGNAC"],
    "VITROLLES": ["REALTOR", "LA DURANNE", "GARDANNE"],
    "ISTRES": ["RASSUEN", "LAVERA", "LAVALDUC"],
    "FOS SUR MER": ["PONTEAU", "LAVERA", "RASSUEN", "FEUILLANE"],
    "FOS": ["PONTEAU", "LAVERA"],
    "BERRE": ["RASSUEN", "LAVERA", "ROGNAC"],
    "BERRE L ETANG": ["RASSUEN", "LAVERA", "ROGNAC"],
    "MARSEILLE NORD": ["ARENC", "SAUMATY", "CHATEAU GOMBERT"],
    "MARSEILLE": ["ARENC", "SAUMATY", "MAZARGUES"],
    "AIX EN PROVENCE": ["LA DURANNE", "GARDANNE"],
    "AIX": ["LA DURANNE", "GARDANNE"],
    "NICE": ["BROC-CARROS", "TRINITE-VICTOR"],
    "TOULON": ["SOLLIES", "NEOULES", "ROCBARON"],
    "AVIGNON": ["SORGUES", "BOLLENE", "PIOLENC"],
    "SALON DE PROVENCE": ["RASSUEN", "ROGNAC"],
    "MIRAMAS": ["RASSUEN", "LAVALDUC"],
    "PORT DE BOUC": ["PONTEAU", "LAVERA"],
    # PACA — Noms OSM
    "JONQUIERES": ["SORGUES", "PIOLENC", "BOLLENE"],
    "SAINT CHAMAS": ["ST-CHAMAS"],
    "AUBETTE": ["BERRE", "ROGNAC", "RASSUEN"],
    "CABRIES": ["REALTOR", "LA DURANNE", "GARDANNE"],
    "SEPTEMES": ["SAINT SAVOURNIN", "L'ESCARELLE"],
    "CAP JANET": ["ARENC", "SAUMATY"],
    "AIX MOURET": ["LA DURANNE", "GARDANNE"],
    # IDF
    "VILLEPINTE": ["VILLENEUVE-ST-GEORGES", "MITRY-MORY"],
    "ROISSY": ["MITRY-MORY"],
    "GONESSE": ["MITRY-MORY", "PUTEAUX"],
    "SAINT DENIS": ["PUTEAUX"],
    "GENNEVILLIERS": ["PUTEAUX"],
    "LA COURNEUVE": ["PUTEAUX", "VILLENEUVE-ST-GEORGES"],
    "CERGY": ["PERSAN", "LES ORMES"],
    "EVRY": ["MASSY", "JUINE"],
    "VITRY": ["RUNGIS", "MASSY"],
    "NANTERRE": ["PUTEAUX"],
    "VERSAILLES": ["MASSY"],
    # HdF
    "LILLE": ["AVELIN", "GAVRELLE"],
    "DUNKERQUE": ["BROUCKERQUE", "WARANDE"],
    "VALENCIENNES": ["HORNAING", "AVESNELLES"],
    "ARRAS": ["GAVRELLE"],
    "AMIENS": ["ARGOEUVRES"],
    "BEAUVAIS": ["EPAUX-BEZU"],
    # HdF — Noms OSM
    "WEPPES": ["AVELIN", "GAVRELLE"],
    "ARMENTIERES": ["AVELIN"],
    "PIERRETTE": ["AVELIN"],
    "LILLE DELIVRANCE": ["AVELIN"],
    "SEQUEDIN": ["AVELIN"],
    "AVELIN": ["AVELIN"],
    "BERCLAU": ["GAVRELLE"],
    "LESTARQUIT": ["GAVRELLE", "HORNAING"],
    "VERTEFEUILLE": ["AVELIN"],
    "ROUBAIX NORD": ["AVELIN"],
    "SAINT ROCH": ["AVELIN"],
    # AuRA
    "LYON": ["GENISSIAT", "CUSSET"],
    "SAINT ETIENNE": ["PRATCLAUX"],
    "GRENOBLE": ["MONTEYNARD"],
}


def _strip_accents(s: str) -> str:
    """é→e, è→e, ê→e, à→a, ù→u, etc."""
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def get_s3renr_for_htb(nearest_htb_name: str, region: str) -> dict:
    """Find S3REnR data for the nearest HTB substation — matching amélioré"""
    from s3renr_data import S3RENR_DATA
    region_data = S3RENR_DATA.get(region, {})
    postes = region_data.get("postes", {})

    if not postes:
        status = region_data.get("status_global", "")
        if status == "SATURE":
            return {"etat": "sature", "mw_dispo": 0, "renforcement": None, "score_dc": 1, "match_method": "region_sature"}
        return {"etat": "inconnu", "mw_dispo": 0, "renforcement": None, "score_dc": 5, "match_method": "no_postes"}

    # 1. Normaliser le nom HTB (accents + préfixes + suffixes)
    norm = nearest_htb_name.upper()
    norm = _strip_accents(norm)
    for prefix in ["POSTE ", "LA ", "LE ", "LES ", "L ", "D ", "DE ", "DES ", "DU "]:
        if norm.startswith(prefix):
            norm = norm[len(prefix):]
    for suffix in ["225KV", "400KV", "63KV", "150KV", "90KV"]:
        norm = norm.replace(suffix, "").strip()
    norm_htb = norm.replace("-", " ").replace("'", " ").strip()

    # FIX 1 — Poste générique sans nom → fallback régional direct
    if not norm_htb or len(norm_htb) < 2:
        status = region_data.get("status_global", "")
        if status == "SATURE":
            return {"etat": "sature", "mw_dispo": 0, "renforcement": None, "score_dc": 1, "match_method": "generic_sature"}
        # Fallback: meilleur poste régional
        best_mw = 0
        best_poste = None
        for pname, pdata in postes.items():
            if pdata.get("mw_dispo", 0) > best_mw:
                best_mw = pdata["mw_dispo"]
                best_poste = (pname, pdata)
        if best_poste:
            pname, pdata = best_poste
            return {
                "etat": pdata.get("etat", "disponible"),
                "mw_dispo": pdata.get("mw_dispo", 0),
                "renforcement": pdata.get("renforcement"),
                "score_dc": max(1, pdata.get("score_dc", 5) - 2),
                "match_method": "generic_regional_best",
                "match_poste": f"~{pname}",
            }
        return {"etat": "inconnu", "mw_dispo": 0, "renforcement": None, "score_dc": 5, "match_method": "generic_no_name"}

    # 2. Match direct par nom (avec accent stripping)
    for poste_name, poste_data in postes.items():
        norm_s3 = _strip_accents(poste_name.upper()).replace("-", " ").replace("'", " ").strip()
        if norm_s3 in norm_htb or norm_htb in norm_s3:
            return {
                "etat": poste_data.get("etat", "inconnu"),
                "mw_dispo": poste_data.get("mw_dispo", 0),
                "renforcement": poste_data.get("renforcement"),
                "score_dc": poste_data.get("score_dc", 5),
                "match_method": "name_direct",
                "match_poste": poste_name,
            }

    # 3. Alias manuels (avec normalisation accents)
    aliases = HTB_TO_S3RENR_ALIASES.get(norm_htb, [])
    if not aliases:
        for alias_key in HTB_TO_S3RENR_ALIASES:
            norm_alias = _strip_accents(alias_key.upper()).replace("-", " ").replace("'", " ").strip()
            if norm_alias in norm_htb or norm_htb in norm_alias:
                aliases = HTB_TO_S3RENR_ALIASES[alias_key]
                break

    if aliases:
        best_match = None
        best_mw = -1
        for alias in aliases:
            alias_upper = alias.upper()
            for poste_name, poste_data in postes.items():
                if poste_name.upper() == alias_upper:
                    mw = poste_data.get("mw_dispo", 0)
                    if mw > best_mw:
                        best_mw = mw
                        best_match = (poste_name, poste_data)
        if best_match:
            poste_name, poste_data = best_match
            return {
                "etat": poste_data.get("etat", "inconnu"),
                "mw_dispo": poste_data.get("mw_dispo", 0),
                "renforcement": poste_data.get("renforcement"),
                "score_dc": poste_data.get("score_dc", 5),
                "match_method": "alias",
                "match_poste": poste_name,
            }

    # 4. Fallback : meilleur poste de la région
    best_regional = None
    best_mw = -1
    for poste_name, poste_data in postes.items():
        mw = poste_data.get("mw_dispo", 0)
        if mw > best_mw:
            best_mw = mw
            best_regional = (poste_name, poste_data)

    if best_regional:
        poste_name, poste_data = best_regional
        return {
            "etat": poste_data.get("etat", "inconnu"),
            "mw_dispo": round(best_mw * 0.5),
            "renforcement": None,
            "score_dc": 5,
            "match_method": "regional_best",
            "match_poste": f"~{poste_name} (estimé)",
        }

    # 5. Fallback ultime
    status = region_data.get("status_global", "")
    if status == "SATURE":
        return {"etat": "sature", "mw_dispo": 0, "renforcement": None, "score_dc": 1, "match_method": "region_sature"}
    return {"etat": "inconnu", "mw_dispo": 0, "renforcement": None, "score_dc": 5, "match_method": "no_match"}


# ═══════════════════════════════════════════════════════════
# SYSTEM PROMPT (Étape 7)
# ═══════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Tu es l'assistant IA de Cockpit Immo, expert en prospection foncière pour data centers en France.
Tu aides les investisseurs, développeurs et consultants immobiliers à trouver les meilleurs terrains pour installer des data centers.

Ton rôle:
1. Trouver des parcelles par zone géographique (commune, région, adresse)
2. Analyser une parcelle spécifique par référence cadastrale
3. Estimer le budget d'un projet DC sur une parcelle
4. Expliquer POURQUOI un terrain est bon ou mauvais (score, PLU, MW, risques)
5. Répondre aux questions sur le marché DC, le réseau RTE, et les capacités S3REnR

Quand tu retournes des résultats, mentionne TOUJOURS: le score, la distance au poste RTE, les MW disponibles, la zone PLU, la surface, et les risques. Utilise le champ 'resume' pour expliquer.

ACTIONS POSSIBLES:

1. action: "find_parcels" — TROUVER DES PARCELLES
Utilise quand l'utilisateur cherche des terrains par zone géographique.
Paramètres:
- mw_target: puissance cible en MW (défaut: 20)
- region: code région "IDF"|"PACA"|"HdF"|"AuRA"|"BRE"|"GES"|"NOR"|"NAQ"|"OCC"|"PDL" (null si pas spécifié)
- commune: nom de commune (null si pas spécifié). PRIORITAIRE sur region.
- min_surface_ha: surface minimum en hectares (défaut: 1.0). Pour 10MW prévoir 2-3 ha, pour 50MW prévoir 5-10 ha.
- max_surface_ha: surface maximum (null = pas de max)
- max_dist_htb_km: distance max au poste HTB en km (défaut: 5)
- plu_zones: zones PLU acceptées (null = toutes). ["UI","UX","UE"] pour industriel.
- nb_parcels: nombre max de résultats (défaut: 10, max: 20)
- search_radius_m: rayon en mètres (défaut: 2000, max: 5000)

2. action: "analyze_parcel" — ANALYSER UNE PARCELLE PAR RÉFÉRENCE
Utilise quand l'utilisateur donne un numéro de parcelle cadastrale.
Paramètres:
- ref: référence cadastrale (ex: "13039000BS0118", "13039 BS 0118", "n°13039000BS0118")
- mw_target: puissance cible pour l'estimation budget (défaut: 10)

3. action: "find_by_address" — CHERCHER PAR ADRESSE
Utilise quand l'utilisateur donne une adresse postale ou un lieu précis qui n'est pas un nom de commune seul.
Paramètres:
- address: l'adresse complète (ex: "4 allée du Port 26200 Montélimar", "Zone industrielle de Fos")
- min_surface_ha: surface minimum (défaut: 1.0)
- max_dist_htb_km: distance max HTB (défaut: 5)
- search_radius_m: rayon de recherche (défaut: 3000)
- nb_parcels: nombre max (défaut: 10)
- plu_zones: zones PLU (null = toutes)

4. action: "estimate_budget" — ESTIMATION BUDGET DC
Utilise quand l'utilisateur demande un budget, un coût, un CAPEX, ou une estimation financière pour un projet.
Paramètres:
- ref: référence cadastrale (si parcelle déjà identifiée)
- commune: nom de commune (si pas de ref, on cherche la meilleure parcelle)
- mw_target: puissance cible en MW (défaut: 10)

5. action: "summary" — RÉSUMÉ CAPACITÉS RÉSEAU
Utilise quand l'utilisateur demande une vue d'ensemble nationale.

6. action: "chat" — QUESTION GÉNÉRALE
- response: ta réponse en texte libre
Utilise pour les questions marché, réglementation, conseils, ou conversation.

MAPPING LINGUISTIQUE:
- "Paris", "Île-de-France", "IDF" → region: "IDF"
- "Marseille", "PACA", "sud", "Provence", "Fos" → region: "PACA"
- "Nord", "Lille", "Hauts-de-France", "HdF" → region: "HdF"
- "Lyon", "Auvergne" → region: "AuRA"
- "à Fos-sur-Mer", "près de Lyon", "commune de Dunkerque" → commune: "nom_ville"
- "parcelle 13039...", "n°13039...", "référence 13039..." → action: "analyze_parcel"
- "4 allée du Port", "zone industrielle de...", "rue..." → action: "find_by_address"
- "combien coûte", "budget", "CAPEX", "estimation financière" → action: "estimate_budget"
- "résumé", "vue d'ensemble", "capacités réseau" → action: "summary"
- "zone industrielle", "UI" → plu_zones: ["UI", "UX", "UE", "I", "IX"]

RÈGLES CRITIQUES:
- Si l'utilisateur donne un numéro qui ressemble à une ref cadastrale (5+ chiffres + lettres + chiffres) → "analyze_parcel"
- Si l'utilisateur donne une adresse avec numéro + rue + code postal → "find_by_address"
- Si l'utilisateur mentionne un lieu/commune sans adresse précise → "find_parcels" avec commune
- TOUJOURS répondre en JSON valide uniquement
- Pour "find_parcels": {"action": "find_parcels", "params": {...}, "intro": "texte"}
- Pour "analyze_parcel": {"action": "analyze_parcel", "params": {"ref": "...", "mw_target": 10}, "intro": "texte"}
- Pour "find_by_address": {"action": "find_by_address", "params": {"address": "...", ...}, "intro": "texte"}
- Pour "estimate_budget": {"action": "estimate_budget", "params": {"ref": "...", "mw_target": 10}, "intro": "texte"}
- Pour "chat": {"action": "chat", "response": "ta réponse"}

CONTEXTE:
- IDF est SATURÉ (0 MW disponible, 10 postes tous saturés)
- PACA a ~3258 MW disponibles, 76 postes (52 dispo, 12 saturés), meilleur potentiel
- HdF a ~2925 MW disponibles, 66 postes (58 dispo, 5 saturés)
- Le projet RTE Fos-Jonquières est le plus grand renforcement réseau en cours :
  → Ligne aérienne 2 circuits 400kV Feuillane (Fos) — Jonquières (Gard), ~65 km
  → +3700 MW de capacité (5600 avec CCG), investissement 400 M€ (1 milliard total)
  → Mise en service 2029. 6 postes clés: Feuillane, Jonquières, Réaltor, Roquerousse, Ponteau, Tavel
  → Alternatives écartées: souterrain (2200 M€, >2035), HVDC (>2035)
- Les scores vont de 0 à 100 (GO ≥70, À ÉTUDIER 40-69, DÉFAVORABLE <40, EXCLU = zone A/N)
- Pour 10 MW, prévoir 2-3 hectares minimum. Pour 50 MW, 5-10 hectares.
- Budget indicatif: CAPEX ~9-12 M€/MW pour colocation Tier 3
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


async def _geocode_address(address: str) -> dict:
    """Geocode a French address via api-adresse.data.gouv.fr"""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://api-adresse.data.gouv.fr/search/",
                params={"q": address, "limit": 1}
            )
            if resp.status_code == 200:
                data = resp.json()
                features = data.get("features", [])
                if features:
                    f = features[0]
                    props = f.get("properties", {})
                    coords = f.get("geometry", {}).get("coordinates", [0, 0])
                    return {
                        "lat": coords[1],
                        "lng": coords[0],
                        "label": props.get("label", address),
                        "commune": props.get("city", ""),
                        "code_commune": props.get("citycode", ""),
                        "departement": props.get("context", "").split(",")[0].strip(),
                        "score": props.get("score", 0),
                    }
    except Exception as e:
        logger.warning(f"Geocoding error for '{address}': {e}")
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
    htb_list = infra.get("postes_htb_all") or infra["postes_htb"]
    for htb in htb_list:
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
    parsed["s3renr_match_method"] = s3renr.get("match_method", "")
    parsed["s3renr_match_poste"] = s3renr.get("match_poste", "")

    # Propager projet Fos-Jonquières depuis S3REnR
    matched_name = s3renr.get("match_poste", "")
    if matched_name and not matched_name.startswith("~"):
        from s3renr_data import S3RENR_DATA
        poste_full = S3RENR_DATA.get(region, {}).get("postes", {}).get(matched_name, {})
        if poste_full.get("projet_fos"):
            parsed["projet_fos"] = poste_full["projet_fos"]

    # ── Fibre réelle (Étape 2B) ──
    code_commune = parsed.get("code_commune", "")
    # BUG 5 FIX — Reconstruire code_commune si vide
    if not code_commune:
        code_dep = parsed.get("departement", "")
        commune_name = parsed.get("commune", "")
        if code_dep and commune_name:
            try:
                communes = await api_search_communes(commune_name, limit=1)
                if communes:
                    code_commune = communes[0].get("code", "")
                    parsed["code_commune"] = code_commune
            except Exception:
                pass
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

    # ── Cours d'eau + Route principale → déplacé en post-enrichment pour top parcelles ──
    # (Overpass API est lent, on enrichit seulement les top résultats après tri)

    # ── DVF réel (Étape 2E — API Cerema avec fallback) ──
    code_dep = parsed.get("departement", "")
    dvf_result = await get_real_dvf_price(code_commune, code_dep, region)
    parsed["dvf_prix_median_m2"] = dvf_result.get("prix_median_m2", 0)
    parsed["dvf_source"] = dvf_result.get("source", "inconnu")
    parsed["dvf_nb_transactions"] = dvf_result.get("nb_transactions", 0)

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
    if bonus_400kv > 0:
        # BUG 3 FIX — Recalculer verdict + resume après bonus
        old_score = score_data["score"]
        score_data["score"] = min(100, old_score + bonus_400kv)
        new_score = score_data["score"]
        # Recalculer le verdict
        if new_score >= 70:
            score_data["verdict"] = "GO"
        elif new_score >= 40:
            score_data["verdict"] = "A_ETUDIER"
        else:
            score_data["verdict"] = "DEFAVORABLE"
        # Reconstruire le resume
        score_data["resume"] = score_data["resume"].replace(
            f"Score {old_score}/100",
            f"Score {new_score}/100"
        )
        # Corriger le verdict dans le resume
        for old_v in ["A_ETUDIER", "DEFAVORABLE", "GO"]:
            if old_v in score_data["resume"] and old_v != score_data["verdict"]:
                score_data["resume"] = score_data["resume"].replace(
                    f"— {old_v}.", f"— {score_data['verdict']}."
                )
                break
        # Ajouter mention du bonus
        if "400kV" not in score_data["resume"]:
            score_data["resume"] = score_data["resume"].rstrip(".") + f", bonus future 400kV (+{bonus_400kv}pts)."
    parsed["score"] = score_data
    parsed["site_origin"] = parsed.get("site_origin", "")

    return parsed


# ═══════════════════════════════════════════════════════════
# CLEAN PARCEL BUILDER (factorized)
# ═══════════════════════════════════════════════════════════

def _build_clean_parcel(p: dict) -> dict:
    """Build a clean parcel dict for JSON response"""
    return {
        "parcel_id": p.get("parcel_id", ""),
        "ref_cadastrale": p.get("ref_cadastrale", ""),
        "commune": p.get("commune", ""),
        "departement": p.get("departement", ""),
        "region": p.get("region", ""),
        "latitude": p.get("latitude", 0),
        "longitude": p.get("longitude", 0),
        "surface_m2": p.get("surface_m2", 0),
        "surface_ha": p.get("surface_ha", 0),
        "geometry": p.get("geometry"),
        "dist_poste_htb_m": p.get("dist_poste_htb_m", 0),
        "tension_htb_kv": p.get("tension_htb_kv", 0),
        "nearest_htb_name": p.get("nearest_htb_name", ""),
        "zone_saturation": p.get("zone_saturation", "inconnu"),
        "mw_dispo": p.get("mw_dispo", 0),
        "renforcement_prevu": p.get("renforcement_prevu"),
        "s3renr_match_method": p.get("s3renr_match_method", ""),
        "s3renr_match_poste": p.get("s3renr_match_poste", ""),
        "dist_landing_point_km": p.get("dist_landing_point_km", 0),
        "landing_point_nom": p.get("landing_point_nom", ""),
        "landing_point_nb_cables": p.get("landing_point_nb_cables", 0),
        "dist_backbone_fibre_m": p.get("dist_backbone_fibre_m", 0),
        "nb_operateurs_fibre": p.get("nb_operateurs_fibre", 0),
        "plu_zone": p.get("plu_zone", "inconnu"),
        "plu_libelle": p.get("plu_libelle", ""),
        "plu_scoring": p.get("plu_scoring"),
        "dvf_prix_median_m2": p.get("dvf_prix_median_m2", 0),
        "dvf_source": p.get("dvf_source", "inconnu"),
        "dvf_nb_transactions": p.get("dvf_nb_transactions", 0),
        "ppri_zone": p.get("ppri_zone"),
        "zone_sismique": p.get("zone_sismique", 1),
        "dist_cours_eau_m": p.get("dist_cours_eau_m"),
        "nom_cours_eau": p.get("nom_cours_eau"),
        "dist_route_m": p.get("dist_route_m"),
        "nom_route": p.get("nom_route"),
        "type_route": p.get("type_route"),
        "dist_future_400kv_m": p.get("dist_future_400kv_m", 0),
        "future_400kv_buffer": p.get("future_400kv_buffer"),
        "future_400kv_score_bonus": p.get("future_400kv_score_bonus", 0),
        "projet_fos": p.get("projet_fos"),
        "score": p.get("score", {}),
        "site_origin": p.get("site_origin", ""),
        "code_commune": p.get("code_commune", ""),
    }


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
            htb_list_commune = infra.get("postes_htb_all") or infra["postes_htb"]
            for htb in htb_list_commune:
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

    # ── ÉTAPE 9: Agrégation parcelles adjacentes ──
    composite_sites = _aggregate_adjacent(unique_parcels)

    final_parcels = unique_parcels[:nb_parcels_max]

    # ── Post-enrichment: Overpass eau + route (top 5 seulement) ──
    async def _enrich_overpass(p):
        plon = p["longitude"]
        plat = p["latitude"]
        try:
            water, road = await asyncio.wait_for(
                asyncio.gather(
                    get_nearest_water(plon, plat),
                    get_nearest_road(plon, plat),
                    return_exceptions=True
                ),
                timeout=6
            )
            if isinstance(water, dict):
                p["dist_cours_eau_m"] = water.get("dist_cours_eau_m")
                p["nom_cours_eau"] = water.get("nom_cours_eau")
            if isinstance(road, dict):
                p["dist_route_m"] = road.get("dist_route_m")
                p["nom_route"] = road.get("nom_route")
                p["type_route"] = road.get("type_route")
        except Exception:
            pass
        return p

    # Enrich top 3 parcels with Overpass data (sequential to respect rate limits)
    for p in final_parcels[:3]:
        await _enrich_overpass(p)

    # BUG 1 FIX — Recalculer le score avec les nouvelles données eau/route
    for p in final_parcels[:3]:
        if p.get("dist_cours_eau_m") or p.get("dist_route_m"):
            new_score = compute_score_simple(p)
            bonus_400kv = p.get("future_400kv_score_bonus", 0)
            if bonus_400kv > 0:
                old_s = new_score["score"]
                new_score["score"] = min(100, old_s + bonus_400kv)
                ns = new_score["score"]
                if ns >= 70:
                    new_score["verdict"] = "GO"
                elif ns >= 40:
                    new_score["verdict"] = "A_ETUDIER"
                else:
                    new_score["verdict"] = "DEFAVORABLE"
                new_score["resume"] = new_score["resume"].replace(
                    f"Score {old_s}/100", f"Score {ns}/100"
                )
                for old_v in ["A_ETUDIER", "DEFAVORABLE", "GO"]:
                    if f"— {old_v}." in new_score["resume"] and old_v != new_score["verdict"]:
                        new_score["resume"] = new_score["resume"].replace(f"— {old_v}.", f"— {new_score['verdict']}.")
                        break
                if "400kV" not in new_score["resume"]:
                    new_score["resume"] = new_score["resume"].rstrip(".") + f", bonus future 400kV (+{bonus_400kv}pts)."
            p["score"] = new_score

    # Clean parcels for JSON response
    clean_parcels = [_build_clean_parcel(p) for p in final_parcels]

    return {
        "parcels": clean_parcels,
        "composite_sites": composite_sites,
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
# ÉTAPE 9: AGRÉGATION PARCELLES ADJACENTES
# ═══════════════════════════════════════════════════════════

def _aggregate_adjacent(parcels: list, max_gap_m: float = 100.0) -> list:
    """Detect composite sites: parcels within max_gap_m of each other.
    Returns list of composite sites with aggregated score."""
    if len(parcels) < 2:
        return []

    # Build adjacency clusters using Union-Find
    parent = list(range(len(parcels)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Check pairwise distances (O(n²) but n is typically < 50)
    for i in range(len(parcels)):
        pi = parcels[i]
        for j in range(i + 1, len(parcels)):
            pj = parcels[j]
            dist = _haversine(pi["longitude"], pi["latitude"], pj["longitude"], pj["latitude"])
            if dist <= max_gap_m:
                union(i, j)

    # Group parcels by cluster
    clusters = {}
    for i in range(len(parcels)):
        root = find(i)
        if root not in clusters:
            clusters[root] = []
        clusters[root].append(parcels[i])

    # Build composite sites (only clusters with 2+ parcels)
    composites = []
    for cluster_parcels in clusters.values():
        if len(cluster_parcels) < 2:
            continue

        total_surface_m2 = sum(p.get("surface_m2", 0) for p in cluster_parcels)
        total_surface_ha = total_surface_m2 / 10000
        avg_lat = sum(p["latitude"] for p in cluster_parcels) / len(cluster_parcels)
        avg_lng = sum(p["longitude"] for p in cluster_parcels) / len(cluster_parcels)

        # Best scoring parcel in the cluster
        best = max(cluster_parcels, key=lambda p: p.get("score", {}).get("score", 0))

        # Rescore the composite site with aggregated surface
        composite_data = {**best}
        composite_data["surface_ha"] = total_surface_ha
        composite_data["surface_m2"] = total_surface_m2
        composite_score = compute_score_simple(composite_data)

        composites.append({
            "type": "composite_site",
            "nb_parcels": len(cluster_parcels),
            "parcel_ids": [p["parcel_id"] for p in cluster_parcels],
            "refs": [p.get("ref_cadastrale", "") for p in cluster_parcels],
            "surface_totale_ha": round(total_surface_ha, 2),
            "latitude": avg_lat,
            "longitude": avg_lng,
            "commune": best.get("commune", ""),
            "score": composite_score,
            "best_parcel_score": best.get("score", {}).get("score", 0),
        })

    composites.sort(key=lambda c: -(c.get("score", {}).get("score", 0)))
    return composites


# ═══════════════════════════════════════════════════════════
# NEW CAPABILITIES: analyze_parcel, find_by_address, estimate_budget
# ═══════════════════════════════════════════════════════════

async def _analyze_single_parcel(ref: str) -> dict:
    """Analyze a specific parcel by cadastral reference"""
    ref_clean = ref.replace(" ", "").replace("-", "").replace("n°", "").replace("N°", "").upper()
    if ref_clean.startswith("FR_"):
        ref_clean = ref_clean[3:]

    feature = await get_parcelle_by_id(ref_clean)
    if not feature:
        parts = ref.replace("-", " ").replace("/", " ").split()
        if len(parts) >= 3:
            code_com = parts[0].zfill(5)
            section = parts[1].upper().zfill(2)
            numero = parts[2].zfill(4)
            alt_ref = f"{code_com}000{section}{numero}"
            feature = await get_parcelle_by_id(alt_ref)
        if not feature:
            return {"error": f"Parcelle {ref} non trouvée dans le cadastre IGN. Vérifiez la référence (format attendu: 13039000BS0118 ou 13039 BS 0118)."}

    parsed = parse_parcelle_feature(feature)
    if not parsed.get("centroid"):
        return {"error": f"Parcelle {ref} trouvée mais sans géométrie exploitable."}

    infra = get_all_france_infra()
    enriched = await _enrich_parcel(parsed, infra, {"min_surface_ha": 0, "max_dist_htb_km": 100, "max_surface_ha": None})
    if not enriched:
        return {"error": f"Parcelle {ref} trouvée mais incompatible (zone PLU non constructible)."}

    plon = enriched["longitude"]
    plat = enriched["latitude"]
    try:
        water, road = await asyncio.wait_for(
            asyncio.gather(
                get_nearest_water(plon, plat),
                get_nearest_road(plon, plat),
                return_exceptions=True
            ),
            timeout=8
        )
        if isinstance(water, dict):
            enriched["dist_cours_eau_m"] = water.get("dist_cours_eau_m")
            enriched["nom_cours_eau"] = water.get("nom_cours_eau")
        if isinstance(road, dict):
            enriched["dist_route_m"] = road.get("dist_route_m")
            enriched["nom_route"] = road.get("nom_route")
            enriched["type_route"] = road.get("type_route")
    except Exception:
        pass

    if enriched.get("dist_cours_eau_m") or enriched.get("dist_route_m"):
        enriched["score"] = compute_score_simple(enriched)
        bonus = enriched.get("future_400kv_score_bonus", 0)
        if bonus > 0:
            enriched["score"]["score"] = min(100, enriched["score"]["score"] + bonus)

    return {"parcel": enriched}


async def _find_parcels_near_address(address: str, params: dict) -> dict:
    """Geocode an address then search for parcels around it"""
    geo = await _geocode_address(address)
    if not geo:
        return {"parcels": [], "message": f"Adresse '{address}' non trouvée. Essayez avec le nom de la commune."}

    infra = get_all_france_infra()
    search_radius = min(params.get("search_radius_m", 3000), 5000)
    nb_parcels_max = min(params.get("nb_parcels", 10), 20)

    try:
        data = await get_parcelles_around_point(geo["lng"], geo["lat"], radius_m=search_radius, limit=120)
        features = data.get("features", [])
    except Exception as e:
        return {"parcels": [], "message": f"Erreur API IGN autour de {geo['label']}: {str(e)}"}

    parsed_list = []
    for feature in features:
        p = parse_parcelle_feature(feature)
        if p.get("centroid"):
            p["site_origin"] = f"adresse: {geo['label']}"
            parsed_list.append(p)

    all_parcels = []
    for i in range(0, len(parsed_list), 10):
        batch = parsed_list[i:i+10]
        enriched = await asyncio.gather(
            *[_enrich_parcel(p, infra, params) for p in batch]
        )
        for ep in enriched:
            if ep is not None:
                all_parcels.append(ep)

    all_parcels.sort(key=lambda p: -(p.get("score", {}).get("score", 0)))

    seen = set()
    unique = []
    for p in all_parcels:
        pid = p["parcel_id"]
        if pid not in seen:
            seen.add(pid)
            unique.append(p)

    final = unique[:nb_parcels_max]

    for p in final[:3]:
        plon, plat = p["longitude"], p["latitude"]
        try:
            water, road = await asyncio.wait_for(
                asyncio.gather(get_nearest_water(plon, plat), get_nearest_road(plon, plat), return_exceptions=True), timeout=6)
            if isinstance(water, dict):
                p["dist_cours_eau_m"] = water.get("dist_cours_eau_m")
                p["nom_cours_eau"] = water.get("nom_cours_eau")
            if isinstance(road, dict):
                p["dist_route_m"] = road.get("dist_route_m")
                p["nom_route"] = road.get("nom_route")
                p["type_route"] = road.get("type_route")
        except Exception:
            pass
        if p.get("dist_cours_eau_m") or p.get("dist_route_m"):
            p["score"] = compute_score_simple(p)

    clean_parcels = [_build_clean_parcel(p) for p in final]

    return {
        "parcels": clean_parcels,
        "geocoded": geo,
        "total_found": len(unique),
        "returned": len(clean_parcels),
    }


def _estimate_dc_budget(parcel: dict, mw_target: int = 10) -> dict:
    """Estimation budgétaire indicative pour un projet DC"""
    surface_m2 = parcel.get("surface_m2", 0)
    dvf_prix = parcel.get("dvf_prix_median_m2", 0) or 80
    dist_htb_m = parcel.get("dist_poste_htb_m", 0) or 5000
    tension_kv = parcel.get("tension_htb_kv", 0) or 225
    mw_dispo = parcel.get("mw_dispo", 0) or 0

    cout_foncier = surface_m2 * dvf_prix

    cout_raccordement_par_mw = 800000 if dist_htb_m < 3000 and tension_kv >= 225 else 1200000 if dist_htb_m < 5000 else 1800000
    if mw_dispo >= mw_target:
        cout_raccordement_par_mw = int(cout_raccordement_par_mw * 0.7)
    cout_raccordement = mw_target * cout_raccordement_par_mw

    cout_construction_par_mw = 9000000
    cout_construction = mw_target * cout_construction_par_mw

    dist_fibre = parcel.get("dist_backbone_fibre_m", 3000) or 3000
    cout_fibre = max(500000, dist_fibre * 300)

    capex_total = cout_foncier + cout_raccordement + cout_construction + cout_fibre

    revenu_annuel_maturite = mw_target * 1000 * 140 * 12 * 0.75
    opex_annuel = revenu_annuel_maturite * 0.58
    ebitda_annuel = revenu_annuel_maturite - opex_annuel

    return {
        "mw_target": mw_target,
        "foncier_eur": round(cout_foncier),
        "foncier_m2_eur": dvf_prix,
        "raccordement_eur": round(cout_raccordement),
        "construction_eur": round(cout_construction),
        "fibre_eur": round(cout_fibre),
        "capex_total_eur": round(capex_total),
        "capex_total_meur": round(capex_total / 1e6, 1),
        "revenu_annuel_maturite_eur": round(revenu_annuel_maturite),
        "ebitda_annuel_eur": round(ebitda_annuel),
        "ebitda_meur": round(ebitda_annuel / 1e6, 1),
        "tri_indicatif_pct": round((ebitda_annuel / capex_total) * 100, 1) if capex_total > 0 else 0,
        "note": "Estimation indicative — pas un conseil financier. Consulter un bureau d'études spécialisé.",
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

    try:
        if not api_key:
            raise ValueError("Clé LLM non configurée")

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
                    "composite_sites": result.get("composite_sites", []),
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
            # BUG 2 FIX — Deprecated action, redirect to find_parcels
            logger.warning("LLM used deprecated 'search' action — redirecting to find_parcels")
            params = parsed.get("params", {})
            try:
                result = await _find_real_parcels(params)
                parcels = result["parcels"]
                if not parcels:
                    return {"type": "text", "text": intro + "\n\nAucune parcelle trouvée."}
                lats = [p["latitude"] for p in parcels]
                lngs = [p["longitude"] for p in parcels]
                return {
                    "type": "parcel_results",
                    "intro": intro,
                    "parcels": parcels,
                    "composite_sites": result.get("composite_sites", []),
                    "sites_searched": result["sites_searched"],
                    "total_found": result["total_found"],
                    "returned": result["returned"],
                    "fly_to": {"lat": sum(lats) / len(lats), "lng": sum(lngs) / len(lngs), "zoom": 14},
                    "params": params,
                    "filters_applied": result.get("filters_applied", {}),
                }
            except Exception as e:
                logger.error(f"search->find_parcels fallback error: {e}")
                return {"type": "error", "text": f"Erreur: {str(e)}"}

        elif action == "site_detail":
            # BUG 2 FIX — Deprecated action, try to find parcels near the site
            logger.warning("LLM used deprecated 'site_detail' action")
            site_id = parsed.get("site_id", "")
            site = dc_get_site(site_id)
            if site:
                return {
                    "type": "text",
                    "intro": intro,
                    "text": f"Site {site.get('name', site_id)} — {site.get('location', {}).get('region', '')}. Utilisez 'find_parcels' pour chercher des parcelles dans cette zone.",
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

        elif action == "analyze_parcel":
            params = parsed.get("params", {})
            ref = params.get("ref", "")
            mw_target = params.get("mw_target", 10)
            if not ref:
                return {"type": "text", "text": "Merci de fournir la référence cadastrale de la parcelle à analyser (ex: 13039000BS0118)."}
            try:
                result = await _analyze_single_parcel(ref)
                if "error" in result:
                    return {"type": "text", "text": intro + "\n\n" + result["error"]}
                parcel = result["parcel"]
                budget = _estimate_dc_budget(parcel, mw_target)
                parcel["budget"] = budget
                clean = _build_clean_parcel(parcel)
                clean["budget"] = budget
                return {
                    "type": "parcel_results",
                    "intro": intro,
                    "parcels": [clean],
                    "total_found": 1,
                    "returned": 1,
                    "sites_searched": [{"name": ref, "type": "ref_cadastrale"}],
                    "fly_to": {"lat": clean["latitude"], "lng": clean["longitude"], "zoom": 16},
                    "params": params,
                }
            except Exception as e:
                logger.error(f"analyze_parcel error: {e}")
                return {"type": "error", "text": f"Erreur lors de l'analyse de la parcelle {ref}: {str(e)}"}

        elif action == "find_by_address":
            params = parsed.get("params", {})
            address = params.get("address", "")
            if not address:
                return {"type": "text", "text": "Merci de fournir une adresse à géocoder (ex: '4 allée du Port 26200 Montélimar')."}
            try:
                result = await _find_parcels_near_address(address, params)
                parcels = result.get("parcels", [])
                geo = result.get("geocoded")
                if not parcels:
                    msg_text = result.get("message", f"Aucune parcelle trouvée autour de '{address}'.")
                    return {"type": "text", "text": intro + "\n\n" + msg_text}
                lats = [p["latitude"] for p in parcels]
                lngs = [p["longitude"] for p in parcels]
                return {
                    "type": "parcel_results",
                    "intro": intro + (f"\n(Adresse géocodée: {geo['label']})" if geo else ""),
                    "parcels": parcels,
                    "total_found": result.get("total_found", len(parcels)),
                    "returned": result.get("returned", len(parcels)),
                    "sites_searched": [{"name": geo["label"] if geo else address, "type": "address"}],
                    "fly_to": {"lat": sum(lats) / len(lats), "lng": sum(lngs) / len(lngs), "zoom": 15},
                    "params": params,
                }
            except Exception as e:
                logger.error(f"find_by_address error: {e}")
                return {"type": "error", "text": f"Erreur lors de la recherche par adresse: {str(e)}"}

        elif action == "estimate_budget":
            params = parsed.get("params", {})
            ref = params.get("ref", "")
            commune = params.get("commune", "")
            mw_target = params.get("mw_target", 10)
            try:
                target_parcel = None
                if ref:
                    result = await _analyze_single_parcel(ref)
                    if "error" not in result:
                        target_parcel = result["parcel"]
                if not target_parcel and commune:
                    search_result = await _find_real_parcels({"commune": commune, "nb_parcels": 1, "min_surface_ha": 2})
                    parcels = search_result.get("parcels", [])
                    if parcels:
                        target_parcel = parcels[0]
                if not target_parcel:
                    return {"type": "text", "text": intro + "\n\nImpossible de trouver une parcelle pour l'estimation. Précisez une référence cadastrale ou une commune."}
                budget = _estimate_dc_budget(target_parcel, mw_target)
                target_parcel["budget"] = budget
                clean = _build_clean_parcel(target_parcel)
                clean["budget"] = budget
                return {
                    "type": "parcel_results",
                    "intro": intro,
                    "parcels": [clean],
                    "total_found": 1,
                    "returned": 1,
                    "sites_searched": [{"name": ref or commune or "estimation", "type": "budget"}],
                    "fly_to": {"lat": clean["latitude"], "lng": clean["longitude"], "zoom": 15},
                    "params": params,
                    "budget_estimation": budget,
                }
            except Exception as e:
                logger.error(f"estimate_budget error: {e}")
                return {"type": "error", "text": f"Erreur lors de l'estimation budget: {str(e)}"}

        else:
            return {
                "type": "text",
                "text": parsed.get("response", response_text),
            }

    except Exception as e:
        logger.error(f"Chat error: {e}")
        # BUG 4 FIX — Fallback: parser directement sans LLM
        fallback = _try_direct_parse(message)
        if fallback and fallback.get("action") == "find_parcels":
            try:
                result = await _find_real_parcels(fallback["params"])
                parcels = result["parcels"]
                if parcels:
                    lats = [p["latitude"] for p in parcels]
                    lngs = [p["longitude"] for p in parcels]
                    return {
                        "type": "parcel_results",
                        "intro": fallback.get("intro", "Résultats (mode fallback) :"),
                        "parcels": parcels,
                        "composite_sites": result.get("composite_sites", []),
                        "sites_searched": result["sites_searched"],
                        "total_found": result["total_found"],
                        "returned": result["returned"],
                        "fly_to": {"lat": sum(lats) / len(lats), "lng": sum(lngs) / len(lngs), "zoom": 14},
                        "params": fallback["params"],
                        "filters_applied": result.get("filters_applied", {}),
                    }
            except Exception as fallback_err:
                logger.error(f"Fallback error: {fallback_err}")
        return {
            "type": "error",
            "text": f"Erreur: {str(e)}",
        }


def _try_direct_parse(message: str) -> dict:
    """BUG 4 FIX — Fallback: parse simple requests without LLM"""
    import re
    msg = message.lower().strip()

    # Détecter une référence cadastrale
    ref_match = re.search(r'(\d{5,}[A-Z]{1,2}\d{3,})', message.upper().replace(" ", "").replace("-", ""))
    if ref_match:
        return {"action": "analyze_parcel", "params": {"ref": ref_match.group(1), "mw_target": 10}, "intro": "Analyse de la parcelle en cours..."}

    # Détecter une adresse (rue + numéro)
    addr_match = re.search(r'(\d+\s+(?:rue|avenue|allée|boulevard|chemin|impasse|route|place|cours|quai)\s+[^\d]+\d{5})', msg)
    if addr_match:
        return {"action": "find_by_address", "params": {"address": addr_match.group(1)}, "intro": "Recherche autour de l'adresse..."}

    # Budget / CAPEX / estimation
    if any(word in msg for word in ["budget", "capex", "coût", "combien", "estimation financ", "investissement"]):
        params = {"mw_target": 10}
        mw_match = re.search(r'(\d+)\s*mw', msg)
        if mw_match:
            params["mw_target"] = int(mw_match.group(1))
        # Check for commune
        for prefix in ["à ", "près de ", "pour "]:
            if prefix in msg:
                commune = msg.split(prefix)[1].split(" pour")[0].split(" de ")[0].strip().rstrip(".,;!?")
                if len(commune) > 2:
                    params["commune"] = commune
                    break
        return {"action": "estimate_budget", "params": params, "intro": "Estimation budgétaire en cours..."}

    if any(word in msg for word in ["parcelle", "terrain", "trouve", "cherche", "propose"]):
        params = {"min_surface_ha": 1.0, "nb_parcels": 10}

        # Détecter la région
        region_map = {
            "paca": "PACA", "marseille": "PACA", "fos": "PACA", "provence": "PACA",
            "idf": "IDF", "paris": "IDF", "île-de-france": "IDF",
            "nord": "HdF", "lille": "HdF", "hauts-de-france": "HdF",
            "lyon": "AuRA", "auvergne": "AuRA",
            "bretagne": "BRE", "rennes": "BRE",
            "nantes": "PDL", "pays de la loire": "PDL",
        }
        for key, region in region_map.items():
            if key in msg:
                params["region"] = region
                break

        # Détecter la surface
        ha_match = re.search(r'(\d+)\s*(?:ha|hectare)', msg)
        if ha_match:
            params["min_surface_ha"] = float(ha_match.group(1))

        # Détecter une commune spécifique
        for prefix in ["à ", "près de ", "autour de ", "commune de "]:
            if prefix in msg:
                commune = msg.split(prefix)[1].split(" pour")[0].split(" de ")[0].strip().rstrip(".,;!?")
                if len(commune) > 2:
                    params["commune"] = commune
                    break

        return {"action": "find_parcels", "params": params, "intro": "Recherche en cours (mode direct)..."}

    return None


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
