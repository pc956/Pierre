"""
Cockpit Immo - Scoring Engine
Implements the complete scoring methodology from spec v5.3
"""
from typing import Dict, Any, Optional, Tuple, List
from models import Parcel, ParcelScore, ProjectType, Verdict, UrbaCompatibilite, ZoneSaturation
import math

# ═══════════════════════════════════════════════════════════
# CONSTANTS & WEIGHTS
# ═══════════════════════════════════════════════════════════

WEIGHTS = {
    'hyperscale': {'elec': 44, 'fibre': 12, 'eau': 19, 'surface': 12, 'marche': 6, 'climat': 7},
    'colocation_t3': {'elec': 38, 'fibre': 23, 'eau': 12, 'surface': 11, 'marche': 8, 'climat': 8},
    'colocation_t4': {'elec': 38, 'fibre': 19, 'eau': 14, 'surface': 10, 'marche': 9, 'climat': 10},
    'edge': {'elec': 24, 'fibre': 33, 'eau': 5, 'surface': 8, 'marche': 22, 'climat': 8},
    'ai_campus': {'elec': 44, 'fibre': 12, 'eau': 21, 'surface': 12, 'marche': 5, 'climat': 6},
}

# Densité MW par hectare selon type de projet
DENSITE_MW_HA = {
    'hyperscale': 4.0,
    'colocation_t3': 3.0,
    'colocation_t4': 3.5,
    'edge': 5.0,
    'ai_campus': 4.5,
}

# Minimum surface par type (hectares)
SURFACE_MIN_HA = {
    'hyperscale': 20.0,
    'colocation_t3': 2.0,
    'colocation_t4': 5.0,
    'edge': 0.3,
    'ai_campus': 8.0,
}

# PLU zones compatibility
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

# Benchmarks économiques
BENCHMARKS = {
    'dvf_fallback_eur_m2': {'IDF': 120, 'PACA': 95, 'AuRA': 70, 'HdF': 55, 'default': 65},
    'region_multiplier': {'IDF': 1.35, 'PACA': 1.15, 'AuRA': 1.0, 'HdF': 0.95},
    'construction_meur_par_mw': {
        'hyperscale': (7.5, 9.5),
        'colocation_t3': (8.5, 11.0),
        'colocation_t4': (9.0, 12.0),
        'edge': (10.0, 14.0),
        'ai_campus': (9.0, 12.0),
    },
    'prix_kw_mois': {
        'hyperscale': {'IDF': 95, 'province': 80},
        'colocation_t3': {'IDF': 140, 'province': 115},
        'colocation_t4': {'IDF': 155, 'province': 130},
        'edge': {'IDF': 180, 'province': 150},
        'ai_campus': {'IDF': 130, 'province': 110},
    },
    'opex_pct': {
        'hyperscale': 0.52,
        'colocation_t3': 0.58,
        'colocation_t4': 0.55,
        'edge': 0.62,
        'ai_campus': 0.54,
    },
    'occupation_ramp': {1: 0.20, 2: 0.45, 3: 0.65, 4: 0.75, 5: 0.78},
    'pue': {
        'free_cooling': (1.15, 1.20, 1.25),
        'free_cooling_partiel': (1.20, 1.28, 1.35),
        'mecanique': (1.35, 1.45, 1.55),
        'liquid_immersion': (1.02, 1.06, 1.10),
    },
}

# Types de travaux raccordement
TRAVAUX_RACCORDEMENT = {
    'simple_piquage': {
        'description': 'Piquage sur ligne existante, proximité poste',
        'delai_base': (6, 12),
        'cout_base_eur_par_mw': (150_000, 300_000),
    },
    'extension_poste': {
        'description': 'Extension poste existant (nouveau transfo ou cellule)',
        'delai_base': (12, 24),
        'cout_base_eur_par_mw': (400_000, 800_000),
    },
    'creation_ligne': {
        'description': 'Création ligne dédiée vers poste existant',
        'delai_base': (18, 36),
        'cout_base_eur_par_mw': (600_000, 1_200_000),
    },
    'creation_poste': {
        'description': 'Création nouveau poste source',
        'delai_base': (36, 72),
        'cout_base_eur_par_mw': (1_500_000, 3_000_000),
    },
    'renforcement_reseau': {
        'description': 'Renforcement réseau amont (file attente RTE)',
        'delai_base': (48, 96),
        'cout_base_eur_par_mw': (2_000_000, 5_000_000),
    },
}


# ═══════════════════════════════════════════════════════════
# SCORING FUNCTIONS
# ═══════════════════════════════════════════════════════════

def score_electricite(parcel: Dict[str, Any], project_type: str) -> float:
    """Score électricité /38 normalisé selon poids du projet"""
    w = WEIGHTS[project_type]['elec']
    
    d_htb = parcel.get('dist_poste_htb_m') or 50000
    
    if d_htb < 2000:
        base = 30
    elif d_htb < 5000:
        base = 22
    elif d_htb < 10000:
        base = 15
    elif d_htb < 15000:
        base = 8
    elif d_htb < 20000:
        base = 3
    else:
        base = 0
        # Fallback HTA
        d_hta = parcel.get('dist_poste_hta_m') or 50000
        if d_hta < 2000:
            base = 8
        elif d_hta < 5000:
            base = 5
        elif d_hta < 10000:
            base = 2
    
    bonus = 0
    if (parcel.get('dist_ligne_400kv_m') or 50000) < 3000:
        bonus += 5
    if (parcel.get('dist_ligne_225kv_m') or 50000) < 3000:
        bonus += 3
    if (parcel.get('dist_ligne_63kv_m') or 50000) < 1000:
        bonus += 2
    if parcel.get('capacite_confirmee_mw'):
        bonus += 4
    if parcel.get('zone_saturation') == 'disponible':
        bonus += 2
    
    raw = min(38, base + bonus)
    return round(raw * w / 38, 2)


