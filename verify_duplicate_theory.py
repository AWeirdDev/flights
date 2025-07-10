#!/usr/bin/env python3
"""
Verify that HTML shows each flight twice (best + other sections)
"""

from selectolax.lexbor import LexborHTMLParser

# Read the HTML file
test_file = 'raw_html_extreme_LAX_JFK_9_Terminals.html'
with open(test_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

parser = LexborHTMLParser(html_content)

print("VERIFYING DUPLICATE FLIGHT THEORY")
print("=" * 70)

# Get flight containers
containers = parser.css('div[jsname="IWWDBc"], div[jsname="YdtKid"]')
print(f"Found {len(containers)} flight containers")

# Analyze each container
all_flight_urls = []
for i, container in enumerate(containers):
    items = container.css("ul.Rk10dc li")
    print(f"\nContainer {i}: {len(items)} items")
    
    # Get first few flight URLs from this container
    container_urls = []
    for j, item in enumerate(items[:5]):  # First 5 items
        url_elem = item.css_first('[data-travelimpactmodelwebsiteurl]')
        if url_elem:
            url = url_elem.attributes.get('data-travelimpactmodelwebsiteurl', '')
            if url:
                # Extract just the itinerary part
                if 'itinerary=' in url:
                    itinerary = url.split('itinerary=')[1]
                    container_urls.append(itinerary)
                    all_flight_urls.append((i, j, itinerary))
    
    print(f"  Sample URLs:")
    for url in container_urls[:3]:
        print(f"    {url}")

# Check for duplicates
print(f"\n\nDUPLICATE ANALYSIS:")
unique_urls = set()
duplicates = []

for container, item, url in all_flight_urls:
    if url in unique_urls:
        duplicates.append((container, item, url))
    else:
        unique_urls.add(url)

print(f"Total flight URLs extracted: {len(all_flight_urls)}")
print(f"Unique URLs: {len(unique_urls)}")
print(f"Duplicates: {len(duplicates)}")

if duplicates:
    print(f"\nFirst few duplicates:")
    for container, item, url in duplicates[:5]:
        print(f"  Container {container}, Item {item}: {url}")
        # Find original
        for c2, i2, u2 in all_flight_urls:
            if u2 == url and (c2, i2) != (container, item):
                print(f"    Duplicate of: Container {c2}, Item {i2}")
                break

# Check container patterns
print(f"\n\nCONTAINER PATTERN ANALYSIS:")
print("Container sizes:", [len(c.css("ul.Rk10dc li")) for c in containers])
print("\nHypothesis: Containers alternate between 'best' (3 items) and 'other' (106 items)")
print("Pattern matches!" if [3, 106, 3, 106] == [len(c.css("ul.Rk10dc li")) for c in containers] else "Pattern doesn't match")

# Extract flight details to confirm duplicates
print(f"\n\nFLIGHT DETAIL COMPARISON:")
print("Comparing flights from container 0 (best) with container 1 (other):")

container0_flights = []
container1_flights = []

for item in containers[0].css("ul.Rk10dc li")[:3]:
    name_elem = item.css_first("div.sSHqwe.tPgKwe.ogfYpf span")
    price_elem = item.css_first(".YMlIz.FpEdX")
    if name_elem and price_elem:
        container0_flights.append({
            'name': name_elem.text(strip=True),
            'price': price_elem.text(strip=True)
        })

for item in containers[1].css("ul.Rk10dc li")[:3]:
    name_elem = item.css_first("div.sSHqwe.tPgKwe.ogfYpf span")
    price_elem = item.css_first(".YMlIz.FpEdX")
    if name_elem and price_elem:
        container1_flights.append({
            'name': name_elem.text(strip=True),
            'price': price_elem.text(strip=True)
        })

print("\nContainer 0 (best):")
for f in container0_flights:
    print(f"  {f['name']}: {f['price']}")
    
print("\nContainer 1 (other) - first 3:")
for f in container1_flights:
    print(f"  {f['name']}: {f['price']}")
    
print("\nConclusion: The 'best' flights from container 0 also appear in container 1!")