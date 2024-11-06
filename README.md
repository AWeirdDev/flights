> ~~I'm looking for maintainers.~~ Nevermind, a bot would work.
>
> **Further development has been moved to the `v2` branch.**

<br /><br />
<div align="center">

# fast-flights

The fast and strongly-typed Google Flights scraper (API) implemented in Python. Based on Base64-encoded Protobuf string.

```haskell
$ pip install fast-flights
```

</div>

## Notes
We're using Protobuf strings to generate the `tfs` query parameter, which stores all the information for a lookup request. We then parse the HTML content and extract the info we need.

Generally speaking, using the `requests` module with naively-inserted `User-Agent` headers to scrape Google websites is a horrible idea since it's too easy to detect on the server-side. I've been blocked once, and it lasted for almost 3 months. If you're looking to be more stable, I recommend using proxies or replace the `requests` module in the source code to `primp`, which is a scraper yet highly optimized for browser impersonation. Since `primp` doesn't come with type annotations, you may create a file named `primp.py` importing the necessary items (`Client`) and constructing a blank class for `Response`, which is not directly importable from `primp`. Type definitions (`.pyi`) for `primp`:

<details>
<summary>Expand <code>primp.pyi</code></summary>

```python
from typing import Dict, Optional, Tuple

class Client:
    """Initializes an HTTP client that can impersonate web browsers.

    Args:
        auth (tuple, optional): A tuple containing the username and password for basic authentication. Default is None.
        auth_bearer (str, optional): Bearer token for authentication. Default is None.
        params (dict, optional): Default query parameters to include in all requests. Default is None.
        headers (dict, optional): Default headers to send with requests. If `impersonate` is set, this will be ignored.
        cookies (dict, optional): - An optional map of cookies to send with requests as the `Cookie` header.
        timeout (float, optional): HTTP request timeout in seconds. Default is 30.
        cookie_store (bool, optional): Enable a persistent cookie store. Received cookies will be preserved and included
            in additional requests. Default is True.
        referer (bool, optional): Enable or disable automatic setting of the `Referer` header. Default is True.
        proxy (str, optional): Proxy URL for HTTP requests. Example: "socks5://127.0.0.1:9150". Default is None.
        impersonate (str, optional): Entity to impersonate. Example: "chrome_124". Default is None.
            Chrome: "chrome_100","chrome_101","chrome_104","chrome_105","chrome_106","chrome_107","chrome_108",
                "chrome_109","chrome_114","chrome_116","chrome_117","chrome_118","chrome_119","chrome_120",
                "chrome_123","chrome_124","chrome_126","chrome_127","chrome_128"
            Safari: "safari_ios_16.5","safari_ios_17.2","safari_ios_17.4.1","safari_15.3","safari_15.5","safari_15.6.1",
                "safari_16","safari_16.5","safari_17.0","safari_17.2.1","safari_17.4.1","safari_17.5"
            OkHttp: "okhttp_3.9","okhttp_3.11","okhttp_3.13","okhttp_3.14","okhttp_4.9","okhttp_4.10","okhttp_5"
            Edge: "edge_101","edge_122","edge_127"
        follow_redirects (bool, optional): Whether to follow redirects. Default is True.
        max_redirects (int, optional): Maximum redirects to follow. Default 20. Applies if `follow_redirects` is True.
        verify (bool, optional): Verify SSL certificates. Default is True.
        ca_cert_file (str, optional): Path to CA certificate store. Default is None.
        http1 (bool, optional): Use only HTTP/1.1. Default is None.
        http2 (bool, optional): Use only HTTP/2. Default is None.

    """

    def __init__(
        self,
        auth: Optional[Tuple[str, Optional[str]]] = None,
        auth_bearer: Optional[str] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = 30,
        cookie_store: Optional[bool] = True,
        referer: Optional[bool] = True,
        proxy: Optional[str] = None,
        impersonate: Optional[str] = None,
        follow_redirects: Optional[bool] = True,
        max_redirects: Optional[int] = 20,
        verify: Optional[bool] = True,
        ca_cert_file: Optional[str] = None,
        http1: Optional[bool] = None,
        http2: Optional[bool] = None,
    ): ...
    def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        auth: Optional[Tuple[str, Optional[str]]] = None,
        auth_bearer: Optional[str] = None,
        timeout: Optional[float] = 30,
    ) -> "Response":
        """Performs a GET request to the specified URL.

        Args:
            url (str): The URL to which the request will be made.
            params (Optional[Dict[str, str]]): A map of query parameters to append to the URL. Default is None.
            headers (Optional[Dict[str, str]]): A map of HTTP headers to send with the request. Default is None.
            cookies (Optional[Dict[str, str]]): - An optional map of cookies to send with requests as the `Cookie` header.
            auth (Optional[Tuple[str, Optional[str]]]): A tuple containing the username and an optional password
                for basic authentication. Default is None.
            auth_bearer (Optional[str]): A string representing the bearer token for bearer token authentication. Default is None.
            timeout (Optional[float]): The timeout for the request in seconds. Default is 30.

        """

class Response:
    content: str
    cookies: Dict[str, str]
    headers: Dict[str, str]
    status_code: int
    text: str
    text_markdown: str
    text_plain: str
    text_rich: str
    url: str
```

