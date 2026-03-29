"""
Cockpit Immo — Géorisques API integration
Enrichit les parcelles avec les risques naturels réels.
Source: https://georisques.gouv.fr/api/v1/
"""
import httpx
import logging

logger = logging.getLogger("georisques")

_risk_cache: dict = {}


async def enrich_georisques(code_commune: str) -> dict:
    """Récupère les risques naturels d'une commune via Géorisques API.
    Retourne ppri_zone, zone_sismique, argiles_alea, risques bruts.
    """
    if code_commune in _risk_cache:
        return _risk_cache[code_commune]

    result = {
        "ppri_zone": None,
        "zone_sismique": 1,
        "argiles_alea": "faible",
        "risques": [],
        "source": "georisques_api",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://georisques.gouv.fr/api/v1/gaspar/risques",
                params={"code_insee": code_commune, "page": 1, "page_size": 50}
            )
            if resp.status_code == 200:
                data = resp.json()
                risques = data.get("data", [])

                for r in risques:
                    libelle = (r.get("libelle_risque_long") or r.get("libelle_risque_jo") or "").lower()
                    result["risques"].append(libelle)

                    # Inondation → PPRI
                    if "inondation" in libelle:
                        result["ppri_zone"] = "rouge"

                    # Séisme
                    if "sism" in libelle or "tremblement" in libelle:
                        # Essayer d'extraire le niveau
                        for word in libelle.split():
                            if word.isdigit():
                                result["zone_sismique"] = max(result["zone_sismique"], int(word))

                    # Mouvement de terrain / argiles
                    if "argile" in libelle or "retrait" in libelle or "gonflement" in libelle:
                        result["argiles_alea"] = "moyen"
                    if "mouvement de terrain" in libelle:
                        result["argiles_alea"] = "fort" if result["argiles_alea"] == "moyen" else "moyen"

    except Exception as e:
        logger.warning(f"Georisques API error for {code_commune}: {e}")
        result["source"] = "georisques_error"

    _risk_cache[code_commune] = result
    return result
