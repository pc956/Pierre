"""
Cockpit Immo - Seed Data Generator
60 parcelles across IDF, PACA, AuRA, HdF, Occitanie
"""
import random
from typing import List, Dict, Any

# Landing points France
LANDING_POINTS = [
    {
        'landing_id': 'lp_marseille',
        'nom': 'Marseille - Prado',
        'ville': 'Marseille',
        'departement': '13',
        'region': 'PACA',
        'geometry': {'type': 'Point', 'coordinates': [5.3858, 43.2744]},
        'nb_cables_connectes': 18,
        'cables_noms': ['SEA-ME-WE 6', 'SEA-ME-WE 5', 'PEACE', '2Africa', 'AAE-1'],
        'is_major_hub': True,
    },
    {
        'landing_id': 'lp_calais',
        'nom': 'Calais',
        'ville': 'Calais',
        'departement': '62',
        'region': 'Hauts-de-France',
        'geometry': {'type': 'Point', 'coordinates': [1.8587, 50.9513]},
        'nb_cables_connectes': 1,
        'cables_noms': ['CROSS Channel Fibre'],
        'is_major_hub': False,
    },
    {
        'landing_id': 'lp_st_hilaire',
        'nom': 'Saint-Hilaire-de-Riez',
        'ville': 'Saint-Hilaire-de-Riez',
        'departement': '85',
        'region': 'Pays de la Loire',
        'geometry': {'type': 'Point', 'coordinates': [-1.9530, 46.7450]},
        'nb_cables_connectes': 3,
        'cables_noms': ['AEC-2', 'Dunant', 'Hugo'],
        'is_major_hub': False,
    },
    {
        'landing_id': 'lp_dunkerque',
        'nom': 'Dunkerque',
        'ville': 'Dunkerque',
        'departement': '59',
        'region': 'Hauts-de-France',
        'geometry': {'type': 'Point', 'coordinates': [2.3768, 51.0347]},
        'nb_cables_connectes': 2,
        'cables_noms': ['Circe North', 'Havhingsten'],
        'is_major_hub': False,
    },
]

# DC existants
DC_EXISTANTS = [
    # IDF
    {'dc_id': 'dc_pa3', 'nom': 'Equinix PA3', 'operateur': 'Equinix', 'type_dc': 'colocation', 'geometry': {'type': 'Point', 'coordinates': [2.3522, 48.9362]}, 'puissance_mw': 35, 'tier': 'T3'},
    {'dc_id': 'dc_pa4', 'nom': 'Equinix PA4', 'operateur': 'Equinix', 'type_dc': 'colocation', 'geometry': {'type': 'Point', 'coordinates': [2.4102, 48.9281]}, 'puissance_mw': 42, 'tier': 'T4'},
    {'dc_id': 'dc_interxion1', 'nom': 'Interxion PAR1', 'operateur': 'Interxion', 'type_dc': 'colocation', 'geometry': {'type': 'Point', 'coordinates': [2.3831, 48.9165]}, 'puissance_mw': 28, 'tier': 'T3'},
    {'dc_id': 'dc_interxion2', 'nom': 'Interxion PAR5', 'operateur': 'Interxion', 'type_dc': 'colocation', 'geometry': {'type': 'Point', 'coordinates': [2.4421, 48.9523]}, 'puissance_mw': 18, 'tier': 'T3'},
    {'dc_id': 'dc_scaleway', 'nom': 'Scaleway DC3', 'operateur': 'Scaleway', 'type_dc': 'cloud', 'geometry': {'type': 'Point', 'coordinates': [2.2932, 48.8821]}, 'puissance_mw': 12, 'tier': 'T3'},
    {'dc_id': 'dc_ovh_rb', 'nom': 'OVH Roubaix', 'operateur': 'OVH', 'type_dc': 'cloud', 'geometry': {'type': 'Point', 'coordinates': [3.1746, 50.6942]}, 'puissance_mw': 65, 'tier': 'T3'},
    # PACA
    {'dc_id': 'dc_mrs1', 'nom': 'Interxion MRS1', 'operateur': 'Interxion', 'type_dc': 'colocation', 'geometry': {'type': 'Point', 'coordinates': [5.3698, 43.3096]}, 'puissance_mw': 22, 'tier': 'T4'},
    {'dc_id': 'dc_mrs2', 'nom': 'Interxion MRS2', 'operateur': 'Interxion', 'type_dc': 'colocation', 'geometry': {'type': 'Point', 'coordinates': [5.3782, 43.3214]}, 'puissance_mw': 30, 'tier': 'T4'},
    # AuRA
    {'dc_id': 'dc_lyon1', 'nom': 'Equinix LY1', 'operateur': 'Equinix', 'type_dc': 'colocation', 'geometry': {'type': 'Point', 'coordinates': [4.9102, 45.7482]}, 'puissance_mw': 15, 'tier': 'T3'},
]

