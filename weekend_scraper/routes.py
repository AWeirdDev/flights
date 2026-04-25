from dataclasses import dataclass

@dataclass(frozen=True)
class Route:
    from_airport: str
    to_airport: str

def get_routes() -> list[Route]:
    """
    Returns the 10 origin/destination pairs for Belfast ↔ London.
    Origins: BHD, BFS
    Destinations: LHR, LGW, STN, LTN, LCY
    """
    origins = ["BHD", "BFS"]
    destinations = ["LHR", "LGW", "STN", "LTN", "LCY"]
    
    routes = []
    for origin in origins:
        for destination in destinations:
            routes.append(Route(from_airport=origin, to_airport=destination))
            
    return routes
