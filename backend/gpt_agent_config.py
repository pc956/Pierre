"""
Cockpit Immo — GPT Agent Configuration
OpenAPI schema + system prompt for ChatGPT Custom GPT Actions
"""

COCKPIT_IMMO_GPT_SYSTEM_PROMPT = """Tu es un expert en prospection foncière pour data centers en France. Tu utilises l'API Cockpit Immo pour trouver les meilleurs terrains.

## Ton rôle
Tu aides les professionnels de l'immobilier et du développement de data centers à identifier les meilleurs sites en France, en analysant les capacités électriques (S3REnR), les délais de raccordement, les coûts fonciers et les risques administratifs.

## Comment utiliser l'API

### Recherche de sites
Quand l'utilisateur cherche des terrains, appelle `POST /api/dc/search` avec les bons paramètres.

Traduis les demandes en paramètres :
- "20MW" → mw_target: 20
- "minimum 10MW" → mw_min: 10  
- "en moins de 12 mois" → max_delay_months: 12
- "en IDF" ou "en Île-de-France" ou "près de Paris" → region: "IDF"
- "en PACA" ou "dans le sud" ou "Marseille" → region: "PACA"
- "dans le Nord" ou "Hauts-de-France" → region: "HdF"
- "le plus vite possible" → strategy: "speed"
- "le moins cher" → strategy: "cost"
- "maximum de puissance" → strategy: "power"
- "terrain industriel" ou "brownfield" → brownfield_only: true
- "réseau disponible" → grid_priority: true

### Fiche site détaillée
Quand l'utilisateur veut plus d'infos sur un site, appelle `GET /api/dc/site/{site_id}`.

### Résumé S3REnR
Pour une vue d'ensemble des capacités réseau par région, appelle `GET /api/s3renr/summary`.

### Top opportunités
Pour les meilleures opportunités de raccordement, appelle `GET /api/s3renr/top-opportunities`.

## Comment présenter les résultats

Présente les résultats sous forme de **tableau synthétique** suivi d'une **analyse** :

### Tableau
| # | Site | Région | MW Dispo | Tension | Score | Délai | Risque |
|---|------|--------|----------|---------|-------|-------|--------|

### Analyse
- Commente le **meilleur choix** et pourquoi
- Signale les **risques** (saturation, délai long, PLU)
- Propose des **alternatives** si la demande est trop contrainte
- Mentionne les **renforcements prévus** (S3REnR) qui pourraient débloquer de la capacité

## Règles importantes
1. TOUJOURS indiquer quand un réseau est **saturé** (IDF notamment)
2. Expliquer le **score** en termes simples (pas juste un chiffre)
3. Si aucun résultat ne correspond, proposer d'**élargir les critères** (région, MW, délai)
4. Mentionner la source des données : "Données S3REnR (RTE) + API Carto IGN"
5. Ne jamais inventer de données — si l'info n'est pas dans l'API, le dire
6. Utiliser le vocabulaire métier : poste source, raccordement, PLU, brownfield, TTM

## Contexte métier
- **S3REnR** = Schéma Régional de Raccordement au Réseau des Énergies Renouvelables (données RTE)
- **PLU** = Plan Local d'Urbanisme (zone U = urbaine, AU = à urbaniser, A = agricole, N = naturelle)
- **Poste HTB** = Poste Haute Tension B (63kV, 225kV, 400kV)
- **IDF est saturé** = Très peu de capacité disponible en Île-de-France
- **HdF et PACA** = Régions avec le plus de capacité disponible actuellement
- Les scores vont de 0 à 100, 80+ = excellent site
"""


