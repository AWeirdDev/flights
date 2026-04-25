from datetime import date
from unittest.mock import patch, MagicMock
from weekend_scraper.scraper import scrape_weekend_route
from weekend_scraper.routes import Route
from fast_flights.parser import MetaList
from fast_flights.model import Flights, SingleFlight, Airport, SimpleDatetime, CarbonEmission

def test_scrape_weekend_route_filtering():
    route = Route(from_airport="BHD", to_airport="LHR")
    friday = date(2026, 5, 1)
    sunday = date(2026, 5, 3)
    
    # Mock return value
    mock_meta = MagicMock(spec=MetaList)
    
    # Flight 1: Too early Friday
    f1 = Flights(
        type="round-trip",
        price=50,
        airlines=["BA"],
        flights=[
            SingleFlight(
                from_airport=Airport(name="BHD", code="BHD"),
                to_airport=Airport(name="LHR", code="LHR"),
                departure=SimpleDatetime(date=(2026, 5, 1), time=(16, 0)),
                arrival=SimpleDatetime(date=(2026, 5, 1), time=(17, 0)),
                duration=60,
                plane_type="A320"
            ),
            SingleFlight(
                from_airport=Airport(name="LHR", code="LHR"),
                to_airport=Airport(name="BHD", code="BHD"),
                departure=SimpleDatetime(date=(2026, 5, 3), time=(18, 0)),
                arrival=SimpleDatetime(date=(2026, 5, 3), time=(19, 0)),
                duration=60,
                plane_type="A320"
            )
        ],
        carbon=CarbonEmission(0, 0)
    )
    
    # Flight 2: Good times
    f2 = Flights(
        type="round-trip",
        price=100,
        airlines=["BA"],
        flights=[
            SingleFlight(
                from_airport=Airport(name="BHD", code="BHD"),
                to_airport=Airport(name="LHR", code="LHR"),
                departure=SimpleDatetime(date=(2026, 5, 1), time=(17, 30)),
                arrival=SimpleDatetime(date=(2026, 5, 1), time=(18, 30)),
                duration=60,
                plane_type="A320"
            ),
            SingleFlight(
                from_airport=Airport(name="LHR", code="LHR"),
                to_airport=Airport(name="BHD", code="BHD"),
                departure=SimpleDatetime(date=(2026, 5, 3), time=(17, 0)),
                arrival=SimpleDatetime(date=(2026, 5, 3), time=(18, 0)),
                duration=60,
                plane_type="A320"
            )
        ],
        carbon=CarbonEmission(0, 0)
    )
    
    # Flight 3: Too early Sunday
    f3 = Flights(
        type="round-trip",
        price=40,
        airlines=["BA"],
        flights=[
            SingleFlight(
                from_airport=Airport(name="BHD", code="BHD"),
                to_airport=Airport(name="LHR", code="LHR"),
                departure=SimpleDatetime(date=(2026, 5, 1), time=(19, 0)),
                arrival=SimpleDatetime(date=(2026, 5, 1), time=(20, 0)),
                duration=60,
                plane_type="A320"
            ),
            SingleFlight(
                from_airport=Airport(name="LHR", code="LHR"),
                to_airport=Airport(name="BHD", code="BHD"),
                departure=SimpleDatetime(date=(2026, 5, 3), time=(16, 59)),
                arrival=SimpleDatetime(date=(2026, 5, 3), time=(17, 59)),
                duration=60,
                plane_type="A320"
            )
        ],
        carbon=CarbonEmission(0, 0)
    )
    
    mock_meta = [f1, f2, f3]
    
    with patch("weekend_scraper.scraper.get_flights", return_value=mock_meta):
        sample = scrape_weekend_route(friday, sunday, route)
        
    assert sample is not None
    assert sample.price_gbp == 10000
    assert sample.out_depart_hhmm == "17:30"
    assert sample.ret_depart_hhmm == "17:00"

def test_scrape_weekend_route_no_matches():
    route = Route(from_airport="BHD", to_airport="LHR")
    friday = date(2026, 5, 1)
    sunday = date(2026, 5, 3)
    
    mock_meta = MagicMock(spec=MetaList)
    # Flight 1: Too early Friday
    f1 = Flights(
        type="round-trip",
        price=50,
        airlines=["BA"],
        flights=[
            SingleFlight(
                from_airport=Airport(name="BHD", code="BHD"),
                to_airport=Airport(name="LHR", code="LHR"),
                departure=SimpleDatetime(date=(2026, 5, 1), time=(16, 0)),
                arrival=SimpleDatetime(date=(2026, 5, 1), time=(17, 0)),
                duration=60,
                plane_type="A320"
            ),
            SingleFlight(
                from_airport=Airport(name="LHR", code="LHR"),
                to_airport=Airport(name="BHD", code="BHD"),
                departure=SimpleDatetime(date=(2026, 5, 3), time=(18, 0)),
                arrival=SimpleDatetime(date=(2026, 5, 3), time=(19, 0)),
                duration=60,
                plane_type="A320"
            )
        ],
        carbon=CarbonEmission(0, 0)
    )
    mock_meta = [f1]
    
    with patch("weekend_scraper.scraper.get_flights", return_value=mock_meta):
        sample = scrape_weekend_route(friday, sunday, route)
        
    assert sample is None
