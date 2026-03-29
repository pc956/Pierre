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
- [x] Carte Leaflet dark + couches infra (HTB, 400/225kV, LP, câbles, DC)
- [x] Chatbot IA (GPT-4.1-mini) — interface exclusive
- [x] Parcelles cadastrales IGN + PLU GPU + S3REnR + Future 400kV + Export PDF + Google Auth

### V2 Refonte (29/03/2026)
- [x] Score universel /100 (RTE/40, MW/30, PLU/20, Surface/10 + malus)
- [x] Données réelles: S3REnR, fibre population, Géorisques, DVF Cerema
- [x] Recherche par commune + parallélisation + cache GPU
- [x] PDF "Fiche d'Opportunité" + SYSTEM_PROMPT simplifié + Score breakdown + Agrégation adjacentes

### V2 Correctifs
- [x] 5 couches carte (zones indus GPU, heatmap MW, inondables, cours d'eau WMS, routes)
- [x] DVF réel cascade (commune API → dept → région fallback)
- [x] Nettoyage complet project_type

### V3 Correctifs
- [x] Distance cours d'eau (Overpass API) + Distance route principale (Overpass API)
- [x] Suggestions rapides chatbot (5 pills) + Liens Satellite + Street View
- [x] Mode comparaison (2-3 parcelles côte-à-côte)

### V4 Bugfixes agent IA (29/03/2026)
- [x] BUG 1: Resume contient désormais eau/route (recalcul post-Overpass)
- [x] BUG 2: SYSTEM_PROMPT simplifié (actions search/site_detail supprimées, fallback vers find_parcels)
- [x] BUG 3: Verdict cohérent après bonus 400kV (GO correct si score passe 70+)
- [x] BUG 4: Fallback sans LLM (_try_direct_parse pour requêtes simples)
- [x] BUG 5: Reconstruction code_commune si vide (via api_search_communes)

## Backlog
- [ ] **P1**: Overlay risques Géorisques vectoriel sur carte
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques
- [ ] **P3**: PDF comparatifs auto (2+ parcelles shortlistées)
