"""
Cockpit Immo - MongoDB Models for DC Land Prospection
Adapted from PostgreSQL/PostGIS schema to MongoDB with GeoJSON
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


def generate_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}" if prefix else uuid.uuid4().hex[:16]


# ═══════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════

class ProjectType(str, Enum):
    HYPERSCALE = "hyperscale"
    COLOCATION_T3 = "colocation_t3"
    COLOCATION_T4 = "colocation_t4"
    EDGE = "edge"
    AI_CAMPUS = "ai_campus"


class Verdict(str, Enum):
    GO = "GO"
    CONDITIONNEL = "CONDITIONNEL"
    NO_GO = "NO_GO"


class UrbaCompatibilite(str, Enum):
    COMPATIBLE = "compatible"
    COMPATIBLE_SOUS_CONDITIONS = "compatible_sous_conditions"
    INCOMPATIBLE = "incompatible"


class ZoneSaturation(str, Enum):
    DISPONIBLE = "disponible"
    TENDU = "tendu"
    SATURE = "sature"
    INCONNU = "inconnu"


class UserRole(str, Enum):
    ADMIN = "admin"
    CONSULTANT = "consultant"
    CLIENT_READONLY = "client_readonly"


# ═══════════════════════════════════════════════════
# USER & AUTH MODELS
# ═══════════════════════════════════════════════════

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    user_id: str = Field(default_factory=lambda: generate_id("user_"))
    email: str
    name: str
    picture: Optional[str] = None
    role: UserRole = UserRole.CONSULTANT
    tenant_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    session_id: str = Field(default_factory=lambda: generate_id("sess_"))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════
# TENANT MODEL (Multi-tenant)
# ═══════════════════════════════════════════════════

class Tenant(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    tenant_id: str = Field(default_factory=lambda: generate_id("tenant_"))
    nom: str
    plan: str = "free"  # free|pro|enterprise
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════
# PARCEL MODEL (with GeoJSON)
# ═══════════════════════════════════════════════════

class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class GeoJSONPolygon(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]  # [[[lng, lat], ...]]


class Parcel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    parcel_id: str = Field(default_factory=lambda: generate_id("parcel_"))
    ref_cadastrale: str
    code_commune: str
    commune: str
    departement: str
    region: str
    
    # GeoJSON geometry
    geometry: Dict[str, Any]  # GeoJSON Polygon
    centroid: Dict[str, Any]  # GeoJSON Point
    
    surface_m2: float
    surface_ha: float
    latitude: float
    longitude: float
    
    # Infrastructure électrique
    dist_poste_htb_m: Optional[float] = None
    tension_htb_kv: Optional[float] = None
    puissance_poste_mva: Optional[float] = None
    dist_poste_hta_m: Optional[float] = None
    dist_ligne_400kv_m: Optional[float] = None
    dist_ligne_225kv_m: Optional[float] = None
    dist_ligne_63kv_m: Optional[float] = None
    capacite_confirmee_mw: Optional[float] = None
    capacite_residuelle_estimee_mw: Optional[float] = None
    zone_saturation: ZoneSaturation = ZoneSaturation.INCONNU
    file_attente_mw: Optional[float] = None
    poste_source_nom: Optional[str] = None
    
    # Estimations raccordement
    racc_tension_cible: Optional[str] = None
    racc_type_travaux: Optional[str] = None
    racc_delai_estime_min_mois: Optional[int] = None
    racc_delai_estime_max_mois: Optional[int] = None
    racc_cout_estime_eur: Optional[float] = None
    racc_proba_obtention_mw: Optional[float] = None
    racc_mw_obtenables_p50: Optional[float] = None
    
    # Estimation puissance
    power_mw_surface: Optional[float] = None
    power_mw_reseau: Optional[float] = None
    power_mw_estime: Optional[float] = None
    power_mw_p10: Optional[float] = None
    power_mw_p50: Optional[float] = None
    power_mw_p90: Optional[float] = None
    power_score: Optional[int] = None
    power_category: Optional[str] = None
    power_limiting_factor: Optional[str] = None
    
    # Fibre
    dist_backbone_fibre_m: Optional[float] = None
    nb_operateurs_fibre: int = 0
    has_international: bool = False
    
    # Connectivité câbles sous-marins
    dist_landing_point_km: Optional[float] = None
    landing_point_nom: Optional[str] = None
    landing_point_nb_cables: Optional[int] = None
    landing_point_is_major_hub: bool = False
    
    # Eau
    cours_eau_dist_m: Optional[float] = None
    zone_stress_hydrique: bool = False
    
    # PLU & Réglementation
    plu_zone: Optional[str] = None
    plu_numerise: bool = True
    dans_zac_active: bool = False
    rezonage_requis: bool = False
    delai_rezonage_plu_mois: Optional[int] = None
    icpe_regime: Optional[str] = None
    
    # ZAN
    commune_zan_pct: Optional[float] = None
    site_type: str = "greenfield"  # greenfield|brownfield|friche_industrielle|zac
    
    # Risques
    ppri_zone: Optional[str] = None
    sismique_zone: int = 1
    argiles_alea: str = "faible"
    drac_zone_archeo: bool = False
    
    # DVF & Propriété
    dvf_prix_m2_p50: Optional[float] = None
    dvf_nb_transactions: Optional[int] = None
    proprietaire_nom: Optional[str] = None
    proprietaire_type: Optional[str] = None
    
    # Shovel-ready
    raccordement_elec_existant: bool = False
    raccordement_fibre_existant: bool = False
    voirie_desserte_existante: bool = False
    
    # Consolidation
    surface_consolidable_ha: Optional[float] = None
    
    # DC voisins (embedded)
    dc_voisins: List[Dict[str, Any]] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════
# PARCEL SCORE MODEL
# ═══════════════════════════════════════════════════

class ParcelScore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    score_id: str = Field(default_factory=lambda: generate_id("score_"))
    parcel_id: str
    project_type: ProjectType
    
    # Verdict global
    verdict: Verdict = Verdict.CONDITIONNEL
    verdict_raison: Optional[str] = None
    risque_global: str = "moyen"
    
    # Éligibilité
    eligibility_status: str = "eligible"
    eligibility_blockers: List[str] = []
    
    # TTM
    ttm_min_months: Optional[int] = None
    ttm_max_months: Optional[int] = None
    ttm_bottleneck: Optional[str] = None
    
    # Raccordement
    racc_delai_min_mois: Optional[int] = None
    racc_delai_max_mois: Optional[int] = None
    racc_cout_eur: Optional[float] = None
    racc_proba_obtention: Optional[float] = None
    racc_mw_obtenables: Optional[float] = None
    racc_tension_cible: Optional[str] = None
    racc_type_travaux: Optional[str] = None
    
    # Puissance
    power_mw_p10: Optional[float] = None
    power_mw_p50: Optional[float] = None
    power_mw_p90: Optional[float] = None
    power_score: Optional[int] = None
    power_category: Optional[str] = None
    power_limiting_factor: Optional[str] = None
    
    # Score technique (6 critères)
    score_electricite: float = 0
    score_fibre: float = 0
    score_connectivite_intl: float = 0
    score_eau: float = 0
    score_surface: float = 0
    score_marche: float = 0
    score_climat: float = 0
    score_total: float = 0
    malus_total: float = 0
    malus_details: Dict[str, Any] = {}
    score_net: float = 0
    
    # Urbanisme
    urba_compatibilite: UrbaCompatibilite = UrbaCompatibilite.COMPATIBLE
    urba_risque: str = "faible"
    urba_delai_min_mois: Optional[int] = None
    urba_delai_max_mois: Optional[int] = None
    urba_conditions: List[Dict[str, Any]] = []
    urba_nb_conditions: int = 0
    urba_proba_succes_combinee: Optional[float] = None
    urba_deal_friction_index: int = 0
    urba_dfi_categorie: str = "faible"
    urba_couts_indirects: Dict[str, Any] = {}
    
    # Confiance
    confidence_score: float = 0
    confidence_missing: List[str] = []
    
    # Capacité
    mw_estime: Optional[float] = None
    pue_expected: Optional[float] = None
    
    # Économique
    capex_p10: Optional[float] = None
    capex_p50: Optional[float] = None
    capex_p90: Optional[float] = None
    cout_mw_p50: Optional[float] = None
    ebitda_maturite: Optional[float] = None
    irr_unlevered_pct: Optional[float] = None
    irr_levered_pct: Optional[float] = None
    faisabilite: str = "moyen"
    
    # CAPEX détaillé
    capex_detail: Dict[str, Any] = {}
    
    is_latest: bool = True
    computed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════
# CRM MODELS
# ═══════════════════════════════════════════════════

class Shortlist(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    shortlist_id: str = Field(default_factory=lambda: generate_id("sl_"))
    tenant_id: str
    nom: str
    description: Optional[str] = None
    project_type: Optional[ProjectType] = None
    share_token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ShortlistItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    item_id: str = Field(default_factory=lambda: generate_id("sli_"))
    shortlist_id: str
    parcel_id: str
    statut: str = "a_analyser"
    interlocuteur: Optional[str] = None
    prix_offert_eur: Optional[float] = None
    notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════
# ALERT MODEL
# ═══════════════════════════════════════════════════

class Alert(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    alert_id: str = Field(default_factory=lambda: generate_id("alert_"))
    parcel_id: Optional[str] = None
    tenant_id: str
    type_alerte: str
    description: str
    severity: str = "info"  # info|warning|critical
    lu: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════
# DC EXISTANT MODEL
# ═══════════════════════════════════════════════════

class DCExistant(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    dc_id: str = Field(default_factory=lambda: generate_id("dc_"))
    nom: str
    operateur: Optional[str] = None
    type_dc: Optional[str] = None
    geometry: Dict[str, Any]  # GeoJSON Point
    puissance_mw: Optional[float] = None
    tier: Optional[str] = None
    source: str = "osm"


# ═══════════════════════════════════════════════════
# LANDING POINT MODEL
# ═══════════════════════════════════════════════════

class LandingPoint(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    landing_id: str = Field(default_factory=lambda: generate_id("lp_"))
    nom: str
    ville: str
    departement: str
    region: str
    geometry: Dict[str, Any]  # GeoJSON Point
    nb_cables_connectes: int = 0
    cables_noms: List[str] = []
    is_major_hub: bool = False


# ═══════════════════════════════════════════════════
# ELECTRICAL ASSET MODEL
# ═══════════════════════════════════════════════════

class ElectricalAsset(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    asset_id: str = Field(default_factory=lambda: generate_id("elec_"))
    nom: Optional[str] = None
    type: str  # poste_htb|poste_hta|ligne_400kv|ligne_225kv|ligne_63kv
    geometry: Dict[str, Any]  # GeoJSON Point or LineString
    tension_kv: Optional[float] = None
    puissance_mva: Optional[float] = None
    zone_saturation: Optional[str] = None
