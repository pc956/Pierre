"""
Cockpit Immo — Module de scoring PLU automatique pour data centers
Évalue la compatibilité urbanistique d'une parcelle avec un projet DC.
Score 0-100, statut, flags de risque, recommandation d'action.
"""
from typing import Optional

# ═══════════════════════════════════════════════════════════
# HARD EXCLUSION ZONES — Score immédiat = 0
# ═══════════════════════════════════════════════════════════

HARD_EXCLUSION_ZONES = {
    "N", "NL", "Nh", "Nl", "A", "Ap", "A0",
    "Nd", "Ns", "Nf", "Nc", "Ne",
    "Ab", "Ac", "Ah",
}

RESIDENTIAL_ZONES = {
    "UA", "UB", "UC", "UD", "UH", "UR",
    "UAa", "UAb", "UBa", "UBb", "UCa", "UCb", "UDa", "UDb",
    "UHa", "UHb",
}

# ═══════════════════════════════════════════════════════════
# BASE SCORE MAP — Par catégorie de zone PLU
# ═══════════════════════════════════════════════════════════

INDUSTRIAL_ZONES = {
    "UI", "UX", "UY", "UZ", "UE", "UF", "UP",
    "UIa", "UIb", "UIc", "UXa", "UXb", "UYa", "UYb",
    "UZa", "UZb", "UEa", "UEb", "UFa", "UFb",
    "UPa", "UPb", "UPm",
    "Ui", "Ux", "Uy", "Uz", "Ue", "Uf",
}

AU_ZONES = {
    "AU", "AUI", "AUX", "AUY", "AUZ", "AUE",
    "1AU", "2AU", "1AUI", "2AUI", "1AUX", "2AUX",
    "AUa", "AUb", "AUc", "AUi", "AUx", "AUy",
    "1AUa", "1AUb", "1AUi", "2AUa", "2AUi",
    "NAi",
}

MIXED_TERTIARY_ZONES = {
    "UM", "UT", "UC", "UV",
    "UMa", "UMb", "UTa", "UTb",
    "UCa", "UCb", "UVa",
    "Um", "Ut",
    "UG", "UGa",
}

# ═══════════════════════════════════════════════════════════
# KEYWORD PARSING — Règlement PLU
# ═══════════════════════════════════════════════════════════

POSITIVE_KEYWORDS = [
    "industrie", "industriel", "industrielle",
    "activité", "activités", "activites",
    "logistique", "logistiques",
    "équipement", "equipement", "équipements techniques",
    "service public", "services publics",
    "entrepôt", "entrepôts", "entrepot",
    "artisanal", "artisanale", "artisanat",
    "installation classée", "icpe",
    "zone portuaire", "portuaire",
    "zone d'activité", "zone d'activités",
    "parc d'activité", "parc d'activités",
    "technologique", "technopôle",
    "data center", "datacenter", "centre de données",
    "énergie", "électrique", "transformateur",
]

NEGATIVE_KEYWORDS = [
    "naturelle", "naturel",
    "agricole", "agriculture",
    "habitat", "habitation", "résidentiel", "résidentielle",
    "patrimonial", "patrimoine", "monument historique",
    "inconstructible", "non constructible",
    "zone humide", "zones humides",
    "ebc", "espace boisé classé", "espace boisé",
    "paysager", "paysage protégé",
    "réserve naturelle", "natura 2000",
    "ppri", "plan de prévention des risques",
    "zone rouge", "risque rouge",
    "inondable", "inondation",
    "zone de danger",
]


def _normalize_zone(code: str) -> str:
    """Normalise le code de zone PLU."""
    if not code:
        return ""
    return code.strip()


