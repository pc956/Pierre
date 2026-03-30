"""
Cockpit Immo - FastAPI Backend
DC Land Prospection Platform with Google OAuth
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

from models import (
    User, UserSession, Tenant, Parcel, ParcelScore, 
    Shortlist, ShortlistItem, Alert, Verdict
)
from scoring import compute_score_simple
from seed_data import get_seed_data
from api_carto import (
    search_communes, get_parcelles_by_commune, get_parcelles_by_bbox,
    get_parcelles_around_point, get_sections_by_commune, parse_parcelle_feature,
    get_gpu_zone_urba_for_point, get_gpu_zones_for_bbox, get_gpu_full_context
)
from france_infra_data import get_all_france_infra
from s3renr_data import S3RENR_DATA, get_s3renr_top_opportunities
from dc_search_api import dc_search, dc_get_site
from gpt_agent_config import get_openapi_schema, COCKPIT_IMMO_GPT_SYSTEM_PROMPT
from chat_assistant import process_chat_message
from dvf_data import get_dvf_for_commune, get_dvf_for_region
from pdf_export import generate_parcel_pdf
from rte_future_line import (
    get_future_line_geojson, distance_to_future_line, get_buffer_zone,
    score_future_400kv, compute_future_grid_potential
)
from plu_scoring import score_plu, parse_reglement_keywords, score_plu_dynamic

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create indexes
async def create_indexes():
    # Parcels geospatial index
    await db.parcels.create_index([("centroid", "2dsphere")])
    await db.parcels.create_index("parcel_id", unique=True)
    await db.parcels.create_index("region")
    await db.parcels.create_index("commune")
    
    # Scores
    await db.parcel_scores.create_index([("parcel_id", 1), ("is_latest", 1)])
    await db.parcel_scores.create_index("score")
    
    # Users
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    
    # Sessions
    await db.user_sessions.create_index("session_token")
    await db.user_sessions.create_index("user_id")

app = FastAPI(title="Cockpit Immo API", version="1.0.0")
api_router = APIRouter(prefix="/api")


# ═══════════════════════════════════════════════════════════
# PYDANTIC MODELS FOR API
# ═══════════════════════════════════════════════════════════

class SessionRequest(BaseModel):
    session_id: str

class SearchRequest(BaseModel):
    mw_target: Optional[float] = None
    budget_max: Optional[float] = None
    ttm_max: Optional[int] = None
    regions: Optional[List[str]] = None
    score_min: Optional[float] = None
    bbox: Optional[List[float]] = None  # [min_lng, min_lat, max_lng, max_lat]

class ShortlistCreate(BaseModel):
    nom: str
    description: Optional[str] = None

class ShortlistItemCreate(BaseModel):
    parcel_id: str
    notes: Optional[str] = None

class ShortlistItemUpdate(BaseModel):
    statut: Optional[str] = None
    interlocuteur: Optional[str] = None
    prix_offert_eur: Optional[float] = None
    notes: Optional[str] = None


# ═══════════════════════════════════════════════════════════
# AUTH HELPERS
# ═══════════════════════════════════════════════════════════

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token (cookie or header)"""
    # Try cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
    if not session_token:
        return None
    
    # Find session
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session_doc:
        return None
    
    # Check expiry
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    
    # Get user
    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]},
        {"_id": 0}
    )
    
    if not user_doc:
        return None
    
    return User(**user_doc)


async def require_auth(request: Request) -> User:
    """Require authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# ═══════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════

@api_router.post("/auth/session")
async def create_session(req: SessionRequest, response: Response):
    """
    Exchange session_id from Emergent Auth for session_token
    REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    """
    try:
        # Call Emergent Auth to get user data
        async with httpx.AsyncClient() as client_http:
            auth_response = await client_http.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": req.session_id}
            )
        
        if auth_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session_id")
        
        auth_data = auth_response.json()
        email = auth_data["email"]
        name = auth_data["name"]
        picture = auth_data.get("picture")
        session_token = auth_data["session_token"]
        
        # Find or create user
        existing_user = await db.users.find_one({"email": email}, {"_id": 0})
        
        if existing_user:
            user_id = existing_user["user_id"]
            # Update user data
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"name": name, "picture": picture}}
            )
        else:
            # Create new user
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            
            # Create or find default tenant
            default_tenant = await db.tenants.find_one({"nom": "Default"}, {"_id": 0})
            if not default_tenant:
                tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
                await db.tenants.insert_one({
                    "tenant_id": tenant_id,
                    "nom": "Default",
                    "plan": "free",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
            else:
                tenant_id = default_tenant["tenant_id"]
            
            user_doc = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "role": "consultant",
                "tenant_id": tenant_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(user_doc)
        
        # Create session
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        session_doc = {
            "session_id": f"sess_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Remove old sessions for this user
        await db.user_sessions.delete_many({"user_id": user_id})
        await db.user_sessions.insert_one(session_doc)
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=7 * 24 * 60 * 60,
            path="/"
        )
        
        # Get user for response
        user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        
        return {
            "success": True,
            "user": user_doc
        }
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=500, detail=f"Auth service error: {str(e)}")


@api_router.get("/auth/me")
async def get_me(request: Request):
    """Get current authenticated user"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user.model_dump()


@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# PARCELS ENDPOINTS
# ═══════════════════════════════════════════════════════════

@api_router.get("/parcels")
async def get_parcels(
    request: Request,
    region: Optional[str] = None,
    score_min: Optional[float] = None,
    limit: int = 100,
    skip: int = 0
):
    """Get parcels with optional filters"""
    query = {}
    
    if region:
        query["region"] = region
    
    parcels = await db.parcels.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    if not parcels:
        return {"parcels": [], "count": 0}
    
    # Batch fetch scores using $in operator (optimized — no N+1)
    parcel_ids = [p["parcel_id"] for p in parcels]
    score_docs = await db.parcel_scores.find(
        {"parcel_id": {"$in": parcel_ids}, "is_latest": True},
        {"_id": 0}
    ).to_list(len(parcel_ids))
    score_map = {s["parcel_id"]: s for s in score_docs}
    
    result = []
    for parcel in parcels:
        score_doc = score_map.get(parcel["parcel_id"])
        if score_min and score_doc and score_doc.get("score_net", 0) < score_min:
            continue
        result.append({**parcel, "score": score_doc})
    
    return {"parcels": result, "count": len(result)}


