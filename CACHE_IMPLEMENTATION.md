# Flight Data Caching Implementation

## Overview

This implementation adds a 5-minute TTL (Time-To-Live) cache to the flight data fetching logic, reducing redundant API calls to Google Flights and improving response times for repeated queries.

## Motivation

As noted in a previous analysis:
> "Flight data doesn't change every second; 5-minute cache could avoid many requests"

Flight prices and availability are relatively stable over short time periods (5-30 minutes). Caching results eliminates:
- Redundant external API calls
- Unnecessary bandwidth consumption
- Risk of rate limiting/IP blocking
- Latency from repeated identical queries

## Implementation Details

### 1. Cache Module (`fast_flights/cache.py`)

A thread-safe, in-memory cache with TTL support:

```python
from fast_flights import get_flight_cache, clear_flight_cache

# Get the global cache instance (default 5-minute TTL)
cache = get_flight_cache(ttl=300)

# Clear the cache if needed
clear_flight_cache()
```

**Features:**
- Thread-safe operations with locking
- Automatic expiration based on TTL
- SHA256-based cache keys for consistency
- Manual cleanup of expired entries
- Global singleton pattern for shared state

### 2. Integration with Flight Queries

The caching is integrated into two main functions:

#### `get_flights()`
```python
from fast_flights import get_flights, FlightData, Passengers

result = get_flights(
    flight_data=[
        FlightData(
            date="2025-12-25",
            from_airport="SFO",
            to_airport="LAX"
        )
    ],
    trip="one-way",
    passengers=Passengers(adults=1),
    seat="economy",
    cache_ttl=300,      # Cache for 5 minutes (default)
    use_cache=True      # Enable caching (default)
)
```

#### `get_flights_from_filter()`
```python
from fast_flights import get_flights_from_filter, TFSData

result = get_flights_from_filter(
    filter=my_tfs_filter,
    currency="USD",
    mode="common",
    data_source="html",
    cache_ttl=300,      # Cache for 5 minutes
    use_cache=True      # Enable caching
)
```

### 3. Cache Key Generation

Cache keys are generated from:
- TFS filter (base64-encoded flight parameters)
- Currency code
- Fetch mode
- Data source type

This ensures that identical queries return cached results, while different queries get fresh data.

**Example:**
```python
# These two queries will share the same cache entry:
result1 = get_flights(..., cache_ttl=300)  # Fetches from API
result2 = get_flights(..., cache_ttl=300)  # Returns cached result

# This query will fetch fresh data (different parameters):
result3 = get_flights(...different params..., cache_ttl=300)
```

## Configuration Options

### TTL (Time-To-Live)

Control how long results are cached:

```python
# 5 minutes (default - recommended)
result = get_flights(..., cache_ttl=300)

# 15 minutes (for less volatile routes)
result = get_flights(..., cache_ttl=900)

# 1 minute (for frequent price checks)
result = get_flights(..., cache_ttl=60)
```

### Disable Caching

For scenarios where fresh data is critical:

```python
# Bypass cache entirely
result = get_flights(..., use_cache=False)
```

### Clear Cache

Manually clear all cached entries:

```python
from fast_flights import clear_flight_cache

clear_flight_cache()
```

## Performance Benefits

### Before Caching
```
Query 1: SFO → LAX → API call → 2.5s
Query 2: SFO → LAX → API call → 2.5s  (redundant!)
Query 3: SFO → LAX → API call → 2.5s  (redundant!)
Total: 7.5s, 3 API calls
```

### After Caching
```
Query 1: SFO → LAX → API call → 2.5s → Cache
Query 2: SFO → LAX → Cache hit → 0.001s
Query 3: SFO → LAX → Cache hit → 0.001s
Total: 2.5s, 1 API call
```

**Improvements:**
- 3x faster for repeated queries
- 66% reduction in API calls
- Lower risk of rate limiting

## Implementation Architecture

### Cache Flow Diagram

```
User Request
    ↓
get_flights()
    ↓
Generate cache key (hash of params)
    ↓
Check cache
    ├─ HIT → Return cached result (fast!)
    │
    └─ MISS → Fetch from API
              ↓
              Parse response
              ↓
              Store in cache (with TTL)
              ↓
              Return result
```

### Thread Safety

The cache uses Python's `threading.Lock()` to ensure thread-safe operations:

```python
with self._lock:
    self._cache[key] = (value, expiry_time)
```

This allows concurrent access from multiple threads/requests without race conditions.

## Testing

Run the test suite to verify caching works correctly:

```bash
python3 test_cache_standalone.py
```

**Test Coverage:**
- ✓ Basic set/get operations
- ✓ Cache key generation
- ✓ TTL expiration
- ✓ Cleanup of expired entries
- ✓ Flight data simulation
- ✓ Thread safety

## Backward Compatibility

The implementation is **fully backward compatible**:

```python
# Old code (still works, caching enabled by default)
result = get_flights(
    flight_data=[...],
    trip="one-way",
    passengers=Passengers(adults=1),
    seat="economy"
)

# New code (explicit control)
result = get_flights(
    flight_data=[...],
    trip="one-way",
    passengers=Passengers(adults=1),
    seat="economy",
    cache_ttl=300,
    use_cache=True
)
```

## API Reference

### `TTLCache`

```python
class TTLCache:
    def __init__(self, default_ttl: int = 300)
    def get(self, key: str) -> Optional[Any]
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None
    def clear(self) -> None
    def cleanup_expired(self) -> int
    def size(self) -> int

    @staticmethod
    def create_cache_key(*args, **kwargs) -> str
```

### Exported Functions

```python
# Get the global cache instance
get_flight_cache(ttl: int = 300) -> TTLCache

# Clear the global cache
clear_flight_cache() -> None
```

## Best Practices

1. **Use default TTL (5 minutes)** for most use cases
2. **Disable cache** when you need real-time pricing
3. **Clear cache** when you suspect stale data
4. **Monitor cache size** for long-running applications
5. **Use longer TTL** for stable routes (international flights)
6. **Use shorter TTL** for volatile routes (last-minute bookings)

## Future Enhancements

Potential improvements for future versions:

1. **Persistent Cache**: Store cache to disk for cross-process sharing
2. **Redis Integration**: Distributed caching for multi-server deployments
3. **Cache Statistics**: Hit/miss ratios, performance metrics
4. **Smart TTL**: Adjust TTL based on route volatility
5. **Partial Cache**: Cache parsed HTML to speed up re-parsing
6. **Compression**: Compress cached data to reduce memory usage

## Files Modified

- `fast_flights/cache.py` - New cache module
- `fast_flights/core.py` - Integration into fetch functions
- `fast_flights/__init__.py` - Export cache functions
- `test_cache_standalone.py` - Test suite

## Migration Guide

No migration needed! The feature is opt-out (enabled by default with 5-minute TTL).

To disable for specific queries:
```python
result = get_flights(..., use_cache=False)
```

To adjust TTL globally:
```python
from fast_flights import get_flight_cache

cache = get_flight_cache(ttl=900)  # 15 minutes
```

---

**Implementation Date**: 2025-11-05
**Version**: 2.2+cache
**Status**: Production Ready ✓