def _classify_zone(code: str) -> str:
    """Classifie une zone PLU en catégorie."""
    c = _normalize_zone(code)
    cu = c.upper()

    if c in HARD_EXCLUSION_ZONES or cu in {z.upper() for z in HARD_EXCLUSION_ZONES}:
        return "excluded"

    if c in RESIDENTIAL_ZONES or cu in {z.upper() for z in RESIDENTIAL_ZONES}:
        return "residential"

    if c in INDUSTRIAL_ZONES or cu in {z.upper() for z in INDUSTRIAL_ZONES}:
        return "industrial"

    if c in AU_ZONES or cu in {z.upper() for z in AU_ZONES}:
        return "au"

    if c in MIXED_TERTIARY_ZONES or cu in {z.upper() for z in MIXED_TERTIARY_ZONES}:
        return "mixed"

    # Fallback pattern matching
    if cu.startswith("UI") or cu.startswith("UX") or cu.startswith("UY") or cu.startswith("UZ") or cu.startswith("UE") or cu.startswith("UF"):
        return "industrial"
    if cu.startswith("AU"):
        return "au"
    if cu.startswith("N"):
        return "excluded"
    if cu.startswith("A") and not cu.startswith("AU"):
        return "excluded"
    if cu.startswith("U"):
        # Generic U zone — check if residential or other
        if cu in ("UA", "UB", "UC", "UD", "UH", "UR"):
            return "residential"
        return "mixed"

    return "unknown"


# ═══════════════════════════════════════════════════════════
# SCORING FUNCTIONS
# ═══════════════════════════════════════════════════════════

def get_base_plu_score(zone_code: str) -> tuple:
    """
    Retourne (score_base, catégorie, exclusion_reason).
    """
    cat = _classify_zone(zone_code)

    if cat == "excluded":
        return (0, cat, f"Zone {zone_code} incompatible (naturelle/agricole)")

    if cat == "residential":
        return (15, cat, None)

    if cat == "industrial":
        return (90, cat, None)

    if cat == "au":
        return (72, cat, None)

    if cat == "mixed":
        return (55, cat, None)

    # Unknown
    return (40, "unknown", None)


def parse_reglement_keywords(reglement_text: str) -> dict:
    """
    Parse le texte du règlement PLU pour détecter des mots-clés
    positifs et négatifs pour un projet data center.
    """
    if not reglement_text:
        return {"positive": [], "negative": [], "net_signal": 0}

    text_lower = reglement_text.lower()
    found_positive = []
    found_negative = []

    for kw in POSITIVE_KEYWORDS:
        if kw in text_lower:
            found_positive.append(kw)

    for kw in NEGATIVE_KEYWORDS:
        if kw in text_lower:
            found_negative.append(kw)

    net = len(found_positive) - len(found_negative)

    return {
        "positive": found_positive,
        "negative": found_negative,
        "net_signal": net,
    }


def apply_plu_adjustments(
    base_score: int,
    category: str,
    is_brownfield: bool = False,
    is_zac_zip_port: bool = False,
    reglement_allows_equipment: bool = False,
    urbanisation_conditionnee: bool = False,
    proximite_habitat: bool = False,
    contrainte_patrimoniale: bool = False,
    risque_reglementaire_majeur: bool = False,
    reglement_text: Optional[str] = None,
) -> tuple:
    """
    Applique les ajustements au score de base.
    Retourne (score_ajusté, flags, ajustements_détail).
    """
    score = base_score
    flags = []
    adjustments = []

    # Hard exclusion checks
    if contrainte_patrimoniale and category in ("residential", "excluded"):
        return (0, ["hard_exclusion_patrimoine"], [("contrainte_patrimoniale", -base_score)])

    if risque_reglementaire_majeur and category in ("residential", "excluded"):
        return (0, ["hard_exclusion_risque"], [("risque_reglementaire_majeur", -base_score)])

    # Positive adjustments
    if is_brownfield:
        adj = 10
        score += adj
        flags.append("brownfield_bonus")
        adjustments.append(("brownfield", f"+{adj}"))

    if is_zac_zip_port:
        adj = 8
        score += adj
        flags.append("zac_zip_port_bonus")
        adjustments.append(("zac_zip_port", f"+{adj}"))

    if reglement_allows_equipment:
        adj = 7
        score += adj
        flags.append("equipement_technique_autorise")
        adjustments.append(("reglement_equipement", f"+{adj}"))

    # Keyword parsing from reglement text
    if reglement_text:
        kw_result = parse_reglement_keywords(reglement_text)
        if kw_result["net_signal"] >= 3:
            adj = 5
            score += adj
            flags.append("reglement_tres_favorable")
            adjustments.append(("keywords_positifs", f"+{adj}"))
        elif kw_result["net_signal"] >= 1:
            adj = 3
            score += adj
            flags.append("reglement_favorable")
            adjustments.append(("keywords_positifs", f"+{adj}"))
        elif kw_result["net_signal"] <= -2:
            adj = -8
            score += adj
            flags.append("reglement_defavorable")
            adjustments.append(("keywords_negatifs", str(adj)))

    # Negative adjustments
    if urbanisation_conditionnee:
        adj = -12
        score += adj
        flags.append("urbanisation_conditionnee")
        adjustments.append(("urbanisation_conditionnee", str(adj)))

    if proximite_habitat:
        adj = -10
        score += adj
        flags.append("proximite_habitat")
        adjustments.append(("proximite_habitat", str(adj)))

    if contrainte_patrimoniale:
        adj = -18
        score += adj
        flags.append("contrainte_patrimoniale")
        adjustments.append(("contrainte_patrimoniale", str(adj)))

    if risque_reglementaire_majeur:
        adj = -20
        score += adj
        flags.append("risque_reglementaire_majeur")
        adjustments.append(("risque_reglementaire", str(adj)))

    # Clamp
    score = max(0, min(100, score))

    return (score, flags, adjustments)


