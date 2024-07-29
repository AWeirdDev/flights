> I'm looking for maintainers. [Open Issue ›](https://github.com/AWeirdDev/flights/issues/new?title=I+want+to+be+a+maintainer&body=i+think+aweirddev+is+so+bad+at+writing+code+lmao)

<br /><br />
<div align="center">

# flights (fast-flights)

The fast, robust, strongly-typed Google Flights scraper (API) implemented in Python. Based on Base64-encoded Protobuf string.

```haskell
$ pip install fast-flights
```

</div>

## Basic

To use `fast-flights`, you'll first create a filter (inherited from `?tfs=`) to perform a request.
Then, add `flight_data`, `trip`, `seat` and `passengers` info to use the API directly.

Honorable mention: I like birds. Yes, I like birds.

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
)

# Get flights with a filter
result = get_flights(filter)

# The price is currently... low/typical/high
print("The price is currently", result.current_price)
```

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

***

The documentation was here. Who the hell moved it?!

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

## Contributing

Yes, please: [github.com/AWeirdDev/flights](https://github.com/AWeirdDev/flights)

<br />

<div align="center>

(c) AWeirdDev

</div>
