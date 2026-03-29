# Cockpit Immo - PRD

## Énoncé du problème
Plateforme de prospection foncière pour data centers en France. Backend FastAPI/MongoDB + Frontend React/Leaflet thème sombre.

## Architecture technique
- **Backend**: FastAPI + MongoDB
- **Frontend**: React + TailwindCSS + React-Leaflet
- **Auth**: Google OAuth via Emergent Auth
- **LLM**: GPT-4.1-mini via Emergent LLM Key
- **APIs externes**: IGN Carto (cadastre), GPU (urbanisme/PLU/prescriptions/infos)
- **PDF**: ReportLab

## Fonctionnalités implémentées

### Phase 1-4 — MVP complet
- [x] Carte + infra + S3REnR + mobile + PLU + API DC + chatbot + DVF + PDF

### Phase 5 — Future ligne 400kV
- [x] Tracé + buffers + scoring + couche toggleable

### Phase 6-7 — Chatbot parcelles + Filtres + Optim N+1
- [x] Recherche parcelles cadastrales réelles + filtres avancés

### Phase 8 — Scoring PLU statique DC
- [x] Score 0-100 par zone + ajustements + parser mots-clés

### Phase 9 — Scoring PLU dynamique GPU
- [x] Fetch parallèle zone-urba + prescription-surf + info-surf
- [x] Analyse prescriptions (EBC, patrimoine), informations (PPRT, ZAC), destination dominante

### Phase 10 — Score PLU composite + Indicateur de confiance (29/03/2026)
- [x] Composite : dynamique GPU (priorité) → fallback statique
- [x] Confidence levels : haute (GPU + prescriptions/infos), moyenne (statique + règlement), basse (code seul)
- [x] confidence_detail expliquant les sources utilisées
- [x] Frontend : indicateur 3 points colorés (vert=haute, orange=moyenne, rouge=basse)
- [x] Intégré dans bbox parcelles, chatbot, fiche parcelle

## Endpoints API
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/scoring/plu-dynamic` | GET | Score PLU dynamique GPU (lon, lat) |
| `/api/scoring/plu/{zone}` | GET | Score PLU statique |
| `/api/scoring/plu` | POST | Score PLU avec ajustements |
| `/api/chat` | POST | Chatbot IA |
| `/api/dc/search` | POST | Recherche DC |
| `/api/map/rte-future-400kv` | GET | Future 400kV |
| `/api/export/pdf/{id}` | GET | Export PDF |

## Backlog
- [ ] **P1**: Couches risques environnementaux (inondations, sismique)
- [ ] **P2**: Comparaison côte-à-côte de sites
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques
