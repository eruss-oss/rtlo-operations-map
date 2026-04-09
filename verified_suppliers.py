"""
Verified supplier addresses from official websites - April 2026
All addresses manually confirmed from official business websites or Yelp/Google Maps
"""

import json, requests, time
from urllib.parse import quote

MAPBOX_TOKEN = 'pk.eyJ1IjoiZXJ1c3Nub2Z1c3MiLCJhIjoiY21ubTRlemtrMTVrczJxcTcwbmk2dnRtOCJ9.zPPUauWOdG2LpSv5q8ZJ1g'

def geocode(address):
    url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(address)}.json'
    params = {'access_token': MAPBOX_TOKEN, 'country': 'US', 'limit': 1}
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data.get('features'):
            coords = data['features'][0]['geometry']['coordinates']
            return {'lng': coords[0], 'lat': coords[1]}
    except Exception as e:
        print(f"    Error: {e}")
    return None

# ─── TURF SUPPLIERS ───────────────────────────────────────────────────────────
turf_suppliers = [
    # SGW / Synthetic Grass Warehouse - verified from syntheticgrasswarehouse.com
    {"name": "Synthetic Grass Warehouse - Glendale", "address": "5700 N 101st Ave, Glendale, AZ 85307"},
    {"name": "Synthetic Grass Warehouse - Gilbert",  "address": "4465 E Nunneley Rd, Gilbert, AZ 85296"},
    # Verde Valley Turf - verified from vvturf.com
    {"name": "Verde Valley Turf - Phoenix",     "address": "430 N 47th Ave, Phoenix, AZ 85043"},
    {"name": "Verde Valley Turf - Queen Creek", "address": "18698 E Business Park Dr, Queen Creek, AZ 85142"},
    # Turf Hub - verified from turfhub.com/contact
    {"name": "Turf Hub - Chandler",  "address": "1725 E Germann Rd, Chandler, AZ 85286"},
    {"name": "Turf Hub - Phoenix",   "address": "180 W Pinnacle Peak Rd, Phoenix, AZ 85027"},
    {"name": "Turf Hub - Peoria",    "address": "9700 N 91st Ave, Peoria, AZ 85345"},
    # No Limit Turf - verified from nolimitturf.com
    {"name": "No Limit Turf - Mesa", "address": "8305 E Sebring Ave, Mesa, AZ 85212"},
    # Turf Sellers - verified from turfsellersaz.com / Yelp
    {"name": "Turf Sellers - Phoenix", "address": "405 N 75th Ave, Phoenix, AZ 85043"},
]

# ─── ROCK & AGGREGATE ─────────────────────────────────────────────────────────
rock_suppliers = [
    # MDI Rock - verified from mdirock.com/locations
    {"name": "MDI Rock - Phoenix",     "address": "2815 E Rose Garden Ln, Phoenix, AZ 85050"},
    # Carso / Karso Landscape Supply - verified from karsolandscapesupplies.com
    {"name": "Carso Landscape Supply - Sun City", "address": "10701 W Hatfield Rd, Sun City, AZ 85373"},
    # QDI Surfaces - verified from Yelp
    {"name": "QDI Surfaces - Phoenix", "address": "2633 N 24th Dr, Phoenix, AZ 85009"},
    # A&A Materials - address provided directly by user
    {"name": "A&A Materials - Scottsdale", "address": "10333 E McDowell Rd, Scottsdale, AZ 85256"},
    # ABC Sand & Rock - verified from abcsandrock.com/contact-us
    {"name": "ABC Sand & Rock - Phoenix", "address": "1804 N 27th Ave, Phoenix, AZ 85009"},
    # A-1 Materials - verified from a-1materialsrocksupply.com
    {"name": "A-1 Materials - Tolleson", "address": "9503 W Buckeye Rd, Tolleson, AZ 85353"},
    # J&J Landscaping Material - verified from jandjmaterialsinc.com
    {"name": "J&J Landscaping Material - Mesa", "address": "5000 E McKellips Rd, Mesa, AZ 85215"},
    # The Stone Yard - verified from Yelp / thestoneyardaz.com (TWO locations)
    {"name": "The Stone Yard - North Phoenix", "address": "1739 W Park View Ln, Phoenix, AZ 85085"},
    {"name": "The Stone Yard - NE Phoenix",    "address": "450 E Pinnacle Peak Rd, Phoenix, AZ 85024"},
]

