#!/usr/bin/env python3.11
"""
Geocode all new vendor locations for RTLO map.
Layers: turf, rock_aggregate, tile_stone, countertop_slab, other_suppliers
"""
import json, requests, time

MAPBOX_TOKEN = 'pk.eyJ1IjoiZXJ1c3Nub2Z1c3MiLCJhIjoiY21ubTRlemtrMTVrczJxcTcwbmk2dnRtOCJ9.zPPUauWOdG2LpSv5q8ZJ1g'

def geocode(address, hint='Phoenix, AZ'):
    try:
        full = f'{address}, {hint}' if hint not in address else address
        url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(full)}.json'
        params = {'access_token': MAPBOX_TOKEN, 'country': 'US', 'bbox': '-114,31.5,-109,35', 'limit': 1}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get('features'):
            f = data['features'][0]
            return f['center'][0], f['center'][1], f['place_name']
    except Exception as e:
        print(f'  Geocode error for "{address}": {e}')
    return None, None, None

# ─── VENDOR DATA ─────────────────────────────────────────────────────────────
# Format: (name, address_or_hint, showroom=False)

TURF = [
    ('No Limit Turf', '4802 E Camelback Rd, Phoenix, AZ'),
    ('Turf Hub', '2020 W Lone Cactus Dr, Phoenix, AZ'),
    ('SGW (Southwest Greens)', '2150 W Pinnacle Peak Rd, Phoenix, AZ'),
    ('Turf Resellers', '3125 S 52nd St, Tempe, AZ'),
    ('Verde Valley Turf', '2255 E Germann Rd, Chandler, AZ'),
]

ROCK_AGGREGATE = [
    ('MDI Rock', '3030 S 7th St, Phoenix, AZ'),
    ('Carso Rock & Landscape Supply', '4110 W Lower Buckeye Rd, Phoenix, AZ'),
    ('QDI Surfaces', '4455 E Camelback Rd, Phoenix, AZ'),
    ('A&A Materials', '3625 W McDowell Rd, Phoenix, AZ'),
    ('ABC Sand & Rock', '4530 E Broadway Rd, Mesa, AZ'),
    ('A1 Materials', '3030 N 35th Ave, Phoenix, AZ'),
    ('J&J Landscaping Supply', '1830 S Country Club Dr, Mesa, AZ'),
]

TILE_STONE = [
    ('Bedrosians Tile & Stone', '4550 E Bell Rd, Phoenix, AZ', True),
    ('Cholla Tile', '2020 E McDowell Rd, Phoenix, AZ'),
    ('Monterey Tile', '1550 E Glendale Ave, Phoenix, AZ', True),
    ('MSI Surfaces', '4455 E Camelback Rd Ste 100, Phoenix, AZ'),
    ('The Stone Yard', '2345 W Buckeye Rd, Phoenix, AZ'),
    ('Floor & Decor', '1616 W Bethany Home Rd, Phoenix, AZ'),
    ('Floor & Decor', '2727 S Market St, Gilbert, AZ'),
    ('Floor & Decor', '16757 N 83rd Ave, Peoria, AZ'),
]

COUNTERTOP_SLAB = [
    ('The Yard (Slab)', '21846 N 21st Ave, Phoenix, AZ'),
    ('Arista Stone', '695 W Elliott Rd, Tempe, AZ'),
    ('MSI Slab Gallery', '4455 E Camelback Rd, Phoenix, AZ'),
]

OTHER_SUPPLIERS = [
    ('RWC Group', '4041 N Central Ave, Phoenix, AZ'),
    ('RWC Group - East Valley', '1550 E Warner Rd, Tempe, AZ'),
    ('RWC Group - North Scottsdale', '7500 E McCormick Pkwy, Scottsdale, AZ'),
]

def build_layer(vendors, layer_key):
    results = []
    for entry in vendors:
        name = entry[0]
        address = entry[1]
        showroom = entry[2] if len(entry) > 2 else False
        print(f'  Geocoding: {name}')
        lon, lat, place = geocode(address)
        if lat:
            results.append({
                'name': name,
                'address': address,
                'place_name': place,
                'lat': lat,
                'lon': lon,
                'layer': layer_key,
                'showroom': showroom
            })
            print(f'    ✓ {lat:.4f}, {lon:.4f}')
        else:
            print(f'    ✗ Failed to geocode')
        time.sleep(0.3)
    return results

print('Building Turf layer...')
turf = build_layer(TURF, 'turf')

print('Building Rock/Aggregate layer...')
rock = build_layer(ROCK_AGGREGATE, 'rock_aggregate')

print('Building Tile/Stone layer...')
tile = build_layer(TILE_STONE, 'tile_stone')

print('Building Countertop/Slab layer...')
slab = build_layer(COUNTERTOP_SLAB, 'countertop_slab')

print('Building Other Suppliers layer...')
other = build_layer(OTHER_SUPPLIERS, 'other_suppliers')

# Save each layer
import os
base = '/home/ubuntu/rtlo-map'
with open(f'{base}/turf_stores.json', 'w') as f: json.dump(turf, f, indent=2)
with open(f'{base}/rock_stores.json', 'w') as f: json.dump(rock, f, indent=2)
with open(f'{base}/tile_stores.json', 'w') as f: json.dump(tile, f, indent=2)
with open(f'{base}/slab_stores.json', 'w') as f: json.dump(slab, f, indent=2)
with open(f'{base}/other_stores.json', 'w') as f: json.dump(other, f, indent=2)

print(f'\nDone! Turf:{len(turf)} Rock:{len(rock)} Tile:{len(tile)} Slab:{len(slab)} Other:{len(other)}')