@api_router.get("/parcels/{parcel_id}")
async def get_parcel(parcel_id: str):
    """Get single parcel with all details"""
    parcel = await db.parcels.find_one({"parcel_id": parcel_id}, {"_id": 0})
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # Get all scores
    scores = await db.parcel_scores.find(
        {"parcel_id": parcel_id, "is_latest": True},
        {"_id": 0}
    ).to_list(10)
    
    return {
        **parcel,
        "score": scores[0] if scores else {}
    }


@api_router.get("/parcels/{parcel_id}/score")
async def get_parcel_score(parcel_id: str):
    """Get or compute score for parcel and project type"""
    # Check if score exists
    score_doc = await db.parcel_scores.find_one(
        {"parcel_id": parcel_id, "is_latest": True},
        {"_id": 0}
    )
    
    if score_doc:
        return score_doc
    
    # Compute score
    parcel = await db.parcels.find_one({"parcel_id": parcel_id}, {"_id": 0})
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    score_data = compute_score_simple(parcel)
    score_data["parcel_id"] = parcel_id
    score_data["score_id"] = f"score_{uuid.uuid4().hex[:12]}"
    score_data["computed_at"] = datetime.now(timezone.utc).isoformat()
    score_data["is_latest"] = True
    
    await db.parcel_scores.insert_one(score_data)
    
    return score_data


@api_router.post("/search/project")
async def search_project(req: SearchRequest, request: Request):
    """Search parcels for a specific project"""
    query = {}
    
    if req.regions:
        query["region"] = {"$in": req.regions}
    
    if req.bbox and len(req.bbox) == 4:
        # GeoJSON query
        query["centroid"] = {
            "$geoWithin": {
                "$box": [
                    [req.bbox[0], req.bbox[1]],
                    [req.bbox[2], req.bbox[3]]
                ]
            }
        }
    
    parcels = await db.parcels.find(query, {"_id": 0}).limit(500).to_list(500)
    
    results = []
    for parcel in parcels:
        # Get or compute score
        score_doc = await db.parcel_scores.find_one(
            {"parcel_id": parcel["parcel_id"], "is_latest": True},
            {"_id": 0}
        )
        
        if not score_doc:
            score_data = compute_score_simple(parcel)
            score_data["parcel_id"] = parcel["parcel_id"]
            score_data["score_id"] = f"score_{uuid.uuid4().hex[:12]}"
            score_data["computed_at"] = datetime.now(timezone.utc).isoformat()
            score_data["is_latest"] = True
            await db.parcel_scores.insert_one(score_data)
            score_doc = score_data
        
        # Apply filters
        if req.score_min and score_doc.get("score", score_doc.get("score_net", 0)) < req.score_min:
            continue
        if req.ttm_max and score_doc.get("ttm_max_months", 999) > req.ttm_max:
            continue
        if req.budget_max and score_doc.get("capex_p50", 0) > req.budget_max:
            continue
        
        results.append({
            **parcel,
            "score": score_doc
        })
    
    # Sort by score
    results.sort(key=lambda x: x.get("score", {}).get("score_net", 0), reverse=True)
    
    # Compute stats
    best_ttm = min((r["score"].get("ttm_min_months", 999) for r in results), default=None)
    best_irr = max((r["score"].get("irr_levered_pct", 0) for r in results), default=None)
    
    return {
        "sites": results[:100],
        "count": len(results),
        "best_ttm": best_ttm,
        "best_irr": best_irr
    }


@api_router.post("/compare")
async def compare_parcels(parcel_ids: List[str]):
    """Compare multiple parcels side by side"""
    results = []
    
    for pid in parcel_ids[:4]:  # Max 4 parcels
        parcel = await db.parcels.find_one({"parcel_id": pid}, {"_id": 0})
        if not parcel:
            continue
        
        score_doc = await db.parcel_scores.find_one(
            {"parcel_id": pid, "is_latest": True},
            {"_id": 0}
        )
        
        if not score_doc:
            score_data = compute_score_simple(parcel)
            score_data["parcel_id"] = pid
            score_data["score_id"] = f"score_{uuid.uuid4().hex[:12]}"
            score_data["computed_at"] = datetime.now(timezone.utc).isoformat()
            score_data["is_latest"] = True
            await db.parcel_scores.insert_one(score_data)
            score_doc = score_data
        
        results.append({
            "parcel": parcel,
            "score": score_doc
        })
    
    return {"comparisons": results}


# ═══════════════════════════════════════════════════════════
# MAP ENDPOINTS - Serve nationwide infrastructure from in-memory data
# ═══════════════════════════════════════════════════════════

# Load France infrastructure once at import time
_FRANCE_INFRA = get_all_france_infra()

# ── S3REnR Enrichment: merge capacity data into HTB postes ──
def _normalize(name):
    """Normalize a poste name for fuzzy matching — with accent stripping"""
    import re
    import unicodedata
    n = name.upper()
    # Strip accents: Réaltor → REALTOR, Lavéra → LAVERA, Jonquières → JONQUIERES
    n = ''.join(c for c in unicodedata.normalize('NFD', n) if unicodedata.category(c) != 'Mn')
    n = n.replace("POSTE ", "").replace("-", " ").replace("'", " ")
    # Strip common OSM prefixes
    for prefix in ["LA ", "LE ", "LES ", "L ", "D ", "DE ", "DES ", "DU "]:
        if n.startswith(prefix):
            n = n[len(prefix):]
    n = re.sub(r'\d+KV', '', n).strip()
    n = re.sub(r'\s+\d+$', '', n).strip()
    # Postes génériques sans vrai nom → ne pas matcher
    if not n or len(n) < 2:
        return "__GENERIC_NO_MATCH__"
    return n

# Region mapping: france_infra_data region -> S3REnR region key
_REGION_MAP = {
    "IDF": "IDF",
    "PACA": "PACA",
    "HdF": "HdF",
}

def _build_s3renr_lookup():
    """Build a lookup dict: normalized_name -> s3renr_data for each region"""
    lookup = {}
    for region_key, region_data in S3RENR_DATA.items():
        for poste_name, poste_data in region_data.get("postes", {}).items():
            norm = _normalize(poste_name)
            lookup[(region_key, norm)] = {
                "s3renr_region": region_key,
                "s3renr_poste": poste_name,
                **poste_data,
            }
            # Also store without region for partial matches
            if norm not in lookup:
                lookup[("ANY", norm)] = {
                    "s3renr_region": region_key,
                    "s3renr_poste": poste_name,
                    **poste_data,
                }
    return lookup

_S3RENR_LOOKUP = _build_s3renr_lookup()

