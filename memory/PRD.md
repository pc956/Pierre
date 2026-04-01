# Cockpit Immo - PRD

## Problème original
Plateforme de prospection foncière pour data centers en France. Interface IA-First via chatbot, carte Leaflet, scoring multi-critères, données PLU réelles, export PDF.

## Architecture
- **Backend**: FastAPI + MongoDB + Emergent LLM (GPT-4.1-mini)
- **Frontend**: React + TailwindCSS + React-Leaflet + Shadcn/UI
- **Auth**: Emergent Google Auth
- **APIs externes**: IGN Carto, GPU Urbanisme, Géorisques, Geo API gouv.fr, DVF Cerema, Overpass OSM, api-adresse.data.gouv.fr

## Fonctionnalités implémentées

### V1-V7 (29-30/03/2026)
- [x] MVP complet + Refonte scoring + Correctifs + Bugfixes + RTE réel + 5 Chantiers Fos

### V8 — Agent IA V3 (30/03/2026)
- [x] 3 nouvelles actions (analyze_parcel, find_by_address, estimate_budget) + SYSTEM_PROMPT V3 + budget CAPEX/EBITDA/TRI

### V9 — DC 10 MW (01/04/2026)
- [x] **Scoring V3**: 5 axes normalisés /100 (Distance RTE /35, MW S3REnR /25, PLU /20, Surface /10, TTM Raccordement /10) + malus
- [x] **TTM (Time-to-Market)**: Délai raccordement estimé (12-48 mois) calculé automatiquement
- [x] **Scan DC 10 MW**: `GET /api/scan/dc-10mw` — scan auto postes RTE ≥10 MW, IGN parcelles en parallèle, scoring instantané
- [x] **Scan par poste**: `GET /api/scan/around-poste/{name}` — scan parcelles autour d'un poste spécifique
- [x] **S3REnR étendu**: 8 régions (IDF, PACA, HdF, OCC, AuRA, GES, NAQ + estimations ETF)
- [x] **Frontend Scan**: Bouton "Scan DC 10MW" + section Scan Automatique (5 régions) + résultats triés par score
- [x] **Frontend TTM**: Badge délai raccordement dans fiche parcelle + panneau "Raccordement 10 MW"
- [x] **Frontend Score V3**: 5 barres détail (Distance RTE, MW dispo, PLU, Surface, Raccordement)
- [x] **Fix PLU matching**: Filter souple (U matche UI/UX/UE et inversement)
- [x] **Fix timeout chat**: Pre-filter surface avant enrichissement, timeout Overpass, max 3 sites/région

### V10 — Fix Agent IA + Scan Région (01/04/2026)
- [x] **P0 — Limites recherche**: nb_parcels 10→30 (max 50), rayon 2000→5000m (max 10000m), suppression "+X non affichées"
- [x] **P1 — Liens Pappers Immo**: `pappers_immo_url`, `pappers_map_url`, `cadastre_gouv_url` sur chaque parcelle (sans clé API)
- [x] **P2 — Scan Région multi-postes**: `GET /api/scan/region/{region_code}` — scan top 15 postes S3REnR par MW dispo, rayon 5km, déduplication, groupement adjacent
- [x] **P3 — Raisonnement IA multi-niveaux**: Stratégie en entonnoir (commune→région→élargi), auto-widen si <5 résultats, instructions Pappers dans SYSTEM_PROMPT
- [x] **Action scan_region**: Nouvelle action IA pour scan automatique régional via chatbot
- [x] **REGION_ALIASES**: Mapping HDF→HdF, AURA→AuRA, etc. dans l'endpoint

### Tests
- [x] Iteration 24: 100% backend (11/11), 100% frontend — V10

## Backlog
- [ ] **P0**: Exécuter PROMPT_V5.3_FINAL.md (138 KB) + PIPELINE_BOOTSTRAP_CLAUDE_CODE.md
- [ ] **P1**: prompt_emergent_acces_restreint.md — whitelist emails + rate limiting
- [ ] **P1**: Overlay risques Géorisques vectoriel sur carte
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques
- [ ] **P2**: Filtres recherche avancés (sliders puissance/délai/distance)
- [ ] **P3**: PDF comparatifs auto
- [ ] **P3**: fibre_data.py données réelles NRO ARCEP