def _get_status(score: int) -> str:
    """Détermine le statut à partir du score."""
    if score == 0:
        return "EXCLUDED"
    if score >= 85:
        return "FAVORABLE"
    if score >= 65:
        return "WATCHLIST"
    if score >= 45:
        return "CONDITIONAL"
    return "UNFAVORABLE"


def _get_recommended_action(status: str) -> str:
    """Recommandation d'action basée sur le statut."""
    return {
        "FAVORABLE": "prospect_now",
        "WATCHLIST": "check_regulation_and_mayor",
        "CONDITIONAL": "manual_review",
        "UNFAVORABLE": "reject",
        "EXCLUDED": "reject",
    }.get(status, "manual_review")


def _get_risk_level(score: int, flags: list) -> str:
    """Évalue le niveau de risque urbanistique."""
    if score == 0:
        return "eliminatoire"
    high_risk_flags = {"risque_reglementaire_majeur", "contrainte_patrimoniale", "hard_exclusion_patrimoine", "hard_exclusion_risque"}
    if high_risk_flags & set(flags):
        return "tres_eleve"
    medium_risk_flags = {"urbanisation_conditionnee", "proximite_habitat", "reglement_defavorable"}
    if medium_risk_flags & set(flags):
        return "eleve"
    if score >= 85:
        return "faible"
    if score >= 65:
        return "modere"
    return "eleve"


# ═══════════════════════════════════════════════════════════
# MAIN SCORING FUNCTION
# ═══════════════════════════════════════════════════════════