def _enrich_poste_with_s3renr(poste):
    """Try to match a HTB poste with S3REnR data and return enriched copy"""
    region = poste.get("region", "")
    s3renr_region = _REGION_MAP.get(region)
    norm_name = _normalize(poste.get("nom", ""))
    
    s3renr = None
    # Try exact region match first
    if s3renr_region:
        s3renr = _S3RENR_LOOKUP.get((s3renr_region, norm_name))
    # Try any region match
    if not s3renr:
        s3renr = _S3RENR_LOOKUP.get(("ANY", norm_name))
    # Try partial: check if any s3renr poste name is contained in the HTB name
    if not s3renr and s3renr_region:
        for poste_name, poste_data in S3RENR_DATA.get(s3renr_region, {}).get("postes", {}).items():
            if _normalize(poste_name) in norm_name or norm_name in _normalize(poste_name):
                s3renr = {"s3renr_region": s3renr_region, "s3renr_poste": poste_name, **poste_data}
                break
    
    enriched = {**poste}
    if s3renr:
        enriched["s3renr"] = {
            "region": s3renr.get("s3renr_region"),
            "poste_s3renr": s3renr.get("s3renr_poste"),
            "mw_reserve": s3renr.get("mw_reserve", 0),
            "mw_consomme": s3renr.get("mw_consomme", 0),
            "mw_dispo": s3renr.get("mw_dispo", 0),
            "etat": s3renr.get("etat", "inconnu"),
            "renforcement": s3renr.get("renforcement"),
            "score_dc": s3renr.get("score_dc", 0),
            "tension_kv": s3renr.get("tension_kv"),
        }
    else:
        # For postes in regions covered by S3REnR but no match, mark as "non référencé"
        if s3renr_region and s3renr_region in S3RENR_DATA:
            region_status = S3RENR_DATA[s3renr_region].get("status_global", "")
            enriched["s3renr"] = {
                "region": s3renr_region,
                "etat": "sature" if region_status == "SATURE" else "non_reference",
                "mw_dispo": 0 if region_status == "SATURE" else None,
                "note": f"Région {s3renr_region}: {region_status}" if region_status == "SATURE" else None,
            }
    return enriched

@api_router.get("/map/parcels")
async def get_map_parcels(
    min_lng: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lng: Optional[float] = None,
    max_lat: Optional[float] = None
):
    """Get parcels for map display"""
    query = {}
    
    if all([min_lng, min_lat, max_lng, max_lat]):
        query["centroid"] = {
            "$geoWithin": {
                "$box": [[min_lng, min_lat], [max_lng, max_lat]]
            }
        }
    
    parcels = await db.parcels.find(
        query,
        {"_id": 0, "parcel_id": 1, "commune": 1, "centroid": 1, "surface_ha": 1, "region": 1}
    ).limit(500).to_list(500)
    
    # Get scores
    parcel_ids = [p["parcel_id"] for p in parcels]
    scores = await db.parcel_scores.find(
        {"parcel_id": {"$in": parcel_ids}, "is_latest": True},
        {"_id": 0, "parcel_id": 1, "score": 1, "verdict": 1}
    ).to_list(500)
    
    score_map = {s["parcel_id"]: s for s in scores}
    
    result = []
    for p in parcels:
        score = score_map.get(p["parcel_id"], {})
        result.append({
            **p,
            "score": score.get("score", 0),
            "verdict": score.get("verdict", "A_ETUDIER"),
        })
    
    return {"parcels": result}


@api_router.get("/map/dc")
async def get_map_dc():
    """Get all DC existants for map - nationwide from in-memory data"""
    return {"dc_existants": _FRANCE_INFRA["dc_existants"]}


@api_router.get("/map/landing-points")
async def get_map_landing_points():
    """Get all landing points for map - nationwide from in-memory data"""
    return {"landing_points": _FRANCE_INFRA["landing_points"]}


@api_router.get("/map/submarine-cables")
async def get_map_submarine_cables():
    """Get all submarine cables for map - nationwide from in-memory data"""
    return {"submarine_cables": _FRANCE_INFRA["submarine_cables"]}


@api_router.get("/map/electrical-assets")
async def get_map_electrical_assets(asset_type: Optional[str] = None):
    """Get electrical assets (postes HTB, lignes 400kV, lignes 225kV) for map - nationwide
    Postes HTB are enriched with S3REnR capacity/saturation data when available."""
    postes = [_enrich_poste_with_s3renr(p) for p in _FRANCE_INFRA["postes_htb"]]
    lignes = _FRANCE_INFRA["lignes_400kv"] + _FRANCE_INFRA["lignes_225kv"]
    
    all_assets = postes + lignes
    if asset_type:
        all_assets = [a for a in all_assets if a.get("type") == asset_type]
    return {"electrical_assets": all_assets}


@api_router.get("/map/rte-future-400kv")
async def get_rte_future_line():
    """Get the future RTE 400kV line Fos→Jonquières with buffer zones for map display"""
    return get_future_line_geojson()


class PLUScoringRequest(BaseModel):
    zone_code: str
    zone_label: str = ""
    is_brownfield: bool = False
    is_zac_zip_port: bool = False
    reglement_allows_equipment: bool = False
    urbanisation_conditionnee: bool = False
    proximite_habitat: bool = False
    contrainte_patrimoniale: bool = False
    risque_reglementaire_majeur: bool = False
    reglement_text: Optional[str] = None


@api_router.post("/scoring/plu")
async def score_plu_endpoint(req: PLUScoringRequest):
    """Score PLU compatibility for a data center project"""
    return score_plu(
        zone_code=req.zone_code,
        zone_label=req.zone_label,
        is_brownfield=req.is_brownfield,
        is_zac_zip_port=req.is_zac_zip_port,
        reglement_allows_equipment=req.reglement_allows_equipment,
        urbanisation_conditionnee=req.urbanisation_conditionnee,
        proximite_habitat=req.proximite_habitat,
        contrainte_patrimoniale=req.contrainte_patrimoniale,
        risque_reglementaire_majeur=req.risque_reglementaire_majeur,
        reglement_text=req.reglement_text,
    )


@api_router.get("/scoring/plu/{zone_code}")
async def score_plu_quick(zone_code: str):
    """Quick PLU scoring by zone code only"""
    return score_plu(zone_code=zone_code)


@api_router.get("/scoring/plu-dynamic")
async def score_plu_dynamic_endpoint(lon: float, lat: float):
    """Dynamic PLU scoring using real GPU API data for a geographic point"""
    gpu_ctx = await get_gpu_full_context(lon, lat)
    if not gpu_ctx.get("zone"):
        return {
            "plu_code": "inconnu",
            "plu_label": "Données GPU non disponibles",
            "plu_score": 40,
            "plu_status": "REVIEW",
            "exclusion_reason": None,
            "flags": ["gpu_data_unavailable"],
            "urbanism_risk": "indetermine",
            "recommended_action": "manual_review",
            "gpu_source": "unavailable",
        }
    return score_plu_dynamic(gpu_ctx)


