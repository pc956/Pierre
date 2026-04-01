"""
Cockpit Immo - Scoring Engine v3
Score universel /100 pour prospection foncière data center.
5 axes + malus. Optimisé pour cible DC 10 MW.
Axes: Distance RTE (35pts), MW S3REnR (25pts), PLU (20pts), Surface (10pts), TTM raccordement (10pts)
"""
from typing import Dict, Any, List

# ═══════════════════════════════════════════════════════════
# PLU ZONES
# ═══════════════════════════════════════════════════════════

PLU_ZONES = {
    'I': {'label': 'Zone industrielle', 'compatible': True, 'commentaire': 'Parfait pour DC'},
    'IX': {'label': 'Zone industrielle étendue', 'compatible': True, 'commentaire': 'Compatible'},
    'UX': {'label': 'Zone urbaine activités', 'compatible': True, 'commentaire': 'Compatible DC'},
    'UI': {'label': 'Zone urbaine industrielle', 'compatible': True, 'commentaire': 'Compatible'},
    'UE': {'label': 'Zone urbaine économique', 'compatible': True, 'commentaire': 'Compatible'},
    'AUX': {'label': 'À urbaniser activités', 'compatible': 'sous_conditions', 'commentaire': 'Procédure PLU requise'},
    'AU': {'label': 'À urbaniser', 'compatible': 'sous_conditions', 'commentaire': 'Modification PLU requise'},
    '1AU': {'label': 'AU ouvert', 'compatible': 'sous_conditions', 'commentaire': 'Procédure simplifiée possible'},
    '2AU': {'label': 'AU fermé', 'compatible': 'sous_conditions', 'commentaire': 'Révision PLU requise'},
    'U': {'label': 'Zone urbaine', 'compatible': 'sous_conditions', 'commentaire': 'Vérifier règlement'},
    'A': {'label': 'Zone agricole', 'compatible': False, 'commentaire': 'Incompatible - zone protégée'},
    'N': {'label': 'Zone naturelle', 'compatible': False, 'commentaire': 'Incompatible - zone protégée'},
}