def score_fibre(parcel: Dict[str, Any], project_type: str) -> float:
    """Score fibre /23 normalisé"""
    w = WEIGHTS[project_type]['fibre']
    
    dist = parcel.get('dist_backbone_fibre_m') or 10000
    
    if dist < 500:
        base = 15
    elif dist < 1500:
        base = 12
    elif dist < 3000:
        base = 8
    elif dist < 5000:
        base = 4
    else:
        base = 1
    
    bonus = 0
    nb_op = parcel.get('nb_operateurs_fibre') or 0
    if nb_op >= 3:
        bonus += 5
    elif nb_op >= 2:
        bonus += 3
    elif nb_op >= 1:
        bonus += 1
    
    if parcel.get('has_international'):
        bonus += 3
    
    raw = min(23, base + bonus)
    return round(raw * w / 23, 2)


def score_connectivite_intl(parcel: Dict[str, Any]) -> float:
    """Bonus connectivité internationale /15 (hors 100 pts)"""
    dist_km = parcel.get('dist_landing_point_km') or 500
    nb_cables = parcel.get('landing_point_nb_cables') or 0
    is_hub = parcel.get('landing_point_is_major_hub', False)
    
    # Score distance
    if dist_km < 50:
        score_dist = 8
    elif dist_km < 100:
        score_dist = 6
    elif dist_km < 200:
        score_dist = 4
    elif dist_km < 350:
        score_dist = 2
    else:
        score_dist = 0
    
    # Score cables
    if nb_cables >= 10:
        score_cables = 5
    elif nb_cables >= 5:
        score_cables = 3
    elif nb_cables >= 2:
        score_cables = 1
    else:
        score_cables = 0
    
    # Bonus hub majeur
    bonus_hub = 2 if is_hub else 0
    
    return min(15, score_dist + score_cables + bonus_hub)


def score_eau(parcel: Dict[str, Any], project_type: str) -> float:
    """Score eau /12 normalisé"""
    w = WEIGHTS[project_type]['eau']
    
    dist_eau = parcel.get('cours_eau_dist_m') or 10000
    stress = parcel.get('zone_stress_hydrique', False)
    
    if dist_eau < 1000:
        base = 10
    elif dist_eau < 3000:
        base = 7
    elif dist_eau < 5000:
        base = 4
    else:
        base = 2
    
    if stress:
        base = max(0, base - 4)
    
    raw = min(12, base)
    return round(raw * w / 12, 2)


def score_surface(parcel: Dict[str, Any], project_type: str) -> float:
    """Score surface /11 normalisé"""
    w = WEIGHTS[project_type]['surface']
    surface_ha = parcel.get('surface_ha') or parcel.get('surface_m2', 0) / 10000
    min_ha = SURFACE_MIN_HA[project_type]
    
    if surface_ha < min_ha:
        return 0  # Inéligible
    
    ratio = surface_ha / min_ha
    
    if ratio >= 3:
        base = 11
    elif ratio >= 2:
        base = 9
    elif ratio >= 1.5:
        base = 7
    elif ratio >= 1.2:
        base = 5
    else:
        base = 3
    
    # Bonus consolidation
    if parcel.get('surface_consolidable_ha'):
        if parcel['surface_consolidable_ha'] > surface_ha * 1.5:
            base = min(11, base + 2)
    
    return round(base * w / 11, 2)


def score_marche(parcel: Dict[str, Any], project_type: str) -> float:
    """Score marché DC /8 normalisé"""
    w = WEIGHTS[project_type]['marche']
    
    # Basé sur les DC voisins (cluster effect)
    dc_voisins = parcel.get('dc_voisins') or []
    nb_dc = len(dc_voisins)
    
    if nb_dc >= 5:
        base = 8  # Cluster majeur
    elif nb_dc >= 3:
        base = 6
    elif nb_dc >= 1:
        base = 4
    else:
        base = 2  # Marché moins mature
    
    # Ajustement région
    region = parcel.get('region', '')
    if region == 'IDF':
        base = min(8, base + 1)
    elif region == 'PACA':
        base = min(8, base + 1)
    
    return round(base * w / 8, 2)


def score_climat(parcel: Dict[str, Any], project_type: str) -> float:
    """Score climat /8 normalisé (favorise le nord pour free cooling)"""
    w = WEIGHTS[project_type]['climat']
    
    lat = parcel.get('latitude') or 46
    
    if lat > 49:
        base = 8
    elif lat > 47:
        base = 7
    elif lat > 45:
        base = 5
    elif lat > 43:
        base = 3
    else:
        base = 2
    
    return round(base * w / 8, 2)


