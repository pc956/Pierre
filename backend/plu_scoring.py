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
