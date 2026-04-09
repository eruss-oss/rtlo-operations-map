#!/usr/bin/env python3.11
"""
RTLO Map Refresh Server
- /refresh  : triggers a live data pull (map refresh button)
- /location : receives crew GPS pings from iOS Shortcuts (every 5 min)
- /crew     : returns current crew_locations.json for the map to display
- /health   : health check

Run with: python3 refresh_server.py
Listens on: 0.0.0.0:5050
"""

import subprocess
import threading
import time
import os
import json
from flask import Flask, jsonify, request, send_file, Response
from datetime import datetime, timezone

app = Flask(__name__)
WORK_DIR = os.environ.get('WORK_DIR', '/home/ubuntu/rtlo-map')
# Use /tmp for crew file since Render's project dir is read-only on free tier
CREW_FILE = os.environ.get('CREW_FILE', '/tmp/crew_locations.json')
# Map HTML is written to /tmp/map.html by the refresh process
MAP_HTML_FILE = os.environ.get('MAP_HTML_FILE', '/tmp/map.html')

# Prevent concurrent refresh runs
_refresh_lock = threading.Lock()
_last_refresh = 0
MIN_REFRESH_INTERVAL = 60  # seconds

# Crew location lock for thread-safe file writes
_crew_lock = threading.Lock()

# Crew member colors — assigned by order of first ping, up to 10
CREW_COLORS = [
    '#FF6B35',  # orange
    '#00D4FF',  # cyan
    '#FFD700',  # gold
    '#FF69B4',  # pink
    '#7CFC00',  # lawn green
    '#DA70D6',  # orchid
    '#00CED1',  # dark turquoise
    '#FF4500',  # orange red
    '#ADFF2F',  # green yellow
    '#FF1493',  # deep pink
]

# Shared API key for Shortcut authentication (simple bearer token)
# Employees enter this once when setting up their Shortcut
CREW_API_KEY = os.environ.get('CREW_API_KEY', 'rtlo-crew-2026')

# On startup, copy map.html from project dir to /tmp so it can be served.
# This ensures the map is available immediately without waiting for a refresh.
def _init_map_html():
    if not os.path.exists(MAP_HTML_FILE):
        src = os.path.join(WORK_DIR, 'map.html')
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, MAP_HTML_FILE)

_init_map_html()


