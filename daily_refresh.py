#!/usr/bin/env python3.11
"""
RTLO Map Daily Refresh Script
Runs at 4:00 AM MST every day.
- Fetches latest JobTread jobs
- Fetches latest GHL pipeline opportunities
- Fetches NWS weather risk for Phoenix metro
- Rebuilds map.html
- Sends daily email summary to eruss@rtloaz.com
"""

import json
import os
import re
import sys
import smtplib
import subprocess
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict

# ─── CONFIG ──────────────────────────────────────────────────────────────────

WORK_DIR = os.environ.get('WORK_DIR', '/home/ubuntu/rtlo-map')
JT_GRANT_KEY = os.environ.get('JT_GRANT_KEY', '22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB')
JT_ORG_ID = os.environ.get('JT_ORG_ID', '22PFyR85uqXr')
GHL_PIT = os.environ.get('GHL_PIT', 'pit-331e79b0-4487-465e-b64c-4849701f07ed')
GHL_LOCATION_ID = os.environ.get('GHL_LOCATION_ID', 'T8yugiCGYxTDnfZR9xG6')
EMAIL_TO = os.environ.get('EMAIL_TO', 'eruss@rtloaz.com')
MAP_URL = os.environ.get('MAP_URL', 'https://map.inhousekru.com')
NWS_HEADERS = {'User-Agent': 'rtlo-map/1.0 (eruss@rtloaz.com)'}
MAPBOX_TOKEN = os.environ.get('MAPBOX_TOKEN', 'pk.eyJ1IjoiZXJ1c3Nub2Z1c3MiLCJhIjoiY21ubTRlemtrMTVrczJxcTcwbmk2dnRtOCJ9.zPPUauWOdG2LpSv5q8ZJ1g')

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        log(f'Could not load {path}: {e}')
        return []

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def geocode_mapbox(address):
    try:
        url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{requests.utils.quote(address)}.json'
        params = {'access_token': MAPBOX_TOKEN, 'country': 'US', 'bbox': '-113.5,32.5,-110.5,34.5', 'limit': 1}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get('features'):
            return data['features'][0]['center']
    except Exception as e:
        log(f'Geocode error for "{address}": {e}')
    return None

# ─── JOBTREAD ────────────────────────────────────────────────────────────────

def fetch_jobtread_jobs():
    log('Fetching JobTread jobs...')
    all_jobs = []
    page = None

    # Fetch in pages of 10 (customFieldValues makes requests large)
    SHOW_STATUSES = ['Sold | Project Intake Phase', 'Active Production Phase']
    while True:
        q = {
            'query': {
                '$': {'grantKey': JT_GRANT_KEY},
                'organization': {
                    '$': {'id': JT_ORG_ID},
                    'jobs': {
                        '$': {'size': 10, **({'page': page} if page else {})},
                        'nextPage': {},
                        'nodes': {
                            'id': {}, 'name': {}, 'number': {}, 'status': {},
                            'location': {'id': {}, 'name': {}, 'address': {}},
                            'customFieldValues': {
                                'nodes': {
                                    'value': {},
                                    'customField': {'id': {}, 'name': {}}
                                }
                            }
                        }
                    }
                }
            }
        }
        try:
            resp = requests.post('https://api.jobtread.com/pave', json=q, timeout=30)
            data = resp.json().get('organization', {}).get('jobs', {})
            nodes = data.get('nodes', [])
            all_jobs.extend(nodes)
            page = data.get('nextPage')
            if not page:
                break
        except Exception as e:
            log(f'JobTread fetch error: {e}')
            break

    log(f'Fetched {len(all_jobs)} total jobs from JobTread')

    # Extract custom Job Status field and filter to Sold/Active only
    def get_custom_job_status(job):
        for cfv in job.get('customFieldValues', {}).get('nodes', []):
            if cfv.get('customField', {}).get('name') == 'Job Status':
                return cfv.get('value')
        return None

    filtered_jobs = []
    for job in all_jobs:
        custom_status = get_custom_job_status(job)
        if custom_status in SHOW_STATUSES:
            job['custom_job_status'] = custom_status
            filtered_jobs.append(job)

    log(f'Filtered to {len(filtered_jobs)} Sold/Active jobs (excluded {len(all_jobs)-len(filtered_jobs)} Opportunities)')

    # Load existing geocoded data to avoid re-geocoding
    existing = {j['id']: j for j in load_json(f'{WORK_DIR}/jobs_geocoded.json')}
    geocoded = []
    new_geocodes = 0

    for job in filtered_jobs:
        jid = job.get('id', '')
        custom_status = job.get('custom_job_status', 'Sold | Project Intake Phase')
        if jid in existing and existing[jid].get('lat'):
            # Keep existing geocode, update custom status
            entry = existing[jid].copy()
            entry['status'] = custom_status
            entry['name'] = job.get('name', entry.get('name', ''))
            geocoded.append(entry)
            continue

        loc = job.get('location', {})
        addr = loc.get('address', '') or loc.get('name', '')
        coords = geocode_mapbox(addr + ', Phoenix, AZ') if addr.strip() else None
        entry = {
            'id': jid,
            'name': job.get('name', ''),
            'number': job.get('number', ''),
            'status': custom_status,
            'location': loc,
            'lat': coords[1] if coords else None,
            'lon': coords[0] if coords else None,
            'ghlId': existing.get(jid, {}).get('ghlId', '')
        }
        geocoded.append(entry)
        if coords:
            new_geocodes += 1

    log(f'Geocoded {new_geocodes} new jobs, total: {len(geocoded)}')
    save_json(f'{WORK_DIR}/jobs_geocoded.json', geocoded)
    # Also return all_jobs (all statuses) so rebuild_map can build a full address→JT lookup
    return geocoded, all_jobs

