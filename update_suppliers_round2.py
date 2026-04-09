#!/usr/bin/env python3.11
"""
Supplier JSON update script - Round 2
All changes confirmed by user before running.
"""
import json, requests, time, os

WORK_DIR = '/home/ubuntu/rtlo-map'
NOMINATIM = 'https://nominatim.openstreetmap.org/search'
HEADERS = {'User-Agent': 'RTLO-Map-Builder/1.0 (eruss@rtloaz.com)'}

def geocode(address):
    try:
        r = requests.get(NOMINATIM, params={'q': address, 'format': 'json', 'limit': 1, 'countrycodes': 'us'}, headers=HEADERS, timeout=10)
        results = r.json()
        if results:
            return float(results[0]['lat']), float(results[0]['lon'])
    except Exception as e:
        print(f'  Geocode error for {address}: {e}')
    return None, None

def load(fname):
    path = os.path.join(WORK_DIR, fname)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

def save(fname, data):
    path = os.path.join(WORK_DIR, fname)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'  Saved {fname} ({len(data)} entries)')

# ─── 1. ROCK & AGGREGATE: Remove Stone Yard NE Phoenix (Pinnacle Peak) ───────
print('1. Updating rock_stores.json...')
rock = load('rock_stores.json')
before = len(rock)
rock = [s for s in rock if '450 E Pinnacle Peak' not in s.get('address', '')]
print(f'  Removed {before - len(rock)} entry (Stone Yard NE Phoenix)')
save('rock_stores.json', rock)
time.sleep(1)

# ─── 2. SITEONE: Add Arizona Stone Brick Pavers (both locations) ─────────────
print('2. Updating siteone_stores.json...')
siteone = load('siteone_stores.json')
# Remove any existing Arizona Stone Brick Pavers entries to avoid duplicates
siteone = [s for s in siteone if 'Arizona Stone Brick' not in s.get('name', '')]

asbp_entries = [
    {'name': 'Arizona Stone Brick Pavers', 'address': '12473 N 92nd Dr, Peoria, AZ 85381', 'showroom': True, 'notes': 'Natural stone, pavers, and hardscape materials. Showroom.', 'phone': '(623) 878-5080'},
    {'name': 'Arizona Stone Brick Pavers', 'address': '4502 E Virginia St, Mesa, AZ 85215', 'showroom': True, 'notes': 'Natural stone, pavers, and hardscape materials. Showroom.', 'phone': '(480) 641-1042'},
]
for entry in asbp_entries:
    lat, lon = geocode(entry['address'])
    entry['lat'] = lat
    entry['lon'] = lon
    print(f"  Geocoded {entry['name']} ({entry['address']}): {lat}, {lon}")
    time.sleep(1.2)
    siteone.append(entry)
save('siteone_stores.json', siteone)

# ─── 3. NURSERIES: Add V&P Nurseries ─────────────────────────────────────────
print('3. Updating nursery_stores.json...')
nursery = load('nursery_stores.json')
nursery = [s for s in nursery if 'V&P' not in s.get('name', '') and 'VNP' not in s.get('name', '')]
vnp = {'name': 'V&P Nurseries', 'address': '21919 E Germann Rd, Queen Creek, AZ 85142', 'showroom': False, 'notes': 'Wholesale plant nursery. Drought-tolerant and subtropical varieties. Landscape professionals.'}
lat, lon = geocode(vnp['address'])
vnp['lat'] = lat; vnp['lon'] = lon
print(f"  Geocoded V&P Nurseries: {lat}, {lon}")
time.sleep(1.2)
nursery.append(vnp)
save('nursery_stores.json', nursery)

# ─── 4. ACE HARDWARE: Add True Value locations ────────────────────────────────
print('4. Updating ace_stores.json...')
ace = load('ace_stores.json')
# Remove any existing True Value entries to avoid duplicates
ace = [s for s in ace if 'True Value' not in s.get('name', '') and 'ADR Hardware' not in s.get('name', '')]
true_value = [
    {'name': 'Sun City True Value', 'address': '15400 N 99th Ave, Sun City, AZ 85351', 'showroom': False, 'notes': 'True Value hardware store.', 'phone': '(623) 815-5200'},
    {'name': 'Sunwest True Value', 'address': '13599 W Camino Del Sol, Sun City West, AZ 85375', 'showroom': False, 'notes': 'True Value hardware store.', 'phone': '(623) 584-7888'},
    {'name': 'ADR Hardware (True Value)', 'address': '237 N Apache Trail, Apache Junction, AZ 85120', 'showroom': False, 'notes': 'True Value hardware store.', 'phone': '(480) 982-7461'},
]
for entry in true_value:
    lat, lon = geocode(entry['address'])
    entry['lat'] = lat; entry['lon'] = lon
    print(f"  Geocoded {entry['name']}: {lat}, {lon}")
    time.sleep(1.2)
    ace.append(entry)
save('ace_stores.json', ace)

