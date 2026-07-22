from dataclasses import dataclass

@dataclass(frozen=True)
class Route:
    from_airport: str
    to_airport: str

def get_routes() -> list[Route]:
    """
    Origins: BHD, BFS
    Destinations:
      London — LHR, LGW, STN, LTN, LCY
      Europe — CDG (Paris), BCN (Barcelona), AMS (Amsterdam), AGP (Malaga)
    Non-existent/seasonal pairs are handled by the scraper returning None.
    """
    origins = ["BHD", "BFS"]
    destinations = ["LHR", "LGW", "STN", "LTN", "LCY", "CDG", "BCN", "AMS", "AGP"]

    return [
        Route(from_airport=origin, to_airport=destination)
        for origin in origins
        for destination in destinations
    ]
