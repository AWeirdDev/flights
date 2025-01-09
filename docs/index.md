# :material-airplane-search: Fast Flights
A fast, robust Google Flights scraper (API) for Python. (Probably)

`fast-flights` uses Base64-encoded [Protobuf](https://developers.google.com/protocol-buffers) strings to generate the **`tfs` query parameter**, which stores all the information for a lookup request. We then parse the HTML content and extract the info we need using `selectolax`.

```sh
pip install fast-flights
```

## Getting started
Here's `fast-flights` in 3 steps:

1. **Import** the package
2. Add the **filters**
3. **Search** for flights

How simple is that? (...and beginner-friendly, too!)

```python
from fast_flights import FlightData, Passengers, Result, get_flights

result: Result = get_flights(
    flight_data=[
        FlightData(date="2025-01-01", from_airport="TPE", to_airport="MYJ")# (1)!
    ],
    trip="one-way",# (2)!
    seat="economy",# (3)!
    passengers=Passengers(adults=2, children=1, infants_in_seat=0, infants_on_lap=0),# (4)!
    fetch_mode="fallback",#(5)!
)

print(result)
```

1. :material-airport: This specifies the (desired) date of departure for the outbound flight. Make sure to change the date!
2. :fontawesome-solid-person-walking-luggage: This specifies the trip type (`round-trip` or `one-way`). Note that `multi-city` is **not yet** supported. Note that if you're having a `round-trip`, you need to add more than one item of flight data (in other words, 2+).
3. :material-seat: Money-spending time! This specifies the seat type, which is `economy`, `premium-economy`, `business`, or `first`.
4. :fontawesome-solid-people-line: Nice interface, eh? This specifies the number of a specific passenger type.
5. :fontawesome-solid-person-falling: Sometimes, the data is built on demand on the client-side, while the core of `fast-flights` is built around scrapers from the ground up. We support fallbacks that run Playwright serverless functions to fetch for us instead. You could either specify `common` (default), `fallback` (recommended), or `force-fallback` (100% serverless Playwright). You do not need to install Playwright in order for this to work.

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
> google flights <s>api</s> scraper pypi

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


## Contributing

Feel free to contribute! Though I won't be online that often, I'll try my best to answer all the whats, hows & WTFs.

:heart: Acknowledgements:

- @d2x made their first contribution in #7
- @PTruscott made their first contribution in #19
- @artiom-matvei made their first contribution in #20
- @esalonico fixed v2.0 currency issues in #25
