"""
Cockpit Immo - Données S3REnR par poste
Données extraites des ETF 2024 et notifications de saturation
Sources: RTE S3REnR Île-de-France, PACA, Hauts-de-France
"""

# ═══════════════════════════════════════════════════════════════════
# S3REnR - Capacités par poste (MW)
# Clés: mw_reserve, mw_consomme, mw_dispo, etat, renforcement, horizon
# ═══════════════════════════════════════════════════════════════════

S3RENR_DATA = {
    # ═══════════════════════════════════════
    # ÎLE-DE-FRANCE — SATURÉ depuis 24/06/2025
    # Révision S3REnR en cours → nouveau schéma 2028
    # ═══════════════════════════════════════
    "IDF": {
        "status_global": "SATURE",
        "date_saturation": "2025-06-24",
        "revision_horizon": 2028,
        "capacite_globale_mw": 721,
        "postes": {
            "VILLENEUVE-ST-GEORGES": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "note": "Plus gros récepteur de transferts (12+ transferts)"},
            "MUREAUX": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature"},
            "TOURNAN-EN-BRIE": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature"},
            "MITRY-MORY": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature"},
            "RUNGIS": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature"},
            "MASSY": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature"},
            "PUTEAUX": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature"},
            "PERSAN": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature"},
            "LES ORMES": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature"},
            "JUINE": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature"},
        }
    },

    # ═══════════════════════════════════════
    # PACA — TOP OPPORTUNITÉS
    # Capacité globale S3REnR : 6400 MW (approuvé juillet 2022)
    # ═══════════════════════════════════════
    "PACA": {
        "status_global": "ACTIF",
        "capacite_globale_mw": 6400,
        "taux_consommation_pct": 20,
        "postes": {
            # TOP TIER — Postes neufs 225kV > 100 MW dispo
            "ASSE-DURANCE": {"mw_reserve": 160, "mw_consomme": 0, "mw_dispo": 160, "etat": "disponible", "tension_kv": 225, "renforcement": "Création poste 225/20kV (2029) + 2nd TR (2035)", "score_dc": 9},
            "BOUTRE-PROVENCE": {"mw_reserve": 160, "mw_consomme": 0, "mw_dispo": 160, "etat": "disponible", "tension_kv": 225, "renforcement": "Création poste 225/20kV (2029) + 2nd TR (2035)", "score_dc": 9},
            "SUD-VALENSOLE": {"mw_reserve": 160, "mw_consomme": 0, "mw_dispo": 160, "etat": "disponible", "tension_kv": 225, "renforcement": "Création poste 225/20kV (2033)", "score_dc": 9},
            "NORD-DE-CRAU": {"mw_reserve": 80, "mw_consomme": 0, "mw_dispo": 80, "etat": "disponible", "tension_kv": 225, "renforcement": "Création poste 225/20kV (2031)", "score_dc": 9},
            "LA GARDE": {"mw_reserve": 140, "mw_consomme": 5, "mw_dispo": 135, "etat": "disponible", "tension_kv": 225, "score_dc": 8},
            "TERRADOU": {"mw_reserve": 133, "mw_consomme": 13, "mw_dispo": 120, "etat": "disponible", "tension_kv": 225, "renforcement": "3ème TR 225/20kV (2032)", "score_dc": 8},
            "PLAN-D'ORGON": {"mw_reserve": 111, "mw_consomme": 10, "mw_dispo": 101, "etat": "disponible", "tension_kv": 225, "renforcement": "3ème TR 225/20kV (2032)", "score_dc": 8},
            "REALTOR": {"mw_reserve": 107, "mw_consomme": 0, "mw_dispo": 107, "etat": "disponible", "tension_kv": 225, "score_dc": 8, "projet_fos": "Noeud réseau renforcé — transit 2x2500 MW, horizon 2029"},
            "LA DURANNE": {"mw_reserve": 102, "mw_consomme": 4, "mw_dispo": 98, "etat": "disponible", "tension_kv": 225, "score_dc": 7},
            "DIGUE-DES-FRANCAIS": {"mw_reserve": 99, "mw_consomme": 1, "mw_dispo": 98, "etat": "disponible", "tension_kv": 225, "score_dc": 7},
            "ROSANAIS": {"mw_reserve": 80, "mw_consomme": 0, "mw_dispo": 80, "etat": "disponible", "tension_kv": 225, "renforcement": "Création poste 225/20kV (2033)", "score_dc": 8},
            "LARAGNAIS": {"mw_reserve": 80, "mw_consomme": 0, "mw_dispo": 80, "etat": "disponible", "tension_kv": 225, "renforcement": "Création poste 225-63-20kV (2033)", "score_dc": 8},
            "CENTRE-BUECH": {"mw_reserve": 80, "mw_consomme": 0, "mw_dispo": 80, "etat": "disponible", "tension_kv": 225, "renforcement": "Création poste 225-63-20kV (2031)", "score_dc": 8},
            "BIANCON": {"mw_reserve": 80, "mw_consomme": 0, "mw_dispo": 80, "etat": "disponible", "tension_kv": 225, "renforcement": "Création poste 225/20kV (2033)", "score_dc": 7},
            "ALBION": {"mw_reserve": 80, "mw_consomme": 4, "mw_dispo": 76, "etat": "disponible", "tension_kv": 225, "renforcement": "Création poste 225/20kV (2030)", "score_dc": 7},
            "HAUT-VAR": {"mw_reserve": 160, "mw_consomme": 85, "mw_dispo": 75, "etat": "disponible", "tension_kv": 225, "renforcement": "Création poste source FOX-AMPHOUX 225/20kV (S2/2028)", "score_dc": 7},
            "FEUILLANE": {"mw_reserve": 426, "mw_consomme": 352, "mw_dispo": 74, "etat": "disponible", "tension_kv": 225, "renforcement": "3ème TR + Création 225/20kV (2032-35)", "score_dc": 8, "projet_fos": "Hub central — départ nouvelle ligne 400kV, +3700 MW transit, horizon 2029"},
            "ENTREVAUX": {"mw_reserve": 80, "mw_consomme": 2, "mw_dispo": 78, "etat": "disponible", "tension_kv": 150, "renforcement": "Mutation TR 150/63kV (2033)", "score_dc": 7},
            "VALDEROURE": {"mw_reserve": 90, "mw_consomme": 18, "mw_dispo": 72, "etat": "disponible", "tension_kv": 225, "score_dc": 7},
            "CHATEAURENARD": {"mw_reserve": 73, "mw_consomme": 8, "mw_dispo": 65, "etat": "disponible", "renforcement": "Mutation TR 225/20kV 40→70MVA (2032)", "score_dc": 7},
            "L'ESCARELLE": {"mw_reserve": 66, "mw_consomme": 3, "mw_dispo": 64, "etat": "disponible", "renforcement": "3ème TR 63/20kV (2032)", "score_dc": 6},
            "SALON BEL AIR": {"mw_reserve": 60, "mw_consomme": 6, "mw_dispo": 54, "etat": "disponible", "tension_kv": 225, "renforcement": "Mutation TR 225/20kV 40→70MVA (2031)", "score_dc": 7},
            "SORGUES": {"mw_reserve": 65, "mw_consomme": 6, "mw_dispo": 59, "etat": "disponible", "score_dc": 6},
            "VEYNES": {"mw_reserve": 69, "mw_consomme": 11, "mw_dispo": 58, "etat": "disponible", "renforcement": "Mutation 2 TR + 3ème TR (2025-31)", "score_dc": 7},
            "SAUMATY": {"mw_reserve": 58, "mw_consomme": 6, "mw_dispo": 52, "etat": "disponible", "score_dc": 6},
            "MALLEMORT": {"mw_reserve": 68, "mw_consomme": 17, "mw_dispo": 51, "etat": "disponible", "renforcement": "3ème TR 63/20kV (2031)", "score_dc": 6},
            "SISTERON": {"mw_reserve": 58, "mw_consomme": 8, "mw_dispo": 50, "etat": "disponible", "renforcement": "2 TR 63/20kV mutation (2031-32)", "score_dc": 7},
            "COLOMB": {"mw_reserve": 44, "mw_consomme": 2, "mw_dispo": 42, "etat": "disponible", "score_dc": 6},
            "DRAGUIGNAN": {"mw_reserve": 43, "mw_consomme": 2, "mw_dispo": 41, "etat": "disponible", "score_dc": 5},
            "LAVERA": {"mw_reserve": 41, "mw_consomme": 1, "mw_dispo": 40, "etat": "disponible", "renforcement": "Mutation 2ème TR 63/20kV (2032)", "score_dc": 6},
            "BROC-CARROS": {"mw_reserve": 41, "mw_consomme": 0, "mw_dispo": 41, "etat": "disponible", "score_dc": 6},
            "ROCBARON": {"mw_reserve": 40, "mw_consomme": 1, "mw_dispo": 39, "etat": "disponible", "score_dc": 5},
            "RASSUEN": {"mw_reserve": 42, "mw_consomme": 4, "mw_dispo": 38, "etat": "disponible", "score_dc": 6},
            "VENTAVON": {"mw_reserve": 46, "mw_consomme": 8, "mw_dispo": 38, "etat": "disponible", "renforcement": "3ème TR 63/20kV (2032)", "score_dc": 6},
            "ARENC": {"mw_reserve": 41, "mw_consomme": 3, "mw_dispo": 38, "etat": "disponible", "score_dc": 6},
            "LES CHABAUDS": {"mw_reserve": 40, "mw_consomme": 3, "mw_dispo": 38, "etat": "disponible", "score_dc": 5},
            "BERRE": {"mw_reserve": 46, "mw_consomme": 12, "mw_dispo": 34, "etat": "disponible", "score_dc": 6},
            "SERRE-PONCON": {"mw_reserve": 38, "mw_consomme": 4, "mw_dispo": 34, "etat": "disponible", "renforcement": "Mutation 2 TR 63/20kV (2032)", "score_dc": 5},
            "TRESCLEOUX": {"mw_reserve": 40, "mw_consomme": 8, "mw_dispo": 32, "etat": "disponible", "renforcement": "3ème TR 63/20kV (S1/2027)", "score_dc": 5},
            "BARCELONNETTE": {"mw_reserve": 38, "mw_consomme": 5, "mw_dispo": 33, "etat": "disponible", "score_dc": 5},
            "LA BOCCA": {"mw_reserve": 35, "mw_consomme": 3, "mw_dispo": 32, "etat": "disponible", "score_dc": 5},
            "GARDANNE": {"mw_reserve": 36, "mw_consomme": 5, "mw_dispo": 31, "etat": "disponible", "score_dc": 6},
            "SOLLIES": {"mw_reserve": 34, "mw_consomme": 3, "mw_dispo": 31, "etat": "disponible", "score_dc": 5},
            "ST-MAXIMIN": {"mw_reserve": 41, "mw_consomme": 12, "mw_dispo": 29, "etat": "disponible", "renforcement": "3ème TR 63/20kV (S1/2026)", "score_dc": 5},
            "RISSO": {"mw_reserve": 33, "mw_consomme": 1, "mw_dispo": 32, "etat": "disponible", "score_dc": 5},
            "CHATEAU GOMBERT": {"mw_reserve": 31, "mw_consomme": 2, "mw_dispo": 29, "etat": "disponible", "score_dc": 5},
            "GONTARD": {"mw_reserve": 33, "mw_consomme": 4, "mw_dispo": 29, "etat": "disponible", "score_dc": 5},
            "SAINT SAVOURNIN": {"mw_reserve": 30, "mw_consomme": 2, "mw_dispo": 28, "etat": "disponible", "score_dc": 5},
            "MAZARGUES": {"mw_reserve": 29, "mw_consomme": 2, "mw_dispo": 27, "etat": "disponible", "score_dc": 5},
            "GRIMAUD": {"mw_reserve": 27, "mw_consomme": 0, "mw_dispo": 27, "etat": "disponible", "score_dc": 5},
            "MIRAMAS": {"mw_reserve": 30, "mw_consomme": 4, "mw_dispo": 27, "etat": "disponible", "renforcement": "3ème TR 63/20kV (2031)", "score_dc": 5},
            "FAVARY": {"mw_reserve": 32, "mw_consomme": 4, "mw_dispo": 28, "etat": "disponible", "score_dc": 5},

            # POSTES CONTRAINTS (< 10 MW dispo)
            "COURTINE": {"mw_reserve": 74, "mw_consomme": 74, "mw_dispo": 0, "etat": "contraint", "score_dc": 1},
            "LA BRILLANNE": {"mw_reserve": 13, "mw_consomme": 11, "mw_dispo": 2, "etat": "contraint", "score_dc": 2},
            "LA MARTINIERE": {"mw_reserve": 46, "mw_consomme": 41, "mw_dispo": 5, "etat": "contraint", "renforcement": "Ajout TR 63/20kV (2027)", "score_dc": 3},
            "GRISOLLES": {"mw_reserve": 16, "mw_consomme": 11, "mw_dispo": 5, "etat": "contraint", "score_dc": 2},
            "PIOLENC": {"mw_reserve": 27, "mw_consomme": 19, "mw_dispo": 8, "etat": "contraint", "score_dc": 3},
            "COMTAT": {"mw_reserve": 24, "mw_consomme": 15, "mw_dispo": 9, "etat": "contraint", "score_dc": 3},
            "COUREGES": {"mw_reserve": 31, "mw_consomme": 20, "mw_dispo": 11, "etat": "contraint", "score_dc": 3},
            "LES OLIVETTES": {"mw_reserve": 11, "mw_consomme": 9, "mw_dispo": 2, "etat": "contraint", "score_dc": 1},
            "STE-TULLE": {"mw_reserve": 10, "mw_consomme": 9, "mw_dispo": 1, "etat": "contraint", "score_dc": 1},
            "TRINITE-VICTOR": {"mw_reserve": 14, "mw_consomme": 13, "mw_dispo": 1, "etat": "contraint", "score_dc": 1},
            "VINON": {"mw_reserve": 6, "mw_consomme": 4, "mw_dispo": 2, "etat": "contraint", "score_dc": 1},
            "LIMANS": {"mw_reserve": 22, "mw_consomme": 16, "mw_dispo": 7, "etat": "contraint", "renforcement": "3ème TR 63/20kV (existant)", "score_dc": 3},
            "CASTILLON": {"mw_reserve": 1, "mw_consomme": 1, "mw_dispo": 0, "etat": "sature", "score_dc": 0},

            # POSTES PROJET FOS-JONQUIÈRES
            "ROQUEROUSSE": {"mw_reserve": 50, "mw_consomme": 50, "mw_dispo": 0, "etat": "contraint", "tension_kv": 225, "score_dc": 4, "note": "Poste 225kV, noeud projet Fos-Jonquières", "projet_fos": "Noeud réseau 400kV — transit 2x2200 MW, horizon 2029"},
            "TAVEL": {"mw_reserve": 100, "mw_consomme": 100, "mw_dispo": 0, "etat": "contraint", "tension_kv": 400, "score_dc": 4, "note": "Poste 400kV Gard, noeud amont projet Fos-Jonquières", "projet_fos": "Noeud amont 400kV — transit 2x2200 MW, horizon 2029"},

            # POSTES SATURÉS (0 MW)
            "BOLLENE": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "BOUTRE": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "renforcement": "Ajout 3ème TR 400/225kV (S2/2025)", "score_dc": 2},
            "CURBANS": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "MONDRAGON": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "ROGNAC": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "ORAISON": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "VIDAUBAN": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "LAVALDUC": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "PONTEAU": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "score_dc": 0, "projet_fos": "Connexion ZIP Fos — transit 2x1300 MW, horizon 2029"},
            "NEOULES": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "ST-CHAMAS": {"mw_reserve": 0, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
        }
    },

    # ═══════════════════════════════════════
    # HAUTS-DE-FRANCE
    # ═══════════════════════════════════════
    "HdF": {
        "status_global": "ACTIF",
        "capacite_globale_mw": 8700,
        "postes": {
            # TOP TIER — > 50 MW dispo
            "PERTAIN 3": {"mw_reserve": 216, "mw_consomme": 43, "mw_dispo": 173, "etat": "disponible", "score_dc": 9},
            "LISLET 3": {"mw_reserve": 216, "mw_consomme": 50, "mw_dispo": 166, "etat": "disponible", "score_dc": 9},
            "FRUGES": {"mw_reserve": 162, "mw_consomme": 6, "mw_dispo": 156, "etat": "disponible", "score_dc": 8},
            "BOIS-BERNARD": {"mw_reserve": 138, "mw_consomme": 0, "mw_dispo": 138, "etat": "disponible", "score_dc": 8},
            "NOGENTEL 3": {"mw_reserve": 137, "mw_consomme": 0, "mw_dispo": 137, "etat": "disponible", "score_dc": 8},
            "SETIER 3": {"mw_reserve": 199, "mw_consomme": 63, "mw_dispo": 136, "etat": "disponible", "score_dc": 8},
            "PLATEAU 3": {"mw_reserve": 108, "mw_consomme": 11, "mw_dispo": 97, "etat": "disponible", "score_dc": 7},
            "FERE-EN-TARDENOIS": {"mw_reserve": 79, "mw_consomme": 0, "mw_dispo": 79, "etat": "disponible", "score_dc": 7},
            "OUEST AMIENOIS": {"mw_reserve": 78, "mw_consomme": 0, "mw_dispo": 78, "etat": "disponible", "score_dc": 7},
            "VALESCOURT 3": {"mw_reserve": 76, "mw_consomme": 0, "mw_dispo": 76, "etat": "disponible", "score_dc": 7},
            "VILLERS-ST-SEPULCRE": {"mw_reserve": 73, "mw_consomme": 0, "mw_dispo": 73, "etat": "disponible", "score_dc": 7},
            "VALENCIENNES": {"mw_reserve": 66, "mw_consomme": 1, "mw_dispo": 65, "etat": "disponible", "score_dc": 7},
            "SANDRICOURT": {"mw_reserve": 65, "mw_consomme": 1, "mw_dispo": 64, "etat": "disponible", "score_dc": 7},
            "LA VICOGNE": {"mw_reserve": 72, "mw_consomme": 10, "mw_dispo": 62, "etat": "disponible", "score_dc": 7},
            "ECUVILLY": {"mw_reserve": 60, "mw_consomme": 0, "mw_dispo": 60, "etat": "disponible", "score_dc": 7},
            "BEVILLERS": {"mw_reserve": 70, "mw_consomme": 14, "mw_dispo": 56, "etat": "disponible", "renforcement": "Création poste (mise en service mars 2025)", "score_dc": 7},
            "SUD ARTOIS": {"mw_reserve": 80, "mw_consomme": 28, "mw_dispo": 52, "etat": "disponible", "score_dc": 7},
            "LE QUESNOY": {"mw_reserve": 51, "mw_consomme": 1, "mw_dispo": 50, "etat": "disponible", "score_dc": 6},
            "ORCHIES": {"mw_reserve": 50, "mw_consomme": 1, "mw_dispo": 49, "etat": "disponible", "score_dc": 6},
            "AVESNES-LE-COMTE": {"mw_reserve": 46, "mw_consomme": 2, "mw_dispo": 44, "etat": "disponible", "score_dc": 6},
            "TRAISNEL": {"mw_reserve": 47, "mw_consomme": 2, "mw_dispo": 45, "etat": "disponible", "score_dc": 6},
            "DOUVRIN": {"mw_reserve": 40, "mw_consomme": 1, "mw_dispo": 39, "etat": "disponible", "score_dc": 6},
            "CAPELLE": {"mw_reserve": 38, "mw_consomme": 0, "mw_dispo": 38, "etat": "disponible", "score_dc": 6},
            "MANOISE": {"mw_reserve": 39, "mw_consomme": 1, "mw_dispo": 38, "etat": "disponible", "score_dc": 6},
            "MARQUISE": {"mw_reserve": 37, "mw_consomme": 0, "mw_dispo": 37, "etat": "disponible", "score_dc": 6},
            "PINON": {"mw_reserve": 38, "mw_consomme": 1, "mw_dispo": 37, "etat": "disponible", "score_dc": 6},
            "LAON": {"mw_reserve": 39, "mw_consomme": 4, "mw_dispo": 35, "etat": "disponible", "score_dc": 6},
            "ST-OMER": {"mw_reserve": 37, "mw_consomme": 2, "mw_dispo": 35, "etat": "disponible", "score_dc": 6},
            "TRIE-CHATEAU": {"mw_reserve": 35, "mw_consomme": 1, "mw_dispo": 34, "etat": "disponible", "score_dc": 6},
            "VERTE-VOIE": {"mw_reserve": 34, "mw_consomme": 0, "mw_dispo": 34, "etat": "disponible", "score_dc": 6},
            "VENDIN": {"mw_reserve": 34, "mw_consomme": 1, "mw_dispo": 33, "etat": "disponible", "score_dc": 6},
            "DENAIN": {"mw_reserve": 39, "mw_consomme": 6, "mw_dispo": 33, "etat": "disponible", "score_dc": 6},
            "ESSARS": {"mw_reserve": 33, "mw_consomme": 1, "mw_dispo": 32, "etat": "disponible", "score_dc": 6},
            "LUMBRES": {"mw_reserve": 33, "mw_consomme": 1, "mw_dispo": 32, "etat": "disponible", "score_dc": 6},
            "RUE": {"mw_reserve": 35, "mw_consomme": 3, "mw_dispo": 32, "etat": "disponible", "score_dc": 6},
            "VIEUX-CONDE": {"mw_reserve": 31, "mw_consomme": 1, "mw_dispo": 30, "etat": "disponible", "score_dc": 6},
            "BUIRE": {"mw_reserve": 30, "mw_consomme": 0, "mw_dispo": 30, "etat": "disponible", "score_dc": 6},
            "CALAIS": {"mw_reserve": 29, "mw_consomme": 1, "mw_dispo": 28, "etat": "disponible", "score_dc": 6},
            "BECQUE": {"mw_reserve": 29, "mw_consomme": 1, "mw_dispo": 28, "etat": "disponible", "score_dc": 6},
            "QUAROUBLE": {"mw_reserve": 28, "mw_consomme": 0, "mw_dispo": 28, "etat": "disponible", "score_dc": 6},
            "COMPIEGNE": {"mw_reserve": 32, "mw_consomme": 6, "mw_dispo": 26, "etat": "disponible", "score_dc": 5},
            "SOISSONS-NOTRE-DAME": {"mw_reserve": 30, "mw_consomme": 1, "mw_dispo": 29, "etat": "disponible", "score_dc": 5},
            "MONTCROISETTE": {"mw_reserve": 26, "mw_consomme": 0, "mw_dispo": 26, "etat": "disponible", "score_dc": 5},
            "NOGENTEL": {"mw_reserve": 27, "mw_consomme": 1, "mw_dispo": 26, "etat": "disponible", "score_dc": 5},
            "PETITE FORET": {"mw_reserve": 26, "mw_consomme": 0, "mw_dispo": 26, "etat": "disponible", "score_dc": 5},
            "DUVY": {"mw_reserve": 25, "mw_consomme": 0, "mw_dispo": 25, "etat": "disponible", "score_dc": 5},
            "AVION": {"mw_reserve": 25, "mw_consomme": 1, "mw_dispo": 24, "etat": "disponible", "score_dc": 5},
            "SEQUEDIN": {"mw_reserve": 25, "mw_consomme": 1, "mw_dispo": 24, "etat": "disponible", "score_dc": 5},
            "ESTAIRES": {"mw_reserve": 31, "mw_consomme": 4, "mw_dispo": 27, "etat": "disponible", "score_dc": 5},
            "AULNOYE": {"mw_reserve": 24, "mw_consomme": 1, "mw_dispo": 23, "etat": "disponible", "score_dc": 5},
            "GRANDE-SYNTHE": {"mw_reserve": 25, "mw_consomme": 3, "mw_dispo": 22, "etat": "disponible", "score_dc": 6},
            "LES ATTAQUES": {"mw_reserve": 23, "mw_consomme": 1, "mw_dispo": 22, "etat": "disponible", "score_dc": 6},
            "HELLEMMES": {"mw_reserve": 23, "mw_consomme": 1, "mw_dispo": 22, "etat": "disponible", "score_dc": 5},
            "CARVIN": {"mw_reserve": 23, "mw_consomme": 1, "mw_dispo": 22, "etat": "disponible", "score_dc": 5},
            "ANSEREUILLES": {"mw_reserve": 23, "mw_consomme": 1, "mw_dispo": 22, "etat": "disponible", "score_dc": 5},
            "FOYAUX": {"mw_reserve": 23, "mw_consomme": 1, "mw_dispo": 22, "etat": "disponible", "score_dc": 5},
            "ST-AMAND": {"mw_reserve": 23, "mw_consomme": 2, "mw_dispo": 21, "etat": "disponible", "score_dc": 5},
            "GARENNES": {"mw_reserve": 21, "mw_consomme": 0, "mw_dispo": 21, "etat": "disponible", "score_dc": 5},

            # POSTES SATURÉS (0 MW)
            "MANDARINS": {"mw_reserve": 200, "mw_consomme": 200, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "LES AVENNES": {"mw_reserve": 191, "mw_consomme": 191, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "HERIE LA VIEVILLE": {"mw_reserve": 178, "mw_consomme": 176, "mw_dispo": 2, "etat": "contraint", "score_dc": 1},
            "BEAUTOR": {"mw_reserve": 303, "mw_consomme": 301, "mw_dispo": 2, "etat": "contraint", "score_dc": 1},
            "CROIXRAULT SUD": {"mw_reserve": 110, "mw_consomme": 108, "mw_dispo": 2, "etat": "contraint", "score_dc": 1},
            "ALBERT": {"mw_reserve": 59, "mw_consomme": 59, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "DECHY": {"mw_reserve": 33, "mw_consomme": 33, "mw_dispo": 0, "etat": "sature", "score_dc": 0},
            "LE THUEL": {"mw_reserve": 61, "mw_consomme": 61, "mw_dispo": 0, "etat": "sature", "renforcement": "Création poste (déc 2026)", "score_dc": 2},
        }
    },

    # ═══════════════════════════════════════════
    # OCCITANIE (estimations ETF 2024-2025)
    # ═══════════════════════════════════════════
    "OCC": {
        "capacite_globale_mw": 3800,
        "status_global": "DISPONIBLE",
        "postes": {
            "GAUDIERE": {"mw_reserve": 410, "mw_consomme": 310, "mw_dispo": 100, "etat": "disponible", "tension_kv": 400, "score_dc": 8},
            "DONZAC": {"mw_reserve": 300, "mw_consomme": 210, "mw_dispo": 90, "etat": "disponible", "tension_kv": 225, "score_dc": 7},
            "BAIXAS": {"mw_reserve": 350, "mw_consomme": 280, "mw_dispo": 70, "etat": "disponible", "tension_kv": 225, "score_dc": 7},
            "TARASCON": {"mw_reserve": 280, "mw_consomme": 220, "mw_dispo": 60, "etat": "disponible", "tension_kv": 225, "score_dc": 6},
            "LANNEMEZAN": {"mw_reserve": 200, "mw_consomme": 150, "mw_dispo": 50, "etat": "disponible", "tension_kv": 225, "score_dc": 6},
            "VERFEIL": {"mw_reserve": 180, "mw_consomme": 140, "mw_dispo": 40, "etat": "disponible", "score_dc": 5},
            "SANILHAC": {"mw_reserve": 150, "mw_consomme": 120, "mw_dispo": 30, "etat": "disponible", "score_dc": 4},
            "BRENS": {"mw_reserve": 120, "mw_consomme": 100, "mw_dispo": 20, "etat": "disponible", "score_dc": 3},
            "CORBIERES": {"mw_reserve": 100, "mw_consomme": 90, "mw_dispo": 10, "etat": "disponible", "score_dc": 3},
            "LÉZIGNAN": {"mw_reserve": 80, "mw_consomme": 75, "mw_dispo": 5, "etat": "contraint", "score_dc": 2},
        }
    },

    # ═══════════════════════════════════════════
    # AUVERGNE-RHÔNE-ALPES (estimations ETF 2024-2025)
    # ═══════════════════════════════════════════
    "AuRA": {
        "capacite_globale_mw": 5200,
        "status_global": "DISPONIBLE",
        "postes": {
            "GENISSIAT": {"mw_reserve": 800, "mw_consomme": 500, "mw_dispo": 300, "etat": "disponible", "tension_kv": 400, "renforcement": "2ème TR 400/225 kV (2028)", "score_dc": 10},
            "CUSSET": {"mw_reserve": 450, "mw_consomme": 280, "mw_dispo": 170, "etat": "disponible", "tension_kv": 225, "score_dc": 9},
            "MONTEYNARD": {"mw_reserve": 500, "mw_consomme": 350, "mw_dispo": 150, "etat": "disponible", "tension_kv": 225, "score_dc": 8},
            "PRATCLAUX": {"mw_reserve": 350, "mw_consomme": 250, "mw_dispo": 100, "etat": "disponible", "tension_kv": 225, "score_dc": 7},
            "LE CHEYLAS": {"mw_reserve": 400, "mw_consomme": 330, "mw_dispo": 70, "etat": "disponible", "tension_kv": 225, "score_dc": 7},
            "BOURG-ST-ANDEOL": {"mw_reserve": 250, "mw_consomme": 200, "mw_dispo": 50, "etat": "disponible", "score_dc": 5},
            "CRENEY": {"mw_reserve": 200, "mw_consomme": 170, "mw_dispo": 30, "etat": "disponible", "score_dc": 4},
            "VENISSIEUX": {"mw_reserve": 300, "mw_consomme": 280, "mw_dispo": 20, "etat": "contraint", "score_dc": 3},
            "SAINT-PRIEST": {"mw_reserve": 250, "mw_consomme": 240, "mw_dispo": 10, "etat": "contraint", "score_dc": 2},
        }
    },

    # ═══════════════════════════════════════════
    # GRAND EST (estimations ETF 2024-2025)
    # ═══════════════════════════════════════════
    "GES": {
        "capacite_globale_mw": 3500,
        "status_global": "DISPONIBLE",
        "postes": {
            "BEZAUMONT": {"mw_reserve": 350, "mw_consomme": 200, "mw_dispo": 150, "etat": "disponible", "tension_kv": 400, "score_dc": 9},
            "MUHLBACH": {"mw_reserve": 300, "mw_consomme": 180, "mw_dispo": 120, "etat": "disponible", "tension_kv": 225, "score_dc": 8},
            "VIGY": {"mw_reserve": 280, "mw_consomme": 200, "mw_dispo": 80, "etat": "disponible", "tension_kv": 225, "score_dc": 7},
            "CATTENOM": {"mw_reserve": 400, "mw_consomme": 340, "mw_dispo": 60, "etat": "disponible", "tension_kv": 400, "score_dc": 7},
            "SCHEER": {"mw_reserve": 200, "mw_consomme": 150, "mw_dispo": 50, "etat": "disponible", "score_dc": 6},
            "BAINVILLE": {"mw_reserve": 180, "mw_consomme": 140, "mw_dispo": 40, "etat": "disponible", "score_dc": 5},
            "REIMS-NORD": {"mw_reserve": 150, "mw_consomme": 120, "mw_dispo": 30, "etat": "disponible", "score_dc": 4},
            "LONNY": {"mw_reserve": 120, "mw_consomme": 100, "mw_dispo": 20, "etat": "contraint", "score_dc": 3},
        }
    },

    # ═══════════════════════════════════════════
    # NOUVELLE-AQUITAINE (estimations ETF 2024-2025)
    # ═══════════════════════════════════════════
    "NAQ": {
        "capacite_globale_mw": 2800,
        "status_global": "DISPONIBLE",
        "postes": {
            "CIVAUX": {"mw_reserve": 500, "mw_consomme": 380, "mw_dispo": 120, "etat": "disponible", "tension_kv": 400, "score_dc": 9},
            "BRAUD": {"mw_reserve": 400, "mw_consomme": 300, "mw_dispo": 100, "etat": "disponible", "tension_kv": 400, "score_dc": 8},
            "DOGNON": {"mw_reserve": 300, "mw_consomme": 230, "mw_dispo": 70, "etat": "disponible", "tension_kv": 225, "score_dc": 7},
            "CUBNEZAIS": {"mw_reserve": 250, "mw_consomme": 200, "mw_dispo": 50, "etat": "disponible", "score_dc": 6},
            "SABAROTS": {"mw_reserve": 180, "mw_consomme": 140, "mw_dispo": 40, "etat": "disponible", "score_dc": 5},
            "SAUCATS": {"mw_reserve": 200, "mw_consomme": 170, "mw_dispo": 30, "etat": "disponible", "score_dc": 4},
            "BIRAC": {"mw_reserve": 150, "mw_consomme": 130, "mw_dispo": 20, "etat": "contraint", "score_dc": 3},
        }
    },
}


def get_s3renr_data():
    """Return all S3REnR data"""
    return S3RENR_DATA


def get_s3renr_top_opportunities(min_mw=30, limit=20):
    """Get top DC opportunities from S3REnR data sorted by MW available"""
    opportunities = []
    for region, data in S3RENR_DATA.items():
        for poste_nom, poste in data.get("postes", {}).items():
            mw = poste.get("mw_dispo", 0)
            if mw >= min_mw:
                opportunities.append({
                    "region": region,
                    "poste": poste_nom,
                    "mw_reserve": poste.get("mw_reserve", 0),
                    "mw_consomme": poste.get("mw_consomme", 0),
                    "mw_dispo": mw,
                    "etat": poste.get("etat", "inconnu"),
                    "tension_kv": poste.get("tension_kv"),
                    "renforcement": poste.get("renforcement"),
                    "score_dc": poste.get("score_dc", 0),
                })
    opportunities.sort(key=lambda x: -x["mw_dispo"])
    return opportunities[:limit]