def generate_polygon_from_center(lng: float, lat: float, size_ha: float) -> Dict[str, Any]:
    """Generate a simple rectangular polygon from center point"""
    # Approximate: 1 degree lat ~ 111km, 1 degree lng ~ 111km * cos(lat)
    import math
    side_m = math.sqrt(size_ha * 10000)  # meters per side
    delta_lat = side_m / 111000 / 2
    delta_lng = side_m / (111000 * math.cos(math.radians(lat))) / 2
    
    return {
        'type': 'Polygon',
        'coordinates': [[
            [lng - delta_lng, lat - delta_lat],
            [lng + delta_lng, lat - delta_lat],
            [lng + delta_lng, lat + delta_lat],
            [lng - delta_lng, lat + delta_lat],
            [lng - delta_lng, lat - delta_lat],
        ]]
    }


def distance_km(p1: Dict[str, Any], lng2: float, lat2: float) -> float:
    """Haversine distance in km"""
    import math
    lng1, lat1 = p1['coordinates']
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def find_nearest_landing(lng: float, lat: float) -> Dict[str, Any]:
    """Find nearest landing point"""
    nearest = None
    min_dist = float('inf')
    for lp in LANDING_POINTS:
        dist = distance_km(lp['geometry'], lng, lat)
        if dist < min_dist:
            min_dist = dist
            nearest = lp
    return {'landing': nearest, 'distance_km': min_dist}


def find_dc_voisins(lng: float, lat: float, radius_km: float = 15) -> List[Dict[str, Any]]:
    """Find DC within radius"""
    voisins = []
    for dc in DC_EXISTANTS:
        dist = distance_km(dc['geometry'], lng, lat)
        if dist <= radius_km:
            voisins.append({
                'dc_id': dc['dc_id'],
                'nom': dc['nom'],
                'type_dc': dc['type_dc'],
                'distance_m': dist * 1000,
                'puissance_mw': dc['puissance_mw'],
            })
    return voisins


