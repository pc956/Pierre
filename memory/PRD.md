# Cockpit Immo - PRD

## Énoncé du problème
Plateforme de prospection foncière pour data centers en France. Backend FastAPI/MongoDB + Frontend React/Leaflet thème sombre.

## Architecture technique
- **Backend**: FastAPI + MongoDB
- **Frontend**: React + TailwindCSS + React-Leaflet
- **Auth**: Google OAuth via Emergent Auth
- **LLM**: GPT-4.1-mini via Emergent LLM Key
- **APIs externes**: IGN Carto (cadastre), GPU (urbanisme/PLU/prescriptions)
- **PDF**: ReportLab

## Fonctionnalités implémentées

### Phase 1-4 — MVP
- [x] Carte + postes HTB + lignes + landing points + DC existants
- [x] S3REnR + Mobile responsive + PLU réel via API GPU
- [x] API DC Search + GPT Agent + Chatbot IA + DVF + PDF Export

### Phase 5 — Future ligne 400kV Fos → Jonquières
- [x] Tracé + buffers + scoring + couche toggleable

### Phase 6-7 — Chatbot parcelles exactes + Filtres avancés + Optim N+1
- [x] Recherche parcelles cadastrales réelles via IGN API
- [x] Filtres : PLU, surface, HTB, tension, 400kV

### Phase 8 — Scoring PLU statique DC
- [x] Score 0-100 par zone : UI=90, AU=72, mixte=55, résidentiel=15, N/A=0
- [x] Ajustements : +brownfield, +ZAC, -patrimoine, -risque, -habitat
- [x] Parser mots-clés règlement PLU

### Phase 9 — Scoring PLU DYNAMIQUE via API GPU (29/03/2026)
- [x] `get_gpu_full_context()` : fetch parallèle zone-urba + prescription-surf + info-surf
- [x] Analyse des prescriptions : EBC (-15), patrimoine (-12), limitation constructibilité (-8)
- [x] Analyse des informations : PPRT/PPR (-10), ZAC (+8), archéologie (-5)
- [x] Analyse destination dominante : keywords industriels (+8/+4), résidentiels (-10/-5), naturels (-15)
- [x] Endpoint `GET /api/scoring/plu-dynamic?lon=X&lat=Y`
- [x] Intégré dans chatbot (scoring dynamique par parcelle)
- [x] Frontend : badge "GPU Dynamique", prescriptions/infos count, risk labels
- [x] Rétrocompatibilité scoring statique (`GET /api/scoring/plu/{zone}`)

## Endpoints API
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/scoring/plu-dynamic` | GET | Score PLU dynamique GPU (lon, lat) |
| `/api/scoring/plu/{zone}` | GET | Score PLU statique par zone |
| `/api/scoring/plu` | POST | Score PLU avec ajustements |
| `/api/chat` | POST | Chatbot IA (parcelles + scoring dynamique) |
| `/api/map/rte-future-400kv` | GET | Future ligne 400kV |
| `/api/dc/search` | POST | Recherche sites DC |
| `/api/export/pdf/{id}` | GET | Export PDF |

## Backlog
- [ ] **P1**: Couches risques environnementaux (inondations, sismique)
- [ ] **P2**: Comparaison côte-à-côte de sites
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques

## Fichiers de référence
- `/app/backend/plu_scoring.py` — Scoring PLU statique + dynamique
- `/app/backend/api_carto.py` — API Carto IGN + GPU full context
- `/app/backend/chat_assistant.py` — Chatbot IA + find_parcels dynamique
- `/app/backend/rte_future_line.py` — Future ligne 400kV
- `/app/backend/server.py` — Routes API
- `/app/backend/dc_search_api.py` — Recherche DC
- `/app/frontend/src/pages/Dashboard.js` — Carte + PLU scoring dynamique
- `/app/frontend/src/components/ChatBot.js` — UI chatbot