</details>

## Basics
To use `fast-flights`, you'll first create a filter (inherited from `?tfs=`) to perform a request.
Then, add `flight_data`, `trip`, `seat`, `passengers`, and (optional) `max_stops` info to use the API directly.

```python
from fast_flights import FlightData, Passengers, create_filter, get_flights

# Create a new filter
filter = create_filter(
    flight_data=[
        # Include more if it's not a one-way trip
        FlightData(
            date="2024-07-02",  # Date of departure
            from_airport="TPE", 
            to_airport="MYJ"
        ),
        # ... include more for round trips
    ],
    trip="one-way",  # Trip (round-trip, one-way)
    seat="economy",  # Seat (economy, premium-economy, business or first)
    passengers=Passengers(
        adults=2,
        children=1,
        infants_in_seat=0,
        infants_on_lap=0
    ),
    max_stops=None  # or specify number
)

# Get flights with a filter
result = get_flights(filter)

# The price is currently... low/typical/high
print("The price is currently", result.current_price)
```

A command-line example script is included as `example.py`. Usage is as follows: 

`python3 example.py --origin LAX --destination LGA --depart_date 2025-2-26 --return_date 2025-02-29 --max_stops 1`

**Information**: Display additional information.
```python
# Get the first flight
flight = result.flights[0]

flight.is_best
flight.name
flight.departure
flight.arrival
flight.arrival_time_ahead
flight.duration
flight.stops
flight.delay?  # may not be present
flight.price
```

**Useless enums**: Additionally, you can use the `Airport` enum to search for airports in code (as you type)! See `_generated_enum.py` in source.

```python
Airport.TAIPEI
              |---------------------------------|
              | TAIPEI_SONGSHAN_AIRPORT         |
              | TAPACHULA_INTERNATIONAL_AIRPORT |
              | TAMPA_INTERNATIONAL_AIRPORT     |
              | ... 5 more                      |
              |---------------------------------|
```

## Cookies & Consent
For EU regions, if you didn't consent to Google's Terms of Service, you'll ultimately get blocked.
You can use the built-in `Cookies` class to pass through this check:

```python
from fast_flights import Cookies

cookies = Cookies.new(locale="de").to_dict()
get_flights(filter, cookies=cookies)
```

See [issue](https://github.com/AWeirdDev/flights/issues/1) #1

## Allow Looping Last Item
In some rare cases, looping into the last item (internally) would lead to an unknown exit. If you believe your computer is a good boy, disable this restriction by adding the `dangerously_allow_looping_last_item` option:

```python
get_flights(filter, dangerously_allow_looping_last_item=True)
```

## About Preflights
We may request to the server twice as sometimes the initial request would not return any results. When this happens, it counts as a preflight agent and we'll send another request to the server as they build data. You can think of this as a "cold start."

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

## Contributing

Yes, please: [github.com/AWeirdDev/flights](https://github.com/AWeirdDev/flights)

<br />

<div align="center>

(c) AWeirdDev

</div>