def score_plu(
    zone_code: str,
    zone_label: str = "",
    is_brownfield: bool = False,
    is_zac_zip_port: bool = False,
    reglement_allows_equipment: bool = False,
    urbanisation_conditionnee: bool = False,
    proximite_habitat: bool = False,
    contrainte_patrimoniale: bool = False,
    risque_reglementaire_majeur: bool = False,
    reglement_text: Optional[str] = None,
) -> dict:
    """
    Scoring PLU complet pour une parcelle data center.

    Returns:
        {
            "plu_code": str,
            "plu_label": str,
            "plu_score": int (0-100),
            "plu_status": str,
            "exclusion_reason": str | None,
            "flags": list[str],
            "urbanism_risk": str,
            "recommended_action": str,
            "category": str,
            "adjustments": list,
            "keyword_analysis": dict | None,
        }
    """
    code = _normalize_zone(zone_code)
    base_score, category, exclusion_reason = get_base_plu_score(code)

    # Hard exclusion — immediate return
    if exclusion_reason and base_score == 0:
        return {
            "plu_code": code,
            "plu_label": zone_label,
            "plu_score": 0,
            "plu_status": "EXCLUDED",
            "exclusion_reason": exclusion_reason,
            "flags": ["hard_exclusion"],
            "urbanism_risk": "eliminatoire",
            "recommended_action": "reject",
            "category": category,
            "adjustments": [],
            "keyword_analysis": None,
        }

    # Residential exclusion
    if category == "residential":
        base_score_res = 15
        # Check if reglement might allow some exceptions
        kw = parse_reglement_keywords(reglement_text) if reglement_text else None
        if kw and kw["net_signal"] >= 2:
            base_score_res = 25  # Slight bump if reglement is favorable
        return {
            "plu_code": code,
            "plu_label": zone_label,
            "plu_score": base_score_res,
            "plu_status": "UNFAVORABLE",
            "exclusion_reason": "Zone résidentielle — projet DC inadapté",
            "flags": ["zone_residentielle"],
            "urbanism_risk": "tres_eleve",
            "recommended_action": "reject",
            "category": category,
            "adjustments": [],
            "keyword_analysis": kw,
        }

    # Apply adjustments
    final_score, flags, adjustments = apply_plu_adjustments(
        base_score=base_score,
        category=category,
        is_brownfield=is_brownfield,
        is_zac_zip_port=is_zac_zip_port,
        reglement_allows_equipment=reglement_allows_equipment,
        urbanisation_conditionnee=urbanisation_conditionnee,
        proximite_habitat=proximite_habitat,
        contrainte_patrimoniale=contrainte_patrimoniale,
        risque_reglementaire_majeur=risque_reglementaire_majeur,
        reglement_text=reglement_text,
    )

    status = _get_status(final_score)
    action = _get_recommended_action(status)
    risk = _get_risk_level(final_score, flags)

    kw_analysis = parse_reglement_keywords(reglement_text) if reglement_text else None

    return {
        "plu_code": code,
        "plu_label": zone_label,
        "plu_score": final_score,
        "plu_status": status,
        "exclusion_reason": None if final_score > 0 else "Score nul après ajustements",
        "flags": flags,
        "urbanism_risk": risk,
        "recommended_action": action,
        "category": category,
        "adjustments": adjustments,
        "keyword_analysis": kw_analysis,
    }


# ═══════════════════════════════════════════════════════════
# PRESCRIPTION & INFO ANALYSIS — GPU data
# ═══════════════════════════════════════════════════════════

# GPU typepsc codes relevant to DC projects
PRESCRIPTION_RISK_CODES = {
    "01": "espace_boise_classe",       # EBC
    "02": "limitation_constructibilite",
    "03": "secteur_nouvelles_urbanisations",
    "05": "emplacements_reserves",
    "07": "patrimoine_protege",
    "25": "secteur_mixite",
}

# GPU typeinf codes relevant to DC projects
INFO_RISK_CODES = {
    "02": "secteur_zac",
    "04": "perimetre_ppr",              # PPR naturel/techno
    "05": "zones_reglement_ppr",
    "14": "voie_bruyante",
    "19": "zone_sensibilite_archeologique",
    "99": "autre_information",
}

PPRT_KEYWORDS = ["pprt", "ppr", "risque technologique", "risque industriel", "seveso"]
ZAC_KEYWORDS = ["zac", "zone d'aménagement concerté", "zone d'aménagement"]
EBC_KEYWORDS = ["ebc", "espace boisé classé", "espace boisé"]
PATRIMOINE_KEYWORDS = ["monument historique", "abf", "patrimoine", "site classé", "site inscrit"]