# ─── GHL ─────────────────────────────────────────────────────────────────────

def fetch_ghl_opportunities():
    log('Fetching GHL opportunities...')
    BASE = 'https://services.leadconnectorhq.com'
    headers = {'Authorization': f'Bearer {GHL_PIT}', 'Version': '2021-07-28', 'Accept': 'application/json'}

    # Get pipeline stages
    stage_map = {}
    try:
        resp = requests.get(f'{BASE}/opportunities/pipelines', headers=headers,
            params={'locationId': GHL_LOCATION_ID}, timeout=15)
        for pl in resp.json().get('pipelines', []):
            for stage in pl.get('stages', []):
                stage_map[stage['id']] = stage['name']
    except Exception as e:
        log(f'GHL pipeline fetch error: {e}')

    # Get all opportunities
    all_opps = []
    after = None
    after_id = None

    while True:
        try:
            params = {'location_id': GHL_LOCATION_ID, 'limit': 100}
            if after:
                params['startAfter'] = after
                params['startAfterId'] = after_id
            resp = requests.get(f'{BASE}/opportunities/search', headers=headers, params=params, timeout=15)
            data = resp.json()
            opps = data.get('opportunities', [])
            all_opps.extend(opps)
            meta = data.get('meta', {})
            if not meta.get('nextPage'):
                break
            after = meta.get('startAfter')
            after_id = meta.get('startAfterId')
        except Exception as e:
            log(f'GHL opportunities fetch error: {e}')
            break

    log(f'Fetched {len(all_opps)} GHL opportunities')

    # Load existing geocoded data
    existing = {o['id']: o for o in load_json(f'{WORK_DIR}/ghl_geocoded.json')}
    geocoded = []
    new_geocodes = 0

    import time as _time
    for opp in all_opps:
        oid = opp.get('id', '')
        stage_name = stage_map.get(opp.get('pipelineStageId', ''), opp.get('stage', {}).get('name', 'Unknown'))

        if oid in existing and existing[oid].get('lat'):
            entry = existing[oid].copy()
            entry['stage_name'] = stage_name
            entry['monetaryValue'] = opp.get('monetaryValue', 0)
            geocoded.append(entry)
            continue

        # Fetch contact for address
        contact_id = opp.get('contactId', '')
        addr = ''
        if contact_id:
            try:
                cr = requests.get(f'{BASE}/contacts/{contact_id}', headers=headers, timeout=10)
                if cr.status_code == 200:
                    c = cr.json().get('contact', {})
                    addr_parts = [c.get('address1',''), c.get('city',''), c.get('state',''), c.get('postalCode','')]
                    addr = ', '.join(p for p in addr_parts if p)
                _time.sleep(0.25)
            except Exception as e:
                log(f'GHL contact fetch error: {e}')

        coords = geocode_mapbox(addr) if addr.strip() else None
        entry = {
            'id': oid,
            'name': opp.get('name', ''),
            'stage_name': stage_name,
            'monetaryValue': opp.get('monetaryValue', 0),
            'lat': coords[1] if coords else None,
            'lon': coords[0] if coords else None,
            'full_address': addr,
            'contactId': contact_id,
            'appt_start': ''
        }
        geocoded.append(entry)
        if coords:
            new_geocodes += 1

    log(f'Geocoded {new_geocodes} new GHL opps, total: {len(geocoded)}')

    # Fetch appointment dates for Appt Booked opportunities
    appt_booked_ids = set()
    for entry in geocoded:
        sn = (entry.get('stage_name') or '').lower()
        if 'appoint' in sn or 'booked' in sn:
            appt_booked_ids.add(entry['contactId'])

    if appt_booked_ids:
        log(f'Fetching appointments for {len(appt_booked_ids)} Appt Booked contacts...')
        contact_appt_map = {}
        for cid in appt_booked_ids:
            if not cid:
                continue
            try:
                ar = requests.get(f'{BASE}/contacts/{cid}/appointments', headers=headers, timeout=10)
                if ar.status_code == 200:
                    appts = ar.json().get('events', []) or ar.json().get('appointments', [])
                    if appts:
                        # Get the most recent upcoming appointment
                        from datetime import timezone
                        now_ts = datetime.now(timezone.utc).isoformat()
                        upcoming = [a for a in appts if a.get('startTime', '') >= now_ts]
                        chosen = upcoming[0] if upcoming else appts[0]
                        contact_appt_map[cid] = chosen.get('startTime', '')
                _time.sleep(0.15)
            except Exception as e:
                log(f'GHL appointment fetch error for {cid}: {e}')

        # Attach appointment dates to entries
        for entry in geocoded:
            if entry.get('contactId') in contact_appt_map:
                entry['appt_start'] = contact_appt_map[entry['contactId']]

        log(f'Attached appointment dates to {len(contact_appt_map)} contacts')

    save_json(f'{WORK_DIR}/ghl_geocoded.json', geocoded)
    return geocoded

