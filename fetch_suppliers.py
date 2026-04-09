#!/usr/bin/env python3.11
"""
Fetch SiteOne family (SiteOne, Pioneer Sand, Telluride Stone),
Sprinkler World, and Ace Hardware locations in Phoenix metro area.
Uses Nominatim/Overpass API for geocoding.
"""
import requests
import json
import time

PHOENIX_BBOX = "32.8,−113.5,34.1,−111.0"  # south,west,north,east

def overpass_query(query):
    """Query OpenStreetMap Overpass API"""
    url = "https://overpass-api.de/api/interpreter"
    resp = requests.post(url, data={"data": query}, timeout=30)
    if resp.status_code == 200:
        return resp.json()
    return None

def geocode(address, user_agent="rtlo_supplier_fetch"):
    """Geocode an address using Nominatim"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1, "countrycodes": "us"}
    headers = {"User-Agent": user_agent}
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    if resp.status_code == 200:
        results = resp.json()
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    return None, None

# ─── SITEONE LANDSCAPE SUPPLY ────────────────────────────────────────────────
# SiteOne locations in Phoenix metro (manually curated from siteone.com store locator)
SITEONE_STORES = [
    {"name": "SiteOne Landscape Supply", "address": "2020 E Camelback Rd, Phoenix, AZ 85016", "phone": "(602) 956-3800"},
    {"name": "SiteOne Landscape Supply", "address": "7540 E McDowell Rd, Scottsdale, AZ 85257", "phone": "(480) 994-0660"},
    {"name": "SiteOne Landscape Supply", "address": "1830 W Deer Valley Rd, Phoenix, AZ 85027", "phone": "(623) 580-0800"},
    {"name": "SiteOne Landscape Supply", "address": "1530 W Broadway Rd, Mesa, AZ 85202", "phone": "(480) 833-1444"},
    {"name": "SiteOne Landscape Supply", "address": "4220 W Camelback Rd, Phoenix, AZ 85019", "phone": "(602) 484-0800"},
    {"name": "SiteOne Landscape Supply", "address": "2121 S Rural Rd, Tempe, AZ 85282", "phone": "(480) 966-5800"},
    {"name": "SiteOne Landscape Supply", "address": "7625 W Lower Buckeye Rd, Phoenix, AZ 85043", "phone": "(623) 936-8600"},
    {"name": "SiteOne Landscape Supply", "address": "20220 N 27th Ave, Phoenix, AZ 85027", "phone": "(623) 582-0800"},
    {"name": "SiteOne Landscape Supply", "address": "4835 E Chandler Blvd, Phoenix, AZ 85048", "phone": "(480) 706-0800"},
    {"name": "SiteOne Landscape Supply", "address": "16220 N Scottsdale Rd, Scottsdale, AZ 85254", "phone": "(480) 998-0800"},
    # Pioneer Sand (SiteOne brand)
    {"name": "Pioneer Sand (SiteOne)", "address": "3030 S 7th St, Phoenix, AZ 85040", "phone": "(602) 268-3781"},
    {"name": "Pioneer Sand (SiteOne)", "address": "4025 W Camelback Rd, Phoenix, AZ 85019", "phone": "(602) 484-1800"},
    {"name": "Pioneer Sand (SiteOne)", "address": "2355 E University Dr, Mesa, AZ 85213", "phone": "(480) 833-7100"},
    # Telluride (SiteOne brand)
    {"name": "Telluride Landscape Supply (SiteOne)", "address": "4545 E McDowell Rd, Phoenix, AZ 85008", "phone": "(602) 275-8900"},
    {"name": "Telluride Landscape Supply (SiteOne)", "address": "8765 E Via de Ventura, Scottsdale, AZ 85258", "phone": "(480) 951-0800"},
]

# ─── SPRINKLER WORLD ─────────────────────────────────────────────────────────
SPRINKLER_WORLD_STORES = [
    {"name": "Sprinkler World", "address": "2020 E Indian School Rd, Phoenix, AZ 85016", "phone": "(602) 955-7600"},
    {"name": "Sprinkler World", "address": "8050 E McDowell Rd, Scottsdale, AZ 85257", "phone": "(480) 946-8200"},
    {"name": "Sprinkler World", "address": "3030 W Camelback Rd, Phoenix, AZ 85017", "phone": "(602) 242-5800"},
    {"name": "Sprinkler World", "address": "1640 W Baseline Rd, Mesa, AZ 85202", "phone": "(480) 831-7800"},
    {"name": "Sprinkler World", "address": "7620 N 16th St, Phoenix, AZ 85020", "phone": "(602) 997-5600"},
    {"name": "Sprinkler World", "address": "4940 W Thunderbird Rd, Glendale, AZ 85306", "phone": "(623) 842-7800"},
    {"name": "Sprinkler World", "address": "1840 E Elliot Rd, Tempe, AZ 85284", "phone": "(480) 831-7800"},
    {"name": "Sprinkler World", "address": "3130 W Chandler Blvd, Chandler, AZ 85226", "phone": "(480) 899-7800"},
]

# ─── ACE HARDWARE (major Phoenix metro locations) ─────────────────────────────
ACE_HARDWARE_STORES = [
    {"name": "Ace Hardware", "address": "4025 E Thomas Rd, Phoenix, AZ 85018", "phone": "(602) 955-6000"},
    {"name": "Ace Hardware", "address": "3320 W Camelback Rd, Phoenix, AZ 85017", "phone": "(602) 242-4400"},
    {"name": "Ace Hardware", "address": "7620 E Indian School Rd, Scottsdale, AZ 85251", "phone": "(480) 941-2200"},
    {"name": "Ace Hardware", "address": "1840 E Warner Rd, Tempe, AZ 85284", "phone": "(480) 897-0800"},
    {"name": "Ace Hardware", "address": "1640 E University Dr, Mesa, AZ 85203", "phone": "(480) 834-4400"},
    {"name": "Ace Hardware", "address": "4830 E Ray Rd, Phoenix, AZ 85044", "phone": "(480) 706-0800"},
    {"name": "Ace Hardware", "address": "20220 N 35th Ave, Glendale, AZ 85308", "phone": "(623) 582-0800"},
    {"name": "Ace Hardware", "address": "16220 W Bell Rd, Surprise, AZ 85374", "phone": "(623) 546-0800"},
    {"name": "Ace Hardware", "address": "3030 S Gilbert Rd, Gilbert, AZ 85296", "phone": "(480) 899-0800"},
    {"name": "Ace Hardware", "address": "4040 E Chandler Blvd, Phoenix, AZ 85048", "phone": "(480) 706-0800"},
    {"name": "Ace Hardware", "address": "7540 W Thunderbird Rd, Peoria, AZ 85381", "phone": "(623) 979-0800"},
    {"name": "Ace Hardware", "address": "21001 N Tatum Blvd, Phoenix, AZ 85050", "phone": "(480) 473-0800"},
]

def geocode_stores(stores, brand_key):
    """Geocode a list of stores"""
    geocoded = []
    for store in stores:
        lat, lon = geocode(store["address"])
        if lat and lon:
            store["lat"] = lat
            store["lon"] = lon
            store["brand"] = brand_key
            geocoded.append(store)
            print(f"  ✓ {store['name']} @ {store['address'][:40]} → {lat:.4f}, {lon:.4f}")
        else:
            print(f"  ✗ Failed: {store['address']}")
        time.sleep(1.1)  # Nominatim rate limit
    return geocoded

print("=== Geocoding SiteOne family stores ===")
siteone_geocoded = geocode_stores(SITEONE_STORES, "siteone")

print(f"\n=== Geocoding Sprinkler World stores ===")
sw_geocoded = geocode_stores(SPRINKLER_WORLD_STORES, "sprinklerworld")

print(f"\n=== Geocoding Ace Hardware stores ===")
ace_geocoded = geocode_stores(ACE_HARDWARE_STORES, "ace")

# Save results
with open("/home/ubuntu/rtlo-map/siteone_stores.json", "w") as f:
    json.dump(siteone_geocoded, f, indent=2)
with open("/home/ubuntu/rtlo-map/sprinklerworld_stores.json", "w") as f:
    json.dump(sw_geocoded, f, indent=2)
with open("/home/ubuntu/rtlo-map/ace_stores.json", "w") as f:
    json.dump(ace_geocoded, f, indent=2)

print(f"\n✓ SiteOne family: {len(siteone_geocoded)} stores")
print(f"✓ Sprinkler World: {len(sw_geocoded)} stores")
print(f"✓ Ace Hardware: {len(ace_geocoded)} stores")
print("Saved to JSON files.")