def _analyze_prescriptions(prescriptions: list) -> dict:
    """Analyse les prescriptions GPU pour en déduire des flags DC."""
    flags = []
    adjustments = []
    has_ebc = False
    has_patrimoine = False
    has_limitation = False

    for p in prescriptions:
        lib = (p.get("libelle", "") or "").lower()
        txt = (p.get("txt", "") or "").lower()
        combined = f"{lib} {txt}"
        typepsc = p.get("typepsc", "")

        if typepsc == "01" or any(k in combined for k in EBC_KEYWORDS):
            has_ebc = True
            flags.append("prescription_ebc")
            adjustments.append(("ebc_prescription", "-15"))

        if typepsc == "07" or any(k in combined for k in PATRIMOINE_KEYWORDS):
            has_patrimoine = True
            flags.append("prescription_patrimoine")
            adjustments.append(("patrimoine_prescription", "-12"))

        if typepsc == "02":
            has_limitation = True
            flags.append("prescription_limitation_constructibilite")
            adjustments.append(("limitation_constructibilite", "-8"))

        if typepsc == "05":
            flags.append("emplacement_reserve")
            adjustments.append(("emplacement_reserve", "-5"))

    score_adj = 0
    if has_ebc:
        score_adj -= 15
    if has_patrimoine:
        score_adj -= 12
    if has_limitation:
        score_adj -= 8

    return {
        "flags": flags,
        "adjustments": adjustments,
        "score_adjustment": score_adj,
        "has_ebc": has_ebc,
        "has_patrimoine": has_patrimoine,
    }


def _analyze_informations(informations: list) -> dict:
    """Analyse les informations GPU (risques, servitudes)."""
    flags = []
    adjustments = []
    has_pprt = False
    has_zac = False
    risk_labels = []

    for info in informations:
        lib = (info.get("libelle", "") or "").lower()
        txt = (info.get("txt", "") or "").lower()
        combined = f"{lib} {txt}"
        typeinf = info.get("typeinf", "")

        # PPRT / PPR
        if typeinf in ("04", "05") or any(k in combined for k in PPRT_KEYWORDS):
            has_pprt = True
            flags.append("zone_pprt_ppr")
            risk_labels.append(info.get("libelle", "PPR"))
            adjustments.append(("pprt_ppr", "-10"))

        # ZAC (positive for DC!)
        if typeinf == "02" or any(k in combined for k in ZAC_KEYWORDS):
            has_zac = True
            flags.append("zone_zac_gpu")
            adjustments.append(("zac_detected_gpu", "+8"))

        # Voie bruyante (neutral — DC are noisy anyway)
        if typeinf == "14":
            flags.append("voie_bruyante")

        # Archaeological sensitivity
        if typeinf == "19":
            flags.append("sensibilite_archeologique")
            adjustments.append(("archeologie", "-5"))

    score_adj = 0
    if has_pprt:
        score_adj -= 10
    if has_zac:
        score_adj += 8

    return {
        "flags": flags,
        "adjustments": adjustments,
        "score_adjustment": score_adj,
        "has_pprt": has_pprt,
        "has_zac": has_zac,
        "risk_labels": risk_labels,
    }


def _detect_destdomi(destdomi: str, libelong: str) -> dict:
    """Analyse la destination dominante et le libelong pour détecter la vocation du sol."""
    flags = []
    score_adj = 0
    text = f"{destdomi or ''} {libelong or ''}".lower()

    # Industrial / activity keywords — very favorable for DC
    industrial_kw = [
        "activit", "industriel", "logistique", "artisan", "entrepôt",
        "zone d'activit", "parc d'activit", "technolog",
        "equipement", "énergie", "portuaire",
    ]
    # Residential keywords — unfavorable
    residential_kw = [
        "habitat", "résidentiel", "logement", "collectif", "pavillonnaire",
        "densité", "maison",
    ]
    # Nature/agriculture keywords — eliminatory
    nature_kw = [
        "naturel", "agricol", "vignoble", "forestier", "espace vert",
    ]

    ind_count = sum(1 for k in industrial_kw if k in text)
    res_count = sum(1 for k in residential_kw if k in text)
    nat_count = sum(1 for k in nature_kw if k in text)

    if ind_count >= 2:
        flags.append("vocation_industrielle_confirmee")
        score_adj += 8
    elif ind_count == 1:
        flags.append("vocation_activite_probable")
        score_adj += 4

    if res_count >= 2:
        flags.append("vocation_residentielle_detectee")
        score_adj -= 10
    elif res_count == 1:
        flags.append("mixite_residentielle_possible")
        score_adj -= 5

    if nat_count >= 1:
        flags.append("vocation_naturelle_agricole_detectee")
        score_adj -= 15

    return {
        "flags": flags,
        "score_adjustment": score_adj,
        "industrial_signals": ind_count,
        "residential_signals": res_count,
        "nature_signals": nat_count,
    }