# Base parcels data
PARCELS_BASE = [
    # ═══════════════════════════════════════════════════
    # IDF (30 parcelles)
    # ═══════════════════════════════════════════════════
    # Gonesse - Zone logistique
    {'commune': 'Gonesse', 'departement': '95', 'region': 'IDF', 'lng': 2.4512, 'lat': 48.9871, 'surface_ha': 8.4, 'plu_zone': 'AU', 'site_type': 'greenfield'},
    {'commune': 'Gonesse', 'departement': '95', 'region': 'IDF', 'lng': 2.4621, 'lat': 48.9912, 'surface_ha': 12.5, 'plu_zone': 'AUX', 'site_type': 'greenfield'},
    # Roissy
    {'commune': 'Roissy-en-France', 'departement': '95', 'region': 'IDF', 'lng': 2.5232, 'lat': 49.0021, 'surface_ha': 15.2, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Roissy-en-France', 'departement': '95', 'region': 'IDF', 'lng': 2.5341, 'lat': 49.0089, 'surface_ha': 6.8, 'plu_zone': 'I', 'site_type': 'brownfield'},
    # Villepinte
    {'commune': 'Villepinte', 'departement': '93', 'region': 'IDF', 'lng': 2.5521, 'lat': 48.9621, 'surface_ha': 4.2, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Villepinte', 'departement': '93', 'region': 'IDF', 'lng': 2.5612, 'lat': 48.9582, 'surface_ha': 7.1, 'plu_zone': 'IX', 'site_type': 'friche_industrielle'},
    # Tremblay-en-France
    {'commune': 'Tremblay-en-France', 'departement': '93', 'region': 'IDF', 'lng': 2.5721, 'lat': 48.9432, 'surface_ha': 9.3, 'plu_zone': 'I', 'site_type': 'zac'},
    {'commune': 'Tremblay-en-France', 'departement': '93', 'region': 'IDF', 'lng': 2.5832, 'lat': 48.9512, 'surface_ha': 5.6, 'plu_zone': 'UX', 'site_type': 'brownfield'},
    # Poissy
    {'commune': 'Poissy', 'departement': '78', 'region': 'IDF', 'lng': 2.0312, 'lat': 48.9312, 'surface_ha': 3.8, 'plu_zone': 'UE', 'site_type': 'friche_industrielle'},
    {'commune': 'Poissy', 'departement': '78', 'region': 'IDF', 'lng': 2.0421, 'lat': 48.9281, 'surface_ha': 6.2, 'plu_zone': 'AU', 'site_type': 'greenfield'},
    # Croissy-Beaubourg
    {'commune': 'Croissy-Beaubourg', 'departement': '77', 'region': 'IDF', 'lng': 2.6521, 'lat': 48.8232, 'surface_ha': 11.4, 'plu_zone': 'I', 'site_type': 'zac'},
    {'commune': 'Croissy-Beaubourg', 'departement': '77', 'region': 'IDF', 'lng': 2.6612, 'lat': 48.8312, 'surface_ha': 8.9, 'plu_zone': 'UX', 'site_type': 'brownfield'},
    # Gennevilliers
    {'commune': 'Gennevilliers', 'departement': '92', 'region': 'IDF', 'lng': 2.2921, 'lat': 48.9321, 'surface_ha': 2.8, 'plu_zone': 'UI', 'site_type': 'friche_industrielle'},
    {'commune': 'Gennevilliers', 'departement': '92', 'region': 'IDF', 'lng': 2.3012, 'lat': 48.9281, 'surface_ha': 4.5, 'plu_zone': 'I', 'site_type': 'brownfield'},
    # Saint-Denis
    {'commune': 'Saint-Denis', 'departement': '93', 'region': 'IDF', 'lng': 2.3621, 'lat': 48.9321, 'surface_ha': 2.1, 'plu_zone': 'UX', 'site_type': 'friche_industrielle'},
    {'commune': 'Saint-Denis', 'departement': '93', 'region': 'IDF', 'lng': 2.3721, 'lat': 48.9412, 'surface_ha': 3.4, 'plu_zone': 'U', 'site_type': 'brownfield'},
    # Aubervilliers
    {'commune': 'Aubervilliers', 'departement': '93', 'region': 'IDF', 'lng': 2.3832, 'lat': 48.9132, 'surface_ha': 1.8, 'plu_zone': 'UX', 'site_type': 'friche_industrielle'},
    # La Courneuve
    {'commune': 'La Courneuve', 'departement': '93', 'region': 'IDF', 'lng': 2.3921, 'lat': 48.9232, 'surface_ha': 5.2, 'plu_zone': 'I', 'site_type': 'zac'},
    # Marne-la-Vallée
    {'commune': 'Serris', 'departement': '77', 'region': 'IDF', 'lng': 2.7821, 'lat': 48.8521, 'surface_ha': 18.5, 'plu_zone': 'AUX', 'site_type': 'greenfield'},
    {'commune': 'Bailly-Romainvilliers', 'departement': '77', 'region': 'IDF', 'lng': 2.8121, 'lat': 48.8621, 'surface_ha': 14.2, 'plu_zone': 'AU', 'site_type': 'greenfield'},
    # Évry
    {'commune': 'Évry-Courcouronnes', 'departement': '91', 'region': 'IDF', 'lng': 2.4321, 'lat': 48.6321, 'surface_ha': 6.8, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Lisses', 'departement': '91', 'region': 'IDF', 'lng': 2.4521, 'lat': 48.6121, 'surface_ha': 9.1, 'plu_zone': 'I', 'site_type': 'brownfield'},
    # Cergy
    {'commune': 'Cergy', 'departement': '95', 'region': 'IDF', 'lng': 2.0621, 'lat': 49.0321, 'surface_ha': 7.4, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Osny', 'departement': '95', 'region': 'IDF', 'lng': 2.0721, 'lat': 49.0521, 'surface_ha': 5.2, 'plu_zone': 'AU', 'site_type': 'greenfield'},
    # Inéligibles IDF
    {'commune': 'Noisy-le-Grand', 'departement': '93', 'region': 'IDF', 'lng': 2.5521, 'lat': 48.8432, 'surface_ha': 0.8, 'plu_zone': 'U', 'site_type': 'greenfield', 'ppri_zone': 'rouge'},
    {'commune': 'Chelles', 'departement': '77', 'region': 'IDF', 'lng': 2.5921, 'lat': 48.8832, 'surface_ha': 1.2, 'plu_zone': 'N', 'site_type': 'greenfield'},
    {'commune': 'Meaux', 'departement': '77', 'region': 'IDF', 'lng': 2.8821, 'lat': 48.9532, 'surface_ha': 3.5, 'plu_zone': 'A', 'site_type': 'greenfield'},
    # Excellents IDF (shovel-ready)
    {'commune': 'Le Bourget', 'departement': '93', 'region': 'IDF', 'lng': 2.4221, 'lat': 48.9421, 'surface_ha': 4.8, 'plu_zone': 'I', 'site_type': 'zac', 'shovel_ready': True},
    {'commune': 'Dugny', 'departement': '93', 'region': 'IDF', 'lng': 2.4121, 'lat': 48.9521, 'surface_ha': 6.3, 'plu_zone': 'UX', 'site_type': 'friche_industrielle', 'shovel_ready': True},
    {'commune': 'Mitry-Mory', 'departement': '77', 'region': 'IDF', 'lng': 2.6221, 'lat': 48.9832, 'surface_ha': 22.5, 'plu_zone': 'I', 'site_type': 'zac', 'shovel_ready': True},

    # ═══════════════════════════════════════════════════
    # PACA (8 parcelles)
    # ═══════════════════════════════════════════════════
    {'commune': 'Vitrolles', 'departement': '13', 'region': 'PACA', 'lng': 5.2421, 'lat': 43.4521, 'surface_ha': 8.2, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Vitrolles', 'departement': '13', 'region': 'PACA', 'lng': 5.2521, 'lat': 43.4621, 'surface_ha': 5.6, 'plu_zone': 'I', 'site_type': 'brownfield'},
    {'commune': 'Les Pennes-Mirabeau', 'departement': '13', 'region': 'PACA', 'lng': 5.3121, 'lat': 43.4121, 'surface_ha': 12.4, 'plu_zone': 'AUX', 'site_type': 'greenfield'},
    {'commune': 'Aix-en-Provence', 'departement': '13', 'region': 'PACA', 'lng': 5.4521, 'lat': 43.5221, 'surface_ha': 6.8, 'plu_zone': 'UE', 'site_type': 'zac'},
    {'commune': 'Marseille', 'departement': '13', 'region': 'PACA', 'lng': 5.3821, 'lat': 43.3321, 'surface_ha': 3.2, 'plu_zone': 'I', 'site_type': 'friche_industrielle'},
    {'commune': 'Marignane', 'departement': '13', 'region': 'PACA', 'lng': 5.2121, 'lat': 43.4221, 'surface_ha': 9.5, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Fos-sur-Mer', 'departement': '13', 'region': 'PACA', 'lng': 4.9421, 'lat': 43.4421, 'surface_ha': 25.0, 'plu_zone': 'I', 'site_type': 'zac', 'shovel_ready': True},
    {'commune': 'Istres', 'departement': '13', 'region': 'PACA', 'lng': 4.9821, 'lat': 43.5121, 'surface_ha': 15.2, 'plu_zone': 'AU', 'site_type': 'greenfield'},

    # ═══════════════════════════════════════════════════
    # AuRA (10 parcelles)
    # ═══════════════════════════════════════════════════
    {'commune': 'Saint-Priest', 'departement': '69', 'region': 'AuRA', 'lng': 4.9421, 'lat': 45.6921, 'surface_ha': 7.8, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Saint-Priest', 'departement': '69', 'region': 'AuRA', 'lng': 4.9521, 'lat': 45.7021, 'surface_ha': 5.4, 'plu_zone': 'I', 'site_type': 'brownfield'},
    {'commune': 'Vénissieux', 'departement': '69', 'region': 'AuRA', 'lng': 4.8821, 'lat': 45.6921, 'surface_ha': 4.2, 'plu_zone': 'UI', 'site_type': 'friche_industrielle'},
    {'commune': 'Vénissieux', 'departement': '69', 'region': 'AuRA', 'lng': 4.8921, 'lat': 45.6821, 'surface_ha': 6.1, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Bourgoin-Jallieu', 'departement': '38', 'region': 'AuRA', 'lng': 5.2721, 'lat': 45.5821, 'surface_ha': 12.5, 'plu_zone': 'AUX', 'site_type': 'greenfield'},
    {'commune': 'Bourgoin-Jallieu', 'departement': '38', 'region': 'AuRA', 'lng': 5.2821, 'lat': 45.5921, 'surface_ha': 8.9, 'plu_zone': 'I', 'site_type': 'zac'},
    {'commune': 'Corbas', 'departement': '69', 'region': 'AuRA', 'lng': 4.9021, 'lat': 45.6621, 'surface_ha': 9.2, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Chassieu', 'departement': '69', 'region': 'AuRA', 'lng': 4.9621, 'lat': 45.7421, 'surface_ha': 6.5, 'plu_zone': 'I', 'site_type': 'brownfield'},
    {'commune': 'Décines-Charpieu', 'departement': '69', 'region': 'AuRA', 'lng': 4.9321, 'lat': 45.7721, 'surface_ha': 3.8, 'plu_zone': 'UE', 'site_type': 'friche_industrielle'},
    {'commune': 'Genas', 'departement': '69', 'region': 'AuRA', 'lng': 4.9921, 'lat': 45.7321, 'surface_ha': 11.2, 'plu_zone': 'AU', 'site_type': 'greenfield'},

    # ═══════════════════════════════════════════════════
    # Hauts-de-France (7 parcelles)
    # ═══════════════════════════════════════════════════
    {'commune': 'Lesquin', 'departement': '59', 'region': 'HdF', 'lng': 3.1121, 'lat': 50.5821, 'surface_ha': 8.5, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Lesquin', 'departement': '59', 'region': 'HdF', 'lng': 3.1221, 'lat': 50.5921, 'surface_ha': 6.2, 'plu_zone': 'I', 'site_type': 'brownfield'},
    {'commune': 'Seclin', 'departement': '59', 'region': 'HdF', 'lng': 3.0321, 'lat': 50.5421, 'surface_ha': 14.8, 'plu_zone': 'AUX', 'site_type': 'greenfield'},
    {'commune': 'Douai', 'departement': '59', 'region': 'HdF', 'lng': 3.0821, 'lat': 50.3721, 'surface_ha': 9.5, 'plu_zone': 'I', 'site_type': 'friche_industrielle'},
    {'commune': 'Roubaix', 'departement': '59', 'region': 'HdF', 'lng': 3.1821, 'lat': 50.6921, 'surface_ha': 4.2, 'plu_zone': 'UI', 'site_type': 'friche_industrielle'},
    {'commune': 'Villeneuve-d\'Ascq', 'departement': '59', 'region': 'HdF', 'lng': 3.1321, 'lat': 50.6321, 'surface_ha': 5.8, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Calais', 'departement': '62', 'region': 'HdF', 'lng': 1.8821, 'lat': 50.9421, 'surface_ha': 7.5, 'plu_zone': 'I', 'site_type': 'zac', 'shovel_ready': True},

    # ═══════════════════════════════════════════════════
    # Occitanie (5 parcelles)
    # ═══════════════════════════════════════════════════
    {'commune': 'Blagnac', 'departement': '31', 'region': 'Occitanie', 'lng': 1.3921, 'lat': 43.6321, 'surface_ha': 10.5, 'plu_zone': 'UX', 'site_type': 'zac'},
    {'commune': 'Blagnac', 'departement': '31', 'region': 'Occitanie', 'lng': 1.4021, 'lat': 43.6421, 'surface_ha': 6.8, 'plu_zone': 'I', 'site_type': 'brownfield'},
    {'commune': 'Labège', 'departement': '31', 'region': 'Occitanie', 'lng': 1.5321, 'lat': 43.5321, 'surface_ha': 8.2, 'plu_zone': 'UE', 'site_type': 'zac'},
    {'commune': 'Colomiers', 'departement': '31', 'region': 'Occitanie', 'lng': 1.3321, 'lat': 43.6121, 'surface_ha': 12.4, 'plu_zone': 'AUX', 'site_type': 'greenfield'},
    {'commune': 'Montpellier', 'departement': '34', 'region': 'Occitanie', 'lng': 3.8721, 'lat': 43.6121, 'surface_ha': 5.5, 'plu_zone': 'UX', 'site_type': 'zac'},
]


def generate_parcel(base: Dict[str, Any], idx: int) -> Dict[str, Any]:
    """Generate a complete parcel from base data"""
    lng = base['lng']
    lat = base['lat']
    surface_ha = base['surface_ha']
    
    # Generate geometry
    geometry = generate_polygon_from_center(lng, lat, surface_ha)
    centroid = {'type': 'Point', 'coordinates': [lng, lat]}
    
    # Find nearest landing point
    landing_info = find_nearest_landing(lng, lat)
    
    # Find DC voisins
    dc_voisins = find_dc_voisins(lng, lat)
    
    # Generate infrastructure data with some randomness
    random.seed(idx)  # Reproducible randomness
    
    is_shovel_ready = base.get('shovel_ready', False)
    region = base['region']
    
    # Distance to electrical infrastructure (varies by region)
    if region == 'IDF':
        dist_htb_base = random.uniform(1500, 8000)
        dist_hta_base = random.uniform(500, 3000)
        zone_sat = random.choice(['disponible', 'tendu', 'tendu', 'sature'])
    elif region == 'PACA':
        dist_htb_base = random.uniform(2000, 10000)
        dist_hta_base = random.uniform(800, 4000)
        zone_sat = random.choice(['disponible', 'disponible', 'tendu'])
    else:
        dist_htb_base = random.uniform(3000, 12000)
        dist_hta_base = random.uniform(1000, 5000)
        zone_sat = random.choice(['disponible', 'disponible', 'tendu', 'inconnu'])
    
    if is_shovel_ready:
        dist_htb_base *= 0.5
        dist_hta_base *= 0.5
        zone_sat = 'disponible'
    
    # Generate parcel
    parcel = {
        'parcel_id': f'parcel_{idx:04d}',
        'ref_cadastrale': f'{base["departement"]}{base["commune"][:3].upper()}{idx:04d}',
        'code_commune': f'{base["departement"]}{str(idx % 100).zfill(3)}',
        'commune': base['commune'],
        'departement': base['departement'],
        'region': region,
        
        'geometry': geometry,
        'centroid': centroid,
        'surface_m2': surface_ha * 10000,
        'surface_ha': surface_ha,
        'latitude': lat,
        'longitude': lng,
        
        # Electrical
        'dist_poste_htb_m': round(dist_htb_base),
        'tension_htb_kv': random.choice([63, 63, 225, 225, 400]),
        'puissance_poste_mva': random.choice([150, 200, 300, 400]),
        'dist_poste_hta_m': round(dist_hta_base),
        'dist_ligne_400kv_m': round(dist_htb_base * random.uniform(0.8, 2.5)),
        'dist_ligne_225kv_m': round(dist_htb_base * random.uniform(0.6, 1.8)),
        'dist_ligne_63kv_m': round(dist_htb_base * random.uniform(0.4, 1.2)),
        'capacite_confirmee_mw': random.choice([None, None, 30, 45, 60, 80]) if not is_shovel_ready else random.choice([50, 80, 100]),
        'capacite_residuelle_estimee_mw': random.uniform(20, 80),
        'zone_saturation': zone_sat,
        'file_attente_mw': random.choice([0, 500, 1200, 2500, 4000]) if zone_sat != 'disponible' else 0,
        'poste_source_nom': f'Poste {base["commune"]}',
        
        # Fibre
        'dist_backbone_fibre_m': round(random.uniform(200, 3000) * (0.3 if is_shovel_ready else 1.0)),
        'nb_operateurs_fibre': random.choice([1, 2, 2, 3, 3, 4]),
        'has_international': region in ['IDF', 'PACA'],
        
        # Landing points
        'dist_landing_point_km': round(landing_info['distance_km'], 1),
        'landing_point_nom': landing_info['landing']['nom'],
        'landing_point_nb_cables': landing_info['landing']['nb_cables_connectes'],
        'landing_point_is_major_hub': landing_info['landing']['is_major_hub'],
        
        # Water
        'cours_eau_dist_m': round(random.uniform(500, 8000)),
        'zone_stress_hydrique': region in ['PACA', 'Occitanie'] and random.random() > 0.6,
        
        # PLU
        'plu_zone': base['plu_zone'],
        'plu_numerise': True,
        'dans_zac_active': base['site_type'] == 'zac',
        'rezonage_requis': base['plu_zone'] in ['AU', '2AU', 'AUX'],
        'delai_rezonage_plu_mois': random.choice([12, 18, 24, 36]) if base['plu_zone'] in ['AU', '2AU', 'AUX'] else None,
        'icpe_regime': random.choice(['enregistrement', 'enregistrement', 'autorisation']),
        
        # ZAN
        'commune_zan_pct': round(random.uniform(20, 75), 1),
        'site_type': base['site_type'],
        
        # Risques
        'ppri_zone': base.get('ppri_zone', random.choice([None, None, None, 'vert', 'bleu'])),
        'sismique_zone': 1 if region not in ['PACA'] else random.choice([2, 3]),
        'argiles_alea': random.choice(['faible', 'faible', 'moyen']) if region != 'IDF' else 'faible',
        'drac_zone_archeo': random.random() > 0.85,
        
        # DVF
        'dvf_prix_m2_p50': round(random.uniform(60, 180) * (1.5 if region == 'IDF' else 1.0), 0),
        'dvf_nb_transactions': random.randint(3, 25),
        'proprietaire_nom': random.choice(['SCI FONCIERE NORD', 'CARREFOUR PROPERTY', 'PROLOGIS FRANCE', 'PRIVATE OWNER', 'GOODMAN FRANCE', 'SEGRO']),
        'proprietaire_type': random.choice(['sci', 'fonciere', 'prive']),
        
        # Shovel-ready
        'raccordement_elec_existant': is_shovel_ready,
        'raccordement_fibre_existant': is_shovel_ready or random.random() > 0.7,
        'voirie_desserte_existante': is_shovel_ready or base['site_type'] in ['zac', 'brownfield'],
        
        # Consolidation
        'surface_consolidable_ha': round(surface_ha * random.uniform(1.0, 2.0), 1),
        
        # DC voisins
        'dc_voisins': dc_voisins,
    }
    
    return parcel


def generate_all_parcels() -> List[Dict[str, Any]]:
    """Generate all 60 parcels"""
    return [generate_parcel(base, idx) for idx, base in enumerate(PARCELS_BASE)]


def get_seed_data() -> Dict[str, Any]:
    """Get all seed data"""
    return {
        'parcels': generate_all_parcels(),
        'landing_points': LANDING_POINTS,
        'dc_existants': DC_EXISTANTS,
    }