# ─── WEATHER ─────────────────────────────────────────────────────────────────

def fetch_weather_risk():
    log('Fetching NWS weather risk...')
    risks = []
    alerts_list = []
    max_wind = 0
    max_precip = 0
    special_conditions = []

    try:
        resp = requests.get('https://api.weather.gov/gridpoints/PSR/160,55/forecast/hourly',
            headers=NWS_HEADERS, timeout=15)
        data = resp.json()
        periods = data.get('properties', {}).get('periods', [])
        today_periods = periods[:24]

        for p in today_periods:
            wind_str = p.get('windSpeed', '0 mph')
            try:
                wind_val = int(wind_str.split(' ')[0])
            except:
                wind_val = 0
            if wind_val > max_wind:
                max_wind = wind_val
            precip = p.get('probabilityOfPrecipitation', {}).get('value', 0) or 0
            if precip > max_precip:
                max_precip = precip
            forecast = p.get('shortForecast', '').lower()
            if any(kw in forecast for kw in ['dust', 'freeze', 'frost', 'blizzard', 'ice', 'snow', 'thunderstorm', 'tornado']):
                sc = p.get('shortForecast')
                if sc not in special_conditions:
                    special_conditions.append(sc)

        if max_wind >= 20:
            risks.append({'type': 'wind', 'label': f'Wind {max_wind} mph', 'severity': 'high' if max_wind >= 30 else 'medium'})
        if max_precip >= 30:
            risks.append({'type': 'rain', 'label': f'Rain {max_precip}%', 'severity': 'high' if max_precip >= 60 else 'medium'})
        for sc in special_conditions:
            risks.append({'type': 'special', 'label': sc, 'severity': 'high'})
    except Exception as e:
        log(f'NWS forecast error: {e}')

    try:
        alert_resp = requests.get('https://api.weather.gov/alerts/active?area=AZ',
            headers=NWS_HEADERS, timeout=10)
        alert_data = alert_resp.json()
        for a in alert_data.get('features', []):
            props = a.get('properties', {})
            event = props.get('event', '')
            area = props.get('areaDesc', '')
            if any(x in area for x in ['Maricopa', 'Phoenix', 'Scottsdale', 'Mesa', 'Tempe', 'Chandler',
                                         'Gilbert', 'Glendale', 'Peoria', 'Surprise', 'Goodyear', 'AZ']):
                alerts_list.append({'event': event, 'area': area, 'severity': props.get('severity', 'Unknown')})
                risks.append({'type': 'alert', 'label': event, 'severity': 'high'})
    except Exception as e:
        log(f'NWS alert error: {e}')

    weather = {
        'risks': risks,
        'alerts': alerts_list,
        'max_wind_mph': max_wind,
        'max_precip_pct': max_precip,
        'special_conditions': special_conditions,
        'has_risk': len(risks) > 0,
        'fetched_at': datetime.now().isoformat()
    }
    save_json(f'{WORK_DIR}/weather_risk.json', weather)
    log(f'Weather: {len(risks)} risks, max wind {max_wind} mph, precip {max_precip}%')
    return weather

# ─── DATA JSON ──────────────────────────────────────────────────────────────

def write_data_json(jt_clean, ghl_clean, weather):
    """Write a compact data.json that the map shell loads dynamically."""
    data = {
        'generated_at': datetime.now().isoformat(),
        'jt_jobs': jt_clean,
        'ghl_opps': ghl_clean,
        'weather': weather
    }
    path = f'{WORK_DIR}/data.json'
    save_json(path, data)
    log(f'data.json written: {len(jt_clean)} JT jobs, {len(ghl_clean)} GHL opps')
    return path

def upload_data_json():
    """Upload data.json to CDN and return the public URL."""
    path = f'{WORK_DIR}/data.json'
    try:
        result = subprocess.run(
            ['manus-upload-file', path],
            capture_output=True, text=True, timeout=120
        )
        output = result.stdout + result.stderr
        # Extract CDN URL from output
        for line in output.splitlines():
            if 'CDN URL:' in line:
                url = line.split('CDN URL:')[-1].strip()
                log(f'data.json uploaded: {url}')
                # Save the URL so the map shell can reference it
                with open(f'{WORK_DIR}/data_cdn_url.txt', 'w') as f:
                    f.write(url)
                return url
        log(f'Upload output: {output}')
    except Exception as e:
        log(f'data.json upload error: {e}')
    return None

