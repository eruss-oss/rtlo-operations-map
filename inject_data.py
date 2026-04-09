#!/usr/bin/env python3.11
"""
RTLO Map Data Injector
Reads all data JSON files and injects them into index_new.html to produce map.html
"""
import json
import re

# ─── LOAD DATA ───────────────────────────────────────────────────────────────

with open('/home/ubuntu/rtlo-map/jobs_geocoded.json') as f:
    jt_jobs = json.load(f)

with open('/home/ubuntu/rtlo-map/ghl_geocoded.json') as f:
    ghl_opps = json.load(f)

with open('/home/ubuntu/rtlo-map/homedepot_enriched.json') as f:
    hd_stores = json.load(f)

with open('/home/ubuntu/rtlo-map/siteone_stores.json') as f:
    siteone_stores = json.load(f)

with open('/home/ubuntu/rtlo-map/sprinklerworld_stores.json') as f:
    sw_stores = json.load(f)

with open('/home/ubuntu/rtlo-map/ace_stores.json') as f:
    ace_stores = json.load(f)

with open('/home/ubuntu/rtlo-map/turf_stores.json') as f:
    turf_stores = json.load(f)

with open('/home/ubuntu/rtlo-map/rock_stores.json') as f:
    rock_stores = json.load(f)

with open('/home/ubuntu/rtlo-map/tile_stores.json') as f:
    tile_stores = json.load(f)

with open('/home/ubuntu/rtlo-map/slab_stores.json') as f:
    slab_stores = json.load(f)

with open('/home/ubuntu/rtlo-map/other_stores.json') as f:
    other_stores = json.load(f)

with open('/home/ubuntu/rtlo-map/weather_risk.json') as f:
    weather_risk = json.load(f)

# ─── CLEAN JT JOBS ───────────────────────────────────────────────────────────

jt_clean = []
for j in jt_jobs:
    jt_clean.append({
        'id': j.get('id', ''),
        'name': j.get('name', ''),
        'number': j.get('number', ''),
        'status': j.get('status', 'created'),
        'lat': j.get('lat'),
        'lon': j.get('lon'),
        'location': j.get('location', {}),
        'ghlId': j.get('ghlId', '')
    })

# ─── DEDUPLICATE GHL OPPS ────────────────────────────────────────────────────

linked_ghl_ids = set(j.get('ghlId', '') for j in jt_jobs if j.get('ghlId'))

def normalize_name(name):
    import re
    name = name.lower().strip()
    name = re.sub(r'[^a-z0-9 ]', '', name)
    return ' '.join(sorted(name.split()))

jt_names = set(normalize_name(j.get('name', '')) for j in jt_jobs if j.get('name'))

ghl_clean = []
ghl_suppressed = 0
for o in ghl_opps:
    opp_id = o.get('id', '')
    opp_name = o.get('name', '')
    if opp_id in linked_ghl_ids:
        ghl_suppressed += 1
        continue
    if opp_name and normalize_name(opp_name) in jt_names:
        ghl_suppressed += 1
        continue
    ghl_clean.append({
        'id': opp_id,
        'name': opp_name,
        'stage_name': o.get('stage_name', 'Unknown'),
        'monetaryValue': o.get('monetaryValue', 0),
        'lat': o.get('lat'),
        'lon': o.get('lon'),
        'full_address': o.get('full_address', ''),
        'contactId': o.get('contactId', '')
    })

print(f"GHL deduplication: {ghl_suppressed} suppressed")

# ─── READ TEMPLATE ───────────────────────────────────────────────────────────

with open('/home/ubuntu/rtlo-map/index_new.html', 'r') as f:
    html = f.read()

# ─── INJECT ZONES BLOCK ──────────────────────────────────────────────────────
# Read the zones block from the original index.html (the proven working zones)
with open('/home/ubuntu/rtlo-map/index.html', 'r') as f:
    orig = f.read()

# Parse zones using brace-matching to get exact JSON object
_z_start_kw = orig.find('const ZONES = {') + len('const ZONES = ')
_depth = 0
_i = _z_start_kw
while _i < len(orig):
    if orig[_i] == '{': _depth += 1
    elif orig[_i] == '}': 
        _depth -= 1
        if _depth == 0:
            _z_end = _i + 1
            break
    _i += 1

import json as _json
_zones = _json.loads(orig[_z_start_kw:_z_end])

# Inject label_anchor overrides for Zone 4B and Zone 2B ONLY
# Zone 4B: far west edge of its polygon, well outside Zone 4A
# Zone 2B: southern portion of its polygon, well below Zone 2A
_zones['Zone 4B']['label_anchor'] = [-112.580, 33.680]
_zones['Zone 2B']['label_anchor'] = [-111.720, 33.180]

zones_block = 'const ZONES = ' + _json.dumps(_zones) + ';'
html = html.replace('ZONES_PLACEHOLDER', zones_block)

# ─── INJECT DATA ─────────────────────────────────────────────────────────────

html = html.replace('JOBTREAD_DATA_PLACEHOLDER', json.dumps(jt_clean))
html = html.replace('GHL_DATA_PLACEHOLDER', json.dumps(ghl_clean))
html = html.replace('HOMEDEPOT_DATA_PLACEHOLDER', json.dumps(hd_stores))
html = html.replace('SITEONE_DATA_PLACEHOLDER', json.dumps(siteone_stores))
html = html.replace('SPRINKLERWORLD_DATA_PLACEHOLDER', json.dumps(sw_stores))
html = html.replace('ACE_DATA_PLACEHOLDER', json.dumps(ace_stores))
html = html.replace('TURF_DATA_PLACEHOLDER', json.dumps(turf_stores))
html = html.replace('ROCK_DATA_PLACEHOLDER', json.dumps(rock_stores))
html = html.replace('TILE_DATA_PLACEHOLDER', json.dumps(tile_stores))
html = html.replace('SLAB_DATA_PLACEHOLDER', json.dumps(slab_stores))
html = html.replace('OTHER_DATA_PLACEHOLDER', json.dumps(other_stores))
html = html.replace('WEATHER_RISK_PLACEHOLDER', json.dumps(weather_risk))

# ─── WRITE OUTPUT ────────────────────────────────────────────────────────────

with open('/home/ubuntu/rtlo-map/map.html', 'w') as f:
    f.write(html)

print(f"JobTread jobs: {len(jt_clean)}")
print(f"GHL opportunities: {len(ghl_clean)}")
print(f"Home Depot stores: {len(hd_stores)}")
print(f"SiteOne stores: {len(siteone_stores)}")
print(f"Sprinkler World stores: {len(sw_stores)}")
print(f"Ace Hardware stores: {len(ace_stores)}")
print(f"Turf suppliers: {len(turf_stores)}")
print(f"Rock/Aggregate: {len(rock_stores)}")
print(f"Tile/Stone: {len(tile_stores)}")
print(f"Countertop/Slab: {len(slab_stores)}")
print(f"Other suppliers: {len(other_stores)}")
print(f"Weather risks: {len(weather_risk.get('risks', []))}")
print("Map generated: /home/ubuntu/rtlo-map/map.html")
