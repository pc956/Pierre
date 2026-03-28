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
    Shortlist, ShortlistItem, Alert, ProjectType, Verdict
)
from scoring import compute_full_score
from seed_data import get_seed_data
from api_carto import (
    search_communes, get_parcelles_by_commune, get_parcelles_by_bbox,
    get_parcelles_around_point, get_sections_by_commune, parse_parcelle_feature
)
from france_infra_data import get_all_france_infra

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
    await db.parcel_scores.create_index([("parcel_id", 1), ("project_type", 1)])
    await db.parcel_scores.create_index("score_net")
    
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
    project_type: str = "colocation_t3"
    mw_target: Optional[float] = None
    budget_max: Optional[float] = None
    ttm_max: Optional[int] = None
    regions: Optional[List[str]] = None
    score_min: Optional[float] = None
    bbox: Optional[List[float]] = None  # [min_lng, min_lat, max_lng, max_lat]

class ShortlistCreate(BaseModel):
    nom: str
    description: Optional[str] = None
    project_type: Optional[str] = None

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
    project_type: str = "colocation_t3",
    score_min: Optional[float] = None,
    limit: int = 100,
    skip: int = 0
):
    """Get parcels with optional filters"""
    query = {}
    
    if region:
        query["region"] = region
    
    parcels = await db.parcels.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Get scores for each parcel
    result = []
    for parcel in parcels:
        score_doc = await db.parcel_scores.find_one(
            {"parcel_id": parcel["parcel_id"], "project_type": project_type, "is_latest": True},
            {"_id": 0}
        )
        
        if score_min and score_doc and score_doc.get("score_net", 0) < score_min:
            continue
        
        result.append({
            **parcel,
            "score": score_doc
        })
    
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
        "scores": {s["project_type"]: s for s in scores}
    }


@api_router.get("/parcels/{parcel_id}/score/{project_type}")
async def get_parcel_score(parcel_id: str, project_type: str):
    """Get or compute score for parcel and project type"""
    # Check if score exists
    score_doc = await db.parcel_scores.find_one(
        {"parcel_id": parcel_id, "project_type": project_type, "is_latest": True},
        {"_id": 0}
    )
    
    if score_doc:
        return score_doc
    
    # Compute score
    parcel = await db.parcels.find_one({"parcel_id": parcel_id}, {"_id": 0})
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    score_data = compute_full_score(parcel, project_type)
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
            {"parcel_id": parcel["parcel_id"], "project_type": req.project_type, "is_latest": True},
            {"_id": 0}
        )
        
        if not score_doc:
            score_data = compute_full_score(parcel, req.project_type)
            score_data["score_id"] = f"score_{uuid.uuid4().hex[:12]}"
            score_data["computed_at"] = datetime.now(timezone.utc).isoformat()
            score_data["is_latest"] = True
            await db.parcel_scores.insert_one(score_data)
            score_doc = score_data
        
        # Apply filters
        if req.score_min and score_doc.get("score_net", 0) < req.score_min:
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
async def compare_parcels(parcel_ids: List[str], project_type: str = "colocation_t3"):
    """Compare multiple parcels side by side"""
    results = []
    
    for pid in parcel_ids[:4]:  # Max 4 parcels
        parcel = await db.parcels.find_one({"parcel_id": pid}, {"_id": 0})
        if not parcel:
            continue
        
        score_doc = await db.parcel_scores.find_one(
            {"parcel_id": pid, "project_type": project_type, "is_latest": True},
            {"_id": 0}
        )
        
        if not score_doc:
            score_data = compute_full_score(parcel, project_type)
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

