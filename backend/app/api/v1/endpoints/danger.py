from fastapi import APIRouter, Query
from app.services.danger_score_service import calculate

router = APIRouter(tags=["Danger Score"])

@router.get("/score")
async def danger_score(
    lat:       float = Query(default=48.5,  description="Latitude"),
    lng:       float = Query(default=31.2,  description="Longitude"),
    radius_km: float = Query(default=50.0,  description="Raio em km"),
):
    """
    Calcula danger score composto para uma localização.
    Combina NASA FIRMS + ReliefWeb + GDELT + UCDP.
    """
    return await calculate(lat=lat, lng=lng, radius_km=radius_km)


@router.get("/grid")
async def danger_grid(
    west:  float = Query(default=22.0),
    south: float = Query(default=44.0),
    east:  float = Query(default=40.0),
    north: float = Query(default=52.0),
    step:  float = Query(default=2.0, description="Grau entre pontos do grid"),
):
    """
    Calcula danger score para uma grelha de pontos (útil para heatmap).
    """
    import asyncio
    points = []
    lat = south
    while lat <= north:
        lng = west
        while lng <= east:
            points.append((round(lat, 2), round(lng, 2)))
            lng += step
        lat += step

    # Limitar a 20 pontos para não sobrecarregar
    points = points[:20]

    results = await asyncio.gather(*[
        calculate(lat=p[0], lng=p[1], radius_km=100) for p in points
    ])
    return {"grid": list(results), "points": len(results)}
