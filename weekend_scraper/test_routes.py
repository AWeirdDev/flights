from weekend_scraper.routes import get_routes, Route

def test_get_routes():
    routes = get_routes()
    assert len(routes) == 10
    assert routes[0] == Route(from_airport="BHD", to_airport="LHR")
    assert routes[-1] == Route(from_airport="BFS", to_airport="LCY")
    
    # Check all expected pairs exist
    origins = {"BHD", "BFS"}
    destinations = {"LHR", "LGW", "STN", "LTN", "LCY"}
    
    actual_pairs = {(r.from_airport, r.to_airport) for r in routes}
    assert len(actual_pairs) == 10
    for origin in origins:
        for dest in destinations:
            assert (origin, dest) in actual_pairs
