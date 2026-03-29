# Cockpit Immo - PRD (Product Requirements Document)

## Énoncé du problème
Plateforme complète de prospection foncière pour data centers en France ("Cockpit Immo"). Backend FastAPI/MongoDB + Frontend React avec carte Leaflet thème sombre. Intégration réseau S3REnR, scoring multi-critères, données PLU réelles, API de recherche pour agents IA, chatbot LLM intégré, prix DVF, exports PDF.

## Architecture technique
- **Backend**: FastAPI + MongoDB (`/app/backend/`)
- **Frontend**: React + TailwindCSS + React-Leaflet (`/app/frontend/`)
- **Auth**: Google OAuth via Emergent Auth
- **LLM**: OpenAI GPT-4o-mini via Emergent LLM Key
- **APIs externes**: IGN Carto (cadastre), GPU (urbanisme/PLU)
- **PDF**: ReportLab

## Fonctionnalités implémentées

### Phase 1 — Infrastructure de base
- [x] Carte Leaflet avec fond sombre (OpenStreetMap dark)
- [x] Postes HTB (400kV, 225kV, 63kV) sur toute la France
- [x] Lignes HTB 400kV et 225kV
- [x] Landing points et câbles sous-marins
- [x] Data centers existants
- [x] Système de scoring multi-critères

### Phase 2 — Données réseau S3REnR
- [x] Capacités et saturation S3REnR par région (IDF, PACA, HdF, AuRA)
- [x] Indicateurs visuels : Disponible / Contraint / Saturé
- [x] Résumé S3REnR dans la sidebar

### Phase 3 — Mobile responsive
- [x] Carte plein écran sur mobile
- [x] Navigation mobile (bottom bar)
- [x] Bottom sheet pour filtres et couches
- [x] Sidebar responsive

### Phase 4 — PLU réel
- [x] API GPU (Géoportail de l'Urbanisme) pour zonage PLU
- [x] Parcelles cadastrales via API Carto IGN

### Phase 5 — API pour agents IA
- [x] `POST /api/dc/search` — endpoint de recherche multi-critères
- [x] `GET /api/gpt/openapi-schema` — schéma pour intégration GPT
- [x] Page de configuration GPT Agent

### Phase 6 — Chatbot IA intégré
- [x] `POST /api/chat` — traitement de messages
- [x] Chatbot UI avec parsing de régions et navigation carte
- [x] Utilisation de l'Emergent LLM Key (GPT-4o-mini)

### Phase 7 — CRM supprimé
- [x] Module CRM entièrement supprimé (demande utilisateur)

### Phase 8 — DVF et Export PDF
- [x] Données DVF par département (fallback statique — API publique instable)
- [x] Export PDF fiche parcelle/site avec ReportLab
- [x] `GET /api/export/pdf/{parcel_id}` endpoint

### Phase 9 — Future ligne RTE 400kV Fos → Jonquières (29/03/2026)
- [x] Tracé approximatif (13 points) de Feuillane → Jonquières
- [x] Buffers géospatiaux : 1km (zone chaude), 3km (zone stratégique), 5km (zone opportunité)
- [x] `GET /api/map/rte-future-400kv` endpoint GeoJSON
- [x] Scoring : +30pts (<1km), +20pts (<3km), +10pts (<5km)
- [x] Indicateur composite `future_grid_potential_score` (0-100)
- [x] Couche toggleable sur la carte (ligne rouge + buffers colorés)
- [x] Popup au clic avec infos projet (~2029)
- [x] Section "Future ligne 400kV" dans ParcelDetail (distance, zone, bonus, potentiel)
- [x] Enrichissement API DC Search (`future_400kv` dans chaque résultat)
- [x] Section future 400kV dans l'export PDF

## Endpoints API clés
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/map/rte-future-400kv` | GET | Future ligne 400kV + buffers GeoJSON |
| `/api/dc/search` | POST | Recherche sites DC multi-critères |
| `/api/chat` | POST | Chatbot IA |
| `/api/export/pdf/{id}` | GET | Export fiche PDF |
| `/api/gpt/openapi-schema` | GET | Schéma GPT Agent |
| `/api/france/parcelles/bbox` | GET | Parcelles par bbox |
| `/api/map/electrical-assets` | GET | Actifs électriques |

## Backlog
- [ ] **P1**: Couches risques environnementaux (inondations, sismique)
- [ ] **P2**: Comparaison côte-à-côte de sites
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques

## Fichiers de référence
- `/app/backend/rte_future_line.py` — Données future ligne 400kV + buffers + scoring
- `/app/backend/server.py` — Routes API principales
- `/app/backend/dc_search_api.py` — Moteur de recherche DC pour agents IA
- `/app/backend/pdf_export.py` — Génération PDF
- `/app/backend/chat_assistant.py` — Chatbot LLM
- `/app/backend/scoring.py` — Moteur de scoring
- `/app/backend/france_infra_data.py` — Données infrastructure France
- `/app/backend/dvf_data.py` — Données DVF statiques
- `/app/frontend/src/pages/Dashboard.js` — Composant principal carte + sidebar
- `/app/frontend/src/components/ChatBot.js` — UI chatbot
- `/app/frontend/src/pages/GPTAgent.js` — Configuration agent GPT
