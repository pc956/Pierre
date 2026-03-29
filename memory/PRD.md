# Cockpit Immo - PRD (Product Requirements Document)

## Énoncé du problème
Plateforme complète de prospection foncière pour data centers en France ("Cockpit Immo"). Backend FastAPI/MongoDB + Frontend React avec carte Leaflet thème sombre. Intégration réseau S3REnR, scoring multi-critères, données PLU réelles, API de recherche pour agents IA, chatbot LLM intégré, prix DVF, exports PDF.

## Architecture technique
- **Backend**: FastAPI + MongoDB (`/app/backend/`)
- **Frontend**: React + TailwindCSS + React-Leaflet (`/app/frontend/`)
- **Auth**: Google OAuth via Emergent Auth
- **LLM**: OpenAI GPT-4.1-mini via Emergent LLM Key
- **APIs externes**: IGN Carto (cadastre), GPU (urbanisme/PLU)
- **PDF**: ReportLab

## Fonctionnalités implémentées

### Phase 1-4 — MVP complet
- [x] Carte Leaflet (fond sombre) avec postes HTB, lignes, landing points, DC existants
- [x] S3REnR capacités/saturation par région
- [x] Mobile responsive (bottom sheets)
- [x] PLU réel via API GPU
- [x] API DC Search + GPT Agent + Chatbot IA
- [x] DVF + Export PDF

### Phase 5 — Future ligne 400kV Fos → Jonquières (29/03/2026)
- [x] Tracé approximatif + buffers 1km/3km/5km + scoring + couche toggleable

### Phase 6 — Chatbot proposant des parcelles exactes (29/03/2026)
- [x] Action `find_parcels` : recherche de parcelles cadastrales réelles via IGN API
- [x] Parcelles enrichies : ref cadastrale, surface, distance HTB, PLU, DVF, score, 400kV
- [x] UI : cartes de parcelles cliquables → navigation carte + sélection

### Phase 7 — Filtres avancés IA + Optimisations DB (29/03/2026)
- [x] Filtre PLU zone (U, AU, UI, AUx, etc.)
- [x] Filtre surface min/max en hectares
- [x] Filtre distance max au poste HTB (km)
- [x] Filtre tension HTB minimum (225kV, 400kV)
- [x] Filtre distance max à la future ligne 400kV (km)
- [x] Badges de filtres actifs dans l'UI chatbot
- [x] Optimisation N+1 : parcels batch $in query pour scores
- [x] Optimisation N+1 : shortlists aggregation pipeline pour item counts
- [x] Optimisation N+1 : shortlist detail batch fetch parcels + scores

## Endpoints API clés
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/chat` | POST | Chatbot IA (parcelles exactes avec filtres avancés) |
| `/api/map/rte-future-400kv` | GET | Future ligne 400kV + buffers |
| `/api/dc/search` | POST | Recherche sites DC multi-critères |
| `/api/export/pdf/{id}` | GET | Export fiche PDF |
| `/api/france/parcelles/bbox` | GET | Parcelles par bbox |
| `/api/shortlists` | GET | Shortlists (optimisé) |

## Backlog
- [ ] **P1**: Couches risques environnementaux (inondations, sismique)
- [ ] **P2**: Comparaison côte-à-côte de sites
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques

## Fichiers de référence
- `/app/backend/chat_assistant.py` — Chatbot LLM + find_parcels + filtres avancés
- `/app/backend/rte_future_line.py` — Future ligne 400kV
- `/app/backend/server.py` — Routes API (optimisées N+1)
- `/app/backend/dc_search_api.py` — Moteur de recherche DC
- `/app/frontend/src/components/ChatBot.js` — UI chatbot + parcelles + badges filtres
- `/app/frontend/src/pages/Dashboard.js` — Carte + sidebar
