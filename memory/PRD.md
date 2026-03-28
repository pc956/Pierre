# Cockpit Immo - PRD (Product Requirements Document)

## Date: 2026-03-28

## Original Problem Statement
Plateforme de prospection foncière pour data centers en France - "Cockpit Immo"
- MVP complet avec Google OAuth
- Priorité: Module de scoring
- Dark mode exclusif (Bloomberg terminal aesthetic)

## What's Been Implemented

### Phase 1 - MVP (2026-03-28)
- Backend FastAPI avec MongoDB
- Scoring engine complet (6 critères + malus + urbanisme + raccordement)
- Frontend React avec Leaflet dark mode
- Google OAuth via Emergent Auth
- Filtres avancés (distance RTE, distance landing, surface, PLU)
- Modal SIREN/Pappers info

### Phase 2 - Données Nationales France (2026-03-28)
- 101 postes HTB + 17 lignes 400kV + 32 lignes 225kV
- 61 DC existants, 15 câbles sous-marins, 8 landing points
- Chargement dynamique des parcelles par BBox (API Carto IGN) au zoom >= 14
- Recherche de communes avec flyTo automatique
- Calcul distances réelles via haversine

### Bug Fix - Parcelles Cliquables (2026-03-28)
- Root cause 1: parcel_id dupliqué (fr_) -> corrigé avec idu de l'API Carto
- Root cause 2: Filtres de distance trop restrictifs -> augmentés à 100km/1000km
- Root cause 3: CircleMarker -> LeafletPolygon avec contours cyan visibles
- Ajout FlyToParcels component pour recentrage automatique

### Phase 3 - Intégration S3REnR (2026-03-28)
- Données S3REnR pour 3 régions: IDF (10 postes, SATURÉ), PACA (76 postes, ACTIF), HdF (66 postes, ACTIF)
- Backend: enrichissement des postes HTB avec données S3REnR (MW dispo, état, renforcements, score DC)
- Backend: `/api/s3renr/summary` et `/api/s3renr/top-opportunities` endpoints
- Frontend: code couleur des postes HTB (vert=disponible, orange=contraint, rouge=saturé)
- Frontend: popups enrichis avec barre de progression MW, score DC, plan de renforcement
- Frontend: panneau régional S3REnR dans la sidebar (IDF SATURÉ, PACA 3258MW, HdF 2925MW)
- Frontend: légende mise à jour avec statuts S3REnR
- Labels MW sur la carte pour les postes avec correspondance directe (CALAIS 28MW, VALENCIENNES 65MW)
- Testing: 19/19 tests passés (backend + frontend)

## Architecture
```
Frontend (React 18 + Tailwind + Leaflet) -> REST API -> Backend (FastAPI)
                                                        |
                                                MongoDB + API Carto IGN
                                                + france_infra_data.py (in-memory)
                                                + s3renr_data.py (in-memory)
```

## Key API Endpoints
- `GET /api/map/electrical-assets` - Postes HTB enrichis S3REnR + lignes
- `GET /api/s3renr/summary` - Résumé par région (MW, postes, statuts)
- `GET /api/s3renr/top-opportunities` - Top opportunités DC par MW dispo
- `GET /api/carto/parcelles` - Parcelles par BBox
- `GET /api/france/communes` - Recherche communes

## Prioritized Backlog

### P0 - Core (Done)
- [x] Scoring engine
- [x] Carte interactive avec polygones cadastraux cliquables
- [x] Google OAuth
- [x] Données nationales France (101 postes, lignes, DC, câbles)
- [x] Lignes 400kV et 225kV
- [x] Intégration S3REnR (capacités MW, saturation, renforcements)

### P1 - Next Sprint
- [ ] CRM Kanban drag & drop
- [ ] API DVF (prix transactions réels)
- [ ] Export PDF fiches sites

### P2 - Future
- [ ] Couches risques environnementaux (inondation, sismique)
- [ ] Comparaison côte-à-côte (4 parcelles)
- [ ] Mode COMEX
- [ ] Alertes automatiques
