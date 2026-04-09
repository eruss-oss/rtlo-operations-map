#!/usr/bin/env python3.11
"""
Fetch vendors/contacts from JobTread API for RTLO
Uses the correct JobTread JSON query format (not GraphQL)
Grant Key: 22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB
"""

import requests
import json

GRANT_KEY = "22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB"
API_URL = "https://api.jobtread.com/pave"

def query(payload):
    resp = requests.post(API_URL, json=payload)
    resp.raise_for_status()
    return resp.json()

# Step 1: Get org ID
print("=== Fetching org info ===")
result = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "currentGrant": {
            "id": {},
            "user": {
                "id": {},
                "name": {},
                "memberships": {
                    "nodes": {
                        "organization": {
                            "id": {},
                            "name": {}
                        }
                    }
                }
            }
        }
    }
})

memberships = result["currentGrant"]["user"]["memberships"]["nodes"]
org_info = memberships[0]["organization"]
ORG_ID = org_info["id"]
ORG_NAME = org_info["name"]
print(f"Organization: {ORG_NAME} ({ORG_ID})")

# Step 2: Fetch all contacts (vendors, customers, etc.)
print("\n=== Fetching contacts ===")
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
                    "$": {"size": 100, **({"page": page} if page else {})},
                    "nextPage": {},
                    "nodes": {
                        "id": {},
                        "name": {},
                        "type": {},
                        "email": {},
                        "phone": {},
                        "address": {},
                        "city": {},
                        "state": {},
                        "zip": {},
                        "notes": {}
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
    print(f"  Got {len(nodes)} contacts (total: {len(all_contacts)}). Next page: {page}")
    if not page:
        break
    page_num += 1

print(f"\nTotal contacts: {len(all_contacts)}")

# Show types
types = {}
for c in all_contacts:
    t = c.get("type", "unknown") or "unknown"
    types[t] = types.get(t, 0) + 1
print(f"Contact types: {types}")

# Print all contacts
print("\n--- All Contacts ---")
for c in all_contacts:
    addr_parts = [c.get("address",""), c.get("city",""), c.get("state",""), c.get("zip","")]
    addr = ", ".join(p for p in addr_parts if p)
    print(f"  [{c.get('type','?')}] {c['name']} | {addr} | {c.get('phone','')} | {c.get('email','')}")

# Save
with open("/home/ubuntu/rtlo-map/jobtread_contacts.json", "w") as f:
    json.dump(all_contacts, f, indent=2)
print(f"\nSaved {len(all_contacts)} contacts to jobtread_contacts.json")