def get_openapi_schema(server_url: str) -> dict:
    """Generate OpenAPI 3.1.0 schema for GPT Actions"""
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Cockpit Immo — DC Site Search API",
            "description": "API de recherche foncière pour data centers en France. Interroge les capacités électriques (S3REnR/RTE), les données cadastrales (IGN), et les zones PLU pour identifier les meilleurs terrains.",
            "version": "1.0.0",
        },
        "servers": [
            {"url": server_url}
        ],
        "paths": {
            "/api/dc/search": {
                "post": {
                    "operationId": "searchDCSites",
                    "summary": "Rechercher des terrains pour data centers",
                    "description": "Recherche multicritères de sites pour data centers en France. Retourne des résultats scorés et triés selon la stratégie choisie.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "mw_target": {
                                            "type": "number",
                                            "description": "Puissance cible en MW (ex: 20 pour un DC de 20MW)",
                                            "default": 20,
                                        },
                                        "mw_min": {
                                            "type": "number",
                                            "description": "Puissance minimum acceptable en MW",
                                            "default": 5,
                                        },
                                        "max_delay_months": {
                                            "type": "integer",
                                            "description": "Délai maximum de raccordement en mois",
                                            "default": 36,
                                        },
                                        "surface_min_ha": {
                                            "type": "number",
                                            "description": "Surface minimum du terrain en hectares",
                                            "default": 0,
                                        },
                                        "region": {
                                            "type": "string",
                                            "description": "Région cible. Valeurs: IDF, PACA, HdF, AuRA, BFC, BRE, CVL, GES, NOR, NAQ, OCC, PDL, COR. Accepte aussi: ile-de-france, paris, provence, marseille, nord, lille, etc.",
                                            "nullable": True,
                                        },
                                        "max_distance_substation_km": {
                                            "type": "number",
                                            "description": "Distance max au poste source HTB en km",
                                            "default": 100,
                                        },
                                        "strategy": {
                                            "type": "string",
                                            "enum": ["speed", "cost", "power", "balanced"],
                                            "description": "Stratégie de scoring: speed (raccordement rapide), cost (foncier pas cher), power (max MW), balanced (équilibré)",
                                            "default": "balanced",
                                        },
                                        "grid_priority": {
                                            "type": "boolean",
                                            "description": "Si true, exclut les sites avec réseau saturé",
                                            "default": False,
                                        },
                                        "brownfield_only": {
                                            "type": "boolean",
                                            "description": "Si true, uniquement les terrains industriels (brownfield)",
                                            "default": False,
                                        },
                                        "page": {
                                            "type": "integer",
                                            "description": "Numéro de page (pagination)",
                                            "default": 1,
                                        },
                                        "per_page": {
                                            "type": "integer",
                                            "description": "Résultats par page (max 50)",
                                            "default": 10,
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Liste de sites scorés et triés",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SearchResponse",
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "/api/dc/site/{site_id}": {
                "get": {
                    "operationId": "getDCSiteDetail",
                    "summary": "Obtenir la fiche complète d'un site",
                    "description": "Retourne toutes les informations détaillées d'un site: grid, connectivité, timeline, urbanisme, scoring.",
                    "parameters": [
                        {
                            "name": "site_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Identifiant unique du site (ex: dc_htb_hdf_001)",
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Fiche site complète",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/SiteDetail",
                                    },
                                },
                            },
                        },
                        "404": {"description": "Site non trouvé"},
                    },
                },
            },
            "/api/s3renr/summary": {
                "get": {
                    "operationId": "getS3REnRSummary",
                    "summary": "Résumé des capacités réseau S3REnR par région",
                    "description": "Vue d'ensemble des capacités électriques disponibles par région (IDF, PACA, HdF). Données issues du S3REnR (RTE).",
                    "responses": {
                        "200": {
                            "description": "Résumé par région",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "summary": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "region": {"type": "string"},
                                                        "status_global": {"type": "string"},
                                                        "capacite_globale_mw": {"type": "number"},
                                                        "mw_dispo_total": {"type": "number"},
                                                        "nb_postes": {"type": "integer"},
                                                        "nb_disponibles": {"type": "integer"},
                                                        "nb_contraints": {"type": "integer"},
                                                        "nb_satures": {"type": "integer"},
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            },
            "/api/s3renr/top-opportunities": {
                "get": {
                    "operationId": "getTopOpportunities",
                    "summary": "Top opportunités de raccordement pour data centers",
                    "description": "Liste des postes avec le plus de MW disponibles, triés par capacité décroissante.",
                    "parameters": [
                        {
                            "name": "min_mw",
                            "in": "query",
                            "schema": {"type": "integer", "default": 30},
                            "description": "MW minimum pour filtrer les résultats",
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 20},
                            "description": "Nombre max de résultats",
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "Liste des meilleures opportunités",
                        },
                    },
                },
            },
        },
        "components": {
            "schemas": {
                "SearchResponse": {
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/SiteResult"},
                        },
                        "meta": {
                            "type": "object",
                            "properties": {
                                "total_results": {"type": "integer"},
                                "page": {"type": "integer"},
                                "per_page": {"type": "integer"},
                                "total_pages": {"type": "integer"},
                                "search_time_ms": {"type": "integer"},
                                "strategy": {"type": "string"},
                                "region_filter": {"type": "string", "nullable": True},
                            },
                        },
                    },
                },
                "SiteResult": {
                    "type": "object",
                    "properties": {
                        "site_id": {"type": "string"},
                        "name": {"type": "string"},
                        "location": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string"},
                                "region": {"type": "string"},
                                "lat": {"type": "number"},
                                "lng": {"type": "number"},
                            },
                        },
                        "land": {
                            "type": "object",
                            "properties": {
                                "surface_ha": {"type": "number"},
                                "price_per_m2": {"type": "number"},
                                "type": {"type": "string", "enum": ["greenfield", "brownfield"]},
                            },
                        },
                        "grid": {
                            "type": "object",
                            "properties": {
                                "distance_to_substation_km": {"type": "number"},
                                "voltage_level": {"type": "string"},
                                "estimated_capacity_mw": {"type": "number"},
                                "available_capacity_mw": {"type": "number"},
                                "saturation_level": {"type": "string", "enum": ["low", "medium", "high"]},
                                "reinforcement_planned": {"type": "boolean"},
                            },
                        },
                        "timeline": {
                            "type": "object",
                            "properties": {
                                "estimated_connection_delay_months": {"type": "integer"},
                                "permitting_risk": {"type": "string", "enum": ["low", "medium", "high"]},
                            },
                        },
                        "urbanism": {
                            "type": "object",
                            "properties": {
                                "plu_zone": {"type": "string"},
                                "data_center_compatible": {"type": "boolean"},
                            },
                        },
                        "score": {
                            "type": "object",
                            "properties": {
                                "global": {"type": "number", "description": "Score global 0-100"},
                                "power": {"type": "number", "description": "Score puissance 0-100"},
                                "speed": {"type": "number", "description": "Score rapidité 0-100"},
                                "cost": {"type": "number", "description": "Score coût 0-100"},
                                "risk": {"type": "number", "description": "Score risque 0-100 (plus haut = moins risqué)"},
                            },
                        },
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "comment": {"type": "string", "description": "Commentaire synthétique pour interprétation IA"},
                    },
                },
                "SiteDetail": {
                    "type": "object",
                    "description": "Fiche site complète avec données de connectivité et S3REnR",
                    "properties": {
                        "site_id": {"type": "string"},
                        "name": {"type": "string"},
                        "location": {"type": "object"},
                        "land": {"type": "object"},
                        "grid": {
                            "type": "object",
                            "properties": {
                                "distance_to_substation_km": {"type": "number"},
                                "voltage_level": {"type": "string"},
                                "estimated_capacity_mw": {"type": "number"},
                                "available_capacity_mw": {"type": "number"},
                                "saturation_level": {"type": "string"},
                                "reinforcement_planned": {"type": "boolean"},
                                "reinforcement_detail": {"type": "string", "nullable": True},
                                "etat_s3renr": {"type": "string"},
                            },
                        },
                        "timeline": {"type": "object"},
                        "urbanism": {"type": "object"},
                        "connectivity": {
                            "type": "object",
                            "properties": {
                                "nearest_landing_point_km": {"type": "number"},
                                "nearest_landing_point": {"type": "string"},
                                "nearest_dc_km": {"type": "number"},
                            },
                        },
                        "score": {"type": "object"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "comment": {"type": "string"},
                    },
                },
            },
        },
    }