# ─── REBUILD MAP ─────────────────────────────────────────────────────────────

def rebuild_map(jt_jobs, ghl_opps, weather, all_jt_jobs=None):
    log('Rebuilding map.html...')

    hd_stores = load_json(f'{WORK_DIR}/homedepot_enriched.json')
    siteone_stores = load_json(f'{WORK_DIR}/siteone_stores.json')
    sw_stores = load_json(f'{WORK_DIR}/sprinklerworld_stores.json')
    ace_stores = load_json(f'{WORK_DIR}/ace_stores.json')
    turf_stores = load_json(f'{WORK_DIR}/turf_stores.json')
    rock_stores = load_json(f'{WORK_DIR}/rock_stores.json')
    tile_stores = load_json(f'{WORK_DIR}/tile_stores.json')
    slab_stores = load_json(f'{WORK_DIR}/slab_stores.json')
    other_stores = load_json(f'{WORK_DIR}/other_stores.json')
    hardscape_stores = load_json(f'{WORK_DIR}/hardscape_stores.json')
    floor_decor_stores = load_json(f'{WORK_DIR}/floor_decor_stores.json')
    horizon_stores = load_json(f'{WORK_DIR}/horizon_stores.json')
    bbq_stores = load_json(f'{WORK_DIR}/bbq_stores.json')
    nursery_stores = load_json(f'{WORK_DIR}/nursery_stores.json')
    plumbing_stores = load_json(f'{WORK_DIR}/plumbing_stores.json')
    pool_stores = load_json(f'{WORK_DIR}/pool_stores.json')
    misc_stores = load_json(f'{WORK_DIR}/misc_stores.json')
    tesla_stores = load_json(f'{WORK_DIR}/tesla_superchargers.json')

    # ─── DRIVE FOLDER INDEX ─────────────────────────────────────────────────
    import subprocess as _sp
    DRIVE_ID = '0AOMdyNURgNqSUk9PVA'
    RCLONE_CONF = '/home/ubuntu/.gdrive-rclone.ini'

    def _build_drive_index():
        """Fetch RTLO-Jobs shared drive folders and build normalized name->url index."""
        try:
            cmd = ['rclone', 'lsjson',
                   f'manus_google_drive,shared_with_me=false,team_drive={DRIVE_ID}:',
                   '--config', RCLONE_CONF, '--dirs-only']
            r = _sp.run(cmd, capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                log(f'rclone Drive error: {r.stderr[:200]}')
                return {}
            folders = json.loads(r.stdout)
            index = {}
            for f in folders:
                name = f.get('Name', '').strip()
                fid = f.get('ID', '')
                if not fid or name.startswith('ARCHIVE') or name.startswith('.'):
                    continue
                url = f'https://drive.google.com/drive/folders/{fid}'
                # Normalize: remove separators, lowercase, strip suffixes
                key = re.sub(r'[\-\u2013\u2014]+', ' ', name.lower())
                key = re.sub(r'\b(for sharing|shared|docs|renders|inspo|family)\b', '', key)
                key = re.sub(r'[^a-z0-9 ]', '', key)
                key = ' '.join(key.split())
                # Normalize common spelling variants
                key = key.replace('rodgers', 'rogers')
                index[key] = (fid, name, url)
            log(f'Drive index built: {len(index)} folders')
            return index
        except Exception as e:
            log(f'Drive index error: {e}')
            return {}

    def _find_drive_url(name, city, drive_index):
        """Find Drive folder URL for a job/lead by name+city fuzzy match."""
        if not name or not drive_index:
            return ''
        # Normalize search key
        key = re.sub(r'[^a-z0-9 ]', '', (name + ' ' + city).lower())
        key = ' '.join(key.split())
        # Direct match
        if key in drive_index:
            return drive_index[key][2]
        # Word overlap match (need ≥2 words matching, score ≥0.5)
        search_words = set(key.split())
        best_score, best_url = 0, ''
        for dk, (fid, fname, furl) in drive_index.items():
            dk_words = set(dk.split())
            common = search_words & dk_words
            if len(common) >= 2:
                score = len(common) / max(len(dk_words), len(search_words))
                if score > best_score:
                    best_score, best_url = score, furl
        return best_url if best_score >= 0.5 else ''

    drive_index = _build_drive_index()

    def _city_from_addr(addr):
        """Extract city from address string."""
        parts = [p.strip() for p in (addr or '').split(',')]
        if len(parts) >= 3:
            return re.sub(r'[^a-z ]', '', parts[-2].lower()).strip()
        elif len(parts) == 2:
            return re.sub(r'[^a-z ]', '', parts[1].lower()).strip()
        return ''

    # Build a normalized-address → JT job URL lookup for GHL→JT linking
    def norm_street(addr):
        """Normalize to 'NUMBER STREETNAME' for fuzzy matching across JT/GHL formats."""
        s = re.sub(r'[^a-z0-9 ]', '', (addr or '').lower())
        tokens = s.split()
        # Keep only first 3 tokens (number + street name words) to avoid city/state noise
        return ' '.join(tokens[:3]) if len(tokens) >= 2 else ''

    # Use ALL JT jobs (all statuses) for address matching so Opportunity-stage jobs also link correctly
    _match_pool = all_jt_jobs if all_jt_jobs else jt_jobs
    jt_street_map = {}  # normalized street → (job_id, job_name)
    for j in _match_pool:
        # Get address from location dict (geocoded jobs) or directly from raw API node
        loc = j.get('location', {})
        raw = loc.get('address', '') or loc.get('name', '')
        if not raw:
            # raw API node format
            raw = j.get('address', '')
        # Also check GHL ID custom field for direct linking
        ghl_id = ''
        for cfv in j.get('customFieldValues', {}).get('nodes', []):
            if cfv.get('customField', {}).get('name') in ('GHL ID', 'GHL Id', 'ghl_id'):
                ghl_id = cfv.get('value', '')
                break
        key = norm_street(raw)
        if key:
            jt_street_map[key] = (j.get('id', ''), j.get('name', ''), ghl_id)

    # Clean JT jobs
    jt_clean = []
    for j in jt_jobs:
        addr = j.get('location', {}).get('address', '') or ''
        city = _city_from_addr(addr)
        drive_url = _find_drive_url(j.get('name', ''), city, drive_index)
        jt_clean.append({
            'id': j.get('id', ''),
            'name': j.get('name', ''),
            'number': j.get('number', ''),
            'status': j.get('status', 'created'),
            'lat': j.get('lat'),
            'lon': j.get('lon'),
            'location': j.get('location', {}),
            'ghlId': j.get('ghlId', ''),
            'driveUrl': drive_url
        })

    # GHL: exclude Closed Won, Closed Lost (these are now tracked in JT)
    # and deduplicate against JT jobs by ghlId or normalized name
    EXCLUDED_GHL_STAGES = ['closed', 'won', 'lost', 'opportunity']
    def is_excluded_stage(stage):
        s = (stage or '').lower()
        if 'closed' in s and ('lost' in s or 'opportunity' in s): return True
        if 'closed' in s or 'won' in s: return True
        return False

    linked_ghl_ids = set(j.get('ghlId', '') for j in jt_jobs if j.get('ghlId'))
    def norm(name):
        name = name.lower().strip()
        name = re.sub(r'[^a-z0-9 ]', '', name)
        return ' '.join(sorted(name.split()))
    jt_names = set(norm(j.get('name', '')) for j in jt_jobs if j.get('name'))
    # Also deduplicate by address (catches name mismatches like 'Dan Schultz' vs 'Schultz')
    def norm_addr(addr):
        return re.sub(r'[^a-z0-9]', '', (addr or '').lower())
    jt_addrs = set(norm_addr(j.get('location', {}).get('address', '')) for j in jt_jobs)
    jt_addrs.discard('')

    ghl_clean = []
    suppressed = 0
    for o in ghl_opps:
        # Skip excluded stages
        if is_excluded_stage(o.get('stage_name', '')):
            suppressed += 1
            continue
        # Skip if already in JT by ghlId
        if o.get('id', '') in linked_ghl_ids:
            suppressed += 1
            continue
        # Skip if already in JT by name
        if o.get('name') and norm(o.get('name', '')) in jt_names:
            suppressed += 1
            continue
        # Skip if already in JT by address
        opp_addr = norm_addr(o.get('full_address', ''))
        if opp_addr and opp_addr in jt_addrs:
            suppressed += 1
            continue
        # Try to match this GHL opp to a JT job by address
        ghl_addr_key = norm_street(o.get('full_address', ''))
        matched_jt = jt_street_map.get(ghl_addr_key)
        jt_url = f'https://app.jobtread.com/jobs/{matched_jt[0]}' if matched_jt else ''
        jt_match_name = matched_jt[1] if matched_jt else ''
        # Also try matching by GHL contact ID stored in JT custom field
        if not jt_url:
            contact_id = o.get('contactId', '')
            for key_addr, (jt_id, jt_name, jt_ghl_id) in jt_street_map.items():
                if jt_ghl_id and jt_ghl_id == contact_id:
                    jt_url = f'https://app.jobtread.com/jobs/{jt_id}'
                    jt_match_name = jt_name
                    break
        ghl_drive_url = _find_drive_url(o.get('name', ''), _city_from_addr(o.get('full_address', '')), drive_index)
        ghl_clean.append({
            'id': o.get('id', ''),
            'name': o.get('name', ''),
            'stage_name': o.get('stage_name', 'Unknown'),
            'monetaryValue': o.get('monetaryValue', 0),
            'lat': o.get('lat'),
            'lon': o.get('lon'),
            'full_address': o.get('full_address', ''),
            'contactId': o.get('contactId', ''),
            'appt_start': o.get('appt_start', ''),
            'jtUrl': jt_url,
            'jtMatchName': jt_match_name,
            'driveUrl': ghl_drive_url
        })
    log(f'GHL deduplication: {suppressed} suppressed (incl. Closed Won/Lost + address matches), {len(ghl_clean)} remaining')

    with open(f'{WORK_DIR}/index_new.html', 'r') as f:
        html = f.read()

    # Inject zones block using brace-matching (same logic as inject_data.py)
    with open(f'{WORK_DIR}/index.html', 'r') as f:
        orig = f.read()
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
    _zones = json.loads(orig[_z_start_kw:_z_end])
    _zones['Zone 4B']['label_anchor'] = [-112.580, 33.680]
    _zones['Zone 2B']['label_anchor'] = [-111.720, 33.180]
    zones_block = 'const ZONES = ' + json.dumps(_zones) + ';'
    html = html.replace('ZONES_PLACEHOLDER', zones_block)

    html = html.replace('JOBTREAD_DATA_PLACEHOLDER', json.dumps(jt_clean))
    html = html.replace('GHL_DATA_PLACEHOLDER', json.dumps(ghl_clean))
    html = html.replace('HOMEDEPOT_DATA_PLACEHOLDER', json.dumps(hd_stores))
    html = html.replace('SITEONE_DATA_PLACEHOLDER', json.dumps(siteone_stores))
    html = html.replace('SPRINKLERWORLD_DATA_PLACEHOLDER', json.dumps(sw_stores))
    html = html.replace('ACE_DATA_PLACEHOLDER', json.dumps(ace_stores))
    html = html.replace('TURF_DATA_PLACEHOLDER', json.dumps(turf_stores))
    html = html.replace('ROCK_DATA_PLACEHOLDER', json.dumps(rock_stores))
    html = html.replace('TILE_DATA_PLACEHOLDER', json.dumps(tile_stores))
    html = html.replace('HARDSCAPE_DATA_PLACEHOLDER', json.dumps(hardscape_stores))
    html = html.replace('FLOOR_DECOR_DATA_PLACEHOLDER', json.dumps(floor_decor_stores))
    html = html.replace('HORIZON_DATA_PLACEHOLDER', json.dumps(horizon_stores))
    html = html.replace('BBQ_DATA_PLACEHOLDER', json.dumps(bbq_stores))
    html = html.replace('OTHER_DATA_PLACEHOLDER', json.dumps(other_stores))
    html = html.replace('NURSERY_DATA_PLACEHOLDER', json.dumps(nursery_stores))
    html = html.replace('PLUMBING_DATA_PLACEHOLDER', json.dumps(plumbing_stores))
    html = html.replace('POOL_DATA_PLACEHOLDER', json.dumps(pool_stores))
    html = html.replace('MISC_DATA_PLACEHOLDER', json.dumps(misc_stores))
    html = html.replace('TESLA_DATA_PLACEHOLDER', json.dumps(tesla_stores))
    html = html.replace('WEATHER_RISK_PLACEHOLDER', json.dumps(weather))

    with open(f'{WORK_DIR}/map.html', 'w') as f:
        f.write(html)

    log(f'Map rebuilt: {len(jt_clean)} JT jobs, {len(ghl_clean)} GHL opps')
    return jt_clean, ghl_clean

# ─── EMAIL ───────────────────────────────────────────────────────────────────

def build_email_html(jt_jobs, ghl_opps, weather, prev_jt_jobs=None):
    now = datetime.now()
    date_str = now.strftime('%A, %B %-d, %Y')
    time_str = now.strftime('%-I:%M %p MST')

    # Status colors — using real custom Job Status values
    status_colors = {
        'Active Production Phase': '#27ae60',
        'Sold | Project Intake Phase': '#9b59b6',
    }
    ghl_colors = {
        'Appt Booked': '#ff6b35',
        'Consultation': '#e91e8c',
        'Proposal': '#3498db',
        'Permitting': '#00e5ff',
    }

    def ghl_cat(stage):
        s = (stage or '').lower()
        # Exclude Closed Won/Lost entirely
        if 'closed' in s or 'won' in s or ('lost' in s and 'closed' in s) or 'opportunity' in s:
            return None
        if 'permitting' in s: return 'Permitting'
        if 'proposal' in s: return 'Proposal'
        if 'consult' in s: return 'Consultation'
        if 'appoint' in s or 'booked' in s: return 'Appt Booked'
        return 'Appt Booked'  # fallback

    # Counts
    jt_by_status = defaultdict(list)
    for j in jt_jobs:
        jt_by_status[j.get('status', 'Sold | Project Intake Phase')].append(j)

    ghl_by_cat = defaultdict(list)
    for o in ghl_opps:
        cat = ghl_cat(o.get('stage_name', ''))
        if cat:
            ghl_by_cat[cat].append(o)

    # Weather section
    if weather.get('has_risk'):
        risk_items = ''.join(f'<li style="margin:4px 0;">{r["label"]}</li>' for r in weather.get('risks', []))
        weather_html = f'''
        <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;padding:12px 16px;margin-bottom:20px;">
          <strong style="color:#856404;">⚠️ Weather Risks Today</strong>
          <ul style="margin:8px 0 0 0;padding-left:18px;color:#856404;">{risk_items}</ul>
        </div>'''
    else:
        weather_html = f'''
        <div style="background:#d4edda;border:1px solid #c3e6cb;border-radius:8px;padding:12px 16px;margin-bottom:20px;">
          <strong style="color:#155724;">✅ No Weather Risks Today</strong>
          <div style="color:#155724;font-size:13px;margin-top:4px;">Max wind: {weather.get("max_wind_mph",0)} mph · Rain: {weather.get("max_precip_pct",0)}%</div>
        </div>'''

    # New jobs since yesterday
    new_activity_html = ''
    if prev_jt_jobs:
        prev_ids = {j['id'] for j in prev_jt_jobs}
        new_jobs = [j for j in jt_jobs if j['id'] not in prev_ids]
        if new_jobs:
            new_rows = ''.join(f'<li style="margin:3px 0;">{j.get("name","")} — <em>{j.get("status","")}</em></li>' for j in new_jobs[:10])
            new_activity_html = f'''
            <div style="background:#e8f4fd;border:1px solid #bee5eb;border-radius:8px;padding:12px 16px;margin-bottom:16px;">
              <strong style="color:#0c5460;">🆕 New Jobs Since Yesterday ({len(new_jobs)})</strong>
              <ul style="margin:8px 0 0 0;padding-left:18px;color:#0c5460;">{new_rows}</ul>
            </div>'''

    # JT table rows — using real custom Job Status values
    status_order = ['Active Production Phase', 'Sold | Project Intake Phase']
    jt_rows = ''
    for s in status_order:
        jobs = jt_by_status.get(s, [])
        if jobs:
            color = status_colors.get(s, '#9b59b6')
            label = 'Active Production' if 'Active' in s else 'Sold / Project Intake'
            jt_rows += f'<tr><td style="padding:6px 10px;"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{color};margin-right:6px;vertical-align:middle;"></span>{label}</td><td style="padding:6px 10px;font-weight:700;text-align:right;">{len(jobs)}</td></tr>'

    # GHL table rows (pre-sale only)
    ghl_rows = ''
    for cat in ['Appt Booked', 'Consultation', 'Proposal', 'Permitting']:
        opps = ghl_by_cat.get(cat, [])
        if opps:
            color = ghl_colors.get(cat, '#aaa')
            total_val = sum(o.get('monetaryValue', 0) or 0 for o in opps)
            val_str = f'<br><span style="font-size:11px;color:#888;">${total_val:,.0f}</span>' if total_val > 0 else ''
            ghl_rows += f'<tr><td style="padding:6px 10px;"><span style="display:inline-block;width:10px;height:10px;background:{color};transform:rotate(45deg);margin-right:6px;vertical-align:middle;"></span>{cat}</td><td style="padding:6px 10px;font-weight:700;text-align:right;">{len(opps)}{val_str}</td></tr>'

    # Active production jobs detail
    active_jobs = jt_by_status.get('Active Production Phase', [])
    active_detail = ''
    if active_jobs:
        rows = ''
        for j in active_jobs[:20]:
            addr = j.get('location', {}).get('address', 'N/A')
            city = j.get('location', {}).get('city', '')
            full_addr = f'{addr}, {city}' if city else addr
            weather_flag = ' ⚠️' if weather.get('has_risk') else ''
            rows += f'<tr><td style="padding:5px 10px;border-bottom:1px solid #eee;">{j.get("name","")}{weather_flag}</td><td style="padding:5px 10px;border-bottom:1px solid #eee;color:#666;font-size:12px;">{full_addr}</td></tr>'
        active_detail = f'''
        <h3 style="font-size:14px;color:#333;margin:20px 0 8px;">🔨 Active Production Jobs ({len(active_jobs)})</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
          <thead><tr style="background:#f8f9fa;"><th style="padding:8px 10px;text-align:left;color:#666;font-weight:600;">Job Name</th><th style="padding:8px 10px;text-align:left;color:#666;font-weight:600;">Address</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>'''

    html = f'''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;background:#f5f7fa;margin:0;padding:20px;">
<div style="max-width:640px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.1);">

  <div style="background:linear-gradient(135deg,#0a0e1a,#14203c);padding:24px 28px;">
    <div style="font-size:20px;font-weight:700;color:#fff;letter-spacing:0.5px;">⚓ RTLO Daily Operations Brief</div>
    <div style="font-size:13px;color:rgba(255,255,255,0.5);margin-top:4px;">{date_str} · Generated {time_str}</div>
  </div>

  <div style="padding:24px 28px;">

    {weather_html}
    {new_activity_html}

    <div style="display:flex;gap:16px;margin-bottom:20px;flex-wrap:wrap;">

      <div style="flex:1;min-width:220px;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
        <div style="background:#f0f7ff;padding:10px 14px;font-size:13px;font-weight:700;color:#1a3a6e;border-bottom:1px solid #e0e0e0;">📋 JobTread Jobs ({len(jt_jobs)})</div>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          {jt_rows}
          <tr style="border-top:2px solid #e0e0e0;background:#f8f9fa;"><td style="padding:7px 10px;font-weight:700;">Total</td><td style="padding:7px 10px;font-weight:700;text-align:right;">{len(jt_jobs)}</td></tr>
        </table>
      </div>

      <div style="flex:1;min-width:220px;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
        <div style="background:#fff5f5;padding:10px 14px;font-size:13px;font-weight:700;color:#6e1a1a;border-bottom:1px solid #e0e0e0;">🎯 GHL Pipeline ({len(ghl_opps)})</div>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          {ghl_rows}
          <tr style="border-top:2px solid #e0e0e0;background:#f8f9fa;"><td style="padding:7px 10px;font-weight:700;">Total</td><td style="padding:7px 10px;font-weight:700;text-align:right;">{len(ghl_opps)}</td></tr>
        </table>
      </div>

    </div>

    {active_detail}

    <div style="margin-top:24px;text-align:center;">
      <a href="{MAP_URL}" style="display:inline-block;padding:12px 28px;background:#1a3a6e;color:#fff;text-decoration:none;border-radius:8px;font-weight:700;font-size:14px;">
        🗺 Open Operations Map →
      </a>
    </div>

  </div>

  <div style="background:#f8f9fa;padding:14px 28px;font-size:11px;color:#999;border-top:1px solid #eee;">
    Rising Tide Luxury Outdoors · Auto-generated daily at 4:00 AM MST · Do not reply
  </div>

</div>
</body>
</html>'''
    return html

def send_email(subject, html_body):
    log(f'Sending email to {EMAIL_TO}: {subject}')

    smtp_user = os.environ.get('SMTP_USER', '')
    smtp_pass = os.environ.get('SMTP_PASS', '')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))

    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = EMAIL_TO
            msg.attach(MIMEText(html_body, 'html'))
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [EMAIL_TO], msg.as_bytes())
            log('Email sent via SMTP')
            return True
        except Exception as e:
            log(f'SMTP error: {e}')

    # Try sendmail
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = 'rtlo-map@rtloaz.com'
        msg['To'] = EMAIL_TO
        msg.attach(MIMEText(html_body, 'html'))
        result = subprocess.run(['sendmail', '-t'], input=msg.as_bytes(), capture_output=True, timeout=15)
        if result.returncode == 0:
            log('Email sent via sendmail')
            return True
    except Exception as e:
        log(f'sendmail error: {e}')

    # Save to file as fallback
    email_path = f'{WORK_DIR}/last_email.html'
    with open(email_path, 'w') as f:
        f.write(html_body)
    log(f'Email saved to {email_path} (configure SMTP_USER/SMTP_PASS env vars to send)')
    return False

# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    log('=== RTLO Daily Refresh Starting ===')

    # Load previous jobs for change detection
    prev_jt_jobs = load_json(f'{WORK_DIR}/jobs_geocoded.json')

    # Fetch all data
    jt_jobs, all_jt_jobs = fetch_jobtread_jobs()
    ghl_opps = fetch_ghl_opportunities()
    weather = fetch_weather_risk()

    # Rebuild map (also returns cleaned data)
    # Pass all_jt_jobs so address matching covers Opportunity-stage jobs too
    jt_clean, ghl_clean = rebuild_map(jt_jobs, ghl_opps, weather, all_jt_jobs=all_jt_jobs)

    # Write and upload data.json (shared live data source for all open map tabs)
    write_data_json(jt_clean, ghl_clean, weather)
    data_url = upload_data_json()
    if data_url:
        log(f'Live data URL: {data_url}')
        # Copy map.html to /tmp/map.html so the Flask server can serve it at /
        # DATA_JSON_URL is now hardcoded to /data endpoint (same-origin, no CORS issues)
        try:
            with open(f'{WORK_DIR}/map.html', 'r') as f:
                mhtml = f.read()
            # Replace placeholder if still present (legacy fallback)
            if 'DATA_JSON_URL_PLACEHOLDER' in mhtml:
                mhtml = mhtml.replace('DATA_JSON_URL_PLACEHOLDER', 'https://map.inhousekru.com/data')
                with open(f'{WORK_DIR}/map.html', 'w') as f:
                    f.write(mhtml)
            map_html_file = os.environ.get('MAP_HTML_FILE', '/tmp/map.html')
            with open(map_html_file, 'w') as f:
                f.write(mhtml)
            log(f'map.html copied to {map_html_file} for server-side serving')
        except Exception as e:
            log(f'Could not copy map.html: {e}')

    # Build and send email
    now = datetime.now()
    weather_flag = '⚠️ Weather Alert' if weather.get('has_risk') else '✅ Clear'
    subject = f'RTLO Daily Brief · {now.strftime("%a %b %-d")} · {len(jt_clean)} Jobs · {weather_flag}'
    email_html = build_email_html(jt_clean, ghl_clean, weather, prev_jt_jobs)
    send_email(subject, email_html)

    log('=== RTLO Daily Refresh Complete ===')

if __name__ == '__main__':
    main()
