# Local Playwright

In case the Playwright serverless functions are down or you prefer not to use them, you can run the Playwright server locally and request against that.

1. Install this package with the dependencies needed for Playwright:

```bash
pip install fast-flights[local]
```

2. Install the Playwright browser:

```bash
python -m playwright install chromium # or `python -m playwright install` if you want to install all browsers
```

3. Now you can use the `fetch_mode="local"` parameter in `get_flights`:

```python
get_flights(
    ...,
    fetch_mode="local"  # common/fallback/force-fallback/local
)

# ...or:

get_fights_from_filter(
    filter,
    mode="local"  # common/fallback/force-fallback/local
)
```
