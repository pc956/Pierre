# Cockpit Immo - PRD (Product Requirements Document)

## Date: 2026-03-28

## Original Problem Statement
Plateforme de prospection foncière pour data centers en France - "Cockpit Immo"

## What's Been Implemented

### Phase 1-4 — MVP + Infra + S3REnR + Responsive + PLU
(Détails dans les itérations précédentes)

### Phase 5 — DC Search API pour Agents IA (2026-03-28)
- POST /api/dc/search — 101 sites scorés, 4 stratégies, pagination
- GET /api/dc/site/:id — Fiche site complète
- Scoring dynamique (power/speed/cost/risk)

### Phase 6 — Agent GPT Custom (2026-03-28)
- Page /gpt-agent avec instructions, system prompt, schema OpenAPI
- Test en direct avec résultats scorés

### Phase 7 — Chatbot IA Intégré au Dashboard (2026-03-28)
- **LLM**: GPT-4.1-mini via Emergent LLM key (emergentintegrations)
- **POST /api/chat**: Parse langage naturel → appels search API → résultats structurés
- **Frontend**: Composant ChatBot.js flottant sur le dashboard
  - Bouton "Assistant IA" en bas de la carte
  - Panel chat avec messages user/assistant
  - Quick actions: "50MW en PACA", "20MW IDF rapide", "Sites HdF réseau dispo", "Résumé S3REnR"
  - Résultats: cartes sites avec score, MW, tension, saturation
  - Détails site: foncier, grid, timeline, connectivité
  - Résumé S3REnR: cards par région
- **Auto-zoom**: La carte se déplace automatiquement vers la région recherchée (FlyToTarget)
- **Testing**: 11/11 tests backend + toutes vérifications frontend
- **Temps de réponse**: ~2-8 secondes

## Architecture
```
Frontend (React 18 + Tailwind + Leaflet)
  ├── /dashboard (Map + Sidebar + ChatBot)
  ├── /gpt-agent (GPT config page)
  └── ChatBot.js → POST /api/chat → LLM → dc_search() → results + fly_to

Backend (FastAPI)
  ├── /api/chat (AI chat via GPT-4.1-mini)
  ├── /api/dc/search + /api/dc/site (AI agent API)
  ├── /api/gpt/* (GPT config)
  ├── /api/map/* (Infrastructure)
  ├── /api/s3renr/* (Capacités réseau)
  └── /api/france/* (Parcelles + GPU PLU)

Data: MongoDB + API Carto IGN + GPU API
      + france_infra_data.py + s3renr_data.py + dc_search_api.py
      + chat_assistant.py (LLM integration)
```

## Key Files
- `/app/backend/chat_assistant.py` — LLM chat processing
- `/app/backend/dc_search_api.py` — DC search engine
- `/app/backend/gpt_agent_config.py` — OpenAPI schema + system prompt
- `/app/frontend/src/components/ChatBot.js` — Chat UI component
- `/app/frontend/src/pages/GPTAgent.js` — GPT config page

## Prioritized Backlog

### P0 - Core (Done)
- [x] Scoring engine + carte interactive + Google OAuth
- [x] Données nationales France + S3REnR
- [x] Responsive mobile + PLU réel GPU
- [x] DC Search API + Agent GPT custom
- [x] Chatbot IA intégré au dashboard

### P1 - Next Sprint
- [ ] CRM Kanban drag & drop
- [ ] API DVF (prix transactions réels)
- [ ] Export PDF fiches sites

### P2 - Future
- [ ] Couches risques environnementaux
- [ ] Comparaison côte-à-côte
- [ ] Mode COMEX
- [ ] Alertes automatiques
