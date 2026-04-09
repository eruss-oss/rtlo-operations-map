"""
Update all supplier JSON files with verified changes.
Run once to geocode and save all new/changed entries.
"""
import json, requests, time, os

WORK_DIR = '/home/ubuntu/rtlo-map'
MAPBOX_TOKEN = 'pk.eyJ1IjoiZXJ1c3Nub2Z1c3MiLCJhIjoiY21ubTRlemtrMTVrczJxcTcwbmk2dnRtOCJ9.zPPUauWOdG2LpSv5q8ZJ1g'

def geocode(address):
    try:
        url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(address)}.json'
        params = {'access_token': MAPBOX_TOKEN, 'country': 'US', 'limit': 1}
        r = requests.get(url, params=params, timeout=10)
        feats = r.json().get('features', [])
        if feats:
            lon, lat = feats[0]['center']
            return lat, lon
    except Exception as e:
        print(f'Geocode error for {address}: {e}')
    return None, None

def load(path):
    try:
        return json.load(open(path))
    except:
        return []

def save(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f'Saved {len(data)} entries to {path}')

# ─── 1. HARDSCAPE: Remove Durango plant, add Belgard Solution Center ──────────
hardscape = load(f'{WORK_DIR}/hardscape_stores.json')
# Remove 2802 W Durango St manufacturing plant
hardscape = [s for s in hardscape if '2802' not in s.get('address', '') and 'durango' not in s.get('address', '').lower()]
# Check if Belgard Solution Center already there
if not any('belgard' in s.get('name','').lower() and 'solution' in s.get('name','').lower() for s in hardscape):
    lat, lon = geocode('1919 W Fairmont Dr Suite 5, Tempe, AZ 85282')
    time.sleep(0.3)
    hardscape.append({
        'name': 'Belgard Solution Center',
        'address': '1919 W Fairmont Dr Suite 5, Tempe, AZ 85282',
        'phone': '(770) 828-5941',
        'website': 'belgard.com',
        'showroom': True,
        'notes': 'Oldcastle APG Solutions Center — full Belgard product showroom with outdoor displays',
        'lat': lat, 'lon': lon
    })
    print(f'Added Belgard Solution Center: {lat}, {lon}')
save(f'{WORK_DIR}/hardscape_stores.json', hardscape)

# ─── 2. SITEONE: Add Pioneer at 1639 E Deer Valley Dr (former Telluride) ──────
siteone = load(f'{WORK_DIR}/siteone_stores.json')
# Remove any existing Telluride entry
siteone = [s for s in siteone if 'telluride' not in s.get('name','').lower()]
# Add Pioneer at Deer Valley if not already there
if not any('deer valley' in s.get('address','').lower() and 'pioneer' in s.get('name','').lower() for s in siteone):
    lat, lon = geocode('1639 E Deer Valley Dr, Phoenix, AZ 85024')
    time.sleep(0.3)
    siteone.append({
        'name': 'Pioneer Landscape Centers - Deer Valley',
        'address': '1639 E Deer Valley Dr, Phoenix, AZ 85024',
        'phone': '(480) 398-2999',
        'website': 'pioneerco.com',
        'showroom': True,
        'notes': 'Former Telluride Natural Stone — now Pioneer/SiteOne. Showroom with stone and hardscape display.',
        'lat': lat, 'lon': lon
    })
    print(f'Added Pioneer Deer Valley: {lat}, {lon}')
save(f'{WORK_DIR}/siteone_stores.json', siteone)

# ─── 3. ROCK: Add MDI Rock Queen Creek / San Tan Valley ───────────────────────
rock = load(f'{WORK_DIR}/rock_stores.json')
if not any('san tan' in s.get('address','').lower() or ('mdi' in s.get('name','').lower() and 'queen' in s.get('name','').lower()) for s in rock):
    lat, lon = geocode('1566 W Ocotillo Rd, San Tan Valley, AZ 85140')
    time.sleep(0.3)
    rock.append({
        'name': 'MDI Rock - Queen Creek / San Tan Valley',
        'address': '1566 W Ocotillo Rd, San Tan Valley, AZ 85140',
        'phone': '(480) 888-0487',
        'website': 'mdirock.com',
        'showroom': False,
        'notes': 'East Valley MDI Rock location. Open to public. Best for boulders + client visits.',
        'lat': lat, 'lon': lon
    })
    print(f'Added MDI Rock Queen Creek: {lat}, {lon}')
save(f'{WORK_DIR}/rock_stores.json', rock)

# ─── 4. FLOOR & DECOR: Add Tempe location ─────────────────────────────────────
floor_decor = load(f'{WORK_DIR}/floor_decor_stores.json')
if not any('tempe' in s.get('address','').lower() or 'priest' in s.get('address','').lower() for s in floor_decor):
    lat, lon = geocode('7500 S Priest Dr, Tempe, AZ 85283')
    time.sleep(0.3)
    floor_decor.append({
        'name': 'Floor & Decor - Tempe',
        'address': '7500 S Priest Dr, Tempe, AZ 85283',
        'phone': '(480) 838-3046',
        'website': 'flooranddecor.com',
        'showroom': True,
        'notes': 'Full tile, stone, and hardwood selection',
        'lat': lat, 'lon': lon
    })
    print(f'Added Floor & Decor Tempe: {lat}, {lon}')
