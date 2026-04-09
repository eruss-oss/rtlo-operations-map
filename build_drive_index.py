"""
Build a Drive folder index from RTLO-Jobs shared drive.
Returns a dict: normalized_name_key -> (folder_id, folder_name, drive_url)
"""
import subprocess
import json
import re

DRIVE_ID = '0AOMdyNURgNqSUk9PVA'
RCLONE_CONF = '/home/ubuntu/.gdrive-rclone.ini'

def norm_drive_name(name):
    """Normalize folder name to 'lastname city' for fuzzy matching."""
    # Strip leading/trailing spaces
    name = name.strip()
    # Remove common suffixes
    for suffix in [' for sharing', ' shared', ' docs', ' renders', ' inspo', ' family']:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)
    # Normalize separators (dash, hyphen, em-dash) to space
    name = re.sub(r'[\-–—]+', ' ', name)
    # Remove special chars except spaces
    name = re.sub(r'[^a-z0-9 ]', '', name.lower())
    # Collapse whitespace
    name = ' '.join(name.split())
    return name

def get_drive_folders():
    """Fetch all folders from RTLO-Jobs shared drive via rclone."""
    cmd = [
        'rclone', 'lsjson',
        f'manus_google_drive,shared_with_me=false,team_drive={DRIVE_ID}:',
        '--config', RCLONE_CONF,
        '--dirs-only'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f'rclone error: {result.stderr}')
        return []
    try:
        return json.loads(result.stdout)
    except Exception as e:
        print(f'JSON parse error: {e}')
        return []

def build_drive_index():
    """Build normalized name -> (id, name, url) lookup."""
    folders = get_drive_folders()
    index = {}
    for f in folders:
        name = f.get('Name', '').strip()
        fid = f.get('ID', '')
        if not fid or name.startswith('ARCHIVE') or name.startswith('.'):
            continue
        url = f'https://drive.google.com/drive/folders/{fid}'
        key = norm_drive_name(name)
        index[key] = (fid, name, url)
    return index

if __name__ == '__main__':
    idx = build_drive_index()
    print(f'Built Drive index with {len(idx)} folders:')
    for k, (fid, name, url) in sorted(idx.items()):
        print(f'  [{k}] -> {name}')
