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
- Chargement dynamique des parcelles par BBox (API Carto IGN) au zoom ≥ 14
- Recherche de communes avec flyTo automatique
- Calcul distances réelles via haversine

### Bug Fix - Parcelles Cliquables (2026-03-28)
- Root cause 1: parcel_id dupliqué (fr_) → corrigé avec idu de l'API Carto
- Root cause 2: Filtres de distance trop restrictifs → augmentés à 100km/1000km
- Root cause 3: CircleMarker → LeafletPolygon avec contours cyan visibles
- Ajout FlyToParcels component pour recentrage automatique

## Architecture
```
Frontend (React 18 + Tailwind + Leaflet) → REST API → Backend (FastAPI)
                                                        ↓
                                                MongoDB + API Carto IGN
                                                + france_infra_data.py (in-memory)
```

## Prioritized Backlog

### P0 - Core (Done)
- [x] Scoring engine
- [x] Carte interactive avec polygones cadastraux cliquables
- [x] Google OAuth
- [x] Données nationales France
- [x] Lignes 400kV et 225kV

### P1 - Next Sprint
- [ ] CRM Kanban drag & drop
- [ ] API DVF (prix transactions réels)
- [ ] Export PDF fiches sites

### P2 - Future
- [ ] Couches risques environnementaux (inondation, sismique)
- [ ] Comparaison côte-à-côte (4 parcelles)
- [ ] Mode COMEX
- [ ] Alertes automatiques
