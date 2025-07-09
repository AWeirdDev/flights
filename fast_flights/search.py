from typing import List, Set
from ._generated_enum import Airport
from .airport_data import get_airport_data


def search_airport(query: str) -> List[Airport]:
    """Search for airports.

    Args:
        query (str): The query. Can match:
            - Airport enum member names (case-insensitive)
            - Airport codes like GCM (case-sensitive)
            - ICAO codes like MWCR (case-sensitive)
            - Country codes like KY (case-sensitive)
            - City names like George Town (case-insensitive)

    Returns:
        list[Airport]: A list of airports (enum `Airports`).
    """
    results: Set[Airport] = set()
    airport_data = get_airport_data()
    
    # Search by enum member name (case-insensitive) - original behavior
    # Also handle spaces as underscores for better matching
    query_normalized = query.lower().replace(' ', '_')
    for aname, ref in Airport.__members__.items():
        aname_lower = aname.lower()
        if query.lower() in aname_lower or query_normalized in aname_lower:
            results.add(ref)
    
    # Search by airport code (case-sensitive)
    if query in airport_data.by_code:
        airport_info = airport_data.by_code[query]
        if airport_info.enum_member:
            results.add(airport_info.enum_member)
    
    # Search by ICAO code (case-sensitive)
    if query in airport_data.by_icao:
        airport_info = airport_data.by_icao[query]
        if airport_info.enum_member:
            results.add(airport_info.enum_member)
    
    # Search by country code (case-sensitive)
    if query in airport_data.by_country:
        for airport_info in airport_data.by_country[query]:
            if airport_info.enum_member:
                results.add(airport_info.enum_member)
    
    # Search by city name (case-insensitive)
    query_lower = query.lower()
    for city_lower, airports in airport_data.by_city_lower.items():
        if query_lower in city_lower:
            for airport_info in airports:
                if airport_info.enum_member:
                    results.add(airport_info.enum_member)
    
    return list(results)
