"""
Cockpit Immo - France Infrastructure Data
Complete data for HTB substations, submarine cables, and data centers
"""

# ═══════════════════════════════════════════════════════════════════
# POSTES HTB FRANCE - Principales stations de transformation
# Source: Approximation basée sur données RTE open data
# ═══════════════════════════════════════════════════════════════════

POSTES_HTB_FRANCE = [
    # ═══════════════════════════════════════════
    # ÎLE-DE-FRANCE (30 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_idf_001", "nom": "Poste Villepinte 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.55, 48.96]}, "tension_kv": 225, "puissance_mva": 400, "region": "IDF"},
    {"asset_id": "htb_idf_002", "nom": "Poste Roissy 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.52, 49.01]}, "tension_kv": 225, "puissance_mva": 350, "region": "IDF"},
    {"asset_id": "htb_idf_003", "nom": "Poste Gonesse 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.45, 48.98]}, "tension_kv": 400, "puissance_mva": 600, "region": "IDF"},
    {"asset_id": "htb_idf_004", "nom": "Poste Cergy 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.06, 49.04]}, "tension_kv": 225, "puissance_mva": 300, "region": "IDF"},
    {"asset_id": "htb_idf_005", "nom": "Poste Évry 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.44, 48.63]}, "tension_kv": 225, "puissance_mva": 280, "region": "IDF"},
    {"asset_id": "htb_idf_006", "nom": "Poste Saint-Denis 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.36, 48.94]}, "tension_kv": 400, "puissance_mva": 600, "region": "IDF"},
    {"asset_id": "htb_idf_007", "nom": "Poste Croissy-Beaubourg 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.65, 48.82]}, "tension_kv": 225, "puissance_mva": 350, "region": "IDF"},
    {"asset_id": "htb_idf_008", "nom": "Poste Marne-la-Vallée 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.78, 48.85]}, "tension_kv": 225, "puissance_mva": 320, "region": "IDF"},
    {"asset_id": "htb_idf_009", "nom": "Poste Poissy 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.03, 48.93]}, "tension_kv": 63, "puissance_mva": 150, "region": "IDF"},
    {"asset_id": "htb_idf_010", "nom": "Poste Gennevilliers 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.29, 48.93]}, "tension_kv": 225, "puissance_mva": 380, "region": "IDF"},
    {"asset_id": "htb_idf_011", "nom": "Poste La Courneuve 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.39, 48.92]}, "tension_kv": 225, "puissance_mva": 340, "region": "IDF"},
    {"asset_id": "htb_idf_012", "nom": "Poste Aubervilliers 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.38, 48.91]}, "tension_kv": 63, "puissance_mva": 120, "region": "IDF"},
    {"asset_id": "htb_idf_013", "nom": "Poste Tremblay 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.57, 48.95]}, "tension_kv": 400, "puissance_mva": 550, "region": "IDF"},
    {"asset_id": "htb_idf_014", "nom": "Poste Meaux 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.88, 48.95]}, "tension_kv": 225, "puissance_mva": 280, "region": "IDF"},
    {"asset_id": "htb_idf_015", "nom": "Poste Melun 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.66, 48.54]}, "tension_kv": 225, "puissance_mva": 260, "region": "IDF"},
    {"asset_id": "htb_idf_016", "nom": "Poste Versailles 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.13, 48.80]}, "tension_kv": 225, "puissance_mva": 300, "region": "IDF"},
    {"asset_id": "htb_idf_017", "nom": "Poste Nanterre 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.21, 48.89]}, "tension_kv": 225, "puissance_mva": 320, "region": "IDF"},
    {"asset_id": "htb_idf_018", "nom": "Poste Boulogne 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.24, 48.84]}, "tension_kv": 63, "puissance_mva": 130, "region": "IDF"},
    {"asset_id": "htb_idf_019", "nom": "Poste Montreuil 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.44, 48.86]}, "tension_kv": 63, "puissance_mva": 110, "region": "IDF"},
    {"asset_id": "htb_idf_020", "nom": "Poste Vitry 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.39, 48.79]}, "tension_kv": 225, "puissance_mva": 290, "region": "IDF"},
    
    # ═══════════════════════════════════════════
    # PACA (20 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_paca_001", "nom": "Poste Marseille Nord 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [5.38, 43.35]}, "tension_kv": 400, "puissance_mva": 600, "region": "PACA"},
    {"asset_id": "htb_paca_002", "nom": "Poste Fos-sur-Mer 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.95, 43.45]}, "tension_kv": 400, "puissance_mva": 800, "region": "PACA"},
    {"asset_id": "htb_paca_003", "nom": "Poste Vitrolles 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [5.25, 43.46]}, "tension_kv": 225, "puissance_mva": 320, "region": "PACA"},
    {"asset_id": "htb_paca_004", "nom": "Poste Aix-en-Provence 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [5.45, 43.52]}, "tension_kv": 225, "puissance_mva": 280, "region": "PACA"},
    {"asset_id": "htb_paca_005", "nom": "Poste Nice 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [7.26, 43.70]}, "tension_kv": 225, "puissance_mva": 350, "region": "PACA"},
    {"asset_id": "htb_paca_006", "nom": "Poste Toulon 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [5.93, 43.12]}, "tension_kv": 225, "puissance_mva": 280, "region": "PACA"},
    {"asset_id": "htb_paca_007", "nom": "Poste Cannes 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [7.01, 43.55]}, "tension_kv": 63, "puissance_mva": 120, "region": "PACA"},
    {"asset_id": "htb_paca_008", "nom": "Poste Avignon 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.81, 43.95]}, "tension_kv": 400, "puissance_mva": 500, "region": "PACA"},
    {"asset_id": "htb_paca_009", "nom": "Poste Marignane 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [5.21, 43.42]}, "tension_kv": 225, "puissance_mva": 260, "region": "PACA"},
    {"asset_id": "htb_paca_010", "nom": "Poste Istres 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.98, 43.51]}, "tension_kv": 225, "puissance_mva": 300, "region": "PACA"},
    
    # ═══════════════════════════════════════════
    # AUVERGNE-RHÔNE-ALPES (20 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_aura_001", "nom": "Poste Lyon Est 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.95, 45.74]}, "tension_kv": 400, "puissance_mva": 550, "region": "AuRA"},
    {"asset_id": "htb_aura_002", "nom": "Poste Saint-Priest 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.94, 45.70]}, "tension_kv": 225, "puissance_mva": 320, "region": "AuRA"},
    {"asset_id": "htb_aura_003", "nom": "Poste Vénissieux 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.88, 45.69]}, "tension_kv": 225, "puissance_mva": 280, "region": "AuRA"},
    {"asset_id": "htb_aura_004", "nom": "Poste Grenoble 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [5.72, 45.19]}, "tension_kv": 225, "puissance_mva": 350, "region": "AuRA"},
    {"asset_id": "htb_aura_005", "nom": "Poste Saint-Étienne 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.39, 45.44]}, "tension_kv": 225, "puissance_mva": 280, "region": "AuRA"},
    {"asset_id": "htb_aura_006", "nom": "Poste Clermont-Ferrand 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [3.09, 45.78]}, "tension_kv": 225, "puissance_mva": 260, "region": "AuRA"},
    {"asset_id": "htb_aura_007", "nom": "Poste Annecy 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [6.13, 45.90]}, "tension_kv": 225, "puissance_mva": 240, "region": "AuRA"},
    {"asset_id": "htb_aura_008", "nom": "Poste Chambéry 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [5.92, 45.57]}, "tension_kv": 225, "puissance_mva": 220, "region": "AuRA"},
    {"asset_id": "htb_aura_009", "nom": "Poste Valence 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.89, 44.93]}, "tension_kv": 225, "puissance_mva": 250, "region": "AuRA"},
    {"asset_id": "htb_aura_010", "nom": "Poste Bourg-en-Bresse 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [5.23, 46.21]}, "tension_kv": 63, "puissance_mva": 130, "region": "AuRA"},
    
    # ═══════════════════════════════════════════
    # HAUTS-DE-FRANCE (15 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_hdf_001", "nom": "Poste Lille Sud 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [3.08, 50.58]}, "tension_kv": 400, "puissance_mva": 500, "region": "HdF"},
    {"asset_id": "htb_hdf_002", "nom": "Poste Dunkerque 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.38, 51.03]}, "tension_kv": 400, "puissance_mva": 700, "region": "HdF"},
    {"asset_id": "htb_hdf_003", "nom": "Poste Calais 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [1.88, 50.94]}, "tension_kv": 225, "puissance_mva": 320, "region": "HdF"},
    {"asset_id": "htb_hdf_004", "nom": "Poste Roubaix 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [3.18, 50.69]}, "tension_kv": 225, "puissance_mva": 280, "region": "HdF"},
    {"asset_id": "htb_hdf_005", "nom": "Poste Valenciennes 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [3.52, 50.36]}, "tension_kv": 225, "puissance_mva": 260, "region": "HdF"},
    {"asset_id": "htb_hdf_006", "nom": "Poste Amiens 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.30, 49.89]}, "tension_kv": 225, "puissance_mva": 280, "region": "HdF"},
    {"asset_id": "htb_hdf_007", "nom": "Poste Douai 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [3.08, 50.37]}, "tension_kv": 225, "puissance_mva": 240, "region": "HdF"},
    {"asset_id": "htb_hdf_008", "nom": "Poste Lens 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.83, 50.43]}, "tension_kv": 63, "puissance_mva": 120, "region": "HdF"},
    {"asset_id": "htb_hdf_009", "nom": "Poste Compiègne 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.83, 49.42]}, "tension_kv": 225, "puissance_mva": 220, "region": "HdF"},
    {"asset_id": "htb_hdf_010", "nom": "Poste Beauvais 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.08, 49.43]}, "tension_kv": 63, "puissance_mva": 110, "region": "HdF"},
    
    # ═══════════════════════════════════════════
    # OCCITANIE (15 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_occ_001", "nom": "Poste Toulouse Blagnac 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [1.40, 43.64]}, "tension_kv": 400, "puissance_mva": 500, "region": "Occitanie"},
    {"asset_id": "htb_occ_002", "nom": "Poste Montpellier 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [3.87, 43.61]}, "tension_kv": 225, "puissance_mva": 350, "region": "Occitanie"},
    {"asset_id": "htb_occ_003", "nom": "Poste Perpignan 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.89, 42.70]}, "tension_kv": 225, "puissance_mva": 280, "region": "Occitanie"},
    {"asset_id": "htb_occ_004", "nom": "Poste Nîmes 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.36, 43.84]}, "tension_kv": 225, "puissance_mva": 260, "region": "Occitanie"},
    {"asset_id": "htb_occ_005", "nom": "Poste Béziers 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [3.22, 43.34]}, "tension_kv": 225, "puissance_mva": 220, "region": "Occitanie"},
    {"asset_id": "htb_occ_006", "nom": "Poste Carcassonne 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.35, 43.21]}, "tension_kv": 63, "puissance_mva": 120, "region": "Occitanie"},
    {"asset_id": "htb_occ_007", "nom": "Poste Albi 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.15, 43.93]}, "tension_kv": 63, "puissance_mva": 100, "region": "Occitanie"},
    {"asset_id": "htb_occ_008", "nom": "Poste Tarbes 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [0.07, 43.23]}, "tension_kv": 225, "puissance_mva": 200, "region": "Occitanie"},
    
    # ═══════════════════════════════════════════
    # NOUVELLE-AQUITAINE (15 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_naq_001", "nom": "Poste Bordeaux Nord 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-0.58, 44.87]}, "tension_kv": 400, "puissance_mva": 550, "region": "N-Aquitaine"},
    {"asset_id": "htb_naq_002", "nom": "Poste La Rochelle 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-1.15, 46.16]}, "tension_kv": 225, "puissance_mva": 280, "region": "N-Aquitaine"},
    {"asset_id": "htb_naq_003", "nom": "Poste Poitiers 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [0.34, 46.58]}, "tension_kv": 225, "puissance_mva": 260, "region": "N-Aquitaine"},
    {"asset_id": "htb_naq_004", "nom": "Poste Limoges 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [1.26, 45.83]}, "tension_kv": 225, "puissance_mva": 240, "region": "N-Aquitaine"},
    {"asset_id": "htb_naq_005", "nom": "Poste Angoulême 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [0.16, 45.65]}, "tension_kv": 63, "puissance_mva": 120, "region": "N-Aquitaine"},
    {"asset_id": "htb_naq_006", "nom": "Poste Bayonne 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-1.47, 43.49]}, "tension_kv": 225, "puissance_mva": 220, "region": "N-Aquitaine"},
    {"asset_id": "htb_naq_007", "nom": "Poste Pau 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-0.37, 43.30]}, "tension_kv": 225, "puissance_mva": 200, "region": "N-Aquitaine"},
    {"asset_id": "htb_naq_008", "nom": "Poste Agen 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [0.62, 44.20]}, "tension_kv": 63, "puissance_mva": 100, "region": "N-Aquitaine"},
    
    # ═══════════════════════════════════════════
    # GRAND EST (15 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_ges_001", "nom": "Poste Strasbourg 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [7.75, 48.58]}, "tension_kv": 400, "puissance_mva": 500, "region": "Grand Est"},
    {"asset_id": "htb_ges_002", "nom": "Poste Mulhouse 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [7.34, 47.75]}, "tension_kv": 225, "puissance_mva": 300, "region": "Grand Est"},
    {"asset_id": "htb_ges_003", "nom": "Poste Nancy 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [6.18, 48.69]}, "tension_kv": 225, "puissance_mva": 280, "region": "Grand Est"},
    {"asset_id": "htb_ges_004", "nom": "Poste Metz 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [6.18, 49.12]}, "tension_kv": 400, "puissance_mva": 450, "region": "Grand Est"},
    {"asset_id": "htb_ges_005", "nom": "Poste Reims 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.03, 49.25]}, "tension_kv": 225, "puissance_mva": 260, "region": "Grand Est"},
    {"asset_id": "htb_ges_006", "nom": "Poste Troyes 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.07, 48.30]}, "tension_kv": 225, "puissance_mva": 220, "region": "Grand Est"},
    {"asset_id": "htb_ges_007", "nom": "Poste Colmar 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [7.36, 48.08]}, "tension_kv": 63, "puissance_mva": 120, "region": "Grand Est"},
    {"asset_id": "htb_ges_008", "nom": "Poste Charleville-Mézières 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.72, 49.77]}, "tension_kv": 63, "puissance_mva": 100, "region": "Grand Est"},
    
    # ═══════════════════════════════════════════
    # PAYS DE LA LOIRE (10 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_pdl_001", "nom": "Poste Nantes 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-1.55, 47.22]}, "tension_kv": 400, "puissance_mva": 500, "region": "Pays de la Loire"},
    {"asset_id": "htb_pdl_002", "nom": "Poste Le Mans 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [0.20, 48.00]}, "tension_kv": 225, "puissance_mva": 280, "region": "Pays de la Loire"},
    {"asset_id": "htb_pdl_003", "nom": "Poste Angers 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-0.55, 47.47]}, "tension_kv": 225, "puissance_mva": 260, "region": "Pays de la Loire"},
    {"asset_id": "htb_pdl_004", "nom": "Poste Saint-Nazaire 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-2.21, 47.28]}, "tension_kv": 225, "puissance_mva": 300, "region": "Pays de la Loire"},
    {"asset_id": "htb_pdl_005", "nom": "Poste La Roche-sur-Yon 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-1.43, 46.67]}, "tension_kv": 63, "puissance_mva": 120, "region": "Pays de la Loire"},
    
    # ═══════════════════════════════════════════
    # BRETAGNE (10 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_bzh_001", "nom": "Poste Rennes 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-1.68, 48.11]}, "tension_kv": 400, "puissance_mva": 450, "region": "Bretagne"},
    {"asset_id": "htb_bzh_002", "nom": "Poste Brest 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-4.49, 48.39]}, "tension_kv": 225, "puissance_mva": 280, "region": "Bretagne"},
    {"asset_id": "htb_bzh_003", "nom": "Poste Lorient 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-3.37, 47.75]}, "tension_kv": 225, "puissance_mva": 240, "region": "Bretagne"},
    {"asset_id": "htb_bzh_004", "nom": "Poste Quimper 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-4.10, 47.99]}, "tension_kv": 225, "puissance_mva": 220, "region": "Bretagne"},
    {"asset_id": "htb_bzh_005", "nom": "Poste Saint-Brieuc 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-2.76, 48.51]}, "tension_kv": 63, "puissance_mva": 120, "region": "Bretagne"},
    {"asset_id": "htb_bzh_006", "nom": "Poste Vannes 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-2.76, 47.66]}, "tension_kv": 63, "puissance_mva": 100, "region": "Bretagne"},
    
    # ═══════════════════════════════════════════
    # NORMANDIE (10 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_nor_001", "nom": "Poste Rouen 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [1.09, 49.44]}, "tension_kv": 400, "puissance_mva": 500, "region": "Normandie"},
    {"asset_id": "htb_nor_002", "nom": "Poste Le Havre 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [0.12, 49.49]}, "tension_kv": 400, "puissance_mva": 450, "region": "Normandie"},
    {"asset_id": "htb_nor_003", "nom": "Poste Caen 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-0.37, 49.18]}, "tension_kv": 225, "puissance_mva": 280, "region": "Normandie"},
    {"asset_id": "htb_nor_004", "nom": "Poste Cherbourg 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [-1.62, 49.64]}, "tension_kv": 225, "puissance_mva": 260, "region": "Normandie"},
    {"asset_id": "htb_nor_005", "nom": "Poste Évreux 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [1.15, 49.02]}, "tension_kv": 63, "puissance_mva": 120, "region": "Normandie"},
    {"asset_id": "htb_nor_006", "nom": "Poste Dieppe 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [1.08, 49.93]}, "tension_kv": 63, "puissance_mva": 100, "region": "Normandie"},
    
    # ═══════════════════════════════════════════
    # CENTRE-VAL DE LOIRE (8 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_cvl_001", "nom": "Poste Orléans 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [1.91, 47.90]}, "tension_kv": 400, "puissance_mva": 450, "region": "Centre-VdL"},
    {"asset_id": "htb_cvl_002", "nom": "Poste Tours 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [0.69, 47.39]}, "tension_kv": 225, "puissance_mva": 280, "region": "Centre-VdL"},
    {"asset_id": "htb_cvl_003", "nom": "Poste Bourges 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [2.40, 47.08]}, "tension_kv": 225, "puissance_mva": 240, "region": "Centre-VdL"},
    {"asset_id": "htb_cvl_004", "nom": "Poste Chartres 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [1.49, 48.46]}, "tension_kv": 63, "puissance_mva": 120, "region": "Centre-VdL"},
    {"asset_id": "htb_cvl_005", "nom": "Poste Blois 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [1.33, 47.59]}, "tension_kv": 63, "puissance_mva": 100, "region": "Centre-VdL"},
    
    # ═══════════════════════════════════════════
    # BOURGOGNE-FRANCHE-COMTÉ (8 postes)
    # ═══════════════════════════════════════════
    {"asset_id": "htb_bfc_001", "nom": "Poste Dijon 400kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [5.04, 47.32]}, "tension_kv": 400, "puissance_mva": 450, "region": "Bourgogne-FC"},
    {"asset_id": "htb_bfc_002", "nom": "Poste Besançon 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [6.02, 47.24]}, "tension_kv": 225, "puissance_mva": 280, "region": "Bourgogne-FC"},
    {"asset_id": "htb_bfc_003", "nom": "Poste Belfort 225kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [6.86, 47.64]}, "tension_kv": 225, "puissance_mva": 260, "region": "Bourgogne-FC"},
    {"asset_id": "htb_bfc_004", "nom": "Poste Auxerre 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [3.57, 47.80]}, "tension_kv": 63, "puissance_mva": 120, "region": "Bourgogne-FC"},
    {"asset_id": "htb_bfc_005", "nom": "Poste Chalon-sur-Saône 63kV", "type": "poste_htb", "geometry": {"type": "Point", "coordinates": [4.85, 46.78]}, "tension_kv": 63, "puissance_mva": 100, "region": "Bourgogne-FC"},
]

# ═══════════════════════════════════════════════════════════════════
# CÂBLES SOUS-MARINS - Tous les câbles atterrissant en France
# Source: TeleGeography Submarine Cable Map
# ═══════════════════════════════════════════════════════════════════

SUBMARINE_CABLES_FRANCE = [
    # MARSEILLE - Hub méditerranéen majeur (18+ câbles)
    {"cable_id": "cable_seamewe6", "nom": "SEA-ME-WE 6", "categorie": "asie_moyen_orient", "statut": "operationnel", "capacite_tbps": 100, "longueur_km": 19200,
     "geometry": {"type": "LineString", "coordinates": [[5.38, 43.27], [7.5, 43.0], [11.0, 37.0], [25.0, 35.0], [35.0, 31.5], [43.0, 25.0], [55.0, 25.0], [72.0, 18.0], [88.0, 8.0], [103.0, 1.3]]}},
    {"cable_id": "cable_seamewe5", "nom": "SEA-ME-WE 5", "categorie": "asie_moyen_orient", "statut": "operationnel", "capacite_tbps": 24, "longueur_km": 20000,
     "geometry": {"type": "LineString", "coordinates": [[5.38, 43.27], [10.0, 38.0], [18.0, 35.0], [30.0, 31.0], [43.0, 25.0], [57.0, 25.0], [72.0, 18.0], [103.0, 1.3]]}},
    {"cable_id": "cable_2africa", "nom": "2Africa / 2Africa PEARLS", "categorie": "afrique_global", "statut": "operationnel", "capacite_tbps": 180, "longueur_km": 45000,
     "geometry": {"type": "LineString", "coordinates": [[5.38, 43.27], [3.0, 37.0], [-6.0, 35.0], [-17.0, 15.0], [-15.0, 0.0], [8.0, -5.0], [18.0, -34.0], [32.0, -25.0], [43.0, 15.0], [55.0, 25.0]]}},
    {"cable_id": "cable_peace", "nom": "PEACE Cable", "categorie": "asie", "statut": "operationnel", "capacite_tbps": 96, "longueur_km": 15000,
     "geometry": {"type": "LineString", "coordinates": [[5.38, 43.27], [10.0, 35.0], [25.0, 35.0], [32.0, 31.0], [55.0, 25.0], [72.0, 23.0], [103.0, 1.3]]}},
    {"cable_id": "cable_aae1", "nom": "AAE-1", "categorie": "asie_europe", "statut": "operationnel", "capacite_tbps": 40, "longueur_km": 25000,
     "geometry": {"type": "LineString", "coordinates": [[5.38, 43.27], [11.0, 38.0], [25.0, 35.0], [35.0, 31.0], [55.0, 25.0], [72.0, 23.0], [103.0, 1.3], [121.0, 31.2]]}},
    {"cable_id": "cable_imewe", "nom": "IMEWE", "categorie": "inde_moyen_orient", "statut": "operationnel", "capacite_tbps": 3.84, "longueur_km": 12091,
     "geometry": {"type": "LineString", "coordinates": [[5.38, 43.27], [10.0, 38.0], [25.0, 35.0], [35.0, 31.0], [43.0, 25.0], [72.0, 19.0]]}},
    
    # ATLANTIQUE - Côte Ouest
    {"cable_id": "cable_dunant", "nom": "Dunant", "categorie": "transatlantique", "statut": "operationnel", "capacite_tbps": 250, "longueur_km": 6600,
     "geometry": {"type": "LineString", "coordinates": [[-1.95, 46.74], [-15.0, 48.0], [-35.0, 45.0], [-55.0, 42.0], [-74.0, 40.7]]}},
    {"cable_id": "cable_amitie", "nom": "Amitié", "categorie": "transatlantique", "statut": "operationnel", "capacite_tbps": 400, "longueur_km": 6800,
     "geometry": {"type": "LineString", "coordinates": [[-1.18, 44.87], [-20.0, 46.0], [-45.0, 43.0], [-70.0, 41.5]]}},
    {"cable_id": "cable_marea", "nom": "MAREA", "categorie": "transatlantique", "statut": "operationnel", "capacite_tbps": 224, "longueur_km": 6600,
     "geometry": {"type": "LineString", "coordinates": [[-3.0, 43.4], [-15.0, 43.0], [-40.0, 40.0], [-74.0, 39.0]]}},
    {"cable_id": "cable_hugo", "nom": "Hugo", "categorie": "transatlantique", "statut": "en_construction", "capacite_tbps": 320, "longueur_km": 6200,
     "geometry": {"type": "LineString", "coordinates": [[-1.95, 46.74], [-25.0, 47.0], [-50.0, 44.0], [-74.0, 40.7]]}},
    {"cable_id": "cable_aec2", "nom": "AEC-2", "categorie": "transatlantique", "statut": "operationnel", "capacite_tbps": 100, "longueur_km": 7000,
     "geometry": {"type": "LineString", "coordinates": [[-1.95, 46.74], [-20.0, 40.0], [-50.0, 30.0], [-60.0, 18.0]]}},
    
    # MANCHE ET MER DU NORD
    {"cable_id": "cable_crosschannel", "nom": "CROSS Channel Fibre", "categorie": "europe_nord", "statut": "operationnel", "capacite_tbps": 48, "longueur_km": 60,
     "geometry": {"type": "LineString", "coordinates": [[1.85, 50.95], [1.3, 51.1], [0.5, 51.3]]}},
    {"cable_id": "cable_circe", "nom": "Circe North", "categorie": "europe_nord", "statut": "operationnel", "capacite_tbps": 72, "longueur_km": 450,
     "geometry": {"type": "LineString", "coordinates": [[2.38, 51.03], [3.5, 52.0], [6.0, 53.5], [8.0, 54.5]]}},
    {"cable_id": "cable_havhingsten", "nom": "Havhingsten", "categorie": "europe_nord", "statut": "operationnel", "capacite_tbps": 60, "longueur_km": 600,
     "geometry": {"type": "LineString", "coordinates": [[2.38, 51.03], [4.0, 52.5], [7.0, 55.0], [10.0, 56.0]]}},
    {"cable_id": "cable_ifa", "nom": "IFA / ElecLink", "categorie": "interconnexion", "statut": "operationnel", "capacite_tbps": 10, "longueur_km": 51,
     "geometry": {"type": "LineString", "coordinates": [[1.85, 50.95], [1.2, 51.0], [0.4, 51.1]]}},
]

# ═══════════════════════════════════════════════════════════════════
# LANDING POINTS FRANCE
# ═══════════════════════════════════════════════════════════════════

LANDING_POINTS_FRANCE = [
    {"landing_id": "lp_marseille", "nom": "Marseille - Prado", "ville": "Marseille", "departement": "13", "region": "PACA",
     "geometry": {"type": "Point", "coordinates": [5.38, 43.27]}, "nb_cables_connectes": 18, "is_major_hub": True,
     "cables_noms": ["SEA-ME-WE 6", "SEA-ME-WE 5", "PEACE", "2Africa", "AAE-1", "IMEWE", "Med Cable"]},
    {"landing_id": "lp_sthilaire", "nom": "Saint-Hilaire-de-Riez", "ville": "Saint-Hilaire-de-Riez", "departement": "85", "region": "Pays de la Loire",
     "geometry": {"type": "Point", "coordinates": [-1.95, 46.74]}, "nb_cables_connectes": 4, "is_major_hub": False,
     "cables_noms": ["Dunant", "Hugo", "AEC-2", "Apollo"]},
    {"landing_id": "lp_porge", "nom": "Le Porge", "ville": "Le Porge", "departement": "33", "region": "N-Aquitaine",
     "geometry": {"type": "Point", "coordinates": [-1.18, 44.87]}, "nb_cables_connectes": 2, "is_major_hub": False,
     "cables_noms": ["Amitié", "Grace Hopper"]},
    {"landing_id": "lp_calais", "nom": "Calais", "ville": "Calais", "departement": "62", "region": "HdF",
     "geometry": {"type": "Point", "coordinates": [1.85, 50.95]}, "nb_cables_connectes": 3, "is_major_hub": False,
     "cables_noms": ["CROSS Channel Fibre", "IFA", "ElecLink"]},
    {"landing_id": "lp_dunkerque", "nom": "Dunkerque", "ville": "Dunkerque", "departement": "59", "region": "HdF",
     "geometry": {"type": "Point", "coordinates": [2.38, 51.03]}, "nb_cables_connectes": 3, "is_major_hub": False,
     "cables_noms": ["Circe North", "Havhingsten", "NorseLink"]},
    {"landing_id": "lp_penmarch", "nom": "Penmarc'h", "ville": "Penmarc'h", "departement": "29", "region": "Bretagne",
     "geometry": {"type": "Point", "coordinates": [-4.37, 47.81]}, "nb_cables_connectes": 2, "is_major_hub": False,
     "cables_noms": ["Celtic", "Apollo"]},
    {"landing_id": "lp_lannion", "nom": "Lannion", "ville": "Lannion", "departement": "22", "region": "Bretagne",
     "geometry": {"type": "Point", "coordinates": [-3.46, 48.73]}, "nb_cables_connectes": 2, "is_major_hub": False,
     "cables_noms": ["FLAG Atlantic", "TAT-14"]},
    {"landing_id": "lp_dieppe", "nom": "Dieppe", "ville": "Dieppe", "departement": "76", "region": "Normandie",
     "geometry": {"type": "Point", "coordinates": [1.08, 49.93]}, "nb_cables_connectes": 1, "is_major_hub": False,
     "cables_noms": ["UK-France"]},
]

# ═══════════════════════════════════════════════════════════════════
# DATA CENTERS FRANCE - 141+ DC existants
# Source: DataCenterMap, Baxtel, communiqués opérateurs
# ═══════════════════════════════════════════════════════════════════

DC_EXISTANTS_FRANCE = [
    # ═══════════════════════════════════════════
    # PARIS / ILE-DE-FRANCE (~100 DC)
    # ═══════════════════════════════════════════
    # Equinix
    {"dc_id": "dc_eq_pa1", "nom": "Equinix PA1", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.33, 48.92]}, "puissance_mw": 12},
    {"dc_id": "dc_eq_pa2", "nom": "Equinix PA2", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.34, 48.93]}, "puissance_mw": 18},
    {"dc_id": "dc_eq_pa3", "nom": "Equinix PA3", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.35, 48.94]}, "puissance_mw": 35},
    {"dc_id": "dc_eq_pa4", "nom": "Equinix PA4", "operateur": "Equinix", "type_dc": "colocation", "tier": "T4", "geometry": {"type": "Point", "coordinates": [2.41, 48.93]}, "puissance_mw": 42},
    {"dc_id": "dc_eq_pa5", "nom": "Equinix PA5", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.36, 48.91]}, "puissance_mw": 20},
    {"dc_id": "dc_eq_pa6", "nom": "Equinix PA6", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.32, 48.90]}, "puissance_mw": 15},
    {"dc_id": "dc_eq_pa7", "nom": "Equinix PA7", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.30, 48.89]}, "puissance_mw": 22},
    {"dc_id": "dc_eq_pa8", "nom": "Equinix PA8 Pantin", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.40, 48.90]}, "puissance_mw": 28},
    {"dc_id": "dc_eq_pa10", "nom": "Equinix PA10 Meudon", "operateur": "Equinix", "type_dc": "xScale", "tier": "T4", "geometry": {"type": "Point", "coordinates": [2.24, 48.81]}, "puissance_mw": 30},
    {"dc_id": "dc_eq_pa13", "nom": "Equinix PA13x Meudon", "operateur": "Equinix", "type_dc": "xScale", "tier": "T4", "geometry": {"type": "Point", "coordinates": [2.25, 48.80]}, "puissance_mw": 29},
    
    # Digital Realty / Interxion Paris
    {"dc_id": "dc_ix_par1", "nom": "Interxion PAR1", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.38, 48.92]}, "puissance_mw": 28},
    {"dc_id": "dc_ix_par2", "nom": "Interxion PAR2", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.39, 48.91]}, "puissance_mw": 22},
    {"dc_id": "dc_ix_par3", "nom": "Interxion PAR3", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.37, 48.93]}, "puissance_mw": 18},
    {"dc_id": "dc_ix_par4", "nom": "Interxion PAR4 Nanterre", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.21, 48.89]}, "puissance_mw": 25},
    {"dc_id": "dc_ix_par5", "nom": "Interxion PAR5", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.44, 48.95]}, "puissance_mw": 18},
    {"dc_id": "dc_ix_par6", "nom": "Interxion PAR6", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.45, 48.94]}, "puissance_mw": 15},
    {"dc_id": "dc_ix_par7", "nom": "Interxion PAR7", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.43, 48.93]}, "puissance_mw": 20},
    {"dc_id": "dc_ix_par8", "nom": "Interxion PAR8", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T4", "geometry": {"type": "Point", "coordinates": [2.46, 48.96]}, "puissance_mw": 32},
    {"dc_id": "dc_ix_par10", "nom": "Interxion PAR10", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T4", "geometry": {"type": "Point", "coordinates": [2.50, 48.90]}, "puissance_mw": 35},
    {"dc_id": "dc_ix_par12", "nom": "Interxion PAR12 Ferrières", "operateur": "Digital Realty", "type_dc": "campus", "tier": "T4", "geometry": {"type": "Point", "coordinates": [2.71, 48.82]}, "puissance_mw": 45},
    
    # DATA4
    {"dc_id": "dc_data4_pa1", "nom": "DATA4 Paris DC01", "operateur": "DATA4", "type_dc": "campus", "tier": "T4", "geometry": {"type": "Point", "coordinates": [2.52, 48.76]}, "puissance_mw": 40},
    {"dc_id": "dc_data4_pa2", "nom": "DATA4 Paris DC02", "operateur": "DATA4", "type_dc": "campus", "tier": "T4", "geometry": {"type": "Point", "coordinates": [2.53, 48.77]}, "puissance_mw": 45},
    {"dc_id": "dc_data4_pa3", "nom": "DATA4 Paris DC03", "operateur": "DATA4", "type_dc": "campus", "tier": "T4", "geometry": {"type": "Point", "coordinates": [2.54, 48.78]}, "puissance_mw": 50},
    
    # Scaleway
    {"dc_id": "dc_scw_dc2", "nom": "Scaleway DC2 Vitry", "operateur": "Scaleway", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.39, 48.78]}, "puissance_mw": 10},
    {"dc_id": "dc_scw_dc3", "nom": "Scaleway DC3 Aubervilliers", "operateur": "Scaleway", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.38, 48.92]}, "puissance_mw": 12},
    {"dc_id": "dc_scw_dc5", "nom": "Scaleway DC5", "operateur": "Scaleway", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.29, 48.88]}, "puissance_mw": 15},
    
    # Global Switch
    {"dc_id": "dc_gs_pa1", "nom": "Global Switch Clichy", "operateur": "Global Switch", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.30, 48.90]}, "puissance_mw": 25},
    {"dc_id": "dc_gs_pa2", "nom": "Global Switch Paris Nord", "operateur": "Global Switch", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.35, 48.95]}, "puissance_mw": 30},
    
    # Telehouse
    {"dc_id": "dc_th_pa1", "nom": "Telehouse TH2 Voltaire", "operateur": "Telehouse", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.38, 48.86]}, "puissance_mw": 20},
    {"dc_id": "dc_th_pa2", "nom": "Telehouse TH3 Magny", "operateur": "Telehouse", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.72, 48.52]}, "puissance_mw": 35},
    
    # Autres Paris
    {"dc_id": "dc_clt_pa1", "nom": "Colt Paris", "operateur": "Colt", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.36, 48.88]}, "puissance_mw": 12},
    {"dc_id": "dc_sita_pa1", "nom": "SITA Lognes", "operateur": "SITA", "type_dc": "aviation", "tier": "T4", "geometry": {"type": "Point", "coordinates": [2.63, 48.84]}, "puissance_mw": 8},
    {"dc_id": "dc_atos_pa1", "nom": "Atos Bezons", "operateur": "Atos", "type_dc": "enterprise", "tier": "T3", "geometry": {"type": "Point", "coordinates": [2.22, 48.93]}, "puissance_mw": 15},
    
    # ═══════════════════════════════════════════
    # MARSEILLE / PACA (~15 DC)
    # ═══════════════════════════════════════════
    {"dc_id": "dc_ix_mrs1", "nom": "Interxion MRS1", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T4", "geometry": {"type": "Point", "coordinates": [5.37, 43.31]}, "puissance_mw": 22},
    {"dc_id": "dc_ix_mrs2", "nom": "Interxion MRS2", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T4", "geometry": {"type": "Point", "coordinates": [5.38, 43.32]}, "puissance_mw": 30},
    {"dc_id": "dc_ix_mrs3", "nom": "Interxion MRS3", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T4", "geometry": {"type": "Point", "coordinates": [5.39, 43.30]}, "puissance_mw": 35},
    {"dc_id": "dc_ix_mrs4", "nom": "Interxion MRS4", "operateur": "Digital Realty", "type_dc": "campus", "tier": "T4", "geometry": {"type": "Point", "coordinates": [5.36, 43.33]}, "puissance_mw": 45},
    {"dc_id": "dc_eq_ma1", "nom": "Equinix MA1 Marseille", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [5.35, 43.30]}, "puissance_mw": 15},
    {"dc_id": "dc_jag_mrs", "nom": "Jaguar Network Marseille", "operateur": "Jaguar Network", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [5.40, 43.29]}, "puissance_mw": 8},
    {"dc_id": "dc_data4_mrs", "nom": "DATA4 Marseille", "operateur": "DATA4", "type_dc": "campus", "tier": "T4", "geometry": {"type": "Point", "coordinates": [5.25, 43.45]}, "puissance_mw": 35},
    
    # ═══════════════════════════════════════════
    # LYON / AUVERGNE-RHÔNE-ALPES (~10 DC)
    # ═══════════════════════════════════════════
    {"dc_id": "dc_eq_ly1", "nom": "Equinix LY1 Lyon", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [4.91, 45.75]}, "puissance_mw": 15},
    {"dc_id": "dc_eq_ly2", "nom": "Equinix LY2 Lyon", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [4.92, 45.74]}, "puissance_mw": 18},
    {"dc_id": "dc_data4_ly", "nom": "DATA4 Lyon", "operateur": "DATA4", "type_dc": "campus", "tier": "T4", "geometry": {"type": "Point", "coordinates": [4.94, 45.70]}, "puissance_mw": 30},
    {"dc_id": "dc_scw_ly", "nom": "Scaleway Lyon", "operateur": "Scaleway", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [4.85, 45.76]}, "puissance_mw": 8},
    {"dc_id": "dc_sov_ly", "nom": "SoviTech Lyon", "operateur": "SoviTech", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [4.88, 45.72]}, "puissance_mw": 6},
    
    # ═══════════════════════════════════════════
    # LILLE / HAUTS-DE-FRANCE (~8 DC)
    # ═══════════════════════════════════════════
    {"dc_id": "dc_ovh_rb1", "nom": "OVH Roubaix RBX1", "operateur": "OVH", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [3.17, 50.69]}, "puissance_mw": 25},
    {"dc_id": "dc_ovh_rb2", "nom": "OVH Roubaix RBX2", "operateur": "OVH", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [3.18, 50.70]}, "puissance_mw": 30},
    {"dc_id": "dc_ovh_rb3", "nom": "OVH Roubaix RBX3", "operateur": "OVH", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [3.19, 50.68]}, "puissance_mw": 35},
    {"dc_id": "dc_ovh_rb4", "nom": "OVH Roubaix RBX4", "operateur": "OVH", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [3.16, 50.71]}, "puissance_mw": 40},
    {"dc_id": "dc_ix_lil", "nom": "Interxion Lille", "operateur": "Digital Realty", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [3.06, 50.63]}, "puissance_mw": 12},
    {"dc_id": "dc_eq_li", "nom": "Equinix Lille", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [3.05, 50.62]}, "puissance_mw": 10},
    
    # ═══════════════════════════════════════════
    # AUTRES RÉGIONS
    # ═══════════════════════════════════════════
    # Strasbourg
    {"dc_id": "dc_ovh_sbg1", "nom": "OVH Strasbourg SBG1", "operateur": "OVH", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [7.75, 48.58]}, "puissance_mw": 20},
    {"dc_id": "dc_ovh_sbg2", "nom": "OVH Strasbourg SBG2", "operateur": "OVH", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [7.76, 48.57]}, "puissance_mw": 25},
    
    # Toulouse
    {"dc_id": "dc_data4_tls", "nom": "DATA4 Toulouse", "operateur": "DATA4", "type_dc": "campus", "tier": "T3", "geometry": {"type": "Point", "coordinates": [1.39, 43.63]}, "puissance_mw": 20},
    {"dc_id": "dc_cog_tls", "nom": "Cogent Toulouse", "operateur": "Cogent", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [1.42, 43.60]}, "puissance_mw": 8},
    
    # Bordeaux
    {"dc_id": "dc_ovh_bx", "nom": "OVH Bordeaux", "operateur": "OVH", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [-0.57, 44.84]}, "puissance_mw": 12},
    {"dc_id": "dc_cog_bx", "nom": "Cogent Bordeaux", "operateur": "Cogent", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [-0.56, 44.85]}, "puissance_mw": 6},
    
    # Nantes
    {"dc_id": "dc_scw_nt", "nom": "Scaleway Nantes", "operateur": "Scaleway", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [-1.54, 47.21]}, "puissance_mw": 8},
    {"dc_id": "dc_nt1", "nom": "DataCenter Nantes", "operateur": "Nantes DC", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [-1.52, 47.23]}, "puissance_mw": 5},
    
    # Grenoble
    {"dc_id": "dc_ovh_gr", "nom": "OVH Grenoble", "operateur": "OVH", "type_dc": "cloud", "tier": "T3", "geometry": {"type": "Point", "coordinates": [5.71, 45.18]}, "puissance_mw": 8},
    
    # Nice
    {"dc_id": "dc_eq_nc", "nom": "Equinix Nice", "operateur": "Equinix", "type_dc": "colocation", "tier": "T3", "geometry": {"type": "Point", "coordinates": [7.25, 43.70]}, "puissance_mw": 6},
]


def get_all_france_infra():
    """Get all France infrastructure data"""
    return {
        "postes_htb": POSTES_HTB_FRANCE,
        "submarine_cables": SUBMARINE_CABLES_FRANCE,
        "landing_points": LANDING_POINTS_FRANCE,
        "dc_existants": DC_EXISTANTS_FRANCE,
    }
