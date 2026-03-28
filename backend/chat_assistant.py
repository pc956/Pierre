"""
Cockpit Immo — AI Chat Assistant
Parses natural language queries into DC search API calls and returns structured results.
Uses Emergent LLM integration for NLP.
"""
import os
import json
import uuid
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

from dc_search_api import dc_search, dc_get_site

load_dotenv()
logger = logging.getLogger("chat_assistant")

SYSTEM_PROMPT = """Tu es l'assistant IA de Cockpit Immo, expert en prospection foncière pour data centers en France.

Quand l'utilisateur pose une question sur des terrains ou sites pour data centers, tu dois:
1. Extraire les paramètres de recherche
2. Retourner un JSON avec la clé "action" et les paramètres

ACTIONS POSSIBLES:

1. action: "search" — Recherche de sites DC
Paramètres à extraire:
- mw_target: puissance cible en MW (défaut: 20)
- mw_min: minimum MW (défaut: 5)
- max_delay_months: délai max raccordement (défaut: 36)
- region: "IDF"|"PACA"|"HdF"|"AuRA"|"BRE"|"GES"|"NOR"|"NAQ"|"OCC"|"PDL" (null si pas spécifié)
- strategy: "speed"|"cost"|"power"|"balanced" (défaut: "balanced")
- grid_priority: true si l'utilisateur veut réseau disponible (défaut: false)
- brownfield_only: true si brownfield/industriel uniquement (défaut: false)
- per_page: nombre de résultats (défaut: 5)

Mapping linguistique:
- "Paris", "Île-de-France", "IDF" → region: "IDF"
- "Marseille", "PACA", "sud", "Provence" → region: "PACA"
- "Nord", "Lille", "Hauts-de-France", "HdF" → region: "HdF"
- "Lyon", "Auvergne" → region: "AuRA"
- "rapide", "vite", "urgent" → strategy: "speed"
- "pas cher", "économique", "coût" → strategy: "cost"
- "puissance", "maximum MW" → strategy: "power"
- "brownfield", "industriel", "friche" → brownfield_only: true
- "réseau dispo", "non saturé" → grid_priority: true

2. action: "site_detail" — Détail d'un site
- site_id: identifiant du site

3. action: "summary" — Résumé S3REnR régional

4. action: "chat" — Question générale (pas de recherche)
- response: ta réponse en texte

RÈGLES:
- TOUJOURS répondre en JSON valide uniquement, rien d'autre
- Pour "search": retourne {"action": "search", "params": {...}, "intro": "texte court"}
- Pour "site_detail": retourne {"action": "site_detail", "site_id": "...", "intro": "texte"}
- Pour "summary": retourne {"action": "summary", "intro": "texte"}
- Pour "chat": retourne {"action": "chat", "response": "ta réponse"}
- "intro" = phrase courte d'introduction à afficher avant les résultats
- Si la demande est floue, propose des clarifications dans "chat"

CONTEXTE:
- IDF est SATURÉ (peu de MW disponible)
- PACA a ~3258 MW de capacité réseau
- HdF a ~2925 MW de capacité réseau
- Les scores vont de 0 à 100
"""


async def process_chat_message(
    message: str,
    session_id: str,
    history: list,
) -> dict:
    """Process a chat message and return structured response"""
    api_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not api_key:
        return {
            "type": "error",
            "text": "Clé LLM non configurée. Contactez l'administrateur.",
        }

    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"cockpit_{session_id}",
            system_message=SYSTEM_PROMPT,
        ).with_model("openai", "gpt-4.1-mini")

        # Send the message directly (session handles history)
        response_text = await chat.send_message(UserMessage(text=message))

        # Parse JSON from response
        parsed = _extract_json(response_text)
        if not parsed:
            return {"type": "text", "text": response_text}

        action = parsed.get("action", "chat")
        intro = parsed.get("intro", "")

        if action == "search":
            params = parsed.get("params", {})
            results = dc_search(params)
            return {
                "type": "search_results",
                "intro": intro,
                "results": results["results"][:10],
                "meta": results["meta"],
                "params": params,
                "fly_to": _get_fly_target(results["results"], params),
            }

        elif action == "site_detail":
            site_id = parsed.get("site_id", "")
            site = dc_get_site(site_id)
            if site:
                return {
                    "type": "site_detail",
                    "intro": intro,
                    "site": site,
                    "fly_to": {
                        "lat": site["location"]["lat"],
                        "lng": site["location"]["lng"],
                        "zoom": 12,
                    },
                }
            return {"type": "text", "text": f"Site {site_id} non trouvé."}

        elif action == "summary":
            from s3renr_data import S3RENR_DATA
            summary = []
            for region_key, region_data in S3RENR_DATA.items():
                postes = region_data.get("postes", {})
                summary.append({
                    "region": region_key,
                    "status": region_data.get("status_global"),
                    "mw_total": region_data.get("capacite_globale_mw"),
                    "nb_postes": len(postes),
                })
            return {
                "type": "summary",
                "intro": intro,
                "summary": summary,
            }

        else:
            return {
                "type": "text",
                "text": parsed.get("response", response_text),
            }

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "type": "error",
            "text": f"Erreur: {str(e)}",
        }


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response (handles markdown code blocks)"""
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from code block
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except json.JSONDecodeError:
                continue
    # Try finding JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return None


def _get_fly_target(results: list, params: dict) -> dict:
    """Compute map fly target from search results"""
    if not results:
        return {"lat": 46.6, "lng": 2.3, "zoom": 6}

    # If region filter, zoom to first result
    if params.get("region"):
        r = results[0]
        return {
            "lat": r["location"]["lat"],
            "lng": r["location"]["lng"],
            "zoom": 8,
        }

    # Otherwise, fit all results
    lats = [r["location"]["lat"] for r in results[:5]]
    lngs = [r["location"]["lng"] for r in results[:5]]
    return {
        "lat": sum(lats) / len(lats),
        "lng": sum(lngs) / len(lngs),
        "zoom": 7,
    }
