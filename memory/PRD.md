# Cockpit Immo - PRD (Product Requirements Document)

## Date: 2026-03-28

## Original Problem Statement
Plateforme de prospection foncière pour data centers en France - "Cockpit Immo"
- MVP complet avec Google OAuth, scoring engine, carte interactive
- Dark mode exclusif (Bloomberg terminal aesthetic)
- API pour agents IA conversationnels

## What's Been Implemented

### Phase 1 - MVP
- Backend FastAPI avec MongoDB
- Scoring engine complet (6 critères + malus + urbanisme + raccordement)
- Frontend React avec Leaflet dark mode
- Google OAuth via Emergent Auth
- Filtres avancés (distance RTE, distance landing, surface, PLU)

### Phase 2 - Données Nationales France
- 101 postes HTB + 17 lignes 400kV + 32 lignes 225kV
- 61 DC existants, 15 câbles sous-marins, 8 landing points
- Chargement dynamique des parcelles par BBox (API Carto IGN)
- Recherche de communes avec flyTo automatique

### Phase 3 - Intégration S3REnR
- Données S3REnR: IDF (10 postes, SATURÉ), PACA (76 postes, ACTIF), HdF (66 postes, ACTIF)
- Enrichissement postes HTB avec MW dispo, état, renforcements, score DC
- Panneau régional S3REnR dans la sidebar + légende

### Phase 4 - Responsive Mobile + PLU Réel GPU
- App fonctionne sur téléphone (carte plein écran, navigation mobile, bottom sheets)
- PLU réel via GPU API (U/AU/A/N avec libellé)

### Phase 5 - DC Search API pour Agents IA (2026-03-28)
**POST /api/dc/search** — Recherche principale
- Input: mw_target, mw_min, max_delay_months, surface_min_ha, region, strategy, grid_priority, brownfield_only, pagination
- Output: sites scorés/triés avec score (global/power/speed/cost/risk), tags, comment AI
- 101 sites générés à partir des postes HTB + enrichissement S3REnR
- Scoring dynamique avec 4 stratégies: speed, cost, power, balanced
- Aliases régions (IDF, ile-de-france, paris, PACA, provence, etc.)
- Pagination (page, per_page, total_pages)

**GET /api/dc/site/:id** — Fiche site complète
- Données grid détaillées (S3REnR, renforcement, délais)
- Connectivité (distance landing point, DC existant le plus proche)
- Score multi-critères

**Logique métier:**
- Bonus: renforcement S3REnR prévu, proximité 225kV/400kV
- Malus: saturation réseau, délai > objectif
- IDF correctement marqué SATURÉ (score power ~0)
- Calais (28MW) et Valenciennes (65MW) avec données S3REnR réelles
- Testing: 26/26 tests passés

## Architecture
```
Frontend (React 18 + Tailwind + Leaflet) -> REST API -> Backend (FastAPI)
                                                        |
                                                MongoDB + API Carto IGN + GPU API
                                                + france_infra_data.py (101 postes HTB)
                                                + s3renr_data.py (152 postes S3REnR)
                                                + dc_search_api.py (AI search engine)
```

## Key API Endpoints
- `POST /api/dc/search` — AI Agent DC search
- `GET /api/dc/site/:id` — AI Agent site detail
- `GET /api/map/electrical-assets` — Postes HTB enrichis S3REnR
- `GET /api/s3renr/summary` — Résumé S3REnR par région
- `GET /api/france/parcelles/bbox` — Parcelles par BBox + PLU GPU

## Prioritized Backlog

### P0 - Core (Done)
- [x] Scoring engine + carte interactive + Google OAuth
- [x] Données nationales France + S3REnR
- [x] Responsive mobile + PLU réel GPU
- [x] DC Search API pour agents IA

### P1 - Next Sprint
- [ ] CRM Kanban drag & drop
- [ ] API DVF (prix transactions réels)
- [ ] Export PDF fiches sites

### P2 - Future
- [ ] Couches risques environnementaux
- [ ] Comparaison côte-à-côte
- [ ] Mode COMEX
- [ ] Alertes automatiques
