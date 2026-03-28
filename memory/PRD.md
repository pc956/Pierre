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
- ✅ Backend FastAPI avec MongoDB
  - Models: User, Parcel, ParcelScore, Shortlist, Alert, DCExistant, LandingPoint
  - Scoring engine complet (6 critères + malus + urbanisme + raccordement)
  - 60 parcelles seed (IDF, PACA, AuRA, HdF, Occitanie)
  - API REST complète (parcels, search, map, shortlists, alerts, admin)
  
- ✅ Frontend React avec Leaflet
  - Page de connexion Google OAuth (Emergent Auth)
  - Dashboard avec carte interactive (dark mode CartoDB)
  - Vue tableau des parcelles
  - Panneau détail parcelle (scores, urbanisme, raccordement, économique)
  - Vue CRM basique
  - Filtres: type projet, région, score minimum

- ✅ Authentification Google OAuth via Emergent Auth
  - Session token avec cookie httpOnly
  - Multi-tenant support

## Architecture
```
Frontend (React 18 + Tailwind + Leaflet)
    ↓ REST API + JWT Cookie
Backend (FastAPI + Python 3.11)
    ↓
MongoDB (parcels, scores, users, shortlists, alerts)
```

## Tech Stack
- Frontend: React 18, Tailwind CSS, Leaflet.js, React Router
- Backend: FastAPI, Motor (async MongoDB), Pydantic v2
- Database: MongoDB with GeoJSON support
- Auth: Emergent Google OAuth

## Prioritized Backlog

### P0 - Core (Done)
- [x] Scoring engine
- [x] Carte interactive
- [x] Google OAuth
- [x] Data seed

### P1 - Next Sprint
- [ ] Export PDF fiches sites
- [ ] Comparaison côte-à-côte (jusqu'à 4 parcelles)
- [ ] Alertes et veille (changement proprio, DVF, etc.)
- [ ] Overrides manuels avec historique

### P2 - Future
- [ ] Pipeline d'ingestion données réelles (IGN, Enedis, RTE, Géorisques)
- [ ] Intégration Caparéseau pour capacité réseau
- [ ] Calcul consolidation parcelles adjacentes
- [ ] Mode COMEX (export PDF 3 pages)
- [ ] Multi-user avec rôles (admin, consultant, client_readonly)

## Next Tasks
1. Ajouter export PDF des fiches sites
2. Implémenter la vue comparaison
3. Intégrer les alertes automatiques
4. Améliorer le CRM Kanban avec drag & drop
