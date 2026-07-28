from datetime import datetime, timezone
from weekend_scraper.telegram import format_segment_messages, SEGMENTS
from weekend_scraper.alerter import Alert
from weekend_scraper.models import PriceSample


def _sample(to_airport, out_date="2026-05-15", ret_date="2026-05-17", price_gbp=5900,
            from_airport="BHD", out_hhmm="19:05", ret_hhmm="20:15"):
    return PriceSample(
        scraped_at=datetime.now(timezone.utc),
        out_date=out_date, ret_date=ret_date,
        from_airport=from_airport, to_airport=to_airport,
        price_gbp=price_gbp, out_depart_hhmm=out_hhmm, ret_depart_hhmm=ret_hhmm,
        airlines=["BA"],
    )


def test_returns_exactly_four_messages_in_segment_order():
    messages = format_segment_messages([])

    assert len(messages) == 4
    assert "Belfast ↔ London" in messages[0]
    assert "Amsterdam" in messages[1]
    assert "Paris" in messages[2]
    assert "Barcelona" in messages[3] and "Málaga" in messages[3]


def test_empty_segments_say_no_deals_with_their_cap():
    messages = format_segment_messages([])

    assert "No deals under £100 this run." in messages[0]
    assert "No deals under £130 this run." in messages[1]
    assert "No deals under £130 this run." in messages[2]
    assert "No deals under £130 this run." in messages[3]


def test_london_deals_only_appear_in_london_message():
    lhr = Alert(sample=_sample("LHR", price_gbp=5900), rule="absolute")
    stn = Alert(sample=_sample("STN", price_gbp=6400, from_airport="BFS",
                               out_date="2026-05-22", ret_date="2026-05-24"),
                rule="absolute")

    messages = format_segment_messages([lhr, stn])
    london = messages[0]

    assert "£59" in london
    assert "BHD→LHR" in london
    assert "£64" in london
    assert "BFS→STN" in london
    # No deals leaked into the international messages
    assert "No deals" in messages[1]
    assert "No deals" in messages[2]
    assert "No deals" in messages[3]


def test_absolute_and_drop_on_same_flight_merge_into_one_deal():
    s = _sample("LHR", price_gbp=5900)
    absolute = Alert(sample=s, rule="absolute")
    drop = Alert(sample=s, rule="drop_20", median_price=8100, drop_percent=0.27)

    london = format_segment_messages([absolute, drop])[0]

    assert "🔥 DEAL" in london
    assert "-27% vs £81 median" in london
    # Only one price line for the single flight
    assert london.count("£59</b>") == 1


def test_spain_message_groups_barcelona_and_malaga_together():
    bcn = Alert(sample=_sample("BCN", price_gbp=11000), rule="absolute")
    agp = Alert(sample=_sample("AGP", price_gbp=12500,
                               out_date="2026-06-19", ret_date="2026-06-21"),
                rule="absolute")

    spain = format_segment_messages([bcn, agp])[3]

    assert "BHD→BCN" in spain
    assert "BHD→AGP" in spain


def test_drop_only_flight_labelled_as_drop_not_deal():
    s = _sample("CDG", price_gbp=14000)  # above £130 cap, only a drop
    drop = Alert(sample=s, rule="drop_15", median_price=17000, drop_percent=0.18)

    paris = format_segment_messages([drop])[2]

    assert "📉 DROP" in paris
    assert "-18% vs £170 median" in paris


def test_segments_cover_all_configured_airports():
    airports = set()
    for seg in SEGMENTS:
        airports |= set(seg.airports)

    assert airports == {"LHR", "LGW", "STN", "LTN", "LCY", "AMS", "CDG", "BCN", "AGP"}
