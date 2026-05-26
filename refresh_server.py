#!/usr/bin/env python3.11
"""
RTLO Map Refresh Server
- /         : serves the map HTML directly
- /refresh  : triggers a live data pull in a BACKGROUND THREAD (never blocks the worker)
- /location : receives crew GPS pings from iOS Shortcuts
- /crew     : returns current crew locations for the map
- /data     : serves data.json directly (avoids CDN CORS issues)
- /health   : health check (returns 200 immediately)
- /healthz  : lightweight health check (no file I/O)

IMPORTANT: daily_refresh.py runs in a background thread so it NEVER blocks
the gunicorn worker. All web requests are served instantly regardless of
whether a refresh is in progress.

Run with: gunicorn refresh_server:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --keep-alive 5 --preload
"""

import subprocess
import threading
import time
import os
import json
from flask import Flask, jsonify, request, send_file, Response
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
WORK_DIR = os.environ.get('WORK_DIR', '/home/ubuntu/rtlo-map')
CREW_FILE = os.environ.get('CREW_FILE', '/tmp/crew_locations.json')
MAP_HTML_FILE = os.environ.get('MAP_HTML_FILE', '/tmp/map.html')

# ─── Refresh state (background thread) ───────────────────────────────────────
_refresh_lock = threading.Lock()
_refresh_running = False
_last_refresh = 0
_last_refresh_status = None   # 'ok' | 'error'
_last_refresh_error = None
MIN_REFRESH_INTERVAL = 60     # seconds between manual refreshes

# ─── Crew location state ──────────────────────────────────────────────────────
_crew_lock = threading.Lock()

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

CREW_API_KEY = os.environ.get('CREW_API_KEY', 'rtlo-crew-2026')


# ─── Startup: copy map.html from project dir to /tmp ─────────────────────────
def _init_map_html():
    if not os.path.exists(MAP_HTML_FILE):
        src = os.path.join(WORK_DIR, 'map.html')
        if os.path.exists(src):
            import shutil
            shutil.copy2(src, MAP_HTML_FILE)

_init_map_html()


# ─── Crew helpers ─────────────────────────────────────────────────────────────
def load_crew():
    try:
        if os.path.exists(CREW_FILE):
            with open(CREW_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_crew(crew):
    with open(CREW_FILE, 'w') as f:
        json.dump(crew, f, indent=2)


def assign_color(name, crew):
    names = sorted(crew.keys())
    if name not in names:
        names.append(name)
    idx = names.index(name) % len(CREW_COLORS)
    return CREW_COLORS[idx]


# ─── Background refresh ───────────────────────────────────────────────────────
def _run_refresh_background():
    """
    Run daily_refresh.py in a background thread.
    Never called directly from a request handler — always via threading.Thread.
    This ensures the gunicorn worker is NEVER blocked.
    """
    global _refresh_running, _last_refresh_status, _last_refresh_error
    try:
        result = subprocess.run(
            ['python3', f'{WORK_DIR}/daily_refresh.py'],
            capture_output=True, text=True,
            timeout=600,   # 10 min hard limit — background, so no worker impact
            cwd=WORK_DIR
        )
        if result.returncode == 0:
            _last_refresh_status = 'ok'
            _last_refresh_error = None
        else:
            _last_refresh_status = 'error'
            _last_refresh_error = (result.stderr or 'Unknown error')[-500:]
    except subprocess.TimeoutExpired:
        _last_refresh_status = 'error'
        _last_refresh_error = 'Refresh timed out after 10 minutes'
    except Exception as e:
        _last_refresh_status = 'error'
        _last_refresh_error = str(e)
    finally:
        _refresh_running = False
        _refresh_lock.release()


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/healthz', methods=['GET'])
def healthz():
    """Lightweight health check — no file I/O, always instant."""
    return 'OK', 200


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'time': datetime.now().isoformat(),
        'refresh_running': _refresh_running,
        'last_refresh_status': _last_refresh_status,
    })


@app.route('/refresh', methods=['GET', 'POST'])
def refresh():
    """
    Trigger a data refresh. Returns immediately — refresh runs in background.
    The map auto-reloads data when the refresh completes.
    """
    global _refresh_running, _last_refresh

    now = time.time()

    if _refresh_running:
        return jsonify({
            'status': 'busy',
            'message': 'A refresh is already in progress. Check back in a few minutes.'
        }), 429

    if now - _last_refresh < MIN_REFRESH_INTERVAL:
        wait = int(MIN_REFRESH_INTERVAL - (now - _last_refresh))
        return jsonify({
            'status': 'throttled',
            'message': f'Refreshed too recently. Try again in {wait}s.'
        }), 429

    # Try to acquire the lock non-blocking
    if not _refresh_lock.acquire(blocking=False):
        return jsonify({
            'status': 'busy',
            'message': 'Refresh lock held. Try again shortly.'
        }), 429

    _refresh_running = True
    _last_refresh = now

    # Fire and forget — background thread, worker stays free
    t = threading.Thread(target=_run_refresh_background, daemon=True)
    t.start()

    return jsonify({
        'status': 'started',
        'message': 'Refresh started in background. Map data will update in ~3 minutes.'
    })


@app.route('/location', methods=['POST'])
def location():
    """
    Receive a crew member's GPS location from their iOS Shortcut.
    Expected JSON: { "name": "Eric", "lat": 33.4484, "lon": -112.0740, "api_key": "rtlo-crew-2026" }
    """
    data = request.get_json(silent=True) or {}

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

    # Sanity check — must be in Arizona-ish area
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
    """Employee turns off location sharing."""
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
    """Return active crew members updated in the last 30 minutes."""
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
                continue
        except Exception:
            continue
        active.append(member)

    return jsonify({'crew': active, 'count': len(active)})


@app.route('/data', methods=['GET'])
def data():
    """Serve data.json directly — avoids CDN CORS issues."""
    data_file = os.path.join(WORK_DIR, 'data.json')
    if os.path.exists(data_file):
        resp = send_file(data_file, mimetype='application/json')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Cache-Control'] = 'no-cache'
        return resp
    return jsonify({'error': 'data.json not found'}), 404


@app.route('/', methods=['GET'])
def index():
    """Serve the map HTML at the root URL."""
    if os.path.exists(MAP_HTML_FILE):
        return send_file(MAP_HTML_FILE, mimetype='text/html')
    # Fallback redirect if map.html hasn't been built yet
    fallback = 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663500405152/WGBQHqsgTnoVcsDn.html'
    return Response(
        f'<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0;url={fallback}">'
        f'<title>RTLO Map</title></head><body>'
        f'<p>Loading map... <a href="{fallback}">Click here if not redirected.</a></p>'
        f'</body></html>',
        mimetype='text/html'
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=False)
