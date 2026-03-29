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

### Phase 1 — Infrastructure de base
- [x] Carte Leaflet avec fond sombre
- [x] Postes HTB (400kV, 225kV, 63kV) sur toute la France
- [x] Lignes HTB, Landing points, câbles sous-marins, DC existants
- [x] Système de scoring multi-critères

### Phase 2 — S3REnR + Mobile + PLU
- [x] Capacités et saturation S3REnR par région
- [x] Mobile responsive (carte plein écran, bottom sheets)
- [x] PLU réel via API GPU

### Phase 3 — API Search + GPT Agent + Chatbot
- [x] `POST /api/dc/search` — recherche multi-critères pour agents IA
- [x] Page configuration GPT Agent
- [x] Chatbot IA intégré (Emergent LLM Key)

### Phase 4 — DVF + PDF Export
- [x] Données DVF par département
- [x] Export PDF fiche parcelle/site

### Phase 5 — Future ligne 400kV Fos → Jonquières (29/03/2026)
- [x] Tracé approximatif + buffers 1km/3km/5km
- [x] Scoring : +30pts (<1km), +20pts (<3km), +10pts (<5km)
- [x] Indicateur composite `future_grid_potential_score`
- [x] Couche toggleable + popup + fiche parcelle + export PDF

### Phase 6 — Chatbot proposant des parcelles exactes (29/03/2026)
- [x] Action `find_parcels` : recherche de parcelles cadastrales réelles via IGN API
- [x] Critères : région, MW cible, surface min, distance HTB max, zones PLU, stratégie
- [x] Parcelles enrichies : ref cadastrale, surface, distance HTB, PLU, DVF, score, 400kV
- [x] UI : cartes de parcelles cliquables → navigation carte + sélection
- [x] Quick actions mises à jour ("Trouve des parcelles 30MW PACA", etc.)
- [x] Actions macro (search/summary/site_detail) toujours fonctionnelles

## Endpoints API clés
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/chat` | POST | Chatbot IA (parcelles, sites, résumé) |
| `/api/map/rte-future-400kv` | GET | Future ligne 400kV + buffers |
| `/api/dc/search` | POST | Recherche sites DC multi-critères |
| `/api/export/pdf/{id}` | GET | Export fiche PDF |
| `/api/france/parcelles/bbox` | GET | Parcelles par bbox |
| `/api/map/electrical-assets` | GET | Actifs électriques |

## Backlog
- [ ] **P1**: Couches risques environnementaux (inondations, sismique)
- [ ] **P2**: Comparaison côte-à-côte de sites
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques

## Fichiers de référence
- `/app/backend/chat_assistant.py` — Chatbot LLM + find_parcels
- `/app/backend/rte_future_line.py` — Future ligne 400kV
- `/app/backend/server.py` — Routes API principales
- `/app/backend/dc_search_api.py` — Moteur de recherche DC
- `/app/backend/pdf_export.py` — Génération PDF
- `/app/backend/scoring.py` — Moteur de scoring
- `/app/frontend/src/components/ChatBot.js` — UI chatbot + parcelles
- `/app/frontend/src/pages/Dashboard.js` — Composant principal carte + sidebar