# ─── 5. MISCELLANEOUS: Add Cholla Tile, Imperial Wholesale, Universal White Cement, ANS Mermer ──
print('5. Updating misc_stores.json...')
misc = load('misc_stores.json')
# Remove any existing entries we're about to re-add
misc = [s for s in misc if s.get('name', '') not in ['Cholla Tile (Mesa)', 'Cholla Tile (Glendale)', 'Imperial Wholesale', 'Universal White Cement', 'ANS Mermer']]

misc_new = [
    {'name': 'Cholla Tile (Mesa)', 'address': '4340 S 80th St, Mesa, AZ 85212', 'showroom': True, 'notes': 'Tile showroom. Phone: (480) 991-1768'},
    {'name': 'Cholla Tile (Glendale)', 'address': '5455 W Montebello Ave, Glendale, AZ 85301', 'showroom': True, 'notes': 'Tile showroom. Phone: (480) 991-1768'},
    {'name': 'Imperial Wholesale', 'address': '9602 E Apache Trail, Mesa, AZ 85207', 'showroom': True, 'notes': '30,000 sq ft showroom. Flooring, countertops, backsplashes. Phone: (480) 986-6900'},
    {'name': 'Universal White Cement', 'address': '5610 W Maryland Ave, Glendale, AZ 85301', 'showroom': False, 'notes': 'Pool interior supply and distribution. Plaster blending facility.'},
    {'name': 'ANS Mermer', 'address': '2850 E Jones Ave, Phoenix, AZ 85040', 'showroom': False, 'notes': 'Closed to public. Visit for samples only. Natural stone and marble supplier.'},
]
for entry in misc_new:
    lat, lon = geocode(entry['address'])
    entry['lat'] = lat; entry['lon'] = lon
    print(f"  Geocoded {entry['name']}: {lat}, {lon}")
    time.sleep(1.2)
    misc.append(entry)
save('misc_stores.json', misc)

# ─── 6. POOL & FOUNTAIN: Create new pool_stores.json ─────────────────────────
print('6. Creating pool_stores.json...')
pool_entries = [
    {'name': 'NPT Pool Tile - Mesa', 'address': '7307 E Hampton Ave Ste 102, Mesa, AZ 85209', 'showroom': True, 'notes': 'National Pool Tile showroom. Mon-Fri 8am-3:30pm, Sat 8am-12pm. Phone: (480) 520-5242', 'water': True},
    {'name': 'NPT Pool Tile - Tempe', 'address': '2440 W University Dr, Tempe, AZ 85281', 'showroom': True, 'notes': 'National Pool Tile showroom. Mon-Fri 8am-3:30pm, Sat 8am-12pm. Phone: (480) 968-9929', 'water': True},
    {'name': 'NPT Pool Tile - West Phoenix', 'address': '640 N 43rd Ave #150, Phoenix, AZ 85009', 'showroom': True, 'notes': 'National Pool Tile showroom. Mon-Fri 8am-2:30pm, Sat 7am-11am. Phone: (602) 278-5179', 'water': True},
    {'name': 'SCP Distributors - Phoenix', 'address': '18201 N 25th Ave, Phoenix, AZ 85023', 'showroom': False, 'notes': 'Pool supply wholesale distributor.', 'water': True},
    {'name': 'SCP Distributors - Chandler', 'address': '261 N Roosevelt Ave, Chandler, AZ 85226', 'showroom': False, 'notes': 'Pool supply wholesale distributor.', 'water': True},
    {'name': 'SCP Distributors - Gilbert', 'address': '560 E Germann Rd, Gilbert, AZ 85297', 'showroom': False, 'notes': 'Pool supply wholesale distributor.', 'water': True},
    {'name': 'SCP Distributors - Mesa', 'address': '2350 W Broadway Rd Ste 110, Mesa, AZ 85202', 'showroom': False, 'notes': 'Pool supply wholesale distributor.', 'water': True},
    {'name': 'SCP Distributors - Scottsdale', 'address': '7841 E Gray Rd Ste A, Scottsdale, AZ 85260', 'showroom': False, 'notes': 'Pool supply wholesale distributor.', 'water': True},
    {'name': 'SCP Distributors - Tempe', 'address': '8945 S Harl Ave Ste 106, Tempe, AZ 85284', 'showroom': False, 'notes': 'Pool supply wholesale distributor.', 'water': True},
    {'name': 'Aquatec Fountains Inc', 'address': '13613 N 32nd St, Phoenix, AZ 85032', 'showroom': False, 'notes': 'Fountain contractor and supply. Design, construction, maintenance, repair. Phone: (602) 589-1000', 'water': True},
    {'name': 'Majestic Water Spouts', 'address': '940 S Park Lane Suite 2, Tempe, AZ 85281', 'showroom': False, 'notes': 'Water spouts, scuppers, and pool water features. Custom design available.', 'water': True},
]
pool = []
for entry in pool_entries:
    lat, lon = geocode(entry['address'])
    entry['lat'] = lat; entry['lon'] = lon
    print(f"  Geocoded {entry['name']}: {lat}, {lon}")
    time.sleep(1.2)
    pool.append(entry)
save('pool_stores.json', pool)

print('\nAll done! Verify counts above before rebuilding the map.')
