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
- [x] BUG 1: Resume eau/route (recalcul post-Overpass)
- [x] BUG 2: SYSTEM_PROMPT simplifié (actions obsolètes supprimées)
- [x] BUG 3: Verdict cohérent après bonus 400kV
- [x] BUG 4: Fallback sans LLM (_try_direct_parse)
- [x] BUG 5: Reconstruction code_commune si vide

### V5 Bugfixes pipeline (29/03/2026)
- [x] **BUG CRITIQUE 1**: code_commune = dept(2) + com(3) = 5 chiffres (api_carto.py). Corrige fibre, georisques, DVF pour TOUTES les parcelles.
- [x] **BUG CRITIQUE 2**: S3REnR matching par aliases manuels HTB→S3REnR (60+ correspondances PACA/IDF/HdF/AuRA) + fallback meilleur poste régional. Champs s3renr_match_method + s3renr_match_poste exposés.

## Impact des fixes V5
- Scores passent de ~75 à **83-95/100** grâce aux vrais MW S3REnR
- Fibre estimée correctement (500m-1500m vs 3000m fallback)
- Resume contient "avec 74 MW disponibles" au lieu de silence

## Backlog
- [ ] **P1**: Overlay risques Géorisques vectoriel sur carte
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques
- [ ] **P3**: PDF comparatifs auto
