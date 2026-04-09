import requests, json, time

HEADERS = {"User-Agent": "RTLOMap/1.0 (eruss@rtloaz.com)"}

def geocode(address):
    url = "https://nominatim.openstreetmap.org/search"
    r = requests.get(url, params={"q": address, "format": "json", "limit": 1}, headers=HEADERS, timeout=10)
    results = r.json()
    if results:
        return float(results[0]["lat"]), float(results[0]["lon"])
    return None, None

addresses = [
    ("Arid Solutions Nursery",    "3815 E Southern Ave, Phoenix, AZ 85040"),
    ("Floor & Decor - Mesa",      "7022 E Hampton Ave, Mesa, AZ 85209"),
    ("Floor & Decor - Scottsdale","15515 N Hayden Rd, Scottsdale, AZ 85260"),
    ("ABC Sand & Rock - Glendale","5401 N 119th Ave, Glendale, AZ 85307"),
    ("Sonoran Lighting Supply",   "2920 E Mohawk Ln, Phoenix, AZ 85050"),
]

results = {}
for name, addr in addresses:
    lat, lng = geocode(addr)
    results[name] = {"lat": lat, "lng": lng, "address": addr}
    print(f"{name}: {lat}, {lng}")
    time.sleep(1.1)

# Floor & Decor Queen Creek - use coords from Google Maps URL
results["Floor & Decor - Queen Creek"] = {
    "lat": 33.391412, "lng": -111.6797212,
    "address": "Queen Creek / San Tan Valley, AZ"
}
print("Floor & Decor - Queen Creek: 33.391412, -111.6797212")

with open("/home/ubuntu/rtlo-map/new_coords.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved to new_coords.json")