@api_router.get("/s3renr/top-opportunities")
async def get_s3renr_opportunities(min_mw: int = 30, limit: int = 20):
    """Get top S3REnR opportunities for DC siting, sorted by MW available"""
    opportunities = get_s3renr_top_opportunities(min_mw=min_mw, limit=limit)
    
    # Add region-level metadata
    regions_meta = {}
    for region_key, region_data in S3RENR_DATA.items():
        regions_meta[region_key] = {
            "status_global": region_data.get("status_global"),
            "capacite_globale_mw": region_data.get("capacite_globale_mw"),
            "taux_consommation_pct": region_data.get("taux_consommation_pct"),
        }
    
    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "regions": regions_meta,
    }


@api_router.get("/s3renr/summary")
async def get_s3renr_summary():
    """Get S3REnR summary stats per region"""
    summary = []
    for region_key, region_data in S3RENR_DATA.items():
        postes = region_data.get("postes", {})
        total_dispo = sum(p.get("mw_dispo", 0) for p in postes.values())
        total_reserve = sum(p.get("mw_reserve", 0) for p in postes.values())
        nb_satures = sum(1 for p in postes.values() if p.get("etat") == "sature")
        nb_disponibles = sum(1 for p in postes.values() if p.get("etat") == "disponible")
        nb_contraints = sum(1 for p in postes.values() if p.get("etat") == "contraint")
        summary.append({
            "region": region_key,
            "status_global": region_data.get("status_global"),
            "capacite_globale_mw": region_data.get("capacite_globale_mw"),
            "mw_dispo_total": total_dispo,
            "mw_reserve_total": total_reserve,
            "nb_postes": len(postes),
            "nb_disponibles": nb_disponibles,
            "nb_contraints": nb_contraints,
            "nb_satures": nb_satures,
        })
    return {"summary": summary}



# ═══════════════════════════════════════════════════════════
# DC SEARCH API — AI Agent Endpoints
# ═══════════════════════════════════════════════════════════

class DCSearchRequest(BaseModel):
    mw_target: float = Field(default=20, description="Puissance cible en MW")
    mw_min: float = Field(default=5, description="Puissance minimum acceptable en MW")
    max_delay_months: int = Field(default=36, description="Délai max de raccordement en mois")
    surface_min_ha: float = Field(default=0, description="Surface minimum en hectares")
    region: Optional[str] = Field(default=None, description="Région (ex: IDF, PACA, HdF)")
    max_distance_substation_km: float = Field(default=100, description="Distance max au poste source")
    strategy: str = Field(default="balanced", description="Stratégie: speed, cost, power, balanced")
    grid_priority: bool = Field(default=False, description="Prioriser accès réseau")
    brownfield_only: bool = Field(default=False, description="Uniquement terrains brownfield")
    page: int = Field(default=1, description="Page de résultats")
    per_page: int = Field(default=10, description="Résultats par page (max 50)")


@api_router.post("/dc/search")
async def search_dc_sites(request: DCSearchRequest):
    """
    AI Agent endpoint — Search for data center sites.
    Accepts structured criteria and returns scored, ranked results.
    Designed for ChatGPT, Claude, or any conversational AI agent.
    
    Example: "Trouve-moi 3 terrains pour un DC de 20MW en IDF en moins de 12 mois"
    """
    params = request.model_dump()
    
    # Log the search for analytics
    logger.info(f"DC Search: mw={params['mw_target']}, region={params.get('region')}, strategy={params['strategy']}")
    
    # Store query in MongoDB for analytics
    try:
        db.dc_search_logs.insert_one({
            "params": params,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "api",
        })
    except Exception:
        pass
    
    result = dc_search(params)
    return result


@api_router.get("/dc/site/{site_id}")
async def get_dc_site_detail(site_id: str):
    """
    AI Agent endpoint — Get full details for a specific site.
    Returns complete site info including grid, timeline, urbanism, and scoring.
    """
    site = dc_get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    return site




# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# DVF (Demandes de Valeurs Foncières) ENDPOINTS
# ═══════════════════════════════════════════════════════════

@api_router.get("/dvf/commune/{code_insee}")
async def get_dvf_commune(code_insee: str):
    """Get DVF price data for a commune (€/m² terrain)"""
    return get_dvf_for_commune(code_insee)


@api_router.get("/dvf/region/{region}")
async def get_dvf_region(region: str):
    """Get aggregated DVF price data for a region"""
    return get_dvf_for_region(region)


# ═══════════════════════════════════════════════════════════
# PDF EXPORT ENDPOINTS
# ═══════════════════════════════════════════════════════════

