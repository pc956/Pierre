# Cockpit Immo - PRD (Product Requirements Document)

## Énoncé du problème
Plateforme complète de prospection foncière pour data centers en France ("Cockpit Immo"). Backend FastAPI/MongoDB + Frontend React avec carte Leaflet thème sombre.

## Architecture technique
- **Backend**: FastAPI + MongoDB (`/app/backend/`)
- **Frontend**: React + TailwindCSS + React-Leaflet (`/app/frontend/`)
- **Auth**: Google OAuth via Emergent Auth
- **LLM**: OpenAI GPT-4.1-mini via Emergent LLM Key
- **APIs externes**: IGN Carto (cadastre), GPU (urbanisme/PLU)
- **PDF**: ReportLab

## Fonctionnalités implémentées

### Phase 1-4 — MVP complet
- [x] Carte Leaflet avec postes HTB, lignes, landing points, DC existants
- [x] S3REnR capacités/saturation, Mobile responsive, PLU réel via API GPU
- [x] API DC Search + GPT Agent + Chatbot IA, DVF + Export PDF

### Phase 5 — Future ligne 400kV Fos → Jonquières
- [x] Tracé + buffers 1km/3km/5km + scoring + couche toggleable

### Phase 6-7 — Chatbot parcelles exactes + Filtres avancés
- [x] Recherche parcelles cadastrales réelles via IGN API
- [x] Filtres : PLU zone, surface min/max, distance HTB, tension kV, distance future 400kV
- [x] Optimisations N+1 (batch queries)

### Phase 8 — Scoring PLU automatique DC (29/03/2026)
- [x] Module `plu_scoring.py` : scoring 0-100 par zone PLU
- [x] Hard exclusions : N, NL, Nh, Nl, A, Ap, A0 → score=0 EXCLUDED
- [x] Scores de base : UI/UX/UY/UZ=90, AU/1AU/AUX=72, mixte=55, résidentiel=15
- [x] Ajustements : +10 brownfield, +8 ZAC, +7 équipement, -12 urba conditionnée, -10 habitat, -18 patrimoine, -20 risque majeur
- [x] Parser mots-clés règlement PLU (positifs/négatifs)
- [x] Statuts : FAVORABLE (85-100), WATCHLIST (65-84), CONDITIONAL (45-64), UNFAVORABLE (1-44), EXCLUDED (0)
- [x] Actions recommandées : prospect_now / check_regulation_and_mayor / manual_review / reject
- [x] Endpoints API : `GET /api/scoring/plu/{zone}`, `POST /api/scoring/plu`
- [x] Intégré dans : parcelles bbox, chatbot, DC search, export PDF
- [x] Frontend : barre de score, badge statut, risque, action, flags dans ParcelDetail
- [x] Chatbot : auto-exclusion des zones incompatibles + badge PLU score

## Endpoints API
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/scoring/plu/{zone}` | GET | Score PLU rapide par code zone |
| `/api/scoring/plu` | POST | Score PLU complet avec ajustements |
| `/api/chat` | POST | Chatbot IA (parcelles avec scoring PLU) |
| `/api/map/rte-future-400kv` | GET | Future ligne 400kV |
| `/api/dc/search` | POST | Recherche sites DC |
| `/api/export/pdf/{id}` | GET | Export PDF |

## Backlog
- [ ] **P1**: Couches risques environnementaux (inondations, sismique)
- [ ] **P2**: Comparaison côte-à-côte de sites
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques

## Fichiers de référence
- `/app/backend/plu_scoring.py` — Scoring PLU automatique DC
- `/app/backend/chat_assistant.py` — Chatbot IA + find_parcels
- `/app/backend/rte_future_line.py` — Future ligne 400kV
- `/app/backend/server.py` — Routes API principales
- `/app/backend/dc_search_api.py` — Moteur de recherche DC
- `/app/backend/pdf_export.py` — Génération PDF
- `/app/frontend/src/pages/Dashboard.js` — Carte + sidebar + PLU scoring
- `/app/frontend/src/components/ChatBot.js` — UI chatbot + parcelles
