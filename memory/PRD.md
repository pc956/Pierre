# Cockpit Immo - PRD

## Énoncé du problème
Plateforme de prospection foncière pour data centers en France. Backend FastAPI/MongoDB + Frontend React/Leaflet thème sombre.

## Architecture technique
- **Backend**: FastAPI + MongoDB
- **Frontend**: React + TailwindCSS + React-Leaflet
- **Auth**: Google OAuth via Emergent Auth
- **LLM**: GPT-4.1-mini via Emergent LLM Key
- **APIs externes**: IGN Carto (cadastre), GPU (urbanisme/PLU/prescriptions/infos)

## Fonctionnalités implémentées

### Phase 1-4 — MVP
- [x] Carte + infra + S3REnR + mobile + PLU + API DC + chatbot + DVF + PDF

### Phase 5 — Future ligne 400kV
- [x] Tracé + buffers + scoring + couche toggleable

### Phase 6-7 — Chatbot parcelles + Filtres + Optim N+1
- [x] Recherche parcelles cadastrales réelles + filtres avancés
- [x] Auto-expansion rayon de recherche selon critères (HTB distance, surface min)

### Phase 8-10 — Scoring PLU complet
- [x] Statique (code zone) + Dynamique GPU (prescriptions + infos + destination)
- [x] Indicateur de confiance (haute/moyenne/basse)
- [x] Composite : dynamique prioritaire → fallback statique

## Endpoints API
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/scoring/plu-dynamic` | GET | Score PLU dynamique GPU |
| `/api/scoring/plu/{zone}` | GET | Score PLU statique |
| `/api/scoring/plu` | POST | Score PLU avec ajustements |
| `/api/chat` | POST | Chatbot IA (parcelles + scoring dynamique) |
| `/api/dc/search` | POST | Recherche DC |
| `/api/map/rte-future-400kv` | GET | Future 400kV |
| `/api/export/pdf/{id}` | GET | Export PDF |

## Backlog
- [ ] **P1**: Couches risques environnementaux (inondations, sismique)
- [ ] **P2**: Comparaison côte-à-côte de sites
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques
