# Cockpit Immo - PRD

## Problème original
Plateforme de prospection foncière pour data centers en France. Interface IA-First via chatbot, carte Leaflet, scoring multi-critères, données PLU réelles, export PDF.

## Architecture
- **Backend**: FastAPI + MongoDB + Emergent LLM (GPT-4.1-mini)
- **Frontend**: React + TailwindCSS + React-Leaflet + Shadcn/UI
- **Auth**: Emergent Google Auth
- **APIs externes**: IGN Carto (cadastre), GPU (urbanisme), Géorisques, Geo API gouv.fr, DVF Cerema

## Fonctionnalités implémentées

### V1 MVP (sessions précédentes)
- [x] Carte Leaflet dark avec couches infra (HTB, lignes 400/225kV, LP, câbles, DC)
- [x] Chatbot IA (GPT-4.1-mini) — interface exclusive
- [x] Parcelles cadastrales IGN dynamiques
- [x] PLU dynamique via GPU API
- [x] S3REnR données réseau par région
- [x] Ligne future 400kV Fos→Jonquières avec buffers
- [x] Export PDF
- [x] Google Auth Emergent

### V2 Refonte complète (29/03/2026)
- [x] **Étape 1**: Score universel /100 (4 axes: RTE/40, MW/30, PLU/20, Surface/10 + malus)
- [x] **Étape 2**: Données réelles — S3REnR postes, fibre population, Géorisques risques, DVF prix
- [x] **Étape 3**: Recherche par commune (Geo API → code INSEE → postes HTB)
- [x] **Étape 4**: Parallélisation asyncio.gather + cache GPU mémoire
- [x] **Étape 5**: Couches carte (postes, lignes, LP, câbles, DC, future 400kV)
- [x] **Étape 6**: PDF "Fiche d'Opportunité" (2 pages: synthèse + plan d'action)
- [x] **Étape 7**: SYSTEM_PROMPT simplifié sans project_type
- [x] **Étape 8**: Score breakdown barres dans chatbot et panel détail
- [x] **Étape 9**: Agrégation parcelles adjacentes (sites composites < 100m)

### V2 Correctifs (29/03/2026)
- [x] **Correctif 1**: 5 nouvelles couches carte (zones industrielles GPU, heatmap MW, zones inondables, cours d'eau WMS IGN, fond routier)
- [x] **Correctif 2**: DVF réel via API Cerema (cascade: commune API → dept hardcode → région fallback)
- [x] **Correctif 3**: Nettoyage complet project_type (supprimé de server.py, models.py, endpoints)

## Verdicts scoring
- **GO** (≥70): Site prometteur
- **À ÉTUDIER** (40-69): Potentiel à confirmer
- **DÉFAVORABLE** (<40): Difficultés majeures
- **EXCLU**: Zone non constructible (A, N)

## Score structure
```json
{
  "score": 75,
  "verdict": "GO",
  "detail": {"distance_rte": 35, "mw_disponibles": 25, "plu": 15, "surface": 10, "malus": -10},
  "flags": ["ZONE INONDABLE (PPRI)"],
  "resume": "Score 75/100 — GO. Parcelle de 3.2 ha en zone PLU UX à 1.2 km du poste FEUILLANE (225kV)..."
}
```

## Backlog
- [ ] **P1**: Couches risques environnementaux avancées (Géorisques overlay direct)
- [ ] **P2**: Comparaison côte-à-côte de sites
- [ ] **P2**: Mode COMEX (vue exécutive)
- [ ] **P2**: Alertes automatiques
- [ ] **P3**: PDF comparatifs auto (2+ parcelles shortlistées)

## Endpoints clés
- `POST /api/chat` — Chatbot IA (recherche parcelles, commune, résumé)
- `GET /api/map/rte-future-400kv` — Future ligne 400kV GeoJSON
- `POST /api/export/pdf` — Fiche d'Opportunité PDF
- `GET /api/s3renr/summary` — Résumé régional
- `GET /api/france/parcelles/bbox` — Parcelles par viewport
- `GET /api/france/gpu-zones` — Zones industrielles GPU par bbox
- `GET /api/parcels/{id}/score` — Score universel d'une parcelle
