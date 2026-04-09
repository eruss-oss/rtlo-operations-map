"""
Test Drive folder matching against current data.json entries.
"""
import json
import re
import sys
sys.path.insert(0, '/home/ubuntu/rtlo-map')
from build_drive_index import build_drive_index, norm_drive_name

def norm_job_name(name, city=''):
    """Normalize a job/lead name + city for Drive folder matching."""
    # Remove special chars, lowercase
    name = re.sub(r'[^a-z0-9 &]', '', (name or '').lower())
    city = re.sub(r'[^a-z0-9 ]', '', (city or '').lower()).strip()
    # Combine
    combined = f'{name} {city}'.strip()
    combined = ' '.join(combined.split())
    return combined

def extract_city_from_address(addr):
    """Extract city from a full address string."""
    if not addr:
        return ''
    # Try to extract city from "123 Street, City, AZ 85xxx" format
    parts = [p.strip() for p in addr.split(',')]
    if len(parts) >= 2:
        # City is typically the second-to-last part before state
        city_candidate = parts[-2].strip() if len(parts) >= 3 else parts[1].strip()
        # Remove state abbreviation if present
        city_candidate = re.sub(r'\b[A-Z]{2}\b', '', city_candidate).strip()
        return city_candidate.lower()
    return ''

def find_drive_folder(name, city, drive_index):
    """Find best matching Drive folder for a job/lead."""
    if not name:
        return None
    
    # Normalize the search key
    search_key = norm_job_name(name, city)
    
    # Direct match
    if search_key in drive_index:
        return drive_index[search_key]
    
    # Try partial matches - check if all words in drive key appear in search key
    best_match = None
    best_score = 0
    search_words = set(search_key.split())
    
    for drive_key, folder_data in drive_index.items():
        drive_words = set(drive_key.split())
        # Score = number of matching words
        common = search_words & drive_words
        if len(common) >= 2:  # At least 2 words must match (name + city)
            score = len(common) / max(len(drive_words), len(search_words))
            if score > best_score:
                best_score = score
                best_match = folder_data
    
    if best_score >= 0.5:  # At least 50% word overlap
        return best_match
    return None

# Load current data.json
with open('/home/ubuntu/rtlo-map/data.json') as f:
    data = json.load(f)

drive_index = build_drive_index()
print(f'Drive index: {len(drive_index)} folders\n')

print('=== JT JOBS ===')
matched_jt = 0
for job in data.get('jt_jobs', []):
    name = job.get('name', '')
    addr = job.get('location', {}).get('address', '') or ''
    city = extract_city_from_address(addr)
    result = find_drive_folder(name, city, drive_index)
    status = '✅' if result else '❌'
    print(f'{status} {name} ({city}) -> {result[1] if result else "NO MATCH"}')
    if result:
        matched_jt += 1

print(f'\nJT: {matched_jt}/{len(data.get("jt_jobs", []))} matched\n')

print('=== GHL OPPS ===')
matched_ghl = 0
for opp in data.get('ghl_opps', []):
    name = opp.get('name', '')
    addr = opp.get('full_address', '')
    city = extract_city_from_address(addr)
    result = find_drive_folder(name, city, drive_index)
    status = '✅' if result else '❌'
    print(f'{status} {name} ({city}) -> {result[1] if result else "NO MATCH"}')
    if result:
        matched_ghl += 1

print(f'\nGHL: {matched_ghl}/{len(data.get("ghl_opps", []))} matched')