@api_router.get("/map/parcels")
async def get_map_parcels(
    project_type: str = "colocation_t3",
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
        {"parcel_id": {"$in": parcel_ids}, "project_type": project_type, "is_latest": True},
        {"_id": 0, "parcel_id": 1, "score_net": 1, "verdict": 1, "power_mw_p50": 1, "ttm_max_months": 1}
    ).to_list(500)
    
    score_map = {s["parcel_id"]: s for s in scores}
    
    result = []
    for p in parcels:
        score = score_map.get(p["parcel_id"], {})
        result.append({
            **p,
            "score_net": score.get("score_net", 0),
            "verdict": score.get("verdict", "CONDITIONNEL"),
            "power_mw_p50": score.get("power_mw_p50"),
            "ttm_max_months": score.get("ttm_max_months")
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
    """Get electrical assets (postes HTB, lignes 400kV, lignes 225kV) for map - nationwide"""
    all_assets = (
        _FRANCE_INFRA["postes_htb"] +
        _FRANCE_INFRA["lignes_400kv"] +
        _FRANCE_INFRA["lignes_225kv"]
    )
    if asset_type:
        all_assets = [a for a in all_assets if a.get("type") == asset_type]
    return {"electrical_assets": all_assets}


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
async def get_commune_parcelles(code_insee: str, section: Optional[str] = None, project_type: str = "colocation_t3"):
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
            for htb in _FRANCE_INFRA["postes_htb"]:
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
            parsed["dist_poste_hta_m"] = 3000
            parsed["dist_backbone_fibre_m"] = 2000
            parsed["nb_operateurs_fibre"] = 2
            parsed["plu_zone"] = "U"
            parsed["zone_saturation"] = "inconnu"
            
            # Compute score
            try:
                score_data = compute_full_score(parsed, project_type)
                parsed["score"] = {
                    "score_net": score_data.get("score_net", 0),
                    "verdict": score_data.get("verdict", "CONDITIONNEL"),
                    "power_mw_p50": score_data.get("power_mw_p50", 0),
                }
            except Exception:
                parsed["score"] = {"score_net": 0, "verdict": "CONDITIONNEL"}
            
            parcelles.append(parsed)
    
    return {
        "parcelles": parcelles,
        "count": len(parcelles),
        "total_raw": len(data.get("features", [])),
        "source": "api_carto_ign"
    }


@api_router.get("/france/parcelles/bbox")
async def get_bbox_parcelles(
    min_lon: float, 
    min_lat: float, 
    max_lon: float, 
    max_lat: float,
    project_type: str = "colocation_t3",
    limit: int = 200
):
    """
    Get parcelles within a bounding box from API Carto
    Use for map viewport queries
    """
    import math
    
    data = await get_parcelles_by_bbox(min_lon, min_lat, max_lon, max_lat, limit)
    
    parcelles = []
    for feature in data.get("features", [])[:limit]:
        parsed = parse_parcelle_feature(feature)
        
        if parsed.get("centroid"):
            # Compute real distances to nearest infrastructure
            plat = parsed["latitude"]
            plon = parsed["longitude"]
            
            # Find nearest HTB post
            min_dist_htb = 999999
            nearest_htb_kv = 0
            for htb in _FRANCE_INFRA["postes_htb"]:
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
            parsed["dist_backbone_fibre_m"] = 2000  # Default
            parsed["nb_operateurs_fibre"] = 2
            parsed["plu_zone"] = "U"  # Default
            parsed["zone_saturation"] = "inconnu"
            
            # Compute score
            try:
                score_data = compute_full_score(parsed, project_type)
                parsed["score"] = {
                    "score_net": score_data.get("score_net", 0),
                    "verdict": score_data.get("verdict", "CONDITIONNEL"),
                    "power_mw_p50": score_data.get("power_mw_p50", 0),
                    "score_electricite": score_data.get("score_electricite", 0),
                    "score_fibre": score_data.get("score_fibre", 0),
                    "ttm_min_months": score_data.get("ttm_min_months"),
                    "ttm_max_months": score_data.get("ttm_max_months"),
                }
            except Exception:
                parsed["score"] = {"score_net": 0, "verdict": "CONDITIONNEL"}
            
            parcelles.append(parsed)
    
    return {
        "parcelles": parcelles,
        "count": len(parcelles),
        "source": "api_carto_ign"
    }


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
    radius_m: float = 2000,
    project_type: str = "colocation_t3"
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
    
    # Count items per shortlist
    for sl in shortlists:
        count = await db.shortlist_items.count_documents({"shortlist_id": sl["shortlist_id"]})
        sl["item_count"] = count
    
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
        "project_type": req.project_type,
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
    
    # Enrich items with parcel data
    for item in items:
        parcel = await db.parcels.find_one(
            {"parcel_id": item["parcel_id"]},
            {"_id": 0, "commune": 1, "region": 1, "surface_ha": 1}
        )
        if parcel:
            item["parcel"] = parcel
        
        score = await db.parcel_scores.find_one(
            {"parcel_id": item["parcel_id"], "project_type": shortlist.get("project_type", "colocation_t3"), "is_latest": True},
            {"_id": 0, "score_net": 1, "verdict": 1, "power_mw_p50": 1, "ttm_max_months": 1}
        )
        if score:
            item["score"] = score
    
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
    
    # Compute scores for all parcels (colocation_t3 as default)
    for parcel in seed_data["parcels"]:
        for project_type in ["colocation_t3", "hyperscale", "edge"]:
            score_data = compute_full_score(parcel, project_type)
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
