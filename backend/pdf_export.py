"""
Cockpit Immo — PDF Export v2 : Fiche d'Opportunité
2 pages max. Fond blanc, lisible, pousse à l'action.
Score /100, points forts, données clés, risques, budget, timeline, prochaines étapes.
"""
import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


# ── Colors ──
GREEN = HexColor('#2ed573')
ORANGE = HexColor('#ffa502')
RED = HexColor('#ff4757')
GREY = HexColor('#95a5a6')
DARK = HexColor('#1a1a2e')
LIGHT_GREY = HexColor('#f8f8fa')
BORDER = HexColor('#dddddd')
TEXT_DIM = HexColor('#666666')
BLACK = HexColor('#000000')
WHITE = HexColor('#ffffff')


def _score_color(score):
    if score >= 70:
        return '#2ed573'
    if score >= 40:
        return '#ffa502'
    return '#ff4757'


def _verdict_color(verdict):
    v = (verdict or "").upper()
    if v == "GO":
        return GREEN
    if v in ("A_ETUDIER", "À ÉTUDIER"):
        return ORANGE
    if v == "EXCLU":
        return GREY
    return RED


def _verdict_label(verdict):
    mapping = {
        "GO": "GO",
        "A_ETUDIER": "À ÉTUDIER",
        "DEFAVORABLE": "DÉFAVORABLE",
        "EXCLU": "EXCLU",
    }
    return mapping.get(verdict, verdict or "N/A")


def _styles():
    return {
        'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=16, textColor=DARK, spaceAfter=2*mm),
        'subtitle': ParagraphStyle('subtitle', fontName='Helvetica', fontSize=9, textColor=TEXT_DIM, spaceAfter=4*mm),
        'section': ParagraphStyle('section', fontName='Helvetica-Bold', fontSize=11, textColor=DARK, spaceBefore=5*mm, spaceAfter=2*mm),
        'body': ParagraphStyle('body', fontName='Helvetica', fontSize=9, textColor=HexColor('#333333'), spaceAfter=1.5*mm, leading=12),
        'small': ParagraphStyle('small', fontName='Helvetica', fontSize=7, textColor=HexColor('#888888')),
        'score_big': ParagraphStyle('score_big', fontName='Helvetica-Bold', fontSize=22, alignment=TA_CENTER),
        'verdict_big': ParagraphStyle('verdict_big', fontName='Helvetica-Bold', fontSize=14, alignment=TA_CENTER),
        'kpi_label': ParagraphStyle('kpi_label', fontName='Helvetica', fontSize=7, textColor=TEXT_DIM, alignment=TA_CENTER),
        'bullet': ParagraphStyle('bullet', fontName='Helvetica', fontSize=9, textColor=HexColor('#333333'), leftIndent=10, spaceAfter=1*mm, leading=12),
    }


def _data_table(rows):
    """Create a clean 2-column data table"""
    styled = []
    for label, value in rows:
        styled.append([
            Paragraph(f"<font color='#666666'>{label}</font>", ParagraphStyle('l', fontName='Helvetica', fontSize=8)),
            Paragraph(f"<font color='#1a1a2e'><b>{value}</b></font>", ParagraphStyle('r', fontName='Helvetica-Bold', fontSize=8, alignment=TA_RIGHT)),
        ])
    t = Table(styled, colWidths=[65*mm, 105*mm])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, LIGHT_GREY]),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
        ('LEFTPADDING', (0, 0), (-1, -1), 3*mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3*mm),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER),
        ('LINEBELOW', (0, 0), (-1, -2), 0.25, HexColor('#eeeeee')),
    ]))
    return t


