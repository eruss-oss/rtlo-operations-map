import json, os

BASE = "/home/ubuntu/rtlo-map"

def load(f): return json.load(open(f"{BASE}/{f}"))
def save(f, data): 
    with open(f"{BASE}/{f}", "w") as fp:
        json.dump(data, fp, indent=2)
    print(f"Saved {f} ({len(data)} entries)")

# ─────────────────────────────────────────────
# 1. NURSERY: Fix Aird Nursery → Arid Solutions Nursery
# ─────────────────────────────────────────────
nursery = load("nursery_stores.json")
# Remove any entry with "Aird" or wrong address
nursery = [s for s in nursery if "aird" not in s["name"].lower() and "northern" not in s.get("address","").lower()]
# Add correct entry
nursery.append({
    "name": "Arid Solutions Nursery",
    "address": "3815 E Southern Ave, Phoenix, AZ 85040",
    "lat": 33.3925554,
    "lng": -111.9996032,
    "showroom": False,
    "notes": "Wholesale plant nursery. Open weekdays 6am–2pm."
})
save("nursery_stores.json", nursery)

# ─────────────────────────────────────────────
# 2. FLOOR & DECOR: Add Mesa and Scottsdale (the link was the Mesa store)
# ─────────────────────────────────────────────
fd = load("floor_decor_stores.json")
existing_addrs = [s["address"].lower() for s in fd]

new_fd = [
    {
        "name": "Floor & Decor - Mesa",
        "address": "7022 E Hampton Ave, Mesa, AZ 85209",
        "lat": 33.3914679,
        "lng": -111.6795474,
        "showroom": True,
        "notes": "Full flooring showroom. Tile, stone, wood, vinyl, fixtures."
    },
    {
        "name": "Floor & Decor - Scottsdale",
        "address": "15515 N Hayden Rd, Scottsdale, AZ 85260",
        "lat": 33.6267448,
        "lng": -111.8966677,
        "showroom": True,
        "notes": "Opened October 2025. Full flooring showroom."
    },
]
for entry in new_fd:
    if entry["address"].lower() not in existing_addrs:
        fd.append(entry)
        print(f"Added: {entry['name']}")
    else:
        print(f"Already exists: {entry['name']}")
save("floor_decor_stores.json", fd)

# ─────────────────────────────────────────────
# 3. HARDSCAPE: Remove Pavestone entry, add Pioneer Landscape Centers at that address
#    Remove "Telluride Stone (SiteOne)" duplicate (already in SiteOne layer)
# ─────────────────────────────────────────────
hardscape = load("hardscape_stores.json")
hardscape = [s for s in hardscape if "pavestone" not in s["name"].lower() and "telluride" not in s["name"].lower()]
hardscape.append({
    "name": "Pioneer Landscape Centers",
    "address": "1515 W Deer Valley Rd, Phoenix, AZ 85027",
    "lat": 33.6862,
    "lng": -112.0467,
    "showroom": True,
    "notes": "SiteOne family. Full hardscape showroom — pavers, walls, edging."
})
save("hardscape_stores.json", hardscape)

# ─────────────────────────────────────────────
# 4. SITEONE: Remove #332 (22010 N 21st Ave)
# ─────────────────────────────────────────────
siteone = load("siteone_stores.json")
before = len(siteone)
siteone = [s for s in siteone if "332" not in s["name"] and "22010" not in s.get("address","")]
print(f"SiteOne: removed {before - len(siteone)} entry/entries")
save("siteone_stores.json", siteone)

# ─────────────────────────────────────────────
# 5. ROCK: Add ABC Sand & Rock - Glendale
# ─────────────────────────────────────────────
rock = load("rock_stores.json")
rock.append({
    "name": "ABC Sand & Rock - Glendale",
    "address": "5401 N 119th Ave, Glendale, AZ 85307",
    "lat": 33.4749439,
    "lng": -112.3151391,
    "showroom": False,
    "notes": "Second ABC Sand & Rock location. Decorative rock, sand, gravel."
})
save("rock_stores.json", rock)

# ─────────────────────────────────────────────
# 6. MISC: Create misc_stores.json with Sonoran Lighting Supply
# ─────────────────────────────────────────────
misc = [
    {
        "name": "Sonoran Lighting Supply",
        "address": "2920 E Mohawk Ln Ste 102, Phoenix, AZ 85050",
        "lat": 33.6738345,
        "lng": -112.0194569,
        "showroom": False,
        "notes": "Lighting wholesale and design center. Outdoor and landscape lighting."
    }
]
save("misc_stores.json", misc)

print("\nAll changes applied successfully.")
