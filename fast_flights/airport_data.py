import csv
import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from ._generated_enum import Airport


@dataclass
class AirportInfo:
    code: str
    name: str
    city: Optional[str]
    country_id: str
    icao: Optional[str]
    enum_member: Optional[Airport]


class AirportData:
    def __init__(self):
        self.airports: List[AirportInfo] = []
        self.by_code: Dict[str, AirportInfo] = {}
        self.by_icao: Dict[str, AirportInfo] = {}
        self.by_country: Dict[str, List[AirportInfo]] = {}
        self.by_city_lower: Dict[str, List[AirportInfo]] = {}
        self._load_data()
    
    def _load_data(self):
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'enums', 'airports.csv')
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['code']
                name = row['name']
                city = row.get('city', '').strip() or None
                country_id = row['country_id']
                icao = row.get('icao', '').strip() or None
                
                # Try to find corresponding enum member
                enum_member = None
                if 'AIRPORT' in name.upper():
                    normalized_name = '_'.join(
                        name.replace('-', ' ')
                            .replace('.', ' ')
                            .replace('/', ' ')
                            .replace("'", '')
                            .replace('(', ' ')
                            .replace(')', ' ')
                            .replace('–', ' ')
                            .split()
                    ).upper()
                    
                    try:
                        enum_member = getattr(Airport, normalized_name, None)
                    except AttributeError:
                        pass
                
                airport_info = AirportInfo(
                    code=code,
                    name=name,
                    city=city,
                    country_id=country_id,
                    icao=icao,
                    enum_member=enum_member
                )
                
                self.airports.append(airport_info)
                
                # Index by code
                self.by_code[code] = airport_info
                
                # Index by ICAO
                if icao:
                    self.by_icao[icao] = airport_info
                
                # Index by country
                if country_id not in self.by_country:
                    self.by_country[country_id] = []
                self.by_country[country_id].append(airport_info)
                
                # Index by city (lowercase for case-insensitive search)
                if city:
                    city_lower = city.lower()
                    if city_lower not in self.by_city_lower:
                        self.by_city_lower[city_lower] = []
                    self.by_city_lower[city_lower].append(airport_info)


# Singleton instance
_airport_data: Optional[AirportData] = None


def get_airport_data() -> AirportData:
    global _airport_data
    if _airport_data is None:
        _airport_data = AirportData()
    return _airport_data