def generate_parcel_pdf(parcel: dict, dvf_data: dict = None) -> bytes:
    """Generate a 2-page Fiche d'Opportunité PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=12*mm, bottomMargin=12*mm,
    )
    s = _styles()
    elements = []

    score_obj = parcel.get("score", {})
    # Support both old format (score_net) and new format (score)
    score_val = score_obj.get("score", score_obj.get("score_net", 0))
    verdict = score_obj.get("verdict", "A_ETUDIER")
    detail = score_obj.get("detail", {})
    flags = score_obj.get("flags", [])
    resume = score_obj.get("resume", "")

    commune = parcel.get("commune", parcel.get("name", "N/A"))
    region = parcel.get("region", parcel.get("location", {}).get("region", ""))
    ref = parcel.get("ref_cadastrale", "")
    surface_m2 = parcel.get("surface_m2", 0)
    surface_ha = parcel.get("surface_ha", surface_m2 / 10000 if surface_m2 else 0)
    dist_htb_m = parcel.get("dist_poste_htb_m", 0)
    tension_kv = parcel.get("tension_htb_kv", 0)
    htb_name = parcel.get("nearest_htb_name", "")
    mw_dispo = parcel.get("mw_dispo", 0)
    zone_sat = parcel.get("zone_saturation", "inconnu")
    plu_zone = parcel.get("plu_zone", "inconnu")
    plu_libelle = parcel.get("plu_libelle", "")
    dvf_prix = parcel.get("dvf_prix_median_m2", 0)
    renforcement = parcel.get("renforcement_prevu", "")
    lat = parcel.get("latitude", parcel.get("location", {}).get("lat", 0))
    lng = parcel.get("longitude", parcel.get("location", {}).get("lng", 0))

    # ════════════════════════════════════════════
    # PAGE 1 — SYNTHÈSE DÉCISIONNELLE
    # ════════════════════════════════════════════

    # Header
    elements.append(Paragraph("COCKPIT IMMO — Fiche d'Opportunité", s['title']))
    date_str = datetime.now(timezone.utc).strftime('%d/%m/%Y')
    elements.append(Paragraph(f"{commune} · {region} · Réf. {ref} · {date_str}", s['subtitle']))

    # Score banner
    sc = _score_color(score_val)
    score_data_table = [
        [
            Paragraph(f"<font color='{sc}'>{score_val}/100</font>", s['score_big']),
            Paragraph(f"<font color='{sc}'>{_verdict_label(verdict)}</font>", s['verdict_big']),
        ],
        [
            Paragraph("Score Global", s['kpi_label']),
            Paragraph("Verdict", s['kpi_label']),
        ],
    ]
    score_t = Table(score_data_table, colWidths=[90*mm, 90*mm])
    score_t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f0f0f0')),
        ('BOX', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 3*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3*mm),
    ]))
    elements.append(score_t)
    elements.append(Spacer(1, 4*mm))

    # ── SECTION 1: POURQUOI CE TERRAIN (max 3 points forts) ──
    elements.append(Paragraph("POURQUOI CE TERRAIN", s['section']))
    strong_points = []
    if detail.get("distance_rte", 0) >= 30:
        strong_points.append(f"Seulement {dist_htb_m/1000:.1f} km du {htb_name} ({int(tension_kv)}kV)")
    if detail.get("mw_disponibles", 0) >= 25:
        strong_points.append(f"{int(mw_dispo)} MW disponibles sur le réseau (statut: {zone_sat})")
    if detail.get("plu", 0) >= 15:
        lbl = f" — {plu_libelle}" if plu_libelle else ""
        strong_points.append(f"Zone PLU {plu_zone}{lbl} compatible activités industrielles")
    if detail.get("surface", 0) >= 8:
        strong_points.append(f"Surface de {surface_ha:.1f} ha — adaptée pour un data center")
    if detail.get("malus", 0) == 0:
        strong_points.append("Aucun risque naturel ou réglementaire identifié")

    if not strong_points:
        strong_points.append(resume or "Parcelle à analyser plus en détail")

    for pt in strong_points[:3]:
        elements.append(Paragraph(f"• {pt}", s['bullet']))
    elements.append(Spacer(1, 2*mm))

    # ── SECTION 2: DONNÉES CLÉS ──
    elements.append(Paragraph("DONNÉES CLÉS", s['section']))
    key_rows = [
        ("Localisation", f"{commune}, {region}"),
        ("Coordonnées GPS", f"{lat:.5f}, {lng:.5f}"),
        ("Surface", f"{surface_m2:,.0f} m² ({surface_ha:.2f} ha)"),
        ("Zone PLU", f"{plu_zone}" + (f" — {plu_libelle}" if plu_libelle else "")),
        ("Poste RTE", f"{htb_name} ({int(tension_kv)}kV) à {dist_htb_m/1000:.1f} km"),
        ("MW disponibles", f"{int(mw_dispo)} MW (S3REnR: {zone_sat})"),
    ]
    if dvf_prix:
        key_rows.append(("Prix foncier estimé", f"{dvf_prix} €/m² (source DVF)"))
    if renforcement:
        key_rows.append(("Renforcement prévu", str(renforcement)))
    dist_eau = parcel.get("dist_cours_eau_m")
    nom_eau = parcel.get("nom_cours_eau")
    if dist_eau:
        key_rows.append(("Cours d'eau", f"{nom_eau or 'Cours d eau'} à {dist_eau/1000:.1f} km"))
    dist_route = parcel.get("dist_route_m")
    if dist_route:
        key_rows.append(("Route principale", f"{parcel.get('nom_route', 'Route')} ({parcel.get('type_route', '')}) à {dist_route/1000:.1f} km"))
    elements.append(_data_table(key_rows))
    elements.append(Spacer(1, 2*mm))

    # ── SECTION 3: RISQUES ──
    elements.append(Paragraph("RISQUES", s['section']))
    if flags:
        for f in flags:
            elements.append(Paragraph(f"⚠ {f}", s['bullet']))
    else:
        elements.append(Paragraph("Aucun risque identifié à ce stade.", s['body']))

    # ── Score breakdown bars ──
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph("DÉTAIL DU SCORE", s['section']))
    breakdown_rows = [
        ("Distance RTE", f"{detail.get('distance_rte', 0)}/40"),
        ("MW disponibles", f"{detail.get('mw_disponibles', 0)}/30"),
        ("Compatibilité PLU", f"{detail.get('plu', 0)}/20"),
        ("Surface", f"{detail.get('surface', 0)}/10"),
        ("Malus", f"{detail.get('malus', 0)}"),
    ]
    elements.append(_data_table(breakdown_rows))

    # ════════════════════════════════════════════
    # PAGE 2 — PLAN D'ACTION
    # ════════════════════════════════════════════

    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#cccccc')))
    elements.append(Spacer(1, 4*mm))

    # ── SECTION 4: BUDGET INDICATIF ──
    elements.append(Paragraph("BUDGET INDICATIF", s['section']))

    foncier_eur = surface_m2 * dvf_prix if dvf_prix and surface_m2 else 0
    foncier_meur = foncier_eur / 1_000_000 if foncier_eur else 0

    # Connection cost estimate
    dist_km = dist_htb_m / 1000 if dist_htb_m else 5
    if dist_km < 2 and zone_sat in ("disponible",):
        racc_low, racc_high = 0.3, 0.8
        racc_note = "0.3 à 0.8 M€/MW"
    elif dist_km < 5 and zone_sat in ("disponible", "inconnu"):
        racc_low, racc_high = 0.5, 1.2
        racc_note = "0.5 à 1.2 M€/MW"
    elif zone_sat == "sature":
        racc_low, racc_high = 0, 0
        racc_note = "Non quantifiable — raccordement très incertain"
    else:
        racc_low, racc_high = 1.0, 3.0
        racc_note = "1.0 à 3.0 M€/MW"

    mw_target = max(mw_dispo, 20) if mw_dispo else 20
    racc_meur = ((racc_low + racc_high) / 2) * mw_target if racc_low else 0

    budget_rows = [
        ("Foncier", f"{surface_ha:.1f} ha × {dvf_prix} €/m² = {foncier_meur:.1f} M€" if foncier_meur else "Données insuffisantes"),
        ("Raccordement électrique", f"~{racc_meur:.1f} M€ ({racc_note})" if racc_meur else racc_note),
        ("Total indicatif", f"~{foncier_meur + racc_meur:.1f} M€" if (foncier_meur or racc_meur) else "À chiffrer"),
    ]
    elements.append(_data_table(budget_rows))
    elements.append(Spacer(1, 2*mm))

    # ── SECTION 5: TIMELINE INDICATIVE ──
    elements.append(Paragraph("TIMELINE INDICATIVE", s['section']))
    timeline_rows = [
        ("1. Due diligence foncière + PLU", "1 à 3 mois"),
        ("2. Demande PTF RTE/Enedis", "3 à 6 mois"),
        ("3. Permis de construire + ICPE", "6 à 18 mois (si zone compatible)"),
    ]
    if zone_sat == "sature":
        timeline_rows.append(("4. Travaux raccordement", "Très incertain (réseau saturé)"))
    elif dist_km > 5:
        timeline_rows.append(("4. Travaux raccordement", "18 à 36 mois (distance élevée)"))
    else:
        timeline_rows.append(("4. Travaux raccordement", "6 à 18 mois"))
    elements.append(_data_table(timeline_rows))
    elements.append(Spacer(1, 2*mm))

    # ── SECTION 6: PROCHAINES ÉTAPES ──
    elements.append(Paragraph("PROCHAINES ÉTAPES", s['section']))
    steps = [
        (
            "VÉRIFIER LA DISPONIBILITÉ DU FONCIER",
            "Consulter le cadastre et identifier le propriétaire via le service de publicité foncière (SPF). Coût : ~15€ par relevé de propriété."
        ),
        (
            "CONTACTER RTE POUR LA FAISABILITÉ ÉLECTRIQUE",
            "Déposer une demande de PTF (Proposition Technique et Financière). Contact : Bureau raccordement RTE — https://www.rte-france.com/nos-activites/raccordement. Délai réponse : ~3 mois."
        ),
        (
            "RENDEZ-VOUS URBANISME EN MAIRIE",
            f"Demander un Certificat d'Urbanisme opérationnel (CUb) pour confirmer la constructibilité. Mairie de {commune}. Délai légal : 2 mois."
        ),
        (
            "ÉTUDE ENVIRONNEMENTALE PRÉLIMINAIRE",
            "Commander une étude d'impact environnemental si nécessaire. Vérifier les servitudes sur Géorisques : https://www.georisques.gouv.fr"
        ),
        (
            "NÉGOCIATION FONCIÈRE",
            f"Engager les discussions avec le propriétaire ou l'aménageur de la ZAE. Budget foncier indicatif : {foncier_meur:.1f} M€." if foncier_meur else "Engager les discussions avec le propriétaire."
        ),
    ]
    for i, (title, desc) in enumerate(steps, 1):
        elements.append(Paragraph(f"<b>{i}. {title}</b>", s['body']))
        elements.append(Paragraph(desc, s['bullet']))
        elements.append(Spacer(1, 1*mm))

    # ── FOOTER ──
    elements.append(Spacer(1, 6*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#cccccc')))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(
        f"Cockpit Immo — Données : RTE S3REnR, IGN Cadastre, GPU Urbanisme, DVF Etalab, Géorisques. "
        f"Généré le {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')}.",
        s['small']
    ))
    elements.append(Paragraph(
        "Ce document est une aide à la décision. Les données sont indicatives et doivent être vérifiées.",
        s['small']
    ))

    doc.build(elements)
    return buffer.getvalue()