save(f'{WORK_DIR}/floor_decor_stores.json', floor_decor)

# ─── 5. TILE: Fix QDI Surfaces to Scottsdale address ─────────────────────────
tile = load(f'{WORK_DIR}/tile_stores.json')
for s in tile:
    if 'qdi' in s.get('name','').lower():
        old_addr = s.get('address','')
        s['address'] = '15678 N Greenway Hayden Loop, Scottsdale, AZ 85254'
        s['name'] = 'QDI Surfaces - Scottsdale'
        lat, lon = geocode('15678 N Greenway Hayden Loop, Scottsdale, AZ 85254')
        time.sleep(0.3)
        s['lat'] = lat
        s['lon'] = lon
        print(f'Fixed QDI Surfaces: {old_addr} -> {s["address"]} ({lat}, {lon})')
save(f'{WORK_DIR}/tile_stores.json', tile)

# ─── 6. NURSERIES: Create new JSON ────────────────────────────────────────────
nursery_raw = [
    {'name': 'Aird Nursery', 'address': '1811 E Northern Ave, Phoenix, AZ 85020', 'phone': '', 'website': 'airdnursery.com', 'notes': 'Strong for curated material — Preferred'},
    {'name': 'Whitfill Nursery', 'address': '824 E Glendale Ave, Phoenix, AZ 85021', 'phone': '(602) 944-8479', 'website': 'whitfillnursery.com', 'notes': 'Best all-around — Preferred'},
    {'name': 'Moon Valley Nurseries', 'address': '18047 N Tatum Blvd, Phoenix, AZ 85032', 'phone': '(480) 374-3964', 'website': 'moonvalley.com', 'notes': 'Specimen trees — Secondary'},
    {'name': 'Sun Valley Nursery', 'address': '11416 E Desert Cove Ave, Scottsdale, AZ 85259', 'phone': '(480) 767-1800', 'website': 'sunvalleynursery.com', 'notes': 'Clean selection — Secondary'},
    {'name': 'SummerWinds Nursery', 'address': '17826 N Tatum Blvd, Phoenix, AZ 85032', 'phone': '', 'website': 'summerwindsnursery.com', 'notes': 'Retail-friendly — Secondary'},
]
nurseries = []
for n in nursery_raw:
    lat, lon = geocode(n['address'])
    time.sleep(0.3)
    nurseries.append({**n, 'showroom': False, 'lat': lat, 'lon': lon})
    print(f'Geocoded {n["name"]}: {lat}, {lon}')
save(f'{WORK_DIR}/nursery_stores.json', nurseries)

# ─── 7. PLUMBING: Create new JSON ─────────────────────────────────────────────
plumbing_raw = [
    {'name': 'Studio 44 Design', 'address': '8924 E Pinnacle Peak Rd Suite G5, Scottsdale, AZ 85255', 'phone': '(602) 309-4161', 'website': 'studio44design.com', 'notes': 'High-end curated interior design + plumbing showroom — Preferred'},
    {'name': 'Kohler Signature Store', 'address': '4513 N Scottsdale Rd Suite 116, Scottsdale, AZ 85251', 'phone': '(480) 397-2021', 'website': 'kohler.com', 'notes': 'Premium Kohler fixtures, Kallista, Robern, Ann Sacks — Preferred'},
    {'name': 'Ferguson Home - Scottsdale', 'address': '15000 N Hayden Rd, Scottsdale, AZ 85260', 'phone': '(480) 556-0103', 'website': 'fergusonhome.com', 'notes': 'Bath, kitchen & lighting showroom — Preferred'},
    {'name': 'Ferguson Home - Mesa', 'address': '3426 E Baseline Rd, Mesa, AZ 85204', 'phone': '(480) 444-5000', 'website': 'fergusonhome.com', 'notes': 'Bath, kitchen & lighting showroom — Preferred'},
    {'name': 'Central Arizona Supply - Scottsdale', 'address': '16431 N 90th St, Scottsdale, AZ 85260', 'phone': '(480) 922-9191', 'website': 'centralazsupply.com', 'notes': 'Contractor plumbing supply + showroom — Preferred'},
    {'name': 'Facets of Arizona', 'address': '9780 W Northern Ave Suite 1120, Peoria, AZ 85345', 'phone': '(623) 220-0704', 'website': 'facetsaz.com', 'notes': 'Ultra high-end decorative plumbing + hardware showroom — Specialty'},
]
plumbing = []
for p in plumbing_raw:
    lat, lon = geocode(p['address'])
    time.sleep(0.3)
    plumbing.append({**p, 'showroom': True, 'lat': lat, 'lon': lon})
    print(f'Geocoded {p["name"]}: {lat}, {lon}')
save(f'{WORK_DIR}/plumbing_stores.json', plumbing)

print('\nAll supplier files updated successfully.')