# ─── TILE & STONE ─────────────────────────────────────────────────────────────
tile_suppliers = [
    # Bedrosians - verified from bedrosians.com (showroom)
    {"name": "Bedrosians Tile & Stone - Phoenix", "address": "2946 E Broadway Rd, Phoenix, AZ 85040", "showroom": True},
    # Cholla Tile - verified from chollatile.com/contact-us (TWO locations)
    {"name": "Cholla Tile - Mesa",    "address": "4340 S 80th St, Mesa, AZ 85212"},
    {"name": "Cholla Tile - Glendale","address": "5455 W Montebello Ave, Glendale, AZ 85301"},
    # Monterey Tile - verified from monterreytile.com/contact-us (showroom)
    {"name": "Monterey Tile - Phoenix", "address": "3232 S 48th St, Phoenix, AZ 85040", "showroom": True},
    # MSI Surfaces - verified from msisurfaces.com/phoenix
    {"name": "MSI Surfaces - Phoenix", "address": "4405 W Roosevelt St, Phoenix, AZ 85043"},
    # Floor & Decor - verified from flooranddecor.com/stores
    {"name": "Floor & Decor - Phoenix",    "address": "1800 E Highland Ave, Phoenix, AZ 85016"},
    {"name": "Floor & Decor - Chandler",   "address": "1901 E Northrop Blvd, Chandler, AZ 85286"},
    {"name": "Floor & Decor - Glendale",   "address": "5880 W Bell Rd, Glendale, AZ 85308"},
    {"name": "Floor & Decor - Scottsdale", "address": "15515 N Hayden Rd, Scottsdale, AZ 85260"},
]

# ─── COUNTERTOP & SLAB ────────────────────────────────────────────────────────
slab_suppliers = [
    # The Yard - address provided directly by user, confirmed on theyardaz.com
    {"name": "The Yard - Stone Slabs & Remnants", "address": "21846 N 21st Ave, Phoenix, AZ 85027"},
    # Arista Stones - address provided directly by user, confirmed on aristastones.com
    {"name": "Arista Stones - Tempe", "address": "695 W Elliot Rd, Tempe, AZ 85284"},
]

# ─── OTHER SUPPLIERS ──────────────────────────────────────────────────────────
other_suppliers = [
    # RWC Building Products - verified from rwc.org/locations (3 Phoenix metro locations)
    {"name": "RWC Building Products - Phoenix",    "address": "1918 W Grant St, Phoenix, AZ 85009"},
    {"name": "RWC Building Products - Scottsdale", "address": "7475 E Williams Dr, Scottsdale, AZ 85255"},
    {"name": "RWC Building Products - Mesa",       "address": "1345 S Center St, Mesa, AZ 85210"},
]

all_layers = {
    "turf_stores":  turf_suppliers,
    "rock_stores":  rock_suppliers,
    "tile_stores":  tile_suppliers,
    "slab_stores":  slab_suppliers,
    "other_stores": other_suppliers,
}

print("Geocoding all verified supplier addresses...")
for layer_name, suppliers in all_layers.items():
    geocoded = []
    for s in suppliers:
        coords = geocode(s["address"])
        if coords:
            entry = {
                "name":    s["name"],
                "address": s["address"],
                "lat":     coords["lat"],
                "lng":     coords["lng"],
            }
            if s.get("showroom"):
                entry["showroom"] = True
            geocoded.append(entry)
            print(f"  ✓ {s['name']}")
        else:
            print(f"  ✗ FAILED: {s['name']} @ {s['address']}")
        time.sleep(0.15)
    
    out_path = f"/home/ubuntu/rtlo-map/{layer_name}.json"
    with open(out_path, "w") as f:
        json.dump(geocoded, f, indent=2)
    print(f"  → Saved {len(geocoded)} entries to {layer_name}.json\n")

print("Done. All supplier JSON files updated.")
