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
- Frontend: popups enrichis avec barres de progression MW, score DC, plan de renforcement
- Frontend: panneau régional S3REnR dans la sidebar
- Labels MW sur la carte pour les postes avec correspondance directe
- Testing: 19/19 tests passés

### Phase 4 - Responsive Mobile + PLU Réel GPU (2026-03-28)
**Responsive Mobile:**
- Suppression du blocage CSS desktop-only, l'app fonctionne sur mobile
- Header compact avec boutons filtre/couches
- Carte plein écran sur mobile
- Barre de navigation mobile en bas (Carte/Tableau/CRM/Stats)
- Filtres en bottom sheet glissant depuis le bas
- Couches en bottom sheet avec grille 2 colonnes
- Sidebar transformée en panneau fixe glissant sur mobile
- Popups Leaflet adaptés pour écrans tactiles
- Contrôle COUCHES desktop caché sur mobile (remplacé par bottom sheet)

**PLU Réel via GPU API:**
- Intégration de l'API GPU (Géoportail de l'Urbanisme) dans `api_carto.py`
- Récupération en parallèle des zones PLU lors du chargement des parcelles par BBox
- Zones PLU réelles: U (Urbain), AU (À Urbaniser), A (Agricole), N (Naturelle)
- Code couleur PLU dans le tableau (vert=U, orange=AU, violet=A, bleu=N)
- Affichage enrichi dans la fiche parcelle: zone PLU + libellé + description longue
- Filtrage par zone PLU fonctionnel avec données réelles
- Testing: 100% tests passés (12 backend + toutes vérifications frontend)

## Architecture
```
Frontend (React 18 + Tailwind + Leaflet) -> REST API -> Backend (FastAPI)
                                                        |
                                                MongoDB + API Carto IGN + GPU API
                                                + france_infra_data.py (in-memory)
                                                + s3renr_data.py (in-memory)
```

## Key API Endpoints
- `GET /api/map/electrical-assets` - Postes HTB enrichis S3REnR + lignes
- `GET /api/s3renr/summary` - Résumé par région (MW, postes, statuts)
- `GET /api/s3renr/top-opportunities` - Top opportunités DC par MW dispo
- `GET /api/france/parcelles/bbox` - Parcelles par BBox + PLU GPU
- `GET /api/france/communes` - Recherche communes

## Prioritized Backlog

### P0 - Core (Done)
- [x] Scoring engine
- [x] Carte interactive avec polygones cadastraux cliquables
- [x] Google OAuth
- [x] Données nationales France (101 postes, lignes, DC, câbles)
- [x] Lignes 400kV et 225kV
- [x] Intégration S3REnR (capacités MW, saturation, renforcements)
- [x] Responsive mobile
- [x] PLU réel via GPU API

### P1 - Next Sprint
- [ ] CRM Kanban drag & drop
- [ ] API DVF (prix transactions réels)
- [ ] Export PDF fiches sites

### P2 - Future
- [ ] Couches risques environnementaux (inondation, sismique)
- [ ] Comparaison côte-à-côte (4 parcelles)
- [ ] Mode COMEX
- [ ] Alertes automatiques
