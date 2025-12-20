import argparse
import json
from fast_flights import FlightData, Passengers, create_filter, get_flights_from_filter

def flight_to_dict(flight):
    return {
        "is_best": getattr(flight, 'is_best', None),
        "name": getattr(flight, 'name', None),
        "flight_code": getattr(flight, 'flight_code', None),
        "departure": getattr(flight, 'departure', None),
        "arrival": getattr(flight, 'arrival', None),
        "arrival_time_ahead": getattr(flight, 'arrival_time_ahead', None),
        "duration": getattr(flight, 'duration', None),
        "stops": getattr(flight, 'stops', None),
        "delay": getattr(flight, 'delay', None),
        "price": getattr(flight, 'price', None),
    }

def result_to_dict(result):
    return {
        "current_price": getattr(result, 'current_price', None),
        "flights": [flight_to_dict(flight) for flight in getattr(result, 'flights', [])]
    }

def main():
    # Argument parser for command-line input
    parser = argparse.ArgumentParser(description="Flight Price Finder")
    parser.add_argument('--origin', required=True, help="Origin airport code")
    parser.add_argument('--destination', required=True, help="Destination airport code")
    parser.add_argument('--depart_date', required=True, help="Beginning trip date (YYYY-MM-DD)")
    parser.add_argument('--return_date', help="Ending trip date (YYYY-MM-DD), optional for one-way")
    parser.add_argument('--adults', type=int, default=1, help="Number of adult passengers")
    parser.add_argument('--children', type=int, default=0, help="Number of children passengers")
    parser.add_argument('--type', type=str, default="economy", help="Fare class (economy, premium-economy, business or first)")
    parser.add_argument('--max_stops', type=int, help="Maximum number of stops (optional, [0|1|2])")
    parser.add_argument('--fetch_mode', type=str, default="common", help="Fetch mode: common, fallback, force-fallback, local, bright-data")
    parser.add_argument('--output_file', type=str, help="Path to save the JSON output file (optional)")


    args = parser.parse_args()

    flight_data = [
        FlightData(
            date=args.depart_date,
            from_airport=args.origin,
            to_airport=args.destination
        )
    ]
    trip_type = "one-way"

    if args.return_date:
        flight_data.append(
            FlightData(
                date=args.return_date,
                from_airport=args.destination,
                to_airport=args.origin
            )
        )
        trip_type = "round-trip"

    # Create a new filter
    filter = create_filter(
        flight_data=flight_data,
        trip=trip_type,
        seat=args.type,  # Seat (economy, premium-economy, business or first)
        passengers=Passengers(
            adults=args.adults,
            children=args.children,
            infants_in_seat=0,
            infants_on_lap=0
        ),
        max_stops=args.max_stops
    )

    b64 = filter.as_b64().decode('utf-8')
    print(
        "https://www.google.com/travel/flights?tfs=%s" % b64
    )

    # Previously we constructed CONSENT/SOCS cookies here and passed them to
    # get_flights_from_filter; the library now embeds a small default consent
    # cookie bundle that will be applied automatically when no cookies are
    # provided. To override or disable this behavior you can pass the
    # `cookie_consent=False` flag or supply your own `cookies`/`request_kwargs`.

    # Preferred: rely on the embedded default consent cookies (no explicit cookies passed)
    result = get_flights_from_filter(filter, mode=args.fetch_mode)

    # If you need to disable the embedded cookies and handle cookies yourself:
    # result = get_flights_from_filter(filter, mode=args.fetch_mode, cookie_consent=False)

    try:
        # Manually convert the result to a dictionary before serialization
        result_dict = result_to_dict(result)
        output_json = json.dumps(result_dict, indent=4)

        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(output_json)
            print(f"Output saved to {args.output_file}")
        else:
            print(output_json)

    except TypeError as e:
        print("Serialization to JSON failed. Raw result output:")
        print(result)
        print("Error details:", str(e))

    # Print price information safely (result may be decoded or None)
    print("The price is currently", getattr(result, 'current_price', None))

if __name__ == "__main__":
    main()