def compute_score_simple(parcel: dict) -> dict:
    """Score universel /100 pour prospection foncière data center.
    5 axes + malus. Retourne score, verdict, ttm_months, détail, flags, resume."""

    flags: List[str] = []

    # ─── AXE 1 — Distance poste RTE (0 à 35 pts) ───
    dist_htb_m = parcel.get("dist_poste_htb_m") or 99999
    dist_htb_km = dist_htb_m / 1000

    if dist_htb_km < 1:
        pts_distance = 35
    elif dist_htb_km < 2:
        pts_distance = 30
    elif dist_htb_km < 3:
        pts_distance = 24
    elif dist_htb_km < 5:
        pts_distance = 17
    elif dist_htb_km < 8:
        pts_distance = 10
    elif dist_htb_km < 12:
        pts_distance = 4
    else:
        pts_distance = 0

    # Bonus tension
    tension_kv = parcel.get("tension_htb_kv") or 0
    if tension_kv >= 400:
        pts_distance = min(35, pts_distance + 4)
    elif tension_kv >= 225:
        pts_distance = min(35, pts_distance + 2)

    # ─── AXE 2 — MW disponibles S3REnR (0 à 25 pts) ───
    etat_s3renr = (parcel.get("zone_saturation") or "inconnu").lower()
    mw_dispo = parcel.get("mw_dispo") or 0
    renforcement = parcel.get("renforcement_prevu")

    if etat_s3renr == "disponible":
        if mw_dispo >= 50:
            pts_mw = 25
        elif mw_dispo >= 20:
            pts_mw = 23
        elif mw_dispo >= 10:
            pts_mw = 20
        elif mw_dispo >= 5:
            pts_mw = 15
        elif mw_dispo > 0:
            pts_mw = 8
        else:
            pts_mw = 10
    elif etat_s3renr in ("contraint", "tendu"):
        pts_mw = 6
    elif etat_s3renr == "sature":
        pts_mw = 0
    else:
        pts_mw = 8  # inconnu

    # Bonus renforcement prévu
    if renforcement:
        pts_mw = min(25, pts_mw + 4)

    # ─── AXE 3 — Compatibilité PLU (0 à 20 pts) ───
    plu_zone = (parcel.get("plu_zone") or "inconnu").upper().strip()
    non_constructible = False

    if plu_zone in ("UI", "UX", "UE", "I", "IX"):
        pts_plu = 20
    elif plu_zone in ("1AU", "AUX"):
        pts_plu = 12
    elif plu_zone == "U":
        pts_plu = 10
    elif plu_zone == "2AU":
        pts_plu = 5
    elif plu_zone == "A":
        pts_plu = 0
        non_constructible = True
        flags.append("NON CONSTRUCTIBLE (zone agricole)")
    elif plu_zone == "N":
        pts_plu = 0
        non_constructible = True
        flags.append("NON CONSTRUCTIBLE (zone naturelle)")
    else:
        pts_plu = 8  # inconnu

    # ─── AXE 4 — Surface (0 à 10 pts) — calibré 10MW (1-2 ha idéal) ───
    surface_ha = parcel.get("surface_ha") or (parcel.get("surface_m2", 0) / 10000)

    if surface_ha >= 3:
        pts_surface = 10
    elif surface_ha >= 2:
        pts_surface = 9
    elif surface_ha >= 1:
        pts_surface = 7
    elif surface_ha >= 0.5:
        pts_surface = 4
    else:
        pts_surface = 0

    # ─── AXE 5 — Délai raccordement estimé (0 à 10 pts) ───
    ttm_months = 36  # Défaut

    if dist_htb_km < 1 and etat_s3renr == "disponible" and mw_dispo >= 10:
        ttm_months = 14
        pts_ttm = 10
    elif dist_htb_km < 3 and etat_s3renr == "disponible" and mw_dispo >= 10:
        ttm_months = 20
        pts_ttm = 7
    elif dist_htb_km < 5 and etat_s3renr == "disponible":
        ttm_months = 28
        pts_ttm = 4
    elif etat_s3renr in ("contraint", "tendu"):
        ttm_months = 36
        pts_ttm = 1
    elif etat_s3renr == "sature":
        ttm_months = 48
        pts_ttm = 0
    else:
        ttm_months = 30
        pts_ttm = 2

    # Si renforcement prévu par RTE, ajuster
    if renforcement:
        ttm_months = max(12, ttm_months - 6)
        pts_ttm = min(10, pts_ttm + 2)

    # ─── MALUS ───
    malus_total = 0

    # PPRI inondation
    ppri = parcel.get("ppri_zone")
    if ppri and ppri.lower() in ("rouge", "true", "oui"):
        malus_total -= 15
        flags.append("ZONE INONDABLE (PPRI)")

    # Sismique
    sismique = parcel.get("sismique_zone") or parcel.get("zone_sismique") or 1
    if isinstance(sismique, str):
        try:
            sismique = int(sismique)
        except ValueError:
            sismique = 1
    if sismique >= 4:
        malus_total -= 8
        flags.append(f"ZONE SISMIQUE {sismique}")

    # Réseau saturé (en plus du 0 pts sur axe 2)
    if etat_s3renr == "sature":
        malus_total -= 10
        flags.append("RESEAU SATURE")

    # Archéologie DRAC
    if parcel.get("drac_zone_archeo"):
        malus_total -= 3
        flags.append("ZONE ARCHEOLOGIQUE (DRAC)")

    # ─── SCORE TOTAL ───
    score_brut = pts_distance + pts_mw + pts_plu + pts_surface + pts_ttm
    score_total = max(0, min(100, score_brut + malus_total))

    # ─── VERDICT ───
    if non_constructible:
        verdict = "EXCLU"
    elif score_total >= 70:
        verdict = "GO"
    elif score_total >= 40:
        verdict = "A_ETUDIER"
    else:
        verdict = "DEFAVORABLE"

    # ─── RESUME AUTO ───
    nearest_htb = parcel.get("nearest_htb_name") or "poste HTB"
    resume_parts = [f"Score {score_total}/100 — {verdict}."]

    if surface_ha > 0:
        resume_parts.append(f"Parcelle de {surface_ha:.1f} ha")

    if plu_zone and plu_zone != "INCONNU":
        resume_parts.append(f"en zone PLU {plu_zone}")

    if dist_htb_km < 50:
        tension_str = f" ({int(tension_kv)}kV)" if tension_kv else ""
        resume_parts.append(f"à {dist_htb_km:.1f} km du {nearest_htb}{tension_str}")

    if etat_s3renr == "disponible" and mw_dispo > 0:
        resume_parts.append(f"avec {int(mw_dispo)} MW disponibles")
    elif etat_s3renr == "sature":
        resume_parts.append("réseau saturé")

    resume_parts.append(f"Raccordement estimé: ~{ttm_months} mois")

    # Cours d'eau
    dist_eau = parcel.get("dist_cours_eau_m")
    nom_eau = parcel.get("nom_cours_eau")
    if dist_eau and dist_eau < 1000:
        resume_parts.append(f"à {dist_eau}m de {nom_eau or 'un cours d eau'} (refroidissement)")
    elif dist_eau and dist_eau < 3000:
        resume_parts.append(f"cours d'eau à {dist_eau/1000:.1f} km")

    # Route principale
    dist_route = parcel.get("dist_route_m")
    if dist_route and dist_route < 2000:
        resume_parts.append(f"à {dist_route}m de {parcel.get('nom_route', 'axe routier')} ({parcel.get('type_route', '')})")

    projet_fos = parcel.get("projet_fos")
    if projet_fos:
        resume_parts.append(f"Projet RTE Fos-Jonquières: {projet_fos}")

    if flags:
        risk_flags = [f for f in flags if "NON CONSTRUCTIBLE" not in f]
        if risk_flags:
            resume_parts.append(f"Risques: {', '.join(risk_flags)}")
        elif non_constructible:
            resume_parts.append("Terrain non constructible")
    else:
        resume_parts.append("Pas de risques identifiés")

    resume = ", ".join(resume_parts) + "."

    return {
        "score": score_total,
        "verdict": verdict,
        "ttm_months": ttm_months,
        "detail": {
            "distance_rte": pts_distance,
            "mw_disponibles": pts_mw,
            "plu": pts_plu,
            "surface": pts_surface,
            "raccordement_speed": pts_ttm,
            "malus": malus_total,
        },
        "flags": flags,
        "resume": resume,
    }
