"""
Cockpit Immo — PDF Export (Fiche Site)
Generates professional PDF reports for DC site analysis.
"""
import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


# Color palette matching the app
DARK = HexColor('#0a0a0f')
SURFACE = HexColor('#12121a')
BORDER = HexColor('#1f1f2e')
TEXT = HexColor('#e8e8ed')
TEXT_DIM = HexColor('#8f8f9d')
ACCENT = HexColor('#00d4aa')
WARNING = HexColor('#ffa502')
DANGER = HexColor('#ff4757')
SUCCESS = HexColor('#2ed573')
BLUE = HexColor('#3b82f6')
WHITE = HexColor('#ffffff')
BLACK = HexColor('#000000')


def _create_styles():
    """Create PDF styles"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='Title_Custom',
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=BLACK,
        spaceAfter=4*mm,
    ))
    styles.add(ParagraphStyle(
        name='Subtitle',
        fontName='Helvetica',
        fontSize=10,
        textColor=HexColor('#555555'),
        spaceAfter=6*mm,
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=HexColor('#1a1a2e'),
        spaceBefore=6*mm,
        spaceAfter=3*mm,
    ))
    styles.add(ParagraphStyle(
        name='BodyText_Custom',
        fontName='Helvetica',
        fontSize=9,
        textColor=HexColor('#333333'),
        spaceAfter=2*mm,
    ))
    styles.add(ParagraphStyle(
        name='SmallText',
        fontName='Helvetica',
        fontSize=7,
        textColor=HexColor('#888888'),
    ))
    styles.add(ParagraphStyle(
        name='KPI_Value',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=HexColor('#1a1a2e'),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name='KPI_Label',
        fontName='Helvetica',
        fontSize=7,
        textColor=HexColor('#888888'),
        alignment=TA_CENTER,
    ))
    return styles


def _score_color(score):
    if score >= 80: return '#2ed573'
    if score >= 50: return '#ffa502'
    return '#ff4757'


def _verdict_text(verdict):
    mapping = {
        'GO': 'GO',
        'CONDITIONNEL': 'CONDITIONNEL',
        'NO_GO': 'NO GO',
    }
    return mapping.get(verdict, verdict or 'N/A')


def generate_parcel_pdf(parcel: dict, dvf_data: dict = None) -> bytes:
    """Generate a PDF fiche for a parcel/site"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )
    
    styles = _create_styles()
    elements = []
    
    score = parcel.get('score', {})
    
    # ── HEADER ──
    elements.append(Paragraph('COCKPIT IMMO — Fiche Site', styles['Title_Custom']))
    
    commune = parcel.get('commune', parcel.get('name', 'N/A'))
    region = parcel.get('region', parcel.get('location', {}).get('region', ''))
    subtitle = f"{commune} · {region} · {datetime.now(timezone.utc).strftime('%d/%m/%Y')}"
    elements.append(Paragraph(subtitle, styles['Subtitle']))
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#cccccc')))
    elements.append(Spacer(1, 4*mm))
    
    # ── SCORE KPI BAR ──
    score_net = score.get('score_net', score.get('global', 0))
    verdict = score.get('verdict', 'N/A')
    power_mw = score.get('power_mw_p50', 0)
    
    kpi_data = [
        [
            Paragraph(f"<font color='{_score_color(score_net)}'>{score_net:.0f}/100</font>", styles['KPI_Value']),
            Paragraph(f"<font color='#1a1a2e'>{_verdict_text(verdict)}</font>", styles['KPI_Value']),
            Paragraph(f"<font color='#00d4aa'>{power_mw:.1f} MW</font>" if power_mw else "<font color='#888'>N/A</font>", styles['KPI_Value']),
            Paragraph(f"<font color='#3b82f6'>{parcel.get('plu_zone', 'N/A')}</font>", styles['KPI_Value']),
        ],
        [
            Paragraph('Score Global', styles['KPI_Label']),
            Paragraph('Verdict', styles['KPI_Label']),
            Paragraph('Puissance P50', styles['KPI_Label']),
            Paragraph('Zone PLU', styles['KPI_Label']),
        ],
    ]
    kpi_table = Table(kpi_data, colWidths=[45*mm]*4)
    kpi_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 0.5, HexColor('#cccccc')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, HexColor('#eeeeee')),
        ('BACKGROUND', (0,0), (-1,0), HexColor('#f8f8f8')),
        ('TOPPADDING', (0,0), (-1,-1), 3*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3*mm),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 5*mm))
    
    # ── LOCALISATION ──
    elements.append(Paragraph('Localisation', styles['SectionTitle']))
    loc_data = [
        ['Commune', commune],
        ['Région', region],
        ['Département', parcel.get('code_dep', parcel.get('location', {}).get('region', 'N/A'))],
    ]
    if parcel.get('latitude') or parcel.get('location', {}).get('lat'):
        lat = parcel.get('latitude', parcel.get('location', {}).get('lat', 0))
        lng = parcel.get('longitude', parcel.get('location', {}).get('lng', 0))
        loc_data.append(['Coordonnées', f"{lat:.5f}, {lng:.5f}"])
    if parcel.get('surface_m2'):
        loc_data.append(['Surface', f"{parcel['surface_m2']:,.0f} m² ({parcel['surface_m2']/10000:.2f} ha)"])
    if parcel.get('plu_libelle'):
        loc_data.append(['PLU Libellé', parcel['plu_libelle']])
    if parcel.get('plu_libelong'):
        loc_data.append(['PLU Description', parcel['plu_libelong'][:80]])
    
    elements.append(_make_data_table(loc_data))
    
    # ── RACCORDEMENT ÉLECTRIQUE ──
    elements.append(Paragraph('Raccordement Électrique', styles['SectionTitle']))
    grid_data = []
    
    if parcel.get('dist_poste_htb_m') is not None:
        grid_data.append(['Distance poste HTB', f"{parcel['dist_poste_htb_m']:,.0f} m ({parcel['dist_poste_htb_m']/1000:.1f} km)"])
    if parcel.get('tension_htb_kv'):
        grid_data.append(['Tension HTB', f"{parcel['tension_htb_kv']} kV"])
    
    # From DC search API format
    grid = parcel.get('grid', {})
    if grid:
        if grid.get('voltage_level'):
            grid_data.append(['Tension', grid['voltage_level']])
        if grid.get('available_capacity_mw') is not None:
            grid_data.append(['Capacité disponible', f"{grid['available_capacity_mw']} MW"])
        if grid.get('estimated_capacity_mw'):
            grid_data.append(['Capacité estimée', f"{grid['estimated_capacity_mw']} MW"])
        if grid.get('saturation_level'):
            grid_data.append(['Saturation réseau', grid['saturation_level'].upper()])
        if grid.get('reinforcement_planned'):
            grid_data.append(['Renforcement prévu', grid.get('reinforcement_detail', 'Oui')])
    
    score_elec = score.get('score_electricite', 0)
    if score_elec:
        grid_data.append(['Score électricité', f"{score_elec:.0f}/100"])
    
    if grid_data:
        elements.append(_make_data_table(grid_data))
    else:
        elements.append(Paragraph("Données non disponibles", styles['BodyText_Custom']))
    
    # ── CONNECTIVITÉ ──
    elements.append(Paragraph('Connectivité', styles['SectionTitle']))
    conn_data = []
    if parcel.get('dist_landing_point_km') is not None:
        conn_data.append(['Distance landing point', f"{parcel['dist_landing_point_km']} km"])
    if parcel.get('landing_point_nom'):
        conn_data.append(['Landing point', parcel['landing_point_nom']])
    
    connectivity = parcel.get('connectivity', {})
    if connectivity:
        if connectivity.get('nearest_landing_point'):
            conn_data.append(['Landing point', f"{connectivity['nearest_landing_point']} ({connectivity.get('nearest_landing_point_km', '?')} km)"])
        if connectivity.get('nearest_dc_km') is not None:
            conn_data.append(['DC le plus proche', f"{connectivity['nearest_dc_km']} km"])
    
    score_fibre = score.get('score_fibre', 0)
    if score_fibre:
        conn_data.append(['Score fibre', f"{score_fibre:.0f}/100"])
    
    if conn_data:
        elements.append(_make_data_table(conn_data))
    
    # ── TIMELINE ──
    timeline = parcel.get('timeline', {})
    if timeline:
        elements.append(Paragraph('Timeline', styles['SectionTitle']))
        tl_data = []
        if timeline.get('estimated_connection_delay_months'):
            tl_data.append(['Délai raccordement estimé', f"{timeline['estimated_connection_delay_months']} mois"])
        if timeline.get('delay_range_months'):
            r = timeline['delay_range_months']
            tl_data.append(['Fourchette', f"{r[0]} - {r[1]} mois"])
        if timeline.get('permitting_risk'):
            tl_data.append(['Risque administratif', timeline['permitting_risk'].upper()])
        ttm_min = score.get('ttm_min_months')
        ttm_max = score.get('ttm_max_months')
        if ttm_min:
            tl_data.append(['TTM estimé', f"{ttm_min} - {ttm_max} mois"])
        if tl_data:
            elements.append(_make_data_table(tl_data))
    
    # ── DVF / FONCIER ──
    elements.append(Paragraph('Données Foncières (DVF)', styles['SectionTitle']))
    dvf_rows = []
    land = parcel.get('land', {})
    if land:
        dvf_rows.append(['Type terrain', land.get('type', 'N/A')])
        dvf_rows.append(['Prix estimé', f"{land.get('price_per_m2', 'N/A')} €/m²"])
        dvf_rows.append(['Surface', f"{land.get('surface_ha', 'N/A')} ha"])
    
    if dvf_data:
        dvf_rows.append(['Prix médian DVF (dépt.)', f"{dvf_data.get('prix_median_m2', 'N/A')} €/m²"])
        dvf_rows.append(['Fourchette DVF', f"{dvf_data.get('prix_q1_m2', '?')} - {dvf_data.get('prix_q3_m2', '?')} €/m²"])
        dvf_rows.append(['Transactions (dépt.)', f"{dvf_data.get('nb_transactions', 0):,}"])
        dvf_rows.append(['Source', dvf_data.get('source', 'DVF')])
    
    if dvf_rows:
        elements.append(_make_data_table(dvf_rows))
    
    # ── FUTURE LIGNE 400kV ──
    future_400kv = parcel.get('future_400kv', {})
    dist_future = parcel.get('dist_future_400kv_m')
    future_buffer = parcel.get('future_400kv_buffer')
    future_bonus = parcel.get('future_400kv_score_bonus', 0)
    future_grid_p = parcel.get('future_grid_potential', {})
    
    if dist_future is not None or future_400kv:
        elements.append(Paragraph('Future Ligne 400 kV (Fos → Jonquières)', styles['SectionTitle']))
        f_rows = []
        d = dist_future or future_400kv.get('distance_m', 0)
        if d:
            f_rows.append(['Distance à la ligne', f"{d:,.0f} m ({d/1000:.1f} km)"])
        bz = future_buffer or future_400kv.get('buffer_zone')
        if bz:
            zone_label = {'1km': 'Zone chaude (1 km)', '3km': 'Zone stratégique (3 km)', '5km': 'Zone opportunité (5 km)'}.get(bz, bz)
            f_rows.append(['Zone', zone_label])
        bonus = future_bonus or future_400kv.get('score_bonus', 0)
        f_rows.append(['Bonus scoring', f"+{bonus} pts"])
        fgp = future_grid_p or future_400kv.get('future_grid_potential', {})
        if fgp:
            f_rows.append(['Potentiel réseau futur', f"{fgp.get('future_grid_potential_score', 0)}/100 ({fgp.get('future_grid_category', 'N/A')})"])
        f_rows.append(['Mise en service estimée', '~2029 (projet RTE)'])
        elements.append(_make_data_table(f_rows))
    
    # ── COMMENTAIRE ──
    comment = parcel.get('comment', '')
    if comment:
        elements.append(Paragraph('Analyse', styles['SectionTitle']))
        elements.append(Paragraph(comment, styles['BodyText_Custom']))
    
    # ── TAGS ──
    tags = parcel.get('tags', [])
    if tags:
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(f"Tags: {', '.join(tags)}", styles['SmallText']))
    
    # ── FOOTER ──
    elements.append(Spacer(1, 8*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#cccccc')))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(
        f"Cockpit Immo — Généré le {datetime.now(timezone.utc).strftime('%d/%m/%Y à %H:%M UTC')} — Données S3REnR (RTE) + API Carto IGN + DVF",
        styles['SmallText'],
    ))
    
    doc.build(elements)
    return buffer.getvalue()


def _make_data_table(data):
    """Create a two-column data table"""
    styled_data = []
    for row in data:
        styled_data.append([
            Paragraph(f"<font color='#666666'>{row[0]}</font>", ParagraphStyle('left', fontName='Helvetica', fontSize=8)),
            Paragraph(f"<font color='#1a1a2e'><b>{row[1]}</b></font>", ParagraphStyle('right', fontName='Helvetica-Bold', fontSize=8, alignment=TA_RIGHT)),
        ])
    
    t = Table(styled_data, colWidths=[60*mm, 110*mm])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [HexColor('#ffffff'), HexColor('#f8f8fa')]),
        ('TOPPADDING', (0,0), (-1,-1), 2*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2*mm),
        ('LEFTPADDING', (0,0), (-1,-1), 3*mm),
        ('RIGHTPADDING', (0,0), (-1,-1), 3*mm),
        ('BOX', (0,0), (-1,-1), 0.5, HexColor('#dddddd')),
        ('LINEBELOW', (0,0), (-1,-2), 0.25, HexColor('#eeeeee')),
    ]))
    return t
