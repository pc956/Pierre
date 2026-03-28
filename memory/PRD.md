# Cockpit Immo - PRD (Product Requirements Document)

## Date: 2026-03-28

## Original Problem Statement
Plateforme de prospection foncière pour data centers en France - "Cockpit Immo"

## What's Been Implemented

### Phase 1 - MVP
- Backend FastAPI + MongoDB + Scoring engine (6 critères)
- Frontend React + Leaflet dark mode + Google OAuth
- Filtres avancés (distance RTE, landing, surface, PLU)

### Phase 2 - Données Nationales France
- 101 postes HTB + lignes 400kV/225kV + 61 DC + 15 câbles + 8 landing points
- Parcelles dynamiques BBox via API Carto IGN

### Phase 3 - Intégration S3REnR
- IDF (SATURÉ), PACA (ACTIF 3258MW), HdF (ACTIF 2925MW)
- Enrichissement postes HTB + popups + panneau sidebar

### Phase 4 - Responsive Mobile + PLU Réel GPU
- App mobile (carte plein écran, nav bas, bottom sheets)
- PLU réel (U/AU/A/N) via API GPU IGN

### Phase 5 - DC Search API pour Agents IA
- POST /api/dc/search — 101 sites scorés, 4 stratégies, pagination
- GET /api/dc/site/:id — Fiche complète
- Testing: 26/26 tests passés

### Phase 6 - Agent GPT Custom (2026-03-28)
- Page /gpt-agent avec instructions de configuration en 6 étapes
- System prompt expert prospection DC (2962 chars) — copie en 1 clic
- Schema OpenAPI 3.1.0 avec 4 endpoints documentés
- URL schema: /api/gpt/openapi-schema (HTTPS, accessible par ChatGPT)
- Test en direct: saisie langage naturel → résultats scorés en tableau
- Boutons exemples: "20MW IDF 12 mois", "50MW PACA puissance max", etc.
- Testing: 24/24 tests passés

## Architecture
```
Frontend (React 18 + Tailwind + Leaflet)
  └→ /gpt-agent (GPT config page)
  └→ /dashboard (Map + Sidebar + Filters)
Backend (FastAPI)
  └→ /api/dc/search (AI Agent)
  └→ /api/gpt/* (GPT config)
  └→ /api/map/* (Infrastructure)
  └→ /api/s3renr/* (Capacités réseau)
  └→ /api/france/* (Parcelles + GPU PLU)
Data: MongoDB + API Carto IGN + GPU API + in-memory (france_infra + s3renr)
```

## Prioritized Backlog

### P0 - Core (Done)
- [x] Scoring engine + carte interactive + Google OAuth
- [x] Données nationales France + S3REnR
- [x] Responsive mobile + PLU réel GPU
- [x] DC Search API + Agent GPT custom

### P1 - Next Sprint
- [ ] CRM Kanban drag & drop
- [ ] API DVF (prix transactions réels)
- [ ] Export PDF fiches sites

### P2 - Future
- [ ] Couches risques environnementaux
- [ ] Comparaison côte-à-côte
- [ ] Mode COMEX
- [ ] Alertes automatiques