def compute_malus(parcel: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """Calcule les malus techniques"""
    malus = 0
    details = {}
    
    # PPRI
    ppri = parcel.get('ppri_zone')
    if ppri == 'rouge':
        malus += 15
        details['ppri'] = {'impact': -15, 'raison': 'Zone PPRI rouge - constructibilité limitée'}
    elif ppri == 'bleu':
        malus += 5
        details['ppri'] = {'impact': -5, 'raison': 'Zone PPRI bleu - contraintes'}
    
    # Sismique
    sismique = parcel.get('sismique_zone', 1)
    if sismique >= 4:
        malus += 8
        details['sismique'] = {'impact': -8, 'raison': f'Zone sismique {sismique}'}
    elif sismique == 3:
        malus += 4
        details['sismique'] = {'impact': -4, 'raison': f'Zone sismique {sismique}'}
    
    # Argiles
    argiles = parcel.get('argiles_alea', 'faible')
    if argiles == 'fort':
        malus += 5
        details['argiles'] = {'impact': -5, 'raison': 'Aléa argiles fort'}
    elif argiles == 'moyen':
        malus += 2
        details['argiles'] = {'impact': -2, 'raison': 'Aléa argiles moyen'}
    
    # DRAC
    if parcel.get('drac_zone_archeo'):
        malus += 3
        details['drac'] = {'impact': -3, 'raison': 'Zone archéologique DRAC'}
    
    # Zone saturation réseau
    saturation = parcel.get('zone_saturation')
    if saturation == 'sature':
        malus += 10
        details['saturation'] = {'impact': -10, 'raison': 'Réseau électrique saturé'}
    elif saturation == 'tendu':
        malus += 5
        details['saturation'] = {'impact': -5, 'raison': 'Réseau électrique tendu'}
    
    return malus, details


def compute_score_technique(parcel: Dict[str, Any], project_type: str) -> Dict[str, Any]:
    """Calcul complet du score technique /100"""
    s_elec = score_electricite(parcel, project_type)
    s_fibre = score_fibre(parcel, project_type)
    s_connect = score_connectivite_intl(parcel)
    s_eau = score_eau(parcel, project_type)
    s_surface = score_surface(parcel, project_type)
    s_marche = score_marche(parcel, project_type)
    s_climat = score_climat(parcel, project_type)
    
    score_total = s_elec + s_fibre + s_eau + s_surface + s_marche + s_climat
    malus, malus_details = compute_malus(parcel)
    score_net = max(0, score_total - malus)
    
    # Shovel-ready bonus
    shovel_score = 0
    if parcel.get('raccordement_elec_existant'):
        shovel_score += 2
    if parcel.get('raccordement_fibre_existant'):
        shovel_score += 1
    if parcel.get('voirie_desserte_existante'):
        shovel_score += 1
    if parcel.get('dans_zac_active'):
        shovel_score += 1
    
    return {
        'score_electricite': s_elec,
        'score_fibre': s_fibre,
        'score_connectivite_intl': s_connect,
        'score_eau': s_eau,
        'score_surface': s_surface,
        'score_marche': s_marche,
        'score_climat': s_climat,
        'score_total': round(score_total, 2),
        'malus_total': malus,
        'malus_details': malus_details,
        'score_net': round(score_net, 2),
        'shovel_ready_score': shovel_score,
    }


# ═══════════════════════════════════════════════════════════
# URBANISME MODULE
# ═══════════════════════════════════════════════════════════

def compute_faisabilite_urbanistique(parcel: Dict[str, Any], project_type: str) -> Dict[str, Any]:
    """Module faisabilité urbanistique avec DFI"""
    plu_zone = parcel.get('plu_zone') or 'inconnu'
    conditions = []
    dfi_complexite_plu = 0
    dfi_risques_regl = 0
    dfi_contraintes_admin = 0
    
    # Analyse zone PLU
    zone_info = PLU_ZONES.get(plu_zone, {'compatible': 'sous_conditions', 'label': 'Zone inconnue'})
    
    if zone_info['compatible'] == True:
        compatibilite = UrbaCompatibilite.COMPATIBLE
        proba_base = 0.95
    elif zone_info['compatible'] == 'sous_conditions':
        compatibilite = UrbaCompatibilite.COMPATIBLE_SOUS_CONDITIONS
        proba_base = 0.70
        
        # Condition modification PLU
        if plu_zone in ['AU', '2AU']:
            conditions.append({
                'type': 'modification_plu',
                'label': 'Modification PLU',
                'delai_min': 18,
                'delai_max': 36,
                'proba_succes': 0.55,
                'sequentiel': True,
                'cout': 150000
            })
            dfi_complexite_plu += 25
        elif plu_zone in ['1AU', 'AUX']:
            conditions.append({
                'type': 'procedure_plu',
                'label': 'Procédure PLU simplifiée',
                'delai_min': 6,
                'delai_max': 12,
                'proba_succes': 0.75,
                'sequentiel': True,
                'cout': 50000
            })
            dfi_complexite_plu += 15
    else:
        compatibilite = UrbaCompatibilite.INCOMPATIBLE
        proba_base = 0.10
        dfi_complexite_plu += 40
    
    # ICPE
    icpe = parcel.get('icpe_regime')
    if icpe == 'autorisation':
        conditions.append({
            'type': 'icpe_autorisation',
            'label': 'ICPE Autorisation',
            'delai_min': 12,
            'delai_max': 24,
            'proba_succes': 0.80,
            'sequentiel': False,
            'cout': 150000
        })
        dfi_risques_regl += 15
    elif icpe == 'enregistrement':
        conditions.append({
            'type': 'icpe_enregistrement',
            'label': 'ICPE Enregistrement',
            'delai_min': 6,
            'delai_max': 8,
            'proba_succes': 0.90,
            'sequentiel': False,
            'cout': 60000
        })
        dfi_risques_regl += 8
    else:
        # Default pour DC: enregistrement
        conditions.append({
            'type': 'icpe_enregistrement',
            'label': 'ICPE Enregistrement',
            'delai_min': 6,
            'delai_max': 8,
            'proba_succes': 0.90,
            'sequentiel': False,
            'cout': 60000
        })
        dfi_risques_regl += 5
    
    # DRAC
    if parcel.get('drac_zone_archeo'):
        conditions.append({
            'type': 'drac_diagnostic',
            'label': 'Diagnostic archéologique DRAC',
            'delai_min': 2,
            'delai_max': 4,
            'proba_succes': 0.92,
            'sequentiel': False,
            'cout': 80000
        })
        dfi_contraintes_admin += 8
    
    # ZAN
    zan_pct = parcel.get('commune_zan_pct') or 0
    if zan_pct > 60:
        conditions.append({
            'type': 'vigilance_zan',
            'label': f'Vigilance ZAN ({zan_pct:.0f}%)',
            'delai_min': 0,
            'delai_max': 6,
            'proba_succes': 0.85,
            'sequentiel': False,
            'cout': 20000
        })
        dfi_contraintes_admin += 8
    elif zan_pct > 40:
        dfi_contraintes_admin += 4
    
    # Calcul probabilité combinée
    proba_combinee = proba_base
    for cond in conditions:
        proba_combinee *= cond['proba_succes']
    
    # Calcul délai total
    delai_seq = 0
    delai_parallel = 0
    for cond in conditions:
        if cond['sequentiel']:
            delai_seq += cond['delai_max']
        else:
            delai_parallel = max(delai_parallel, cond['delai_max'])
    
    delai_min = max(c['delai_min'] for c in conditions) if conditions else 0
    delai_max = delai_seq + delai_parallel
    
    # DFI total
    dfi = min(100, dfi_complexite_plu + dfi_risques_regl + dfi_contraintes_admin)
    
    if dfi < 15:
        dfi_cat = 'tres_faible'
    elif dfi < 30:
        dfi_cat = 'faible'
    elif dfi < 50:
        dfi_cat = 'moyen'
    elif dfi < 70:
        dfi_cat = 'eleve'
    else:
        dfi_cat = 'tres_eleve'
    
    # Risque
    if proba_combinee > 0.80:
        risque = 'faible'
    elif proba_combinee > 0.50:
        risque = 'moyen'
    elif proba_combinee > 0.20:
        risque = 'eleve'
    else:
        risque = 'bloquant'
    
    # Coûts indirects
    cout_etudes = sum(c['cout'] for c in conditions)
    cout_portage = 0
    if delai_max > 0:
        prix_m2 = parcel.get('dvf_prix_m2_p50') or 80
        surface_m2 = parcel.get('surface_m2') or 30000
        cout_portage = prix_m2 * surface_m2 * (delai_max / 12) * 0.07
    
    return {
        'urba_compatibilite': compatibilite.value,
        'urba_risque': risque,
        'urba_delai_min_mois': delai_min,
        'urba_delai_max_mois': delai_max,
        'urba_conditions': conditions,
        'urba_nb_conditions': len(conditions),
        'urba_proba_succes_combinee': round(proba_combinee, 2),
        'urba_deal_friction_index': dfi,
        'urba_dfi_categorie': dfi_cat,
        'urba_dfi_detail': {
            'complexite_plu': dfi_complexite_plu,
            'risques_reglementaires': dfi_risques_regl,
            'contraintes_admin': dfi_contraintes_admin,
        },
        'urba_couts_indirects': {
            'etudes_urbanistiques': round(cout_etudes),
            'portage_foncier': round(cout_portage),
            'total': round(cout_etudes + cout_portage),
        },
        'plu_zone_info': zone_info,
    }


# ═══════════════════════════════════════════════════════════
# RACCORDEMENT ESTIMATION
# ═══════════════════════════════════════════════════════════

def estimate_raccordement(parcel: Dict[str, Any], project_type: str, mw_demande: float) -> Dict[str, Any]:
    """Estimation délai et coût raccordement électrique"""
    
    # Déterminer tension cible
    if project_type in ('hyperscale', 'ai_campus') or mw_demande > 30:
        if (parcel.get('dist_ligne_400kv_m') or 50000) < 10000:
            tension_cible = 'htb_400'
        elif (parcel.get('dist_poste_htb_m') or 50000) < 20000:
            tension = parcel.get('tension_htb_kv') or 63
            tension_cible = 'htb_225' if tension >= 225 else 'htb_63'
        else:
            tension_cible = 'htb_225'
    elif project_type == 'edge' or mw_demande <= 3:
        tension_cible = 'hta'
    else:
        if mw_demande <= 10 and (parcel.get('dist_poste_hta_m') or 50000) < 5000:
            tension_cible = 'hta'
        elif (parcel.get('dist_poste_htb_m') or 50000) < 15000:
            tension = parcel.get('tension_htb_kv') or 63
            tension_cible = 'htb_225' if tension >= 225 else 'htb_63'
        else:
            tension_cible = 'htb_63'
    
    # Distance au poste pertinent
    if tension_cible == 'hta':
        dist = parcel.get('dist_poste_hta_m') or 10000
    else:
        dist = parcel.get('dist_poste_htb_m') or 15000
    
    # Déterminer type travaux
    capa = parcel.get('capacite_confirmee_mw') or parcel.get('capacite_residuelle_estimee_mw') or 0
    satur = parcel.get('zone_saturation', 'inconnu')
    
    if satur == 'sature' and mw_demande > 10:
        type_travaux = 'renforcement_reseau'
    elif dist > 15000:
        type_travaux = 'creation_poste'
    elif capa >= mw_demande and dist < 2000:
        type_travaux = 'simple_piquage'
    elif dist < 5000:
        type_travaux = 'extension_poste'
    else:
        type_travaux = 'creation_ligne'
    
    # Délai de base
    travaux_info = TRAVAUX_RACCORDEMENT[type_travaux]
    delai_min, delai_max = travaux_info['delai_base']
    
    # Ajustements
    ajustements = {}
    
    if dist > 10000:
        facteur = 1.0 + (dist - 10000) / 20000
        delai_min = round(delai_min * facteur)
        delai_max = round(delai_max * facteur)
        ajustements['distance'] = f"+{round((facteur-1)*100)}%"
    
    if satur == 'sature':
        delai_min = max(delai_min, 36)
        delai_max = max(delai_max, 72)
        ajustements['saturation'] = "Zone saturée"
    elif satur == 'tendu':
        delai_min = round(delai_min * 1.4)
        delai_max = round(delai_max * 1.5)
        ajustements['saturation'] = "Zone tendue +40%"
    
    file_attente = parcel.get('file_attente_mw') or 0
    if file_attente > 5000:
        delai_min = max(delai_min, 48)
        delai_max = max(delai_max, 84)
        ajustements['file_attente'] = f"{file_attente/1000:.1f} GW"
    elif file_attente > 1000:
        delai_max = round(delai_max * 1.1)
    
    region = parcel.get('region', '')
    if region == 'IDF':
        delai_min = round(delai_min * 1.15)
        delai_max = round(delai_max * 1.20)
        ajustements['region'] = "IDF +15%"
    
    if mw_demande > 50:
        delai_min = round(delai_min * 1.2)
        delai_max = round(delai_max * 1.3)
        ajustements['mw_eleve'] = f"{mw_demande} MW"
    
    if parcel.get('raccordement_elec_existant'):
        delai_min = max(3, round(delai_min * 0.6))
        delai_max = round(delai_max * 0.7)
        ajustements['existant'] = "-30%"
    
    # Coût
    cout_min, cout_max = travaux_info['cout_base_eur_par_mw']
    cout_p50 = mw_demande * (cout_min + cout_max) / 2
    
    if dist > 5000:
        cout_p50 *= 1.0 + (dist - 5000) / 15000
    if satur == 'sature':
        cout_p50 *= 1.5
    
    # Probabilité obtention MW
    proba = 0.85
    if satur == 'sature':
        proba *= 0.5
    elif satur == 'tendu':
        proba *= 0.65
    
    if file_attente > 3000:
        proba *= 0.7
    elif file_attente > 1000:
        proba *= 0.85
    
    if dist > 10000:
        proba *= 0.85
    
    # Confiance
    if parcel.get('capacite_confirmee_mw'):
        confiance = 'haute'
    elif satur != 'inconnu':
        confiance = 'moyenne'
    else:
        confiance = 'faible'
    
    return {
        'racc_tension_cible': tension_cible,
        'racc_type_travaux': type_travaux,
        'racc_delai_min_mois': delai_min,
        'racc_delai_max_mois': delai_max,
        'racc_cout_eur': round(cout_p50),
        'racc_proba_obtention': round(proba, 2),
        'racc_mw_obtenables': round(mw_demande * proba, 1),
        'racc_facteur_confiance': confiance,
        'racc_details': {
            'type_description': travaux_info['description'],
            'ajustements': ajustements,
            'distance_m': dist,
        },
    }


# ═══════════════════════════════════════════════════════════
# POWER ESTIMATION
# ═══════════════════════════════════════════════════════════

def estimate_power(parcel: Dict[str, Any], project_type: str) -> Dict[str, Any]:
    """Estimation puissance MW disponible"""
    surface_ha = parcel.get('surface_ha') or parcel.get('surface_m2', 0) / 10000
    densite = DENSITE_MW_HA.get(project_type, 3.0)
    
    # MW par surface
    mw_surface = surface_ha * densite
    
    # MW par réseau
    capa = parcel.get('capacite_confirmee_mw') or parcel.get('capacite_residuelle_estimee_mw') or 50
    satur = parcel.get('zone_saturation', 'inconnu')
    dist_htb = parcel.get('dist_poste_htb_m') or 15000
    
    # Facteur saturation
    if satur == 'disponible':
        facteur_satur = 0.80
    elif satur == 'tendu':
        facteur_satur = 0.45
    elif satur == 'sature':
        facteur_satur = 0.20
    else:
        facteur_satur = 0.60
    
    # Facteur distance
    if dist_htb < 5000:
        facteur_dist = 0.95
    elif dist_htb < 10000:
        facteur_dist = 0.85
    elif dist_htb < 15000:
        facteur_dist = 0.70
    else:
        facteur_dist = 0.50
    
    # Facteur administratif
    facteur_admin = 0.90
    
    mw_reseau = capa * facteur_satur * facteur_dist * facteur_admin
    
    # MW réel = min des deux
    mw_estime = min(mw_surface, mw_reseau)
    
    # Fourchette
    mw_p10 = mw_estime * 0.55
    mw_p50 = mw_estime
    mw_p90 = mw_estime * 1.40
    
    # Facteur limitant
    if mw_reseau < mw_surface:
        limiting = 'reseau'
    else:
        limiting = 'surface'
    
    if satur == 'sature':
        limiting = 'saturation'
    
    # Score puissance
    if mw_estime >= 50:
        score = 95
        category = 'mega'
    elif mw_estime >= 20:
        score = 80
        category = 'large'
    elif mw_estime >= 10:
        score = 65
        category = 'medium'
    elif mw_estime >= 5:
        score = 45
        category = 'small'
    else:
        score = 25
        category = 'micro'
    
    return {
        'power_mw_surface': round(mw_surface, 1),
        'power_mw_reseau': round(mw_reseau, 1),
        'power_mw_estime': round(mw_estime, 1),
        'power_mw_p10': round(mw_p10, 1),
        'power_mw_p50': round(mw_p50, 1),
        'power_mw_p90': round(mw_p90, 1),
        'power_score': score,
        'power_category': category,
        'power_limiting_factor': limiting,
    }


# ═══════════════════════════════════════════════════════════
# ECONOMICS
# ═══════════════════════════════════════════════════════════

def compute_capex(parcel: Dict[str, Any], project_type: str, mw: float, urba_result: Dict[str, Any]) -> Dict[str, Any]:
    """Calcul CAPEX complet"""
    region = parcel.get('region', 'default')
    mult = BENCHMARKS['region_multiplier'].get(region, 1.0)
    
    # Foncier
    prix_m2 = parcel.get('dvf_prix_m2_p50') or BENCHMARKS['dvf_fallback_eur_m2'].get(region, 65)
    surface_m2 = parcel.get('surface_m2') or 30000
    foncier_p50 = prix_m2 * surface_m2
    foncier_p10 = foncier_p50 * 0.85
    foncier_p90 = foncier_p50 * 1.30
    
    # Portage + coûts urbanisme
    portage = urba_result.get('urba_couts_indirects', {}).get('portage_foncier', 0)
    couts_urba = urba_result.get('urba_couts_indirects', {}).get('etudes_urbanistiques', 0)
    
    # Raccordement électrique
    dist = min(parcel.get('dist_poste_htb_m') or 10000, 20000)
    tension = parcel.get('tension_htb_kv') or 63
    
    if tension >= 225:
        racc_rate = (800, 1200)
    elif tension >= 63:
        racc_rate = (600, 1000)
    else:
        racc_rate = (400, 700)
    
    racc_elec_p50 = dist * (racc_rate[0] + racc_rate[1]) / 2
    racc_elec_p10 = dist * racc_rate[0]
    racc_elec_p90 = dist * racc_rate[1]
    
    # Raccordement fibre
    racc_fibre = (parcel.get('dist_backbone_fibre_m') or 2000) * 1200
    
    # Construction
    bench = BENCHMARKS['construction_meur_par_mw'][project_type]
    const_p50 = mw * ((bench[0] + bench[1]) / 2) * mult * 1e6
    const_p10 = mw * bench[0] * mult * 1e6
    const_p90 = mw * bench[1] * mult * 1e6
    
    # Études
    etudes = 3e6
    
    # Totaux
    total_p50 = foncier_p50 + portage + couts_urba + racc_elec_p50 + racc_fibre + const_p50 + etudes
    total_p10 = foncier_p10 + portage*0.8 + couts_urba*0.7 + racc_elec_p10 + racc_fibre*0.7 + const_p10 + 2e6
    total_p90 = foncier_p90 + portage*1.3 + couts_urba*1.4 + racc_elec_p90 + racc_fibre*1.5 + const_p90 + 5e6
    
    return {
        'foncier': {'p10': foncier_p10, 'p50': foncier_p50, 'p90': foncier_p90},
        'portage': portage,
        'couts_urbanisme': couts_urba,
        'racc_elec': {'p10': racc_elec_p10, 'p50': racc_elec_p50, 'p90': racc_elec_p90},
        'racc_fibre': racc_fibre,
        'construction': {'p10': const_p10, 'p50': const_p50, 'p90': const_p90},
        'etudes': etudes,
        'total': {'p10': total_p10, 'p50': total_p50, 'p90': total_p90},
        'cout_mw': {
            'p10': total_p10 / mw / 1e6 if mw > 0 else 0,
            'p50': total_p50 / mw / 1e6 if mw > 0 else 0,
            'p90': total_p90 / mw / 1e6 if mw > 0 else 0,
        },
    }


def compute_irr(cash_flows: List[float], guess: float = 0.10) -> float:
    """Newton-Raphson IRR calculation"""
    rate = guess
    for _ in range(100):
        npv = sum(cf / (1 + rate)**t for t, cf in enumerate(cash_flows))
        dnpv = sum(-t * cf / (1 + rate)**(t+1) for t, cf in enumerate(cash_flows))
        if abs(dnpv) < 1e-12:
            break
        new_rate = rate - npv / dnpv
        if abs(new_rate - rate) < 1e-6:
            return new_rate
        rate = new_rate
    return rate


def compute_rentabilite(parcel: Dict[str, Any], project_type: str, mw: float, capex_p50: float) -> Dict[str, Any]:
    """Calcul P&L et IRR"""
    region = parcel.get('region', 'default')
    prix_data = BENCHMARKS['prix_kw_mois'][project_type]
    prix_kw_mois = prix_data['IDF'] if region == 'IDF' else prix_data['province']
    opex_pct = BENCHMARKS['opex_pct'][project_type]
    ramp = BENCHMARKS['occupation_ramp']
    
    def revenu(year):
        occ = ramp.get(year, 0.78)
        return mw * 1000 * prix_kw_mois * 12 * occ
    
    rev_maturite = revenu(5)
    opex_mat = rev_maturite * opex_pct
    ebitda_mat = rev_maturite - opex_mat
    
    # Payback
    payback = capex_p50 / ebitda_mat if ebitda_mat > 0 else 99
    
    # IRR unlevered
    cf = [-capex_p50]
    for y in range(1, 16):
        ebitda_y = revenu(y) * (1 - opex_pct)
        if y == 15:
            cf.append(ebitda_y + ebitda_mat * 18)
        else:
            cf.append(ebitda_y)
    irr_unlev = compute_irr(cf)
    
    # IRR levered
    ltv = 0.60
    dette = capex_p50 * ltv
    equity = capex_p50 * (1 - ltv)
    taux = 0.045
    rembours = dette / 10
    
    ecf = [-equity]
    for y in range(1, 16):
        ebitda_y = revenu(y) * (1 - opex_pct)
        service = 0
        if y <= 10:
            dette_restante = dette - rembours * (y - 1)
            service = taux * dette_restante + rembours
        terminal = ebitda_mat * 18 if y == 15 else 0
        ecf.append(ebitda_y - service + terminal)
    irr_lev = compute_irr(ecf)
    
    # Faisabilité
    if irr_lev > 0.20:
        faisabilite = 'excellent'
    elif irr_lev > 0.15:
        faisabilite = 'bon'
    elif irr_lev > 0.10:
        faisabilite = 'moyen'
    else:
        faisabilite = 'difficile'
    
    return {
        'revenu_maturite': round(rev_maturite),
        'opex_maturite': round(opex_mat),
        'ebitda_maturite': round(ebitda_mat),
        'ebitda_margin_pct': round((1 - opex_pct) * 100, 1),
        'payback_ans': round(payback, 1),
        'irr_unlevered_pct': round(irr_unlev * 100, 1),
        'irr_levered_pct': round(irr_lev * 100, 1),
        'faisabilite': faisabilite,
    }


# ═══════════════════════════════════════════════════════════
# CONFIDENCE & VERDICT
# ═══════════════════════════════════════════════════════════

def compute_confidence(parcel: Dict[str, Any]) -> Dict[str, Any]:
    """Calcul score de confiance basé sur les données disponibles"""
    score = 100
    missing = []
    
    if not parcel.get('dist_poste_htb_m'):
        score -= 15
        missing.append('distance_poste_htb')
    if not parcel.get('zone_saturation') or parcel.get('zone_saturation') == 'inconnu':
        score -= 12
        missing.append('zone_saturation')
    if not parcel.get('capacite_confirmee_mw') and not parcel.get('capacite_residuelle_estimee_mw'):
        score -= 10
        missing.append('capacite_reseau')
    if not parcel.get('plu_zone'):
        score -= 10
        missing.append('plu_zone')
    if not parcel.get('dvf_prix_m2_p50'):
        score -= 8
        missing.append('dvf_prix')
    if not parcel.get('dist_backbone_fibre_m'):
        score -= 8
        missing.append('distance_fibre')
    if not parcel.get('ppri_zone'):
        score -= 5
        missing.append('ppri')
    if not parcel.get('dist_landing_point_km'):
        score -= 5
        missing.append('landing_point')
    
    return {
        'confidence_score': max(0, score),
        'confidence_missing': missing,
    }


def compute_verdict_global(
    parcel: Dict[str, Any],
    project_type: str,
    tech_score: Dict[str, Any],
    urba_result: Dict[str, Any],
    racc_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Verdict final GO/CONDITIONNEL/NO_GO"""
    
    # Check éligibilité
    blockers = []
    surface_ha = parcel.get('surface_ha') or parcel.get('surface_m2', 0) / 10000
    min_ha = SURFACE_MIN_HA[project_type]
    
    if surface_ha < min_ha:
        blockers.append(f'Surface insuffisante ({surface_ha:.1f} ha < {min_ha} ha)')
    
    if parcel.get('ppri_zone') == 'rouge':
        blockers.append('Zone PPRI rouge - inconstructible')
    
    if urba_result.get('urba_compatibilite') == 'incompatible':
        blockers.append(f"Zone PLU incompatible ({parcel.get('plu_zone')})")
    
    if blockers:
        return {
            'verdict': Verdict.NO_GO.value,
            'verdict_raison': '; '.join(blockers),
            'risque_global': 'bloquant',
            'eligibility_status': 'ineligible',
            'eligibility_blockers': blockers,
        }
    
    # TTM = max(urbanisme, raccordement)
    ttm_urba_max = urba_result.get('urba_delai_max_mois') or 0
    ttm_racc_max = racc_result.get('racc_delai_max_mois') or 12
    ttm_max = max(ttm_urba_max, ttm_racc_max)
    ttm_min = max(urba_result.get('urba_delai_min_mois') or 0, racc_result.get('racc_delai_min_mois') or 6)
    
    bottleneck = 'urbanisme' if ttm_urba_max >= ttm_racc_max else 'raccordement'
    
    # Verdict
    score_net = tech_score.get('score_net', 0)
    proba_urba = urba_result.get('urba_proba_succes_combinee', 1)
    proba_racc = racc_result.get('racc_proba_obtention', 1)
    dfi = urba_result.get('urba_deal_friction_index', 0)
    
    if score_net >= 70 and proba_urba >= 0.80 and proba_racc >= 0.70 and dfi < 30:
        verdict = Verdict.GO
        risque = 'faible'
        raison = 'Site technique excellent, urbanisme favorable'
    elif score_net >= 50 and proba_urba >= 0.40 and proba_racc >= 0.40:
        verdict = Verdict.CONDITIONNEL
        if dfi >= 50:
            risque = 'eleve'
            raison = f"DFI élevé ({dfi}/100), conditions suspensives nombreuses"
        elif proba_urba < 0.60:
            risque = 'eleve'
            raison = f"Probabilité urbanisme faible ({proba_urba*100:.0f}%)"
        else:
            risque = 'moyen'
            raison = 'Site viable sous conditions'
    else:
        verdict = Verdict.NO_GO
        risque = 'bloquant'
        if score_net < 50:
            raison = f'Score technique insuffisant ({score_net}/100)'
        else:
            raison = f'Probabilités trop faibles (urba: {proba_urba*100:.0f}%, racc: {proba_racc*100:.0f}%)'
    
    return {
        'verdict': verdict.value,
        'verdict_raison': raison,
        'risque_global': risque,
        'ttm_min_months': ttm_min,
        'ttm_max_months': ttm_max,
        'ttm_bottleneck': bottleneck,
        'eligibility_status': 'eligible',
        'eligibility_blockers': [],
    }


# ═══════════════════════════════════════════════════════════
# MAIN SCORING FUNCTION
# ═══════════════════════════════════════════════════════════

def compute_full_score(parcel: Dict[str, Any], project_type: str) -> Dict[str, Any]:
    """Compute all scores for a parcel and project type"""
    
    # 1. Score technique
    tech_score = compute_score_technique(parcel, project_type)
    
    # 2. Urbanisme
    urba_result = compute_faisabilite_urbanistique(parcel, project_type)
    
    # 3. Estimation puissance
    power_result = estimate_power(parcel, project_type)
    mw_p50 = power_result['power_mw_p50']
    
    # 4. Raccordement
    racc_result = estimate_raccordement(parcel, project_type, mw_p50)
    
    # 5. CAPEX
    capex_result = compute_capex(parcel, project_type, mw_p50, urba_result)
    
    # 6. Rentabilité
    renta_result = compute_rentabilite(parcel, project_type, mw_p50, capex_result['total']['p50'])
    
    # 7. Confiance
    conf_result = compute_confidence(parcel)
    
    # 8. Verdict
    verdict_result = compute_verdict_global(parcel, project_type, tech_score, urba_result, racc_result)
    
    # 9. PUE
    lat = parcel.get('latitude') or 46
    if project_type == 'ai_campus':
        pue = BENCHMARKS['pue']['liquid_immersion']
    elif lat > 47:
        pue = BENCHMARKS['pue']['free_cooling']
    elif lat > 45:
        pue = BENCHMARKS['pue']['free_cooling_partiel']
    else:
        pue = BENCHMARKS['pue']['mecanique']
    
    return {
        'parcel_id': parcel.get('parcel_id'),
        'project_type': project_type,
        
        # Score technique
        **tech_score,
        
        # Urbanisme
        **{k: v for k, v in urba_result.items() if not k.startswith('plu_')},
        
        # Puissance
        **power_result,
        
        # Raccordement
        'racc_delai_min_mois': racc_result['racc_delai_min_mois'],
        'racc_delai_max_mois': racc_result['racc_delai_max_mois'],
        'racc_cout_eur': racc_result['racc_cout_eur'],
        'racc_proba_obtention': racc_result['racc_proba_obtention'],
        'racc_mw_obtenables': racc_result['racc_mw_obtenables'],
        'racc_tension_cible': racc_result['racc_tension_cible'],
        'racc_type_travaux': racc_result['racc_type_travaux'],
        'racc_facteur_confiance': racc_result['racc_facteur_confiance'],
        
        # CAPEX
        'capex_p10': capex_result['total']['p10'],
        'capex_p50': capex_result['total']['p50'],
        'capex_p90': capex_result['total']['p90'],
        'cout_mw_p50': capex_result['cout_mw']['p50'],
        'capex_detail': capex_result,
        
        # Rentabilité
        'ebitda_maturite': renta_result['ebitda_maturite'],
        'irr_unlevered_pct': renta_result['irr_unlevered_pct'],
        'irr_levered_pct': renta_result['irr_levered_pct'],
        'faisabilite': renta_result['faisabilite'],
        
        # Confiance
        **conf_result,
        
        # Verdict
        **verdict_result,
        
        # Capacité
        'mw_estime': mw_p50,
        'pue_expected': pue[1],
    }
