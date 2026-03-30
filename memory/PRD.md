# Cockpit Immo - PRD

## Problème original
Plateforme de prospection foncière pour data centers en France. Interface IA-First via chatbot, carte Leaflet, scoring multi-critères, données PLU réelles, export PDF.

## Architecture
- **Backend**: FastAPI + MongoDB + Emergent LLM (GPT-4.1-mini)
- **Frontend**: React + TailwindCSS + React-Leaflet + Shadcn/UI
- **Auth**: Emergent Google Auth
- **APIs externes**: IGN Carto, GPU Urbanisme, Géorisques, Geo API gouv.fr, DVF Cerema, Overpass OSM, api-adresse.data.gouv.fr

## Fonctionnalités implémentées

### V1 MVP
- [x] Carte Leaflet dark + couches infra + Chatbot IA + Parcelles IGN + PLU GPU + S3REnR + Future 400kV + PDF + Google Auth

### V2 Refonte (29/03/2026)
- [x] Score universel /100 + Données réelles S3REnR/fibre/Géorisques/DVF + Recherche commune + PDF Fiche d'Opportunité

### V2-V3 Correctifs
- [x] 5 couches carte + DVF cascade + Distance eau/route Overpass + Suggestions chatbot + Street View + Mode comparaison

### V4-V5 Bugfixes
- [x] 5 bugs agent IA + 2 bugs pipeline critiques (code_commune 5 digits, S3REnR aliases)

### V6 Coordonnées RTE réelles (30/03/2026)
- [x] 3 569 postes OSM/Overpass (distance) + 1 091 postes (carte)

### V7 — 5 Chantiers (30/03/2026)
- [x] Fix S3REnR accents + heatmap MW + Projet RTE Fos-Jonquières + Fix PDF + EmptyStatePanel + projet_fos en frontend

### V8 — Agent IA V3 (30/03/2026)
- [x] **FIX 1**: Postes génériques sans nom → fallback régional best (plus de "inconnu" pour postes sans nom)
- [x] **FIX 2**: Géocodage adresse via api-adresse.data.gouv.fr (httpx async)
- [x] **ACTION analyze_parcel**: Analyse parcelle par référence cadastrale (IGN + enrichissement + score + budget)
- [x] **ACTION find_by_address**: Géocode adresse → recherche parcelles autour (rayon configurable)
- [x] **ACTION estimate_budget**: Estimation CAPEX/EBITDA/TRI indicatif (foncier + raccordement + construction + fibre)
- [x] **SYSTEM_PROMPT V3**: 6 actions (find_parcels, analyze_parcel, find_by_address, estimate_budget, summary, chat) + mapping linguistique + contexte enrichi
- [x] **_build_clean_parcel()**: Factorisation du nettoyage parcelle
- [x] **Frontend**: Carte budget (CAPEX/EBITDA/TRI) dans ChatBot.js
- [x] **_try_direct_parse()**: Fallback enrichi (regex cadastrale, adresse, budget)

### Tests
- [x] Iteration 20-21: 100% (V6-V7)
- [x] Iteration 22: 91% backend (10/11, 1 transient 502), 100% frontend (V8)

## Backlog
- [ ] **P1**: Overlay risques Géorisques vectoriel sur carte
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques
- [ ] **P3**: PDF comparatifs auto
