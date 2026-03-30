"""
Cockpit Immo - France Infrastructure Data
Complete data for HTB substations, submarine cables, and data centers.
HTB substations loaded from real OSM/Overpass data (rte_postes_*.json).
"""
import json
import os

_DATA_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_json(filename):
    path = os.path.join(_DATA_DIR, filename)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

# ═══════════════════════════════════════════════════════════════════
# POSTES HTB FRANCE - Loaded from real geographic data (OSM/Overpass)
# rte_postes_map.json: ≥225kV postes for map display (~1000+)
# rte_postes_all.json: all ≥63kV postes for distance calculations (~3500+)
# ═══════════════════════════════════════════════════════════════════

POSTES_HTB_FRANCE = _load_json("rte_postes_map.json")
POSTES_HTB_ALL = _load_json("rte_postes_all.json")

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


# ═══════════════════════════════════════════════════════════════════
# LIGNES HAUTE TENSION 400kV - Corridors principaux RTE
# Tracés simplifiés reliant les postes 400kV majeurs
# ═══════════════════════════════════════════════════════════════════

LIGNES_400KV_FRANCE = [
    # Grand axe Nord-Sud (colonne vertébrale)
    {"asset_id": "l400_ns1", "nom": "400kV Lille-Paris Nord", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[3.08, 50.58], [2.83, 50.43], [2.30, 49.89], [2.45, 49.42], [2.45, 48.98]]}},
    {"asset_id": "l400_ns2", "nom": "400kV Paris-Lyon", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[2.36, 48.94], [2.44, 48.63], [2.66, 48.54], [3.09, 47.90], [4.07, 48.30], [4.85, 46.78], [4.88, 45.69], [4.95, 45.74]]}},
    {"asset_id": "l400_ns3", "nom": "400kV Lyon-Marseille", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[4.95, 45.74], [4.89, 44.93], [4.81, 43.95], [5.25, 43.46], [5.38, 43.35]]}},

    # Axe Est
    {"asset_id": "l400_e1", "nom": "400kV Paris-Strasbourg", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[2.45, 48.98], [4.03, 49.25], [6.18, 49.12], [7.75, 48.58]]}},
    {"asset_id": "l400_e2", "nom": "400kV Strasbourg-Lyon", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[7.75, 48.58], [7.34, 47.75], [6.86, 47.64], [6.02, 47.24], [5.04, 47.32], [4.95, 45.74]]}},

    # Axe Ouest
    {"asset_id": "l400_w1", "nom": "400kV Paris-Nantes", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[2.36, 48.94], [2.06, 49.04], [1.91, 47.90], [0.69, 47.39], [0.20, 48.00], [-0.55, 47.47], [-1.55, 47.22]]}},
    {"asset_id": "l400_w2", "nom": "400kV Nantes-Bordeaux", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[-1.55, 47.22], [-1.43, 46.67], [-1.15, 46.16], [-0.58, 44.87]]}},

    # Axe Nord-Ouest
    {"asset_id": "l400_nw1", "nom": "400kV Paris-Rouen-Le Havre", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[2.36, 48.94], [2.13, 48.80], [1.15, 49.02], [1.09, 49.44], [0.12, 49.49]]}},
    {"asset_id": "l400_nw2", "nom": "400kV Rouen-Rennes", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[1.09, 49.44], [-0.37, 49.18], [-1.62, 49.64], [-1.68, 48.11]]}},
    {"asset_id": "l400_nw3", "nom": "400kV Rennes-Brest", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[-1.68, 48.11], [-2.76, 48.51], [-4.10, 47.99], [-4.49, 48.39]]}},

    # Axe Sud
    {"asset_id": "l400_s1", "nom": "400kV Bordeaux-Toulouse", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[-0.58, 44.87], [0.62, 44.20], [1.40, 43.64]]}},
    {"asset_id": "l400_s2", "nom": "400kV Toulouse-Marseille", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[1.40, 43.64], [2.35, 43.21], [3.22, 43.34], [3.87, 43.61], [4.36, 43.84], [4.81, 43.95], [4.95, 43.45], [5.38, 43.35]]}},

    # Interconnexions
    {"asset_id": "l400_ic1", "nom": "400kV Dunkerque-Lille", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[2.38, 51.03], [2.83, 50.43], [3.08, 50.58]]}},
    {"asset_id": "l400_ic2", "nom": "400kV Lyon-Grenoble", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[4.95, 45.74], [5.72, 45.19]]}},
    {"asset_id": "l400_ic3", "nom": "400kV Nice-Marseille", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[5.38, 43.35], [5.93, 43.12], [7.01, 43.55], [7.26, 43.70]]}},
    {"asset_id": "l400_ic4", "nom": "400kV Dijon-Orléans", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[5.04, 47.32], [3.57, 47.80], [2.40, 47.08], [1.91, 47.90]]}},
    {"asset_id": "l400_ic5", "nom": "400kV Metz-Strasbourg", "type": "ligne_400kv", "tension_kv": 400,
     "geometry": {"type": "LineString", "coordinates": [[6.18, 49.12], [6.18, 48.69], [7.75, 48.58]]}},
]

