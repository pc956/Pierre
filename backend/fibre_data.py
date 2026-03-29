"""
Cockpit Immo — Estimation fibre optique par population communale
Source: API Geo gouv.fr (population INSEE)
"""
import httpx
import logging

logger = logging.getLogger("fibre_data")

# Cache en mémoire : code_commune -> population
_pop_cache: dict = {}


async def get_population_commune(code_commune: str) -> int:
    """Récupère la population d'une commune via API Geo"""
    if code_commune in _pop_cache:
        return _pop_cache[code_commune]
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                f"https://geo.api.gouv.fr/communes/{code_commune}",
                params={"fields": "population"}
            )
            if resp.status_code == 200:
                pop = resp.json().get("population", 0)
                _pop_cache[code_commune] = pop
                return pop
    except Exception as e:
        logger.warning(f"Geo API population error for {code_commune}: {e}")
    _pop_cache[code_commune] = 0
    return 0


async def estimate_fibre(code_commune: str, plu_zone: str = "") -> dict:
    """Estime distance fibre et nb opérateurs selon la population communale.
    Bonus si zone industrielle (UI/UX/UE).
    """
    population = await get_population_commune(code_commune)

    if population > 50000:
        dist_m = 500
        nb_op = 3
    elif population > 10000:
        dist_m = 1500
        nb_op = 2
    elif population > 2000:
        dist_m = 3000
        nb_op = 1
    else:
        dist_m = 5000
        nb_op = 1

    # Bonus zone industrielle
    zone_upper = (plu_zone or "").upper().strip()
    if zone_upper in ("UI", "UX", "UE", "I", "IX"):
        dist_m = int(dist_m * 0.6)
        nb_op = min(nb_op + 1, 4)

    return {
        "dist_backbone_fibre_m": dist_m,
        "nb_operateurs_fibre": nb_op,
        "population_commune": population,
        "estimation_method": "population_geo_api",
    }
