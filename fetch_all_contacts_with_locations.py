#!/usr/bin/env python3.11
"""
Fetch ALL contacts from JobTread with their locations
"""
import requests
import json

GRANT_KEY = "22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB"
API_URL = "https://api.jobtread.com/pave"
ORG_ID = "22PFyR85uqXr"

def query(payload):
    resp = requests.post(API_URL, json=payload)
    resp.raise_for_status()
    return resp.json()

all_contacts = []
page = None
page_num = 1

while True:
    print(f"Fetching contacts page {page_num}...")
    q = {
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                "contacts": {
                    "$": {"size": 25, **({"page": page} if page else {})},
                    "nextPage": {},
                    "nodes": {
                        "id": {},
                        "name": {},
                        "firstName": {},
                        "lastName": {},
                        "createdAt": {},
                        "locations": {
                            "nodes": {
                                "id": {},
                                "address": {}
                            }
                        }
                    }
                }
            }
        }
    }
    result = query(q)
    contacts_data = result.get("organization", {}).get("contacts", {})
    nodes = contacts_data.get("nodes", [])
    all_contacts.extend(nodes)
    page = contacts_data.get("nextPage")
    print(f"  Got {len(nodes)} contacts (total: {len(all_contacts)})")
    if not page:
        break
    page_num += 1

print(f"\nTotal contacts: {len(all_contacts)}")

# Print all contacts
print("\n--- All Contacts ---")
for c in all_contacts:
    locs = c.get("locations", {}).get("nodes", [])
    addr = locs[0]["address"] if locs else "No address"
    print(f"  {c['name']} | {addr}")

# Save
with open("/home/ubuntu/rtlo-map/jobtread_contacts.json", "w") as f:
    json.dump(all_contacts, f, indent=2)
print(f"\nSaved to jobtread_contacts.json")
