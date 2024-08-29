# functions having to do with finding local airports
# also functions handling city names and location references / cleaning up and filtering them
# so they are processed correctly, such as spell check
import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderInsufficientPrivileges
import re


def find_nearby_airports(airport_code_or_city):
    """
    Find international airports within 50 miles of a given airport code or city name.

    Args:
        airport_code_or_city (str): The IATA code of the airport or the name of the city to search from.

    Returns:
        pd.DataFrame: A DataFrame containing information about nearby international airports.
    """
    file_path = 'airports.csv'
    airports_df = pd.read_csv(file_path)  # Load airport data from the CSV file

    if re.match(r'^[A-Z]{3}$', airport_code_or_city):  # Check if the input is an airport code
        origin_coords = get_coords_airport(airport_code_or_city, airports_df)
        remove_origin = True
    # If it's not an airport code, assume it's a city
    else:
        # run it through autocorrect first to check / fix common shortened names for cities i use
        airport_code_or_city = autocorrect_cities(airport_code_or_city)
        # then pull the coordinates for the city
        origin_coords = get_coords_city(airport_code_or_city)
        remove_origin = False

    # Filter for international airports
    international_airports = airports_df[airports_df['category'].str.lower() == 'international']

    # Calculate distances and filter within 50 miles
    international_airports['distance'] = international_airports.apply(
        lambda row: geodesic(origin_coords, parse_location(row['location'])).miles, axis=1)

    nearby_international_airports = international_airports[international_airports['distance'] <= 50]

    return nearby_international_airports


def get_coords_airport(airport_code, airports_df):
    """
    Get coordinates from an airport code.

    Args:
        airport_code (str): The IATA code of the airport.
        airports_df (pd.DataFrame): DataFrame containing airport data.

    Returns:
        tuple: A tuple containing (latitude, longitude).
    """
    origin_airport = airports_df[airports_df['code'] == airport_code].iloc[0]
    return parse_location(origin_airport['location'])  # Parse location for coordinates


def get_coords_city(city_name):
    """
    Get coordinates from a city name.

    Args:
        city_name (str): The name of the city.

    Returns:
        tuple: A tuple containing (latitude, longitude).
    """
    geolocator = Nominatim(user_agent="joseph_carley_flight_app", timeout=10)  # Initialize geolocator with user agent
    location = geolocator.geocode(city_name)  # Geocode the city name to get coordinates
    if location:
        return (location.latitude, location.longitude)
    else:
        raise ValueError(f"City name '{city_name}' not found")  # Raise error if city name is not found


def parse_location(location):
    """
    Parse the 'location' column to extract latitude and longitude.

    Args:
        location (str): The location string in the format 'POINT (longitude latitude)'.

    Returns:
        tuple: A tuple containing (latitude, longitude).
    """
    point = location.strip('POINT ()').split()
    return float(point[1]), float(point[0])  # Return latitude and longitude as a tuple


def autocorrect_cities(city_input):
    '''
    Takes an input that is a city (because it's not an airport code) and auto-corrects it to the proper
    formatting.
    Right now it only works for cities I fly to most often.
    :param city_input: str input city
    :return: city_formatted
    '''
    city_input_formatted = ''

    # Mapping of common abbreviations or alternate names to proper city names
    city_corrections = {
        'dc': 'Washington, D.C.',
        'la': 'Los Angeles',
        'nyc': 'New York',
        'sf': 'San Francisco',
        'vegas': 'Las Vegas'
    }

    # Check if the input matches any of the predefined patterns
    if city_input.lower() in city_corrections:
        city_input_formatted = city_corrections[city_input.lower()]

    # If it doesn't match a specific pattern, return the same input unchanged
    return city_input_formatted if city_input_formatted else city_input


if __name__ == '__main__':
    # Example usage
    try:
        nearby_airports = find_nearby_airports('sf')  # or 'New York'
        print(nearby_airports)
    except GeocoderInsufficientPrivileges as e:
        print("Geocoding request was denied. Please check your user agent and try again later.")
    except ValueError as e:
        print(e)