def score_plu_dynamic(gpu_context: dict) -> dict:
    """
    Scoring PLU DYNAMIQUE basé sur les données réelles de l'API GPU.
    Exploite zone-urba, prescriptions, informations, et le texte du règlement.

    Args:
        gpu_context: dict from api_carto.get_gpu_full_context()
            {
                "zone": {typezone, libelle, libelong, destdomi, nomfic, idurba, ...},
                "prescriptions": [{libelle, txt, typepsc, stypepsc}, ...],
                "informations": [{libelle, txt, typeinf, stypeinf}, ...],
            }

    Returns:
        Full PLU scoring dict with dynamic enrichment
    """
    zone = gpu_context.get("zone") or {}
    prescriptions = gpu_context.get("prescriptions", [])
    informations = gpu_context.get("informations", [])

    zone_code = zone.get("libelle", "") or zone.get("typezone", "inconnu")
    type_zone = zone.get("typezone", "")
    libelong = zone.get("libelong", "")
    destdomi = zone.get("destdomi", "")

    # Step 1: Base static scoring
    base_result = score_plu(
        zone_code=zone_code if zone_code else type_zone,
        zone_label=libelong,
        reglement_text=libelong,
    )

    # If already excluded, return immediately
    if base_result["plu_status"] == "EXCLUDED":
        base_result["gpu_source"] = "dynamic"
        base_result["gpu_data"] = {
            "zone_raw": zone,
            "prescriptions_count": len(prescriptions),
            "informations_count": len(informations),
        }
        return base_result

    # Step 2: Analyze prescriptions
    presc_analysis = _analyze_prescriptions(prescriptions)

    # Step 3: Analyze informations (risques, ZAC)
    info_analysis = _analyze_informations(informations)

    # Step 4: Analyze destination dominante + libelong
    dest_analysis = _detect_destdomi(destdomi, libelong)

    # Step 5: Combine all adjustments
    dynamic_adj = (
        presc_analysis["score_adjustment"]
        + info_analysis["score_adjustment"]
        + dest_analysis["score_adjustment"]
    )

    all_flags = (
        base_result.get("flags", [])
        + presc_analysis["flags"]
        + info_analysis["flags"]
        + dest_analysis["flags"]
    )

    all_adjustments = (
        base_result.get("adjustments", [])
        + presc_analysis["adjustments"]
        + info_analysis["adjustments"]
    )
    if dest_analysis["score_adjustment"] != 0:
        all_adjustments.append(("destination_dominante", f"{dest_analysis['score_adjustment']:+d}"))

    # Final score
    final_score = max(0, min(100, base_result["plu_score"] + dynamic_adj))

    # Hard exclusion override
    if presc_analysis["has_ebc"] and base_result["plu_score"] < 50:
        final_score = 0
        all_flags.append("hard_exclusion_ebc")

    status = _get_status(final_score)
    action = _get_recommended_action(status)
    risk = _get_risk_level(final_score, all_flags)

    # Deduplicate flags
    seen = set()
    unique_flags = []
    for f in all_flags:
        if f not in seen:
            seen.add(f)
            unique_flags.append(f)

    return {
        "plu_code": zone_code,
        "plu_label": libelong or base_result.get("plu_label", ""),
        "plu_score": final_score,
        "plu_score_base": base_result["plu_score"],
        "plu_score_dynamic_adj": dynamic_adj,
        "plu_status": status,
        "exclusion_reason": None if final_score > 0 else "Score nul après analyse dynamique GPU",
        "flags": unique_flags,
        "urbanism_risk": risk,
        "recommended_action": action,
        "category": base_result.get("category", "unknown"),
        "adjustments": all_adjustments,
        "keyword_analysis": base_result.get("keyword_analysis"),
        "gpu_source": "dynamic",
        "gpu_data": {
            "zone_raw": zone,
            "prescriptions_count": len(prescriptions),
            "informations_count": len(informations),
            "prescriptions_flags": presc_analysis["flags"],
            "informations_flags": info_analysis["flags"],
            "destination_analysis": dest_analysis,
            "risk_labels": info_analysis.get("risk_labels", []),
        },
    }
