from python.airflights import make_tfs

print(
    make_tfs(
        [
            {
                "date": "2022-01-01",
                "from": "SFO",
                "to": "LAX",
                "max_stops": 3,
            }
        ],
        "economy",
        ["adult"],
        "round_trip",
    ).base64()
)
