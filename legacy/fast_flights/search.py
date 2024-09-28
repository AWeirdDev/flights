from typing import List
from ._generated_enum import Airport


def search_airport(query: str) -> List[Airport]:
    """Search for airports.

    Args:
        query (str): The query.

    Returns:
        list[Airport]: A list of airports (enum `Airports`).
    """
    return [
        ref
        for aname, ref in Airport.__members__.items()
        if query.lower() in aname.lower()
    ]
