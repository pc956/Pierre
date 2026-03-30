# Cockpit Immo - PRD

## Problème original
Plateforme de prospection foncière pour data centers en France. Interface IA-First via chatbot, carte Leaflet, scoring multi-critères, données PLU réelles, export PDF.

## Architecture
- **Backend**: FastAPI + MongoDB + Emergent LLM (GPT-4.1-mini)
- **Frontend**: React + TailwindCSS + React-Leaflet + Shadcn/UI
- **Auth**: Emergent Google Auth
- **APIs externes**: IGN Carto, GPU Urbanisme, Géorisques, Geo API gouv.fr, DVF Cerema, Overpass OSM

## Fonctionnalités implémentées

### V1 MVP
- [x] Carte Leaflet dark + couches infra + Chatbot IA + Parcelles IGN + PLU GPU + S3REnR + Future 400kV + PDF + Google Auth

### V2 Refonte (29/03/2026)
- [x] Score universel /100 (RTE/40, MW/30, PLU/20, Surface/10 + malus)
- [x] Données réelles: S3REnR, fibre, Géorisques, DVF Cerema
- [x] Recherche par commune + parallélisation + cache GPU + SYSTEM_PROMPT + Score breakdown + Agrégation adjacentes + PDF Fiche d'Opportunité

### V2-V3 Correctifs
- [x] 5 couches carte + DVF cascade + Nettoyage project_type
- [x] Distance cours d'eau + route (Overpass) + Suggestions chatbot + Street View/Satellite + Mode comparaison

### V4 Bugfixes agent IA
- [x] 5 bugs corrigés (recalcul post-Overpass, SYSTEM_PROMPT, 400kV bonus, fallback sans LLM, code_commune)

### V5 Bugfixes pipeline (29/03/2026)
- [x] code_commune 5 chiffres (api_carto.py) + S3REnR matching aliases manuels

### V6 Coordonnées RTE réelles (30/03/2026)
- [x] 3 569 postes OSM/Overpass (distance) + 1 091 postes (carte) — remplace 101 hardcodés

### V7 — 5 Chantiers (30/03/2026)
- [x] **Chantier 1**: Fix matching S3REnR — `_strip_accents()`, préfixes/suffixes stripping, 19 nouveaux alias (Aubette, Cap Janet, Weppes, etc.)
- [x] **Chantier 1bis**: Fix heatmap MW — `_normalize()` avec accent stripping dans `server.py`
- [x] **Chantier 2**: Données projet RTE Fos-Jonquières — ROQUEROUSSE & TAVEL ajoutés, `projet_fos` sur FEUILLANE/PONTEAU/REALTOR, FUTURE_LINE_METADATA enrichi, SYSTEM_PROMPT mis à jour
- [x] **Chantier 3**: Fix export PDF — try/except, sécurisation None, `projet_fos` dans données clés et points forts
- [x] **Chantier 4**: EmptyStatePanel — Recherche rapide (6 pills), Projet Fos card (3700/400/2029), Capacités réseau, KPIs infra, Guide, `externalChatMessage`
- [x] **Chantier 5**: Projet Fos dans ParcelDetail + table de comparaison

### Tests
- [x] Iteration 20: 100% backend (11/11), 100% frontend — V6
- [x] Iteration 21: 100% backend (15/15), 100% frontend — V7 (5 chantiers)

## Backlog
- [ ] **P1**: Overlay risques Géorisques vectoriel sur carte
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques
- [ ] **P3**: PDF comparatifs auto
