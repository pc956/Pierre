# Cockpit Immo - PRD (Product Requirements Document)

## Date: 2026-03-28

## Original Problem Statement
Plateforme de prospection foncière pour data centers en France - "Cockpit Immo"
- MVP complet avec Google OAuth
- Priorité: Module de scoring
- Dark mode exclusif (Bloomberg terminal aesthetic)

## User Personas
1. **Consultant DC** - Recherche les meilleures parcelles pour ses clients
2. **Investisseur** - Analyse la rentabilité et les risques
3. **Opérateur DC** - Évalue la faisabilité technique et urbanistique

## Core Requirements (Static)
- Carte interactive avec parcelles scorées
- Module de scoring multi-critères (6 critères: électricité, fibre, eau, surface, marché, climat)
- Faisabilité urbanistique (PLU, ICPE, ZAN, DFI)
- Estimation raccordement électrique (délai, coût, proba MW)
- Analyse économique (CAPEX, IRR, P&L)
- CRM/Pipeline Kanban
- Multi-tenant avec Google OAuth

## What's Been Implemented

### Phase 1 - MVP (2026-03-28)
- Backend FastAPI avec MongoDB
  - Models: User, Parcel, ParcelScore, Shortlist, Alert, DCExistant, LandingPoint
  - Scoring engine complet (6 critères + malus + urbanisme + raccordement)
  - API REST complète (parcels, search, map, shortlists, alerts, admin)
  
- Frontend React avec Leaflet
  - Page de connexion Google OAuth (Emergent Auth)
  - Dashboard avec carte interactive (dark mode CartoDB)
  - Vue tableau des parcelles
  - Panneau détail parcelle (scores, urbanisme, raccordement, économique)
  - Vue CRM basique
  - Filtres avancés (distance RTE, distance landing, surface, PLU)

- Authentification Google OAuth via Emergent Auth

### Phase 2 - Données Nationales France (2026-03-28)
- 101 postes HTB (toutes régions métropolitaines) - données in-memory
- 61 DC existants (Equinix, Digital Realty, OVH, DATA4, Scaleway, etc.)
- 15 câbles sous-marins (SEA-ME-WE, 2Africa, Dunant, Amitié, etc.)
- 8 landing points (Marseille, Saint-Hilaire, Le Porge, Calais, Dunkerque, etc.)
- Chargement dynamique des parcelles par BBox (API Carto IGN) au zoom ≥ 14
- Recherche de communes avec chargement automatique des parcelles
- Calcul des distances réelles aux postes HTB et landing points via haversine
- Indicateur de zoom sur la carte

## Architecture
```
Frontend (React 18 + Tailwind + Leaflet)
    ↓ REST API + JWT Cookie
Backend (FastAPI + Python 3.11)
    ↓
MongoDB (parcels, scores, users, shortlists, alerts)
+ france_infra_data.py (infrastructure statique in-memory)
+ API Carto IGN (parcelles cadastrales en temps réel)
```

## Tech Stack
- Frontend: React 18, Tailwind CSS, Leaflet.js, React Router
- Backend: FastAPI, Motor (async MongoDB), Pydantic v2
- Database: MongoDB with GeoJSON support
- Auth: Emergent Google OAuth
- External APIs: API Carto IGN (free, no key), geo.api.gouv.fr

## Prioritized Backlog

### P0 - Core (Done)
- [x] Scoring engine
- [x] Carte interactive
- [x] Google OAuth
- [x] Données nationales France (infrastructure + parcelles dynamiques)

### P1 - Next Sprint
- [ ] CRM Kanban drag & drop
- [ ] Export PDF fiches sites
- [ ] Comparaison côte-à-côte (jusqu'à 4 parcelles)
- [ ] DVF (Demandes de Valeurs Foncières) - prix transactions réels

### P2 - Future
- [ ] Couches risques environnementaux (inondation, sismique)
- [ ] Intégration Caparéseau pour capacité réseau
- [ ] Calcul consolidation parcelles adjacentes
- [ ] Mode COMEX (export PDF 3 pages)
- [ ] Multi-user avec rôles (admin, consultant, client_readonly)
- [ ] Alertes automatiques

## Next Tasks
1. CRM Kanban avec drag & drop
2. Intégrer l'API DVF pour les prix de transactions
3. Couches risques environnementaux
4. Export PDF des fiches sites