def load_crew():
    """Load crew_locations.json, return dict keyed by employee name."""
    try:
        if os.path.exists(CREW_FILE):
            with open(CREW_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_crew(crew):
    """Save crew dict to crew_locations.json."""
    with open(CREW_FILE, 'w') as f:
        json.dump(crew, f, indent=2)


def assign_color(name, crew):
    """Assign a consistent color to a crew member based on their position in the roster."""
    names = sorted(crew.keys())
    if name not in names:
        names.append(name)
    idx = names.index(name) % len(CREW_COLORS)
    return CREW_COLORS[idx]


def run_refresh():
    """Run daily_refresh.py and return the new data.json CDN URL."""
    try:
        result = subprocess.run(
            ['python3', f'{WORK_DIR}/daily_refresh.py'],
            capture_output=True, text=True, timeout=300,
            cwd=WORK_DIR
        )
        for line in result.stdout.splitlines():
            if 'data.json uploaded:' in line:
                url = line.split('data.json uploaded:')[-1].strip()
                return url, None
        if result.returncode != 0:
            return None, result.stderr[-500:] if result.stderr else 'Unknown error'
        url_file = f'{WORK_DIR}/data_cdn_url.txt'
        if os.path.exists(url_file):
            with open(url_file) as f:
                return f.read().strip(), None
        return None, 'Could not extract CDN URL from output'
    except subprocess.TimeoutExpired:
        return None, 'Refresh timed out after 5 minutes'
    except Exception as e:
        return None, str(e)


@app.route('/refresh', methods=['GET', 'POST'])
def refresh():
    global _last_refresh
    now = time.time()

    if not _refresh_lock.acquire(blocking=False):
        return jsonify({
            'status': 'busy',
            'message': 'A refresh is already in progress. Please wait.'
        }), 429

    try:
        if now - _last_refresh < MIN_REFRESH_INTERVAL:
            wait = int(MIN_REFRESH_INTERVAL - (now - _last_refresh))
            return jsonify({
                'status': 'throttled',
                'message': f'Refreshed too recently. Try again in {wait}s.'
            }), 429

        _last_refresh = now
        url, error = run_refresh()

        if url:
            return jsonify({
                'status': 'ok',
                'data_url': url,
                'refreshed_at': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'message': error or 'Refresh failed'
            }), 500
    finally:
        _refresh_lock.release()


@app.route('/location', methods=['POST'])
def location():
    """
    Receive a crew member's GPS location from their iOS Shortcut.

    Expected JSON body:
    {
        "name": "Eric",          # employee first name
        "lat": 33.4484,          # latitude
        "lon": -112.0740,        # longitude
        "api_key": "rtlo-crew-2026"  # shared auth key
    }

    Returns:
    { "status": "ok", "color": "#FF6B35" }
    """
    data = request.get_json(silent=True) or {}

    # Auth check
    if data.get('api_key') != CREW_API_KEY:
        return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401

    name = (data.get('name') or '').strip()
    lat = data.get('lat')
    lon = data.get('lon')

    if not name:
        return jsonify({'status': 'error', 'message': 'name is required'}), 400
    if lat is None or lon is None:
        return jsonify({'status': 'error', 'message': 'lat and lon are required'}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'lat/lon must be numbers'}), 400

    # Sanity check — must be in Arizona-ish area (loose bounds)
    if not (30.0 <= lat <= 38.0 and -115.0 <= lon <= -108.0):
        return jsonify({'status': 'error', 'message': 'Coordinates out of expected range'}), 400

    with _crew_lock:
        crew = load_crew()
        color = assign_color(name, crew)
        crew[name] = {
            'name': name,
            'lat': lat,
            'lon': lon,
            'color': color,
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'active': True
        }
        save_crew(crew)

    return jsonify({'status': 'ok', 'color': color})


@app.route('/location', methods=['DELETE'])
def location_off():
    """
    Employee turns off their location sharing.
    Body: { "name": "Eric", "api_key": "rtlo-crew-2026" }
    Sets active: false so they disappear from the map.
    """
    data = request.get_json(silent=True) or {}

    if data.get('api_key') != CREW_API_KEY:
        return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401

    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'status': 'error', 'message': 'name is required'}), 400

    with _crew_lock:
        crew = load_crew()
        if name in crew:
            crew[name]['active'] = False
            save_crew(crew)

    return jsonify({'status': 'ok', 'message': f'{name} location sharing paused'})


@app.route('/crew', methods=['GET'])
def crew():
    """
    Return current crew locations for the map to display.
    Only returns active members (active: true) updated in the last 30 minutes.
    """
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=30)

    crew_data = load_crew()
    active = []
    for member in crew_data.values():
        if not member.get('active', True):
            continue
        try:
            updated = datetime.fromisoformat(member['updated_at'])
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
            if updated < cutoff:
                continue  # stale — phone off or app paused
        except Exception:
            continue
        active.append(member)

    return jsonify({'crew': active, 'count': len(active)})


@app.route('/', methods=['GET'])
def index():
    """Serve the map HTML directly at the root URL."""
    if os.path.exists(MAP_HTML_FILE):
        return send_file(MAP_HTML_FILE, mimetype='text/html')
    # Fallback: redirect to CDN version if map.html hasn't been built yet
    cdn_url_file = os.path.join(WORK_DIR, 'data_cdn_url.txt')
    fallback = 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663500405152/WGBQHqsgTnoVcsDn.html'
    return Response(
        f'<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0;url={fallback}">'
        f'<title>RTLO Map</title></head><body>'
        f'<p>Loading map... <a href="{fallback}">Click here if not redirected.</a></p>'
        f'</body></html>',
        mimetype='text/html'
    )


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)