@api_router.post("/export/pdf")
async def export_parcel_pdf(parcel: Dict[str, Any]):
    """Generate a PDF fiche for a parcel or DC site"""
    from starlette.responses import Response
    import traceback
    try:
        code_insee = parcel.get("code_commune", "")
        code_dep = parcel.get("departement", "") or parcel.get("code_dep", "")
        dvf = None
        if code_insee:
            dvf = get_dvf_for_commune(code_insee)
        elif code_dep:
            dvf = get_dvf_for_commune(code_dep + "000")
        pdf_bytes = generate_parcel_pdf(parcel, dvf)
        commune = parcel.get("commune") or parcel.get("name") or "site"
        filename = f"cockpit_immo_{commune.replace(' ', '_')}.pdf"
        return Response(content=pdf_bytes, media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    except Exception as e:
        import logging
        logging.getLogger("server").error(f"PDF export error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur PDF: {str(e)}")


@api_router.post("/export/pdf/dc-site")
async def export_dc_site_pdf(request: Dict[str, Any]):
    """Generate PDF fiche for a DC site (from search results)"""
    from starlette.responses import Response
    
    site_id = request.get("site_id", "")
    site = dc_get_site(site_id)
    if not site:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    
    # Get DVF data for the site's region
    region = site.get("location", {}).get("region", "")
    dvf = get_dvf_for_region(region) if region else None
    
    # Convert DVF region data to parcel-compatible format
    dvf_parcel = None
    if dvf and not dvf.get("error"):
        dvf_parcel = {
            "prix_median_m2": dvf.get("prix_moyen_pondere_m2", 65),
            "prix_q1_m2": dvf.get("prix_min_m2", 35),
            "prix_q3_m2": dvf.get("prix_max_m2", 110),
            "nb_transactions": dvf.get("nb_transactions_total", 0),
            "source": f"DVF {region} ({dvf.get('nb_departements', 0)} départements)",
        }
    
    pdf_bytes = generate_parcel_pdf(site, dvf_parcel)
    
    city = site.get("location", {}).get("city", "site")
    filename = f"cockpit_immo_DC_{city.replace(' ', '_')}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# AI CHAT ASSISTANT ENDPOINT
# ═══════════════════════════════════════════════════════════

class ChatMessage(BaseModel):
    message: str = Field(..., description="User message in natural language")
    session_id: str = Field(default="default", description="Chat session ID")
    history: List[Dict[str, str]] = Field(default=[], description="Recent chat history")


@api_router.post("/chat")
async def chat_endpoint(req: ChatMessage):
    """
    AI Chat Assistant — processes natural language queries about DC sites.
    Parses user intent, calls the search API, and returns structured results + map coordinates.
    """
    result = await process_chat_message(
        message=req.message,
        session_id=req.session_id,
        history=req.history,
    )
    
    # Log chat for analytics
    try:
        db.chat_logs.insert_one({
            "session_id": req.session_id,
            "message": req.message,
            "response_type": result.get("type"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:
        pass
    
    return result


# ═══════════════════════════════════════════════════════════
# GPT AGENT CONFIGURATION ENDPOINTS
# ═══════════════════════════════════════════════════════════

@api_router.get("/gpt/openapi-schema")
async def get_gpt_openapi_schema(request: Request):
    """Returns the OpenAPI 3.1.0 schema for ChatGPT Custom GPT Actions"""
    # Use X-Forwarded headers for proper external URL behind proxy
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    if forwarded_host:
        server_url = f"{forwarded_proto}://{forwarded_host}"
    else:
        server_url = str(request.base_url).rstrip("/")
    return get_openapi_schema(server_url)


@api_router.get("/gpt/system-prompt")
async def get_gpt_system_prompt():
    """Returns the system prompt for the custom GPT"""
    return {"system_prompt": COCKPIT_IMMO_GPT_SYSTEM_PROMPT}


@api_router.get("/gpt/config")
async def get_gpt_config(request: Request):
    """Returns full GPT configuration (schema + prompt + instructions)"""
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    if forwarded_host:
        server_url = f"{forwarded_proto}://{forwarded_host}"
    else:
        server_url = str(request.base_url).rstrip("/")
    return {
        "name": "Cockpit Immo — Expert DC France",
        "description": "Expert en prospection foncière pour data centers en France. Interroge les capacités électriques S3REnR, les données cadastrales IGN, et les zones PLU pour identifier les meilleurs terrains.",
        "system_prompt": COCKPIT_IMMO_GPT_SYSTEM_PROMPT,
        "openapi_schema_url": f"{server_url}/api/gpt/openapi-schema",
        "actions_server_url": server_url,
        "setup_instructions": {
            "step_1": "Aller sur https://chatgpt.com/gpts/editor",
            "step_2": "Copier le System Prompt ci-dessous dans le champ 'Instructions'",
            "step_3": "Aller dans l'onglet 'Configure' > 'Actions' > 'Create new action'",
            "step_4": f"Dans 'Import from URL', coller: {server_url}/api/gpt/openapi-schema",
            "step_5": "Authentication: sélectionner 'None' (API publique)",
            "step_6": "Cliquer 'Save' puis tester avec: 'Trouve-moi un terrain pour un DC de 20MW en PACA'",
        },
    }


# ═══════════════════════════════════════════════════════════
# API CARTO ENDPOINTS (French Cadastre - All France)
# ═══════════════════════════════════════════════════════════

@api_router.get("/france/communes")
async def search_french_communes(q: str, limit: int = 20):
    """Search French communes by name"""
    if len(q) < 2:
        return {"communes": []}
    
    communes = await search_communes(q, limit)
    return {"communes": communes}


@api_router.get("/france/parcelles/commune/{code_insee}")
async def get_commune_parcelles(code_insee: str, section: Optional[str] = None):
    """
    Get all parcelles for a French commune from API Carto
    Warning: Large communes can return thousands of parcels
    """
    data = await get_parcelles_by_commune(code_insee, section)
    
    # Parse features and compute scores
    parcelles = []
    for feature in data.get("features", [])[:500]:  # Limit to 500
        parsed = parse_parcelle_feature(feature)
        
        # Only include parcels > 0.5 ha for DC relevance
        if parsed["surface_ha"] >= 0.5 and parsed.get("centroid"):
            plat = parsed["latitude"]
            plon = parsed["longitude"]
            
            # Find nearest HTB post
            min_dist_htb = 999999
            nearest_htb_kv = 0
            nearest_htb_name = ""
            for htb in _FRANCE_INFRA["postes_htb_all"]:
                hcoords = htb["geometry"]["coordinates"]
                dist = _haversine(plon, plat, hcoords[0], hcoords[1])
                if dist < min_dist_htb:
                    min_dist_htb = dist
                    nearest_htb_kv = htb["tension_kv"]
                    nearest_htb_name = htb.get("nom", "")
            
            # Find nearest landing point
            min_dist_lp = 999999
            nearest_lp_name = ""
            nearest_lp_cables = 0
            for lp in _FRANCE_INFRA["landing_points"]:
                lcoords = lp["geometry"]["coordinates"]
                dist = _haversine(plon, plat, lcoords[0], lcoords[1])
                if dist < min_dist_lp:
                    min_dist_lp = dist
                    nearest_lp_name = lp["nom"]
                    nearest_lp_cables = lp["nb_cables_connectes"]
            
            parsed["dist_poste_htb_m"] = int(min_dist_htb)
            parsed["tension_htb_kv"] = nearest_htb_kv
            parsed["nearest_htb_name"] = nearest_htb_name
            parsed["dist_landing_point_km"] = round(min_dist_lp / 1000, 1)
            parsed["landing_point_nom"] = nearest_lp_name
            parsed["landing_point_nb_cables"] = nearest_lp_cables
            parsed["zone_saturation"] = "inconnu"
            
            # Future 400kV line distance & scoring
            dist_future_400kv = distance_to_future_line(plon, plat)
            parsed["dist_future_400kv_m"] = round(dist_future_400kv)
            parsed["future_400kv_buffer"] = get_buffer_zone(plon, plat)
            parsed["future_400kv_score_bonus"] = score_future_400kv(plon, plat)
            
            # Compute score (universel /100)
            try:
                score_data = compute_score_simple(parsed)
                bonus_400kv = score_future_400kv(plon, plat)
                score_data["score"] = min(100, score_data["score"] + bonus_400kv)
                parsed["score"] = score_data
            except Exception:
                parsed["score"] = {"score": 0, "verdict": "A_ETUDIER", "detail": {}, "flags": [], "resume": ""}
            
            parcelles.append(parsed)
    
    return {
        "parcelles": parcelles,
        "count": len(parcelles),
        "total_raw": len(data.get("features", [])),
        "source": "api_carto_ign"
    }


@api_router.get("/france/gpu-zones")
async def get_gpu_zones_endpoint(min_lon: float, min_lat: float, max_lon: float, max_lat: float):
    """Get GPU industrial/activity zones in bbox"""
    zones = await get_gpu_zones_for_bbox(min_lon, min_lat, max_lon, max_lat)
    industrial = []
    for z in zones:
        props = z.get("properties", {})
        typezone = (props.get("typezone") or "").upper()
        libelle = (props.get("libelle") or "").lower()
        destdomi = (props.get("destdomi") or "").lower()
        if typezone in ("UX", "UI", "UE", "IX", "I") or \
           "industriel" in libelle or "activit" in libelle or "économ" in libelle or \
           "industriel" in destdomi or "activit" in destdomi:
            industrial.append(z)
    return {"zones": industrial}



@api_router.get("/france/parcelles/bbox")
async def get_bbox_parcelles(
    min_lon: float, 
    min_lat: float, 
    max_lon: float, 
    max_lat: float,
    limit: int = 200
):
    """
    Get parcelles within a bounding box from API Carto
    Also fetches PLU zones from GPU API
    """
    import math
    import asyncio
    
    # Fetch parcels and GPU zones in parallel
    parcels_task = get_parcelles_by_bbox(min_lon, min_lat, max_lon, max_lat, limit)
    gpu_task = get_gpu_zones_for_bbox(min_lon, min_lat, max_lon, max_lat)
    
    data, gpu_zones = await asyncio.gather(parcels_task, gpu_task)
    
    # Build a simple lookup: for each GPU zone, store its typezone/libelle and centroid
    # We'll assign each parcel the PLU of the nearest GPU zone (or containing zone)
    gpu_zone_list = []
    for gz in gpu_zones[:500]:  # Limit zones processed
        gz_props = gz.get("properties", {})
        gz_geom = gz.get("geometry", {})
        gz_type = gz_props.get("typezone", "")
        gz_libelle = gz_props.get("libelle", "")
        gz_libelong = gz_props.get("libelong", "")
        # Compute centroid of GPU zone for proximity matching
        gz_centroid = _get_geom_centroid(gz_geom)
        if gz_centroid:
            gpu_zone_list.append({
                "typezone": gz_type,
                "libelle": gz_libelle,
                "libelong": gz_libelong,
                "lon": gz_centroid[0],
                "lat": gz_centroid[1],
            })
    
    parcelles = []
    for feature in data.get("features", [])[:limit]:
        parsed = parse_parcelle_feature(feature)
        
        if parsed.get("centroid"):
            plat = parsed["latitude"]
            plon = parsed["longitude"]
            
            # Find nearest HTB post
            min_dist_htb = 999999
            nearest_htb_kv = 0
            for htb in _FRANCE_INFRA["postes_htb_all"]:
                hcoords = htb["geometry"]["coordinates"]
                dist = _haversine(plon, plat, hcoords[0], hcoords[1])
                if dist < min_dist_htb:
                    min_dist_htb = dist
                    nearest_htb_kv = htb["tension_kv"]
            
            # Find nearest landing point
            min_dist_lp = 999999
            nearest_lp_name = ""
            nearest_lp_cables = 0
            for lp in _FRANCE_INFRA["landing_points"]:
                lcoords = lp["geometry"]["coordinates"]
                dist = _haversine(plon, plat, lcoords[0], lcoords[1])
                if dist < min_dist_lp:
                    min_dist_lp = dist
                    nearest_lp_name = lp["nom"]
                    nearest_lp_cables = lp["nb_cables_connectes"]
            
            parsed["dist_poste_htb_m"] = int(min_dist_htb)
            parsed["tension_htb_kv"] = nearest_htb_kv
            parsed["dist_landing_point_km"] = round(min_dist_lp / 1000, 1)
            parsed["landing_point_nom"] = nearest_lp_name
            parsed["landing_point_nb_cables"] = nearest_lp_cables
            parsed["dist_backbone_fibre_m"] = 2000
            parsed["nb_operateurs_fibre"] = 2
            
            # DVF price data
            code_dep = parsed.get("departement", "")
            if code_dep:
                dvf = get_dvf_for_commune(code_dep + "000")
                parsed["dvf_prix_median_m2"] = dvf.get("prix_median_m2", 0)
                parsed["dvf_prix_q1_m2"] = dvf.get("prix_q1_m2", 0)
                parsed["dvf_prix_q3_m2"] = dvf.get("prix_q3_m2", 0)
                parsed["dvf_source"] = dvf.get("source", "")
            
            # Assign PLU zone from GPU data (nearest zone)
            plu_zone = "inconnu"
            plu_libelle = ""
            plu_libelong = ""
            if gpu_zone_list:
                min_dist_plu = 999999
                for gz in gpu_zone_list:
                    d = math.sqrt((plon - gz["lon"])**2 + (plat - gz["lat"])**2)
                    if d < min_dist_plu:
                        min_dist_plu = d
                        plu_zone = gz["typezone"] or "inconnu"
                        plu_libelle = gz["libelle"]
                        plu_libelong = gz["libelong"]
            
            parsed["plu_zone"] = plu_zone
            parsed["plu_libelle"] = plu_libelle
            parsed["plu_libelong"] = plu_libelong
            parsed["zone_saturation"] = "inconnu"
            
            # PLU Scoring — Composite: try dynamic GPU first, fallback to static
            try:
                gpu_ctx = await get_gpu_full_context(plon, plat)
                if gpu_ctx.get("zone"):
                    plu_scoring_result = score_plu_dynamic(gpu_ctx)
                    # Override zone info with GPU data if richer
                    if gpu_ctx["zone"].get("typezone"):
                        parsed["plu_zone"] = gpu_ctx["zone"]["typezone"]
                    if gpu_ctx["zone"].get("libelle"):
                        parsed["plu_libelle"] = gpu_ctx["zone"]["libelle"]
                    if gpu_ctx["zone"].get("libelong"):
                        parsed["plu_libelong"] = gpu_ctx["zone"]["libelong"]
                else:
                    raise ValueError("GPU zone unavailable")
            except Exception:
                # Fallback to static scoring
                if plu_zone and plu_zone != "inconnu":
                    plu_scoring_result = score_plu(
                        zone_code=plu_zone,
                        zone_label=plu_libelle,
                        reglement_text=plu_libelong if plu_libelong else None,
                    )
                    plu_scoring_result["gpu_source"] = "static_from_zone"
                else:
                    plu_scoring_result = score_plu(zone_code="inconnu")
                    plu_scoring_result["gpu_source"] = "fallback"
            parsed["plu_scoring"] = plu_scoring_result
            
            # Future 400kV line distance & scoring
            dist_future_400kv = distance_to_future_line(plon, plat)
            parsed["dist_future_400kv_m"] = round(dist_future_400kv)
            parsed["future_400kv_buffer"] = get_buffer_zone(plon, plat)
            parsed["future_400kv_score_bonus"] = score_future_400kv(plon, plat)
            fgp = compute_future_grid_potential(
                plon, plat,
                dist_poste_htb_m=min_dist_htb,
            )
            parsed["future_grid_potential"] = fgp
            
            # Compute score (universel /100)
            try:
                score_data = compute_score_simple(parsed)
                bonus_400kv = score_future_400kv(plon, plat)
                score_data["score"] = min(100, score_data["score"] + bonus_400kv)
                parsed["score"] = score_data
            except Exception:
                parsed["score"] = {"score": 0, "verdict": "A_ETUDIER", "detail": {}, "flags": [], "resume": ""}
            
            parcelles.append(parsed)
    
    return {
        "parcelles": parcelles,
        "count": len(parcelles),
        "source": "api_carto_ign",
        "gpu_zones_count": len(gpu_zone_list),
    }


def _get_geom_centroid(geom):
    """Get centroid [lon, lat] from a GeoJSON geometry"""
    if not geom:
        return None
    coords = geom.get("coordinates", [])
    try:
        if geom["type"] == "Polygon" and coords and coords[0]:
            pts = coords[0]
            return [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]
        elif geom["type"] == "MultiPolygon" and coords and coords[0] and coords[0][0]:
            pts = coords[0][0]
            return [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]
    except (IndexError, TypeError, ZeroDivisionError):
        pass
    return None


def _haversine(lon1, lat1, lon2, lat2):
    """Calculate distance in meters between two GPS points"""
    import math
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


@api_router.get("/france/parcelles/around")
async def get_parcelles_around(
    lon: float,
    lat: float,
    radius_m: float = 2000
):
    """
    Get parcelles around a point (e.g., around a poste HTB or landing point)
    """
    data = await get_parcelles_around_point(lon, lat, radius_m, limit=100)
    
    parcelles = []
    for feature in data.get("features", []):
        parsed = parse_parcelle_feature(feature)
        
        if parsed["surface_ha"] >= 0.3:
            parcelles.append(parsed)
    
    return {
        "parcelles": parcelles,
        "count": len(parcelles),
        "center": {"lon": lon, "lat": lat},
        "radius_m": radius_m,
        "source": "api_carto_ign"
    }


@api_router.get("/france/sections/{code_insee}")
async def get_commune_sections(code_insee: str):
    """Get cadastral sections for a commune"""
    sections = await get_sections_by_commune(code_insee)
    
    return {
        "sections": [
            {
                "section": s.get("properties", {}).get("section", ""),
                "feuille": s.get("properties", {}).get("feuille", ""),
            }
            for s in sections
        ],
        "count": len(sections)
    }


# ═══════════════════════════════════════════════════════════
# CRM ENDPOINTS
# ═══════════════════════════════════════════════════════════

@api_router.get("/shortlists")
async def get_shortlists(request: Request):
    """Get user's shortlists"""
    user = await require_auth(request)
    
    shortlists = await db.shortlists.find(
        {"tenant_id": user.tenant_id},
        {"_id": 0}
    ).to_list(100)
    
    if not shortlists:
        return {"shortlists": []}
    
    # Batch count items per shortlist using aggregation (optimized — no N+1)
    sl_ids = [sl["shortlist_id"] for sl in shortlists]
    pipeline = [
        {"$match": {"shortlist_id": {"$in": sl_ids}}},
        {"$group": {"_id": "$shortlist_id", "count": {"$sum": 1}}},
    ]
    counts = await db.shortlist_items.aggregate(pipeline).to_list(len(sl_ids))
    count_map = {c["_id"]: c["count"] for c in counts}
    
    for sl in shortlists:
        sl["item_count"] = count_map.get(sl["shortlist_id"], 0)
    
    return {"shortlists": shortlists}


@api_router.post("/shortlists")
async def create_shortlist(req: ShortlistCreate, request: Request):
    """Create new shortlist"""
    user = await require_auth(request)
    
    shortlist = {
        "shortlist_id": f"sl_{uuid.uuid4().hex[:12]}",
        "tenant_id": user.tenant_id,
        "nom": req.nom,
        "description": req.description,
        "share_token": uuid.uuid4().hex,
        "created_by": user.user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.shortlists.insert_one(shortlist)
    return shortlist


@api_router.get("/shortlists/{shortlist_id}")
async def get_shortlist(shortlist_id: str, request: Request):
    """Get shortlist with items"""
    user = await require_auth(request)
    
    shortlist = await db.shortlists.find_one(
        {"shortlist_id": shortlist_id, "tenant_id": user.tenant_id},
        {"_id": 0}
    )
    
    if not shortlist:
        raise HTTPException(status_code=404, detail="Shortlist not found")
    
    items = await db.shortlist_items.find(
        {"shortlist_id": shortlist_id},
        {"_id": 0}
    ).to_list(100)
    
    if not items:
        return {**shortlist, "items": []}
    
    # Batch fetch parcel data and scores (optimized — no N+1)
    parcel_ids = [item["parcel_id"] for item in items]
    
    parcels_cursor = db.parcels.find(
        {"parcel_id": {"$in": parcel_ids}},
        {"_id": 0, "parcel_id": 1, "commune": 1, "region": 1, "surface_ha": 1}
    )
    parcels_list = await parcels_cursor.to_list(len(parcel_ids))
    parcel_map = {p["parcel_id"]: p for p in parcels_list}
    
    scores_cursor = db.parcel_scores.find(
        {"parcel_id": {"$in": parcel_ids}, "is_latest": True},
        {"_id": 0, "parcel_id": 1, "score": 1, "verdict": 1}
    )
    scores_list = await scores_cursor.to_list(len(parcel_ids))
    score_map = {s["parcel_id"]: s for s in scores_list}
    
    for item in items:
        pid = item["parcel_id"]
        parcel_data = parcel_map.get(pid)
        if parcel_data:
            item["parcel"] = {k: v for k, v in parcel_data.items() if k != "parcel_id"}
        score_data = score_map.get(pid)
        if score_data:
            item["score"] = {k: v for k, v in score_data.items() if k != "parcel_id"}
    
    return {**shortlist, "items": items}


@api_router.post("/shortlists/{shortlist_id}/items")
async def add_shortlist_item(shortlist_id: str, req: ShortlistItemCreate, request: Request):
    """Add parcel to shortlist"""
    user = await require_auth(request)
    
    # Verify shortlist exists and belongs to user's tenant
    shortlist = await db.shortlists.find_one(
        {"shortlist_id": shortlist_id, "tenant_id": user.tenant_id}
    )
    if not shortlist:
        raise HTTPException(status_code=404, detail="Shortlist not found")
    
    # Check if parcel already in shortlist
    existing = await db.shortlist_items.find_one(
        {"shortlist_id": shortlist_id, "parcel_id": req.parcel_id}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Parcel already in shortlist")
    
    item = {
        "item_id": f"sli_{uuid.uuid4().hex[:12]}",
        "shortlist_id": shortlist_id,
        "parcel_id": req.parcel_id,
        "statut": "a_analyser",
        "notes": req.notes,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.shortlist_items.insert_one(item)
    return item


@api_router.patch("/shortlists/{shortlist_id}/items/{item_id}")
async def update_shortlist_item(shortlist_id: str, item_id: str, req: ShortlistItemUpdate, request: Request):
    """Update shortlist item"""
    user = await require_auth(request)
    
    # Verify ownership
    shortlist = await db.shortlists.find_one(
        {"shortlist_id": shortlist_id, "tenant_id": user.tenant_id}
    )
    if not shortlist:
        raise HTTPException(status_code=404, detail="Shortlist not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if req.statut:
        update_data["statut"] = req.statut
    if req.interlocuteur:
        update_data["interlocuteur"] = req.interlocuteur
    if req.prix_offert_eur is not None:
        update_data["prix_offert_eur"] = req.prix_offert_eur
    if req.notes is not None:
        update_data["notes"] = req.notes
    
    await db.shortlist_items.update_one(
        {"item_id": item_id, "shortlist_id": shortlist_id},
        {"$set": update_data}
    )
    
    updated = await db.shortlist_items.find_one({"item_id": item_id}, {"_id": 0})
    return updated


@api_router.delete("/shortlists/{shortlist_id}/items/{item_id}")
async def delete_shortlist_item(shortlist_id: str, item_id: str, request: Request):
    """Remove item from shortlist"""
    user = await require_auth(request)
    
    shortlist = await db.shortlists.find_one(
        {"shortlist_id": shortlist_id, "tenant_id": user.tenant_id}
    )
    if not shortlist:
        raise HTTPException(status_code=404, detail="Shortlist not found")
    
    await db.shortlist_items.delete_one({"item_id": item_id, "shortlist_id": shortlist_id})
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# ALERTS ENDPOINTS
# ═══════════════════════════════════════════════════════════

@api_router.get("/alerts")
async def get_alerts(request: Request, unread: bool = False):
    """Get user's alerts"""
    user = await require_auth(request)
    
    query = {"tenant_id": user.tenant_id}
    if unread:
        query["lu"] = False
    
    alerts = await db.alerts.find(query, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return {"alerts": alerts, "unread_count": sum(1 for a in alerts if not a.get("lu", False))}


@api_router.patch("/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str, request: Request):
    """Mark alert as read"""
    user = await require_auth(request)
    
    await db.alerts.update_one(
        {"alert_id": alert_id, "tenant_id": user.tenant_id},
        {"$set": {"lu": True}}
    )
    return {"success": True}


# ═══════════════════════════════════════════════════════════
# ADMIN / SEED ENDPOINTS
# ═══════════════════════════════════════════════════════════

@api_router.post("/admin/seed")
async def seed_database():
    """Seed database with test data"""
    seed_data = get_seed_data()
    
    # Clear existing data
    await db.parcels.delete_many({})
    await db.parcel_scores.delete_many({})
    await db.dc_existants.delete_many({})
    await db.landing_points.delete_many({})
    await db.submarine_cables.delete_many({})
    await db.electrical_assets.delete_many({})
    
    # Insert parcels
    if seed_data["parcels"]:
        await db.parcels.insert_many(seed_data["parcels"])
    
    # Insert DC
    if seed_data["dc_existants"]:
        await db.dc_existants.insert_many(seed_data["dc_existants"])
    
    # Insert landing points
    if seed_data["landing_points"]:
        await db.landing_points.insert_many(seed_data["landing_points"])
    
    # Insert submarine cables
    if seed_data.get("submarine_cables"):
        await db.submarine_cables.insert_many(seed_data["submarine_cables"])
    
    # Insert electrical assets
    if seed_data.get("electrical_assets"):
        await db.electrical_assets.insert_many(seed_data["electrical_assets"])
    
    # Compute scores for all parcels (universel /100)
    for parcel in seed_data["parcels"]:
        score_data = compute_score_simple(parcel)
        score_data["parcel_id"] = parcel["parcel_id"]
        score_data["score_id"] = f"score_{uuid.uuid4().hex[:12]}"
        score_data["computed_at"] = datetime.now(timezone.utc).isoformat()
        score_data["is_latest"] = True
        await db.parcel_scores.insert_one(score_data)
    
    return {
        "success": True,
        "parcels_count": len(seed_data["parcels"]),
        "dc_count": len(seed_data["dc_existants"]),
        "landing_points_count": len(seed_data["landing_points"]),
        "submarine_cables_count": len(seed_data.get("submarine_cables", [])),
        "electrical_assets_count": len(seed_data.get("electrical_assets", []))
    }


@api_router.get("/admin/stats")
async def get_stats():
    """Get database statistics"""
    parcels_count = await db.parcels.count_documents({})
    scores_count = await db.parcel_scores.count_documents({})
    users_count = await db.users.count_documents({})
    shortlists_count = await db.shortlists.count_documents({})
    
    # Region distribution
    pipeline = [
        {"$group": {"_id": "$region", "count": {"$sum": 1}}}
    ]
    regions = await db.parcels.aggregate(pipeline).to_list(20)
    
    return {
        "parcels": parcels_count,
        "scores": scores_count,
        "users": users_count,
        "shortlists": shortlists_count,
        "regions": {r["_id"]: r["count"] for r in regions}
    }


@api_router.get("/")
async def root():
    return {"message": "Cockpit Immo API", "version": "1.0.0"}


# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    await create_indexes()
    logger.info("Database indexes created")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