# ═══════════════════════════════════════════════════════════════════
# LIGNES HAUTE TENSION 225kV - Réseau de répartition
# Tracés simplifiés reliant les postes 225kV entre eux et aux 400kV
# ═══════════════════════════════════════════════════════════════════

LIGNES_225KV_FRANCE = [
    # IDF maillage dense
    {"asset_id": "l225_idf1", "nom": "225kV IDF Nord - Villepinte-Gonesse", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[2.55, 48.96], [2.52, 49.01], [2.45, 48.98], [2.39, 48.92]]}},
    {"asset_id": "l225_idf2", "nom": "225kV IDF Est - Croissy-MlV", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[2.65, 48.82], [2.78, 48.85], [2.88, 48.95]]}},
    {"asset_id": "l225_idf3", "nom": "225kV IDF Ouest - Nanterre-Versailles", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[2.21, 48.89], [2.29, 48.93], [2.36, 48.94], [2.39, 48.79]]}},
    {"asset_id": "l225_idf4", "nom": "225kV IDF Sud - Vitry-Évry", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[2.39, 48.79], [2.44, 48.63], [2.66, 48.54]]}},
    {"asset_id": "l225_idf5", "nom": "225kV IDF Tremblay-La Courneuve", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[2.57, 48.95], [2.45, 48.98], [2.39, 48.92], [2.36, 48.94]]}},

    # PACA
    {"asset_id": "l225_paca1", "nom": "225kV Marseille-Vitrolles-Aix", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[5.38, 43.35], [5.21, 43.42], [5.25, 43.46], [5.45, 43.52]]}},
    {"asset_id": "l225_paca2", "nom": "225kV Fos-Istres-Marignane", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[4.95, 43.45], [4.98, 43.51], [5.21, 43.42]]}},
    {"asset_id": "l225_paca3", "nom": "225kV Nice-Toulon", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[7.26, 43.70], [7.01, 43.55], [5.93, 43.12]]}},

    # Auvergne-Rhône-Alpes
    {"asset_id": "l225_aura1", "nom": "225kV Lyon-St Priest-Vénissieux", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[4.95, 45.74], [4.94, 45.70], [4.88, 45.69]]}},
    {"asset_id": "l225_aura2", "nom": "225kV Lyon-St Étienne", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[4.88, 45.69], [4.39, 45.44]]}},
    {"asset_id": "l225_aura3", "nom": "225kV Grenoble-Chambéry-Annecy", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[5.72, 45.19], [5.92, 45.57], [6.13, 45.90]]}},
    {"asset_id": "l225_aura4", "nom": "225kV Lyon-Valence", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[4.88, 45.69], [4.89, 44.93]]}},
    {"asset_id": "l225_aura5", "nom": "225kV Clermont-Lyon", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[3.09, 45.78], [4.39, 45.44], [4.88, 45.69]]}},

    # Hauts-de-France
    {"asset_id": "l225_hdf1", "nom": "225kV Lille-Roubaix-Valenciennes", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[3.08, 50.58], [3.18, 50.69], [3.52, 50.36]]}},
    {"asset_id": "l225_hdf2", "nom": "225kV Calais-Dunkerque", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[1.88, 50.94], [2.38, 51.03]]}},
    {"asset_id": "l225_hdf3", "nom": "225kV Douai-Amiens-Compiègne", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[3.08, 50.37], [2.30, 49.89], [2.83, 49.42]]}},

    # Occitanie
    {"asset_id": "l225_occ1", "nom": "225kV Toulouse-Montpellier", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[1.40, 43.64], [2.35, 43.21], [3.22, 43.34], [3.87, 43.61]]}},
    {"asset_id": "l225_occ2", "nom": "225kV Montpellier-Nîmes-Avignon", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[3.87, 43.61], [4.36, 43.84], [4.81, 43.95]]}},
    {"asset_id": "l225_occ3", "nom": "225kV Perpignan-Béziers", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[2.89, 42.70], [3.22, 43.34]]}},

    # Nouvelle-Aquitaine
    {"asset_id": "l225_naq1", "nom": "225kV Bordeaux-La Rochelle-Poitiers", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[-0.58, 44.87], [-1.15, 46.16], [0.34, 46.58]]}},
    {"asset_id": "l225_naq2", "nom": "225kV Bordeaux-Bayonne-Pau", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[-0.58, 44.87], [-1.47, 43.49], [-0.37, 43.30]]}},
    {"asset_id": "l225_naq3", "nom": "225kV Poitiers-Limoges", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[0.34, 46.58], [1.26, 45.83]]}},

    # Grand Est
    {"asset_id": "l225_ges1", "nom": "225kV Nancy-Metz-Reims", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[6.18, 48.69], [6.18, 49.12], [4.03, 49.25]]}},
    {"asset_id": "l225_ges2", "nom": "225kV Strasbourg-Mulhouse", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[7.75, 48.58], [7.36, 48.08], [7.34, 47.75]]}},
    {"asset_id": "l225_ges3", "nom": "225kV Reims-Troyes", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[4.03, 49.25], [4.07, 48.30]]}},

    # Normandie
    {"asset_id": "l225_nor1", "nom": "225kV Caen-Cherbourg", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[-0.37, 49.18], [-1.62, 49.64]]}},

    # Bretagne
    {"asset_id": "l225_bzh1", "nom": "225kV Rennes-Lorient-Quimper", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[-1.68, 48.11], [-2.76, 47.66], [-3.37, 47.75], [-4.10, 47.99]]}},
    {"asset_id": "l225_bzh2", "nom": "225kV Rennes-Brest", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[-1.68, 48.11], [-2.76, 48.51], [-4.49, 48.39]]}},

    # Pays de la Loire
    {"asset_id": "l225_pdl1", "nom": "225kV Nantes-Angers-Le Mans", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[-1.55, 47.22], [-0.55, 47.47], [0.20, 48.00]]}},
    {"asset_id": "l225_pdl2", "nom": "225kV Nantes-St Nazaire", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[-1.55, 47.22], [-2.21, 47.28]]}},

    # Centre-Val de Loire
    {"asset_id": "l225_cvl1", "nom": "225kV Orléans-Tours-Bourges", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[1.91, 47.90], [0.69, 47.39], [2.40, 47.08]]}},

    # Bourgogne-Franche-Comté
    {"asset_id": "l225_bfc1", "nom": "225kV Dijon-Besançon-Belfort", "type": "ligne_225kv", "tension_kv": 225,
     "geometry": {"type": "LineString", "coordinates": [[5.04, 47.32], [6.02, 47.24], [6.86, 47.64]]}},
]


def get_all_france_infra():
    """Get all France infrastructure data.
    postes_htb: major substations (≥225kV) for map display
    postes_htb_all: all substations (≥63kV) for distance calculations
    """
    return {
        "postes_htb": POSTES_HTB_FRANCE,
        "postes_htb_all": POSTES_HTB_ALL if POSTES_HTB_ALL else POSTES_HTB_FRANCE,
        "lignes_400kv": LIGNES_400KV_FRANCE,
        "lignes_225kv": LIGNES_225KV_FRANCE,
        "submarine_cables": SUBMARINE_CABLES_FRANCE,
        "landing_points": LANDING_POINTS_FRANCE,
        "dc_existants": DC_EXISTANTS_FRANCE,
    }
