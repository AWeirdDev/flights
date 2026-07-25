<div align="center">
    <a href="https://www.searchapi.io/google-flights-api?utm_source=github&utm_medium=sponsorship&utm_campaign=google_flights_api&utm_content=AWeirdDev_flights">
        <img width="2560" alt="searchapi-banner" src="https://github.com/user-attachments/assets/05adb599-e875-4ed7-9498-8bc4165ce4d5" />
        <p>Made possible with support from SearchApi</p>
    </a>
</div>

<br />

<div align="center">

# ✈️ fast-flights (v3.0)

The fast and strongly-typed Google Flights scraper (API) implemented in Python.
Based on Base64-encoded Protobuf string.

[**Documentation (v3)**](https://aweirddev.github.io/flights) • [Issues](https://github.com/AWeirdDev/flights/issues) • [PyPi (v3)](https://pypi.org/project/fast-flights)

```haskell
$ pip install fast-flights
```

</div>

<details>
    <summary><b>What's New</b></summary>

- `v2.0` – New (much more succinct) API, fallback support for Playwright serverless functions, and [documentation](https://aweirddev.github.io/flights)!
- `v2.2` – Now supports **local playwright** for sending requests.
- `v3.0rc0` – Uses JavaScript data instead.
- `v3.0` – Polished new API! I suppose.

</details>

## At a glance
```python
from fast_flights import (
    FlightQuery,
    Passengers, 
    create_query, 
    get_flights
)

query = create_query(
    flights=[
        FlightQuery(
            date="YYYY-MM-DD",   # change the date
            from_airport="MYJ",  # three-letter name
            to_airport="TPE",    # three-letter name
        ),
    ],
    seat="economy",  # business/economy/first/premium-economy
    trip="one-way",  # multi-city/one-way/round-trip
    passengers=Passengers(adults=1),
    language="zh-TW",
)
res = get_flights(query)
```

## Search filters

`FlightQuery` supports filters for each flight leg:

```python
flight = FlightQuery(
    date="YYYY-MM-DD",
    from_airport="MYJ",
    to_airport="TPE",
    max_stops=1,
    airlines=["JL", "ONEWORLD"],
    earliest_departure_hour=7,
    latest_departure_hour=18,
    earliest_arrival_hour=10,
    latest_arrival_hour=23,
    max_duration_minutes=720,
    connecting_airports=["HND", "NRT"],
    min_layover_minutes=60,
    max_layover_minutes=240,
    less_emissions_only=True,
)
```

Filters for the whole search are passed to `create_query`:

```python
query = create_query(
    flights=[flight],
    currency="USD",
    max_price=1500,
    carry_on_bags=1,
    checked_bags=1,
    hide_separate_and_self_transfer=True,
    exclude_basic_economy=True,
)
```

Hours use local airport time on a 0–23 clock. Duration and layover values use
minutes, and `max_price` uses the selected `currency`. Google currently applies
the first leg's airline filter to the whole search.

## Integrations
If you'd like, you can use integrations.

### Bright Data
Use the [BrightData](https://brightdata.com) integration to protect your IP.

```python
from fast_flights.integrations import BrightData

result = get_flights(
    ..., 
    integration=BrightData(zone="...")
)

# ... same as normal queries
```

### SearchApi <kbd>Sponsored</kbd>
If you want better consistency and richer data, consider using [SearchApi](https://www.searchapi.io/google-flights-api?utm_source=github&utm_medium=sponsorship&utm_campaign=google_flights_api&utm_content=AWeirdDev_flights).

```python
from fast_flights.integrations import SearchApi, SearchApiResult

result: SearchApiResult = get_flights(
    ...,
    integration=SearchApi()
)

# rich data!
result.flights
result.cheaper_alternatives
result.price_insights
result.booking_options
...
```

## Roadmap
- [x] Use JavaScript data instead of traditional HTML parsing
- [x] Add support for integrations
- [ ] Dangerously use Google's `GetShoppingResults` internal API. Get ready to get banned.

## Contributing
Contributing is welcomed! A few notes though:
1. please no ai slop. i am not reading all that.
2. im really busy with life; im not a full-time reddit mod.

***

## How it's made

The other day, I was making a chat-interface-based trip recommendation app and wanted to add a feature that can search for flights available for booking. My personal choice is definitely [Google Flights](https://flights.google.com) since Google always has the best and most organized data on the web. Therefore, I searched for APIs on Google.

> 🔎 **Search** <br />
> google flights api

The results? Bad. It seems like they discontinued this service and it now lives in the Graveyard of Google.

> <sup><a href="https://duffel.com/blog/google-flights-api" target="_blank">🧏‍♂️ <b>duffel.com</b></a></sup><br />
> <sup><i>Google Flights API: How did it work & what happened to it?</i></b>
>
> The Google Flights API offered developers access to aggregated airline data, including flight times, availability, and prices. Over a decade ago, Google announced the acquisition of ITA Software Inc. which it used to develop its API. **However, in 2018, Google ended access to the public-facing API and now only offers access through the QPX enterprise product**.

That's awful! I've also looked for free alternatives but their rate limits and pricing are just 😬 (not a good fit/deal for everyone).

<br />

However, Google Flights has their UI – [flights.google.com](https://flights.google.com). So, maybe I could just use Developer Tools to log the requests made and just replicate all of that? Undoubtedly not! Their requests are just full of numbers and unreadable text, so that's not the solution.

Perhaps, we could scrape it? I mean, Google allowed many companies like [Serpapi](https://google.com/search?q=serpapi) to scrape their web just pretending like nothing happened... So let's scrape our own.

> 🔎 **Search** <br />
> google flights ~~api~~ scraper pypi

Excluding the ones that are not active, I came across [hugoglvs/google-flights-scraper](https://pypi.org/project/google-flights-scraper) on Pypi. I thought to myself: "aint no way this is the solution!"

I checked hugoglvs's code on [GitHub](https://github.com/hugoglvs/google-flights-scraper), and I immediately detected "playwright," my worst enemy. One word can describe it well: slow. Two words? Extremely slow. What's more, it doesn't even run on the **🗻 Edge** because of configuration errors, missing libraries... etc. I could just reverse [try.playwright.tech](https://try.playwright.tech) and use a better environment, but that's just too risky if they added Cloudflare as an additional security barrier 😳.

Life tells me to never give up. Let's just take a look at their URL params...

```markdown
https://www.google.com/travel/flights/search?tfs=CBwQAhoeEgoyMDI0LTA1LTI4agcIARIDVFBFcgcIARIDTVlKGh4SCjIwMjQtMDUtMzBqBwgBEgNNWUpyBwgBEgNUUEVAAUgBcAGCAQsI____________AZgBAQ&hl=en
```

| Param | Content | My past understanding |
|-------|---------|-----------------------|
| hl    | en      | Sets the language.    |
| tfs   | CBwQAhoeEgoyMDI0LTA1LTI4agcIARID… | What is this???? 🤮🤮 |

I removed the `?tfs=` parameter and found out that this is the control of our request! And it looks so base64-y.

If we decode it to raw text, we can still see the dates, but we're not quite there — there's too much unwanted Unicode text.

Or maybe it's some kind of a **data-storing method** Google uses? What if it's something like JSON? Let's look it up.

> 🔎 **Search** <br />
> google's json alternative

> 🐣 **Result**<br />
> Solution: The Power of **Protocol Buffers**
> 
> LinkedIn turned to Protocol Buffers, often referred to as **protobuf**, a binary serialization format developed by Google. The key advantage of Protocol Buffers is its efficiency, compactness, and speed, making it significantly faster than JSON for serialization and deserialization.

Gotcha, Protobuf! Let's feed it to an online decoder and see how it does:

> 🔎 **Search** <br />
> protobuf decoder

> 🐣 **Result**<br />
> [protobuf-decoder.netlify.app](https://protobuf-decoder.netlify.app)

I then pasted the Base64-encoded string to the decoder and no way! It DID return valid data!

![annotated, Protobuf Decoder screenshot](https://github.com/AWeirdDev/flights/assets/90096971/77dfb097-f961-4494-be88-3640763dbc8c)

I immediately recognized the values — that's my data, that's my query!

So, I wrote some simple Protobuf code to decode the data.

```protobuf
syntax = "proto3"

message Airport {
    string name = 2;
}

message FlightInfo {
    string date = 2;
    Airport dep_airport = 13;
    Airport arr_airport = 14;
}

message GoogleSucks {
    repeated FlightInfo = 3;
}
```

It works! Now, I won't consider myself an "experienced Protobuf developer" but rather a complete beginner.

I have no idea what I wrote but... it worked! And here it is, `fast-flights`.

***

<div align="center">

(c) 2024-2026 AWeirdDev, and all the awesome people

</div>
