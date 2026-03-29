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

### V2 Correctifs (29/03/2026)
- [x] 5 couches carte (zones indus GPU, heatmap MW, inondables, cours d'eau WMS, routes)
- [x] DVF réel cascade (commune API → dept → région fallback)
- [x] Nettoyage complet project_type

### V3 Correctifs (29/03/2026)
- [x] Distance cours d'eau (Overpass API) — dist_cours_eau_m, nom_cours_eau
- [x] Distance route principale (Overpass API) — dist_route_m, nom_route, type_route
- [x] Suggestions rapides chatbot (5 pills)
- [x] Liens Google Maps Satellite + Street View dans ParcelDetail
- [x] Mode comparaison (2-3 parcelles côte-à-côte)
- [x] Eau + route intégrés dans scoring resume et PDF

## Score structure
```json
{
  "score": 75, "verdict": "GO",
  "detail": {"distance_rte": 35, "mw_disponibles": 25, "plu": 15, "surface": 10, "malus": -10},
  "flags": ["ZONE INONDABLE (PPRI)"],
  "resume": "Score 75/100 — GO. 3.2 ha en zone PLU UX à 1.2km du poste FEUILLANE (225kV), cours d'eau à 1.2km..."
}
```

## Backlog
- [ ] **P1**: Overlay risques Géorisques vectoriel sur carte
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques
- [ ] **P3**: PDF comparatifs auto (2+ parcelles shortlistées)

## Endpoints clés
- `POST /api/chat` — Chatbot IA
- `GET /api/france/gpu-zones` — Zones industrielles par bbox
- `POST /api/export/pdf` — Fiche d'Opportunité PDF
- `GET /api/parcels/{id}/score` — Score universel
