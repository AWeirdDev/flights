import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
from itertools import product
from threading import Lock
from typing import Dict, List, Literal, Optional, TypeGuard, Union

from fast_flights import (
    FlightData,
    Passengers,
    Result,
    create_filter,
    get_flights,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG level
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class SearchProgress:
    """Track search progress and results"""

    total_tasks: int = 0
    completed_tasks: int = 0
    found_flights: int = 0
    current_searches: Dict[str, str] = field(default_factory=dict)
    best_price: Optional[float] = None
    lock: Lock = field(default_factory=Lock)

    def update_best_price(self, price: float):
        """Update best price found so far"""
        with self.lock:
            if self.best_price is None or price < self.best_price:
                self.best_price = price
                logger.info(f"New best price found: €{price:.2f}")

    def add_current_search(self, task_id: str, description: str):
        """Add a current search task"""
        with self.lock:
            self.current_searches[task_id] = description

    def remove_current_search(self, task_id: str):
        """Remove a completed search task"""
        with self.lock:
            self.current_searches.pop(task_id, None)

    def increment_completed(self):
        """Increment completed tasks counter"""
        with self.lock:
            self.completed_tasks += 1

    def increment_found_flights(self, count: int = 1):
        """Increment found flights counter"""
        with self.lock:
            self.found_flights += count

    def get_progress_string(self) -> str:
        """Get current progress as a string"""
        with self.lock:
            progress_pct = (
                (self.completed_tasks / self.total_tasks * 100)
                if self.total_tasks > 0
                else 0
            )
            return (
                f"Progress: {self.completed_tasks}/{self.total_tasks} ({progress_pct:.1f}%) "
                f"Found flights: {self.found_flights} "
                f"Best price: {f'€{self.best_price:.2f}' if self.best_price is not None else 'N/A'}"
            )

    def get_current_searches(self) -> List[str]:
        """Get list of current searches"""
        with self.lock:
            return list(self.current_searches.values())


# Global progress tracker
search_progress = SearchProgress()

# South Asian major airports
SOUTH_ASIA_AIRPORTS = [
    "SIN",  # Singapore
    # "BKK",  # Bangkok
    # "KUL",  # Kuala Lumpur
    # "CGK",  # Jakarta
    # "MNL",  # Manila
    # "SGN",  # Ho Chi Minh City
    # "HAN",  # Hanoi
    # "RGN",  # Yangon
    # "PNH",  # Phnom Penh
    # "DAD",  # Da Nang
]

SeatClass = Literal["economy", "premium-economy", "business", "first"]


class SearchOptimizer:
    """Manages search patterns and optimizes request distribution"""

    def __init__(self, max_concurrent_searches: int = 3):
        self.max_concurrent_searches = max_concurrent_searches
        self.search_patterns: Dict[str, List[str]] = {}
        self.successful_patterns: Dict[str, int] = {}
        self.lock = Lock()

    def optimize_search_order(self, combinations: List[tuple]) -> List[tuple]:
        """Optimize the order of search combinations based on past successes"""
        if not self.successful_patterns:
            # Randomize if no history
            shuffled = list(combinations)
            random.shuffle(shuffled)
            return shuffled

        # Sort combinations based on success patterns
        def get_pattern_score(combo: tuple) -> float:
            pattern = f"{combo[0]}-{combo[1]}"  # airport pair pattern
            success_count = self.successful_patterns.get(pattern, 0)
            return success_count

        return sorted(combinations, key=get_pattern_score, reverse=True)

    def record_success(self, dep_airport: str, dest_airport: str):
        """Record successful search pattern"""
        pattern = f"{dep_airport}-{dest_airport}"
        with self.lock:
            self.successful_patterns[pattern] = (
                self.successful_patterns.get(pattern, 0) + 1
            )

    def record_failure(self, dep_airport: str, dest_airport: str):
        """Record failed search pattern"""
        pattern = f"{dep_airport}-{dest_airport}"
        with self.lock:
            self.successful_patterns[pattern] = max(
                0, self.successful_patterns.get(pattern, 0) - 1
            )


# Global search optimizer
search_optimizer = SearchOptimizer()


def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """Generate a list of dates between start and end date."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_list = []

    if start > end:
        logger.error("Start date must be before or equal to end date.")
        return []

    current = start
    while current <= end:
        date_list.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    logger.debug(
        f"Generated date range from {start_date} to {end_date}: {len(date_list)} dates"
    )
    return date_list


@lru_cache(maxsize=1000)
def cached_get_flights(
    outbound_date: str,
    return_date: str,
    from_airport: str,
    to_airport: str,
    seat_class: SeatClass = "economy",
    max_stops: Optional[int] = None,
) -> Optional[Result]:
    """Cache flight search results to avoid duplicate requests"""
    try:
        filter = create_filter(
            flight_data=[
                FlightData(
                    date=outbound_date,
                    from_airport=from_airport,
                    to_airport=to_airport,
                ),
                FlightData(
                    date=return_date,
                    from_airport=to_airport,
                    to_airport=from_airport,
                ),
            ],
            trip="round-trip",
            seat=seat_class,
            passengers=Passengers(adults=1),
            max_stops=max_stops,
        )
        return get_flights(filter, inject_eu_cookies=True)
    except Exception as e:
        logger.error(f"Error in cached_get_flights: {str(e)}")
        return None


async def search_flight_combination(args: tuple) -> List[dict]:
    """Search for flights for a specific combination of parameters"""
    dep_airport, dest_airport, outbound_date, return_date, params = args
    found_flights = []

    # Create unique task ID and description
    task_id = f"{dep_airport}-{dest_airport}-{outbound_date}-{return_date}"
    task_description = (
        f"{dep_airport} → {dest_airport} ({outbound_date} - {return_date})"
    )

    try:
        # Update current searches
        search_progress.add_current_search(task_id, task_description)
        logger.info(f"Searching: {task_description}")

        # Create flight filter
        filter = create_filter(
            flight_data=[
                FlightData(
                    date=outbound_date,
                    from_airport=dep_airport,
                    to_airport=dest_airport,
                ),
                FlightData(
                    date=return_date,
                    from_airport=dest_airport,
                    to_airport=dep_airport,
                ),
            ],
            trip="round-trip",
            seat=params["seat_class"],
            passengers=Passengers(adults=1),
            max_stops=params["max_stops"],
        )

        # Get flights with improved retry mechanism
        max_retries = 3
        retry_delay = 5  # Initial delay in seconds
        last_error = None
        result = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.debug(
                        f"Retry attempt {attempt + 1}/{max_retries} for {task_description}"
                    )
                    await asyncio.sleep(retry_delay)

                # Make request using async get_flights
                result = await get_flights(filter, inject_eu_cookies=True)

                # If we got flights, process them
                if result and result.flights:
                    break

                # If no flights found but request was successful, wait before retry
                retry_delay = min(retry_delay * 2, 30)  # Exponential backoff, max 30s
                logger.debug(
                    f"No flights found on attempt {attempt + 1}/{max_retries}, waiting {retry_delay}s"
                )

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                retry_delay = min(retry_delay * 2, 30)
                continue

        # Process results if we found any flights
        if result and result.flights:
            for flight in result.flights:
                # Extract price value (assuming EUR)
                price_str = flight.price.replace("€", "").replace(",", "").strip()
                try:
                    price = float(price_str)
                    if price <= params["max_price"]:
                        flight_info = {
                            "departure_airport": dep_airport,
                            "destination_airport": dest_airport,
                            "outbound_date": outbound_date,
                            "return_date": return_date,
                            "price": price,
                            "airline": flight.name,
                            "stops": flight.stops,
                            "duration": flight.duration,
                            "current_price_indicator": result.current_price,
                        }
                        found_flights.append(flight_info)

                        # Update progress
                        search_progress.increment_found_flights()
                        search_progress.update_best_price(price)

                        # Log new flight found
                        logger.info(
                            f"Found flight: {dep_airport} → {dest_airport} "
                            f"({outbound_date} - {return_date}) "
                            f"€{price:.2f} with {flight.name}"
                        )
                except ValueError:
                    continue
        elif last_error:
            raise last_error
        else:
            logger.warning("No flights found after retries")

        # Record successful search if we found flights
        if found_flights:
            search_optimizer.record_success(dep_airport, dest_airport)
        else:
            search_optimizer.record_failure(dep_airport, dest_airport)

    except Exception as e:
        logger.error(f"Error searching {task_description}: {str(e)}")
        search_optimizer.record_failure(dep_airport, dest_airport)
    finally:
        # Update progress
        search_progress.increment_completed()
        search_progress.remove_current_search(task_id)

        # Log progress
        logger.info(search_progress.get_progress_string())

    return found_flights


def validate_dates(start_date: str, end_date: str) -> tuple[bool, Optional[str]]:
    """
    Validate search dates.
    Returns (is_valid, error_message)
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = datetime.now()

        # Check if dates are too close to current date
        min_future_days = 7  # Minimum days in future
        if (start - current).days < min_future_days:
            return (
                False,
                f"Start date must be at least {min_future_days} days in the future",
            )

        # Check if dates are too far in the future (Google Flights limitation)
        max_future_days = 365 * 2  # Allow up to two years in the future
        if (start - current).days > max_future_days:
            return (
                False,
                f"Start date cannot be more than {max_future_days // 365} years in the future",
            )

        # Check if end date is after start date
        if end < start:
            return False, "End date must be after start date"

        return True, None

    except ValueError as e:
        return False, f"Invalid date format: {str(e)}"


def calculate_search_scope(
    departure_airports: List[str],
    destination_airports: List[str],
    start_date: str,
    end_date: str,
    min_duration_days: int,
    max_duration_days: int,
) -> tuple[int, float]:
    """
    Calculate the total number of possible flight combinations and estimated search time.
    Returns (total_combinations, estimated_minutes)
    """
    # Calculate date ranges
    date_range = generate_date_range(start_date, end_date)
    total_outbound_dates = len(date_range)

    # Calculate average return dates per outbound date
    avg_return_dates = min(max_duration_days - min_duration_days + 1, len(date_range))

    # Calculate total airport pairs
    airport_pairs = len(departure_airports) * len(destination_airports)

    # Calculate total possible combinations
    total_combinations = airport_pairs * total_outbound_dates * avg_return_dates

    # Estimate search time (assuming ~3 seconds per search with parallel execution)
    estimated_minutes = (total_combinations * 3) / (60 * 3)  # 3 concurrent searches

    return total_combinations, estimated_minutes


def is_flight_list(result: Union[List[dict], BaseException]) -> TypeGuard[List[dict]]:
    """Type guard to check if result is a list of flight dictionaries"""
    return isinstance(result, list)


async def search_flights(
    departure_airports: List[str],
    destination_airports: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_duration_days: int = 11,
    max_duration_days: int = 25,
    max_price: float = 500,
    max_stops: Optional[int] = None,
    seat_class: SeatClass = "economy",
    max_concurrent_searches: int = 3,
) -> List[dict]:
    """
    Search for flights based on multiple parameters.
    """
    if destination_airports is None:
        destination_airports = SOUTH_ASIA_AIRPORTS

    # Reset progress tracker
    global search_progress
    search_progress = SearchProgress()

    # Set default dates if not provided
    current_date = datetime.now()
    search_start_date = (
        start_date if start_date is not None else current_date.strftime("%Y-%m-%d")
    )
    search_end_date = (
        end_date
        if end_date is not None
        else (current_date + timedelta(days=90)).strftime("%Y-%m-%d")
    )

    # Validate dates before proceeding
    is_valid, error_message = validate_dates(search_start_date, search_end_date)
    if not is_valid:
        logger.error(f"Date validation failed: {error_message}")
        return []

    # Validate duration constraints
    if min_duration_days > max_duration_days:
        logger.error("Minimum duration cannot be greater than maximum duration")
        return []

    if min_duration_days < 1:
        logger.error("Minimum duration must be at least 1 day")
        return []

    if max_duration_days > 90:
        logger.error("Maximum duration cannot exceed 90 days")
        return []

    # Adjust end date to accommodate return flights
    end_datetime = datetime.strptime(search_end_date, "%Y-%m-%d")
    start_datetime = datetime.strptime(search_start_date, "%Y-%m-%d")

    # The last possible outbound date should allow for min_duration_days
    last_outbound = end_datetime - timedelta(days=min_duration_days)
    if last_outbound < start_datetime:
        logger.error("Search period too short for minimum duration")
        return []

    # Generate outbound dates
    outbound_dates = generate_date_range(
        search_start_date, last_outbound.strftime("%Y-%m-%d")
    )

    logger.debug(f"Generated {len(outbound_dates)} possible outbound dates")

    # Create all possible combinations of parameters
    combinations = list(
        product(departure_airports, destination_airports, outbound_dates)
    )
    logger.debug(f"Generated {len(combinations)} airport-date combinations")

    # Calculate and display search scope
    total_combinations, estimated_minutes = calculate_search_scope(
        departure_airports,
        destination_airports,
        search_start_date,
        search_end_date,
        min_duration_days,
        max_duration_days,
    )

    logger.info("\nSearch Scope:")
    logger.info(f"Total possible flight combinations: {total_combinations:,}")
    logger.info(f"Estimated search time: {estimated_minutes:.1f} minutes")
    logger.info(
        "Note: Actual search time may vary based on network conditions and flight availability"
    )

    # Ask for confirmation if the search scope is large
    if total_combinations > 1000:
        logger.warning("\nWarning: Large search scope detected!")
        try:
            user_input = input(
                "Do you want to proceed with the search? (y/n): "
            ).lower()
            if user_input != "y":
                logger.info("Search cancelled by user")
                return []
        except KeyboardInterrupt:
            logger.info("\nSearch cancelled by user")
            return []

    logger.info(
        f"\nStarting search for flights from {departure_airports} to {destination_airports}"
    )
    logger.info(f"Date range: {search_start_date} to {search_end_date}")
    logger.info(f"Duration: {min_duration_days}-{max_duration_days} days")
    logger.info(f"Max price: €{max_price:.2f}")

    # Initialize results list
    found_flights = []

    # Validate if we have any valid combinations
    if not combinations:
        logger.error("No valid date combinations found for the given parameters")
        return []

    # Optimize search order
    combinations = search_optimizer.optimize_search_order(combinations)

    # Prepare search tasks
    search_tasks = []
    logger.info(f"Processing {len(combinations)} possible outbound combinations")

    for dep_airport, dest_airport, outbound_date in combinations:
        # Calculate return dates based on duration constraints
        outbound_datetime = datetime.strptime(outbound_date, "%Y-%m-%d")
        min_return_date = outbound_datetime + timedelta(days=min_duration_days)
        max_return_date = outbound_datetime + timedelta(days=max_duration_days)
        end_datetime = datetime.strptime(search_end_date, "%Y-%m-%d")

        logger.debug(
            f"Outbound: {outbound_date}, Min Return: {min_return_date.strftime('%Y-%m-%d')}, Max Return: {max_return_date.strftime('%Y-%m-%d')}"
        )

        # Skip if min return date is beyond the search period
        if min_return_date > end_datetime:
            logger.debug(
                f"Skipping {outbound_date} - min return date {min_return_date.strftime('%Y-%m-%d')} beyond search period"
            )
            continue

        # Adjust max return date to not exceed search period
        max_return_date = min(max_return_date, end_datetime)

        # Generate valid return dates
        return_dates = generate_date_range(
            min_return_date.strftime("%Y-%m-%d"), max_return_date.strftime("%Y-%m-%d")
        )

        logger.debug(
            f"Found {len(return_dates)} possible return dates for {outbound_date}"
        )

        # Skip if no valid return dates
        if not return_dates:
            logger.warning(
                f"No valid return dates found for outbound date {outbound_date}"
            )
            continue

        # Create search parameters
        params = {
            "seat_class": seat_class,
            "max_stops": max_stops,
            "max_price": max_price,
        }

        # Add tasks for each return date
        for return_date in return_dates:
            search_tasks.append(
                (dep_airport, dest_airport, outbound_date, return_date, params)
            )
            logger.debug(f"Added task: {outbound_date} -> {return_date}")

    logger.info(f"Generated {len(search_tasks)} search tasks")

    # Validate if we have any tasks after all constraints
    if not search_tasks:
        logger.error(
            "No valid search combinations found after applying all constraints"
        )
        return []

    # Update total tasks in progress tracker
    search_progress.total_tasks = len(search_tasks)
    logger.info(f"Total search combinations: {len(search_tasks)}")

    # Randomize task order to distribute load
    random.shuffle(search_tasks)

    # Create semaphore to limit concurrent tasks
    semaphore = asyncio.Semaphore(max_concurrent_searches)

    async def bounded_search(task):
        async with semaphore:
            return await search_flight_combination(task)

    # Execute searches with controlled concurrency
    tasks = [asyncio.create_task(bounded_search(task)) for task in search_tasks]
    try:
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if is_flight_list(result):
                found_flights.extend(result)
            else:
                logger.error(f"Task failed: {str(result)}")

    except asyncio.CancelledError:
        logger.warning("Search interrupted by user, cancelling tasks...")
        # Cancel all pending tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        # Wait for tasks to finish cancellation with a timeout
        try:
            await asyncio.wait(tasks, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("Some tasks did not cancel in time")
        raise
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise

    # Sort results by price
    found_flights.sort(key=lambda x: x["price"])

    # Log final summary
    logger.info("\nSearch completed!")
    logger.info(f"Total flights found: {len(found_flights)}")
    if found_flights:
        logger.info(f"Best price found: €{found_flights[0]['price']:.2f}")

    return found_flights


async def main_async():
    departure_airports = ["VNO"]  # Vilnius only for testing

    try:
        results = await search_flights(
            departure_airports=departure_airports,
            start_date="2025-02-05",
            end_date="2025-02-16",
            min_duration_days=11,
            max_duration_days=30,
            max_price=700,
            max_stops=2,
            max_concurrent_searches=3,
        )

        # Print results
        if not results:
            print("No flights found matching your criteria.")
            return

        print(f"\nFound {len(results)} flights matching your criteria:\n")
        for flight in results:
            print(
                f"Route: {flight['departure_airport']} → {flight['destination_airport']}"
            )
            print(f"Dates: {flight['outbound_date']} - {flight['return_date']}")
            print(
                f"Price: €{flight['price']:.2f} ({flight['current_price_indicator']} price)"
            )
            print(f"Airline: {flight['airline']}")
            print(f"Stops: {flight['stops']}")
            print(f"Duration: {flight['duration']}")
            print("-" * 50)

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("\nSearch interrupted by user, cleaning up...")
        return
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise


def main():
    """Run the async main function"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("\nSearch cancelled.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
