#!/usr/bin/env python3.11
"""
Build supplier JSON files from the RTLO Design Resource Directory.
Uses Mapbox geocoding for addresses. Produces JSON files ready for map injection.
"""
import json, requests, time, re

MAPBOX_TOKEN = 'pk.eyJ1IjoiZXJ1c3Nub2Z1c3MiLCJhIjoiY21ubTRlemtrMTVrczJxcTcwbmk2dnRtOCJ9.zPPUauWOdG2LpSv5q8ZJ1g'

def geocode(address):
    """Geocode an address using Mapbox, restricted to AZ bounding box."""
    url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(address)}.json'
    params = {
        'access_token': MAPBOX_TOKEN,
        'country': 'US',
        'bbox': '-114.5,31.5,-109.0,37.5',
        'limit': 1
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data.get('features'):
            coords = data['features'][0]['geometry']['coordinates']
            return coords[1], coords[0]  # lat, lon
    except Exception as e:
        print(f'  Geocode error for "{address}": {e}')
    return None, None

def build_entry(name, address, phone, website, notes, is_showroom=False, ranking=None):
    lat, lon = geocode(address)
    time.sleep(0.15)
    entry = {
        'name': name,
        'address': address,
        'phone': phone if phone and phone != '—' else '',
        'website': website if website and website != '—' else '',
        'notes': notes if notes else '',
        'showroom': is_showroom,
        'ranking': ranking or '',
        'lat': lat,
        'lon': lon
    }
    print(f'  {"★" if is_showroom else "◆"} {name} → {lat}, {lon}')
    return entry

# ─── HARDSCAPES / PAVERS / STONE (from directory - all showrooms) ─────────────
print('\n=== HARDSCAPES / STONE (showrooms) ===')
hardscape_stores = [
    build_entry('MSI Surfaces', '4405 W Roosevelt St, Phoenix, AZ 85009', '(602) 393-6330', 'msisurfaces.com', 'Large inventory, fast availability', is_showroom=True, ranking='Preferred'),
    build_entry('The Stone Collection', '4101 S 38th St, Phoenix, AZ 85040', '(602) 889-2067', 'thestonecollection.com', 'High-end curated slabs', is_showroom=True, ranking='Preferred'),
    build_entry('Durango Stone', '15550 N 84th St #105, Scottsdale, AZ 85260', '(602) 438-1001', 'durangostone.com', 'Luxury travertine/limestone', is_showroom=True, ranking='Preferred'),
    build_entry('Belgard Hardscapes', '2802 W Durango St, Phoenix, AZ 85009', '(602) 272-7211', 'belgard.com', 'Paver manufacturer showroom', is_showroom=True, ranking='Preferred'),
    build_entry('Pavestone', '1515 W Deer Valley Rd, Phoenix, AZ 85027', '(623) 580-1200', 'pavestone.com', 'Concrete paver supplier', is_showroom=False, ranking='Secondary'),
    build_entry('Telluride Stone (SiteOne)', '2514 E Indian School Rd, Phoenix, AZ 85016', '', 'siteone.com', 'SiteOne Stone Center - Indian School', is_showroom=True, ranking='Preferred'),
]
with open('/home/ubuntu/rtlo-map/hardscape_stores.json', 'w') as f:
    json.dump(hardscape_stores, f, indent=2)
print(f'Saved {len(hardscape_stores)} hardscape stores')

# ─── TILE / SLABS (from directory - all showrooms) ────────────────────────────
print('\n=== TILE / SLABS (showrooms) ===')
tile_stores = [
    build_entry('Monterrey Tile (Phoenix)', '3232 S 48th St #111, Phoenix, AZ 85040', '(480) 219-2494', 'monterreytile.com', 'Strongest showroom experience', is_showroom=True, ranking='Preferred'),
    build_entry('Monterrey Tile (Chandler)', '401 E Ray Rd, Chandler, AZ 85225', '(480) 855-6622', 'monterreytile.com', 'Slab yard', is_showroom=True, ranking='Preferred'),
    build_entry('QDI Surfaces', '2633 N 24th Dr, Phoenix, AZ 85009', '(480) 903-0011', 'qdisurfaces.com', 'Design-forward', is_showroom=True, ranking='Preferred'),
    build_entry('Arizona Tile', '1855 W Broadway Rd, Tempe, AZ 85282', '(480) 893-9393', 'arizonatile.com', 'Reliable', is_showroom=True, ranking='Preferred'),
    build_entry('Bedrosians Tile & Stone', '15440 N 84th St, Scottsdale, AZ 85260', '(480) 922-9770', 'bedrosians.com', 'Strong for porcelain, slab, and design-forward materials', is_showroom=True, ranking='Preferred'),
    build_entry('Aqua Bella Tile', '2850 S Roosevelt St, Tempe, AZ 85282', '(602) 748-4080', 'aquabellatile.com', 'Pool tile specialist', is_showroom=True, ranking='Preferred'),
]
with open('/home/ubuntu/rtlo-map/tile_stores.json', 'w') as f:
    json.dump(tile_stores, f, indent=2)
print(f'Saved {len(tile_stores)} tile/slab stores')

# ─── ROCK / AGGREGATE (existing + new from directory + B-Line) ────────────────
print('\n=== ROCK / AGGREGATE ===')
rock_stores = [
    # From existing map (confirmed in directory)
    build_entry('MDI Rock', '2815 E Rose Garden Ln, Phoenix, AZ 85050', '(602) 569-8722', 'mdirock.com', 'Best for boulders + client visits', is_showroom=False, ranking='Preferred'),
    build_entry('ABC Sand & Rock', '1804 N 27th Ave, Phoenix, AZ 85009', '(602) 272-1792', 'abcsandrock.com', 'Most consistent supply', is_showroom=False, ranking='Preferred'),
    build_entry('A&A Materials', '10333 E McDowell Rd, Scottsdale, AZ 85256', '(480) 986-1110', '', 'Bulk aggregate', is_showroom=False, ranking='Secondary'),
    build_entry('A-1 Materials', '9503 W Buckeye Rd, Tolleson, AZ 85353', '(623) 936-9600', '', 'West Valley aggregate', is_showroom=False, ranking='Secondary'),
    build_entry('J&J Landscaping Material', '5000 E McKellips Rd, Mesa, AZ 85215', '(480) 832-0500', '', 'East Valley bulk material', is_showroom=False, ranking='Secondary'),
    build_entry('The Stone Yard - North Phoenix', '1739 W Park View Ln, Phoenix, AZ 85085', '(623) 580-1234', '', 'Decorative rock yard', is_showroom=False, ranking='Secondary'),
    build_entry('The Stone Yard - NE Phoenix', '450 E Pinnacle Peak Rd, Phoenix, AZ 85024', '', '', 'Decorative rock yard', is_showroom=False, ranking='Secondary'),
    build_entry('Carso Landscape Supply', '10701 W Hatfield Rd, Sun City, AZ 85373', '(623) 977-3800', '', 'West Valley landscape supply', is_showroom=False, ranking='Secondary'),
    # New from directory
    build_entry('Rock 4 Less', '21839 N 16th Ave, Phoenix, AZ 85027', '', 'rock4lessaz.com', 'Cost-effective', is_showroom=False, ranking='Secondary'),
    build_entry('West Valley Rock', '25376 W Tonopah Salome Hwy, Buckeye, AZ 85396', '', 'westvalleyrock.com', 'Large boulder sourcing', is_showroom=False, ranking='Specialty'),
    # B-Line Materials (user provided)
    build_entry('B-Line Materials', '3318 S 80th St, Mesa, AZ 85212', '(602) 432-5230', 'blinematerials.com', 'Decorative rock, sand and gravel - East Valley', is_showroom=False, ranking='Preferred'),
]
with open('/home/ubuntu/rtlo-map/rock_stores.json', 'w') as f:
    json.dump(rock_stores, f, indent=2)
print(f'Saved {len(rock_stores)} rock stores')

# ─── FLOOR & DECOR ────────────────────────────────────────────────────────────
print('\n=== FLOOR & DECOR ===')
floor_decor_stores = [
    build_entry('Floor & Decor - Phoenix', '1800 E Highland Ave, Phoenix, AZ 85016', '', 'flooranddecor.com', 'Full tile, stone, and hardwood selection', is_showroom=True, ranking='Preferred'),
    build_entry('Floor & Decor - Chandler', '1901 E Northrop Blvd, Chandler, AZ 85286', '', 'flooranddecor.com', 'Full tile, stone, and hardwood selection', is_showroom=True, ranking='Preferred'),
    build_entry('Floor & Decor - Glendale', '5880 W Bell Rd, Glendale, AZ 85308', '', 'flooranddecor.com', 'Full tile, stone, and hardwood selection', is_showroom=True, ranking='Preferred'),
    build_entry('Floor & Decor - Surprise', '13230 N Prasada Pkwy, Surprise, AZ 85388', '', 'flooranddecor.com', 'Full tile, stone, and hardwood selection', is_showroom=True, ranking='Preferred'),
    build_entry('Floor & Decor - Tolleson', '9261 W McDowell Rd, Tolleson, AZ 85353', '', 'flooranddecor.com', 'Full tile, stone, and hardwood selection', is_showroom=True, ranking='Preferred'),
]
with open('/home/ubuntu/rtlo-map/floor_decor_stores.json', 'w') as f:
    json.dump(floor_decor_stores, f, indent=2)
print(f'Saved {len(floor_decor_stores)} Floor & Decor stores')

# ─── HORIZON LANDSCAPE SUPPLY ─────────────────────────────────────────────────
print('\n=== HORIZON LANDSCAPE SUPPLY ===')
horizon_stores = [
    build_entry('Horizon Landscape Supply - Chandler', '4055 W Saturn Way, Chandler, AZ 85226', '', 'horizononline.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('Horizon Landscape Supply - Gilbert', '4635 E Warner Rd, Gilbert, AZ 85296', '', 'horizononline.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('Horizon Landscape Supply - Goodyear', '13920 W El Cielo, Goodyear, AZ 85338', '', 'horizononline.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('Horizon Landscape Supply - Mesa', '201 W Juanita Ave, Mesa, AZ 85210', '', 'horizononline.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('Horizon Landscape Supply - Phoenix (Tatum)', '17826 N Tatum Blvd, Phoenix, AZ 85032', '', 'horizononline.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('Horizon Landscape Supply - Peoria', '8746 W Kelton Ln, Peoria, AZ 85382', '', 'horizononline.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('Horizon Landscape Supply - Phoenix (S 30th)', '5214 S 30th St, Phoenix, AZ 85040', '', 'horizononline.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('Horizon Landscape Supply - Queen Creek', '21515 E Ocotillo Rd, Queen Creek, AZ 85142', '', 'horizononline.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('Horizon Landscape Supply - Scottsdale', '15517 N 77th St, Scottsdale, AZ 85260', '', 'horizononline.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
]
with open('/home/ubuntu/rtlo-map/horizon_stores.json', 'w') as f:
    json.dump(horizon_stores, f, indent=2)
print(f'Saved {len(horizon_stores)} Horizon stores')

# ─── BBQ ISLANDS / OUTDOOR LIVING (showrooms) ─────────────────────────────────
print('\n=== BBQ ISLANDS / OUTDOOR LIVING (showrooms) ===')
bbq_stores = [
    build_entry('BBQ Island - Scottsdale', '14987 N Northsight Blvd, Scottsdale, AZ 85260', '', 'bbqislandinc.com', 'Best showroom', is_showroom=True, ranking='Preferred'),
    build_entry('BBQ Island - Tempe', '1715 W Ruby Dr #105, Tempe, AZ 85284', '', 'bbqislandinc.com', 'Showroom', is_showroom=True, ranking='Preferred'),
    build_entry('BBQ Island - Peoria', '8155 W Bell Rd #111, Peoria, AZ 85382', '', 'bbqislandinc.com', 'Showroom', is_showroom=True, ranking='Preferred'),
    build_entry('BBQ Island - Gilbert', '4630 E Ray Rd, Gilbert, AZ 85296', '', 'bbqislandinc.com', 'Showroom', is_showroom=True, ranking='Preferred'),
    build_entry('Best BBQ & Islands', '16255 N Scottsdale Rd C4, Scottsdale, AZ 85254', '', 'bestbbqislands.com', 'Strong service', is_showroom=True, ranking='Preferred'),
    build_entry('KoKoMo Grills', '21415 N Black Canyon Hwy, Phoenix, AZ 85027', '', 'kokomogrills.com', 'Direct manufacturer showroom', is_showroom=True, ranking='Secondary'),
    build_entry('Arizona Fireplaces - North', '20835 N 25th Pl, Phoenix, AZ 85024', '(602) 343-1000', 'arizonafireplaces.com', 'Strong fireplace/fire feature displays', is_showroom=True, ranking='Preferred'),
    build_entry('Arizona Fireplaces - South', '3435 E Atlanta Ave, Phoenix, AZ 85040', '(602) 243-6423', 'arizonafireplaces.com', 'Inventory hub', is_showroom=True, ranking='Preferred'),
]
with open('/home/ubuntu/rtlo-map/bbq_stores.json', 'w') as f:
    json.dump(bbq_stores, f, indent=2)
print(f'Saved {len(bbq_stores)} BBQ/outdoor living stores')

# ─── SITEONE FAMILY (updated with new locations) ──────────────────────────────
print('\n=== SITEONE FAMILY (updated) ===')
siteone_stores = [
    build_entry('SiteOne Stone Center #1108', '1639 E Deer Valley Rd, Phoenix, AZ 85024', '', 'siteone.com', 'Stone center', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply #332', '22010 N 21st Ave, Phoenix, AZ 85027', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply - Scottsdale', '7501 E Monte Cristo Ave, Scottsdale, AZ 85260', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Stone Center (Cutting Edge) - Glendale', '7540 N 67th Ave, Glendale, AZ 85301', '', 'siteone.com', 'Cutting Edge Stone - acquired by SiteOne', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply #1106 - Goodyear', '3595 N Cotton Ln, Goodyear, AZ 85395', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply - Mesa', '1530 W Broadway Rd, Mesa, AZ 85202', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply - Peoria', '9350 W Peoria Ave, Peoria, AZ 85345', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply - Gilbert (Val Vista)', '1155 N Val Vista Dr, Gilbert, AZ 85234', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply - Gilbert (S Gilbert)', '3030 S Gilbert Rd, Gilbert, AZ 85295', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply - Chandler', '4835 E Chandler Blvd, Chandler, AZ 85226', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply - Surprise', '13415 W Westgate Dr, Surprise, AZ 85378', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply - Tempe', '2121 S Rural Rd, Tempe, AZ 85282', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply - Queen Creek', '22705 S Ellsworth Rd, Queen Creek, AZ 85142', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
    build_entry('Pioneer Landscape Centers (SiteOne) - Apache Junction', '3451 S Meridian Rd, Apache Junction, AZ 85120', '', 'pioneerco.com', 'Pioneer - acquired by SiteOne', is_showroom=False, ranking='Preferred'),
    build_entry('Pioneer Landscape Centers (SiteOne) - N Scottsdale', '7452 E Adobe Dr, Scottsdale, AZ 85255', '', 'pioneerco.com', 'Good client-facing yard. Pioneer - acquired by SiteOne', is_showroom=False, ranking='Preferred'),
    build_entry('Pioneer Landscape Centers (SiteOne) - Peoria North', '11450 W Northern Ave, Peoria, AZ 85345', '', 'pioneerco.com', 'Pioneer - acquired by SiteOne', is_showroom=False, ranking='Preferred'),
    build_entry('Pioneer Landscape Centers (SiteOne) - Gilbert/Guadalupe', '609 W Guadalupe Rd, Gilbert, AZ 85233', '', 'pioneerco.com', 'Pioneer - acquired by SiteOne', is_showroom=False, ranking='Preferred'),
    build_entry('Pioneer Landscape Centers (SiteOne) - N Chandler', '11243 E Willis Rd, Chandler, AZ 85286', '', 'pioneerco.com', 'Pioneer - acquired by SiteOne', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Stone Center (Arizona Stone Brick Pavers) - Peoria', '12473 N 92nd Dr, Peoria, AZ 85381', '', 'siteone.com', 'Arizona Stone Brick Pavers - acquired by SiteOne', is_showroom=False, ranking='Preferred'),
    build_entry('Pioneer Sand (SiteOne)', '1638 E Deer Valley Rd, Phoenix, AZ 85024', '', 'siteone.com', 'Pioneer Sand - acquired by SiteOne', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Stone Center - Indian School', '2514 E Indian School Rd, Phoenix, AZ 85016', '', 'siteone.com', 'Stone center', is_showroom=False, ranking='Preferred'),
    build_entry('SiteOne Landscape Supply - Scottsdale McDowell', '7025 E McDowell Rd, Scottsdale, AZ 85257', '', 'siteone.com', 'Full landscape supply', is_showroom=False, ranking='Preferred'),
]
with open('/home/ubuntu/rtlo-map/siteone_stores.json', 'w') as f:
    json.dump(siteone_stores, f, indent=2)
print(f'Saved {len(siteone_stores)} SiteOne stores')

print('\nAll supplier files built successfully.')
