#!/usr/bin/env python3.11
"""
Explore contact sub-objects in JobTread API
"""
import requests
import json

GRANT_KEY = "22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB"
API_URL = "https://api.jobtread.com/pave"
ORG_ID = "22PFyR85uqXr"
CONTACT_ID = "22PGgX9Hm7Q5"  # Eric Russell

def query(payload):
    resp = requests.post(API_URL, json=payload)
    return resp.status_code, resp.text

# Try sub-objects on contact
print("=== Contact sub-objects ===")
sub_objects = [
    ("emails", {"nodes": {"id": {}, "address": {}}}),
    ("phones", {"nodes": {"id": {}, "number": {}}}),
    ("locations", {"nodes": {"id": {}, "address": {}}}),
    ("addresses", {"nodes": {"id": {}, "address": {}}}),
    ("location", {"id": {}, "address": {}}),
    ("jobs", {"nodes": {"id": {}, "name": {}}}),
    ("tags", {"nodes": {"id": {}, "name": {}}}),
    ("customFields", {"nodes": {"id": {}, "name": {}, "value": {}}}),
    ("contactType", {"id": {}, "name": {}}),
    ("contactTypes", {"nodes": {"id": {}, "name": {}}}),
]

for field, sub in sub_objects:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "contact": {
                "$": {"id": CONTACT_ID},
                "id": {},
                "name": {},
                field: sub
            }
        }
    })
    if status == 200:
        data = json.loads(text)
        val = data.get("contact", {}).get(field, "N/A")
        print(f"  OK: {field} = {json.dumps(val)[:200]}")
    else:
        print(f"  ERR: {field} -> {text[:80]}")

# Also check what fields are on the organization's contacts
print("\n=== Organization contacts - more fields ===")
more_fields = [
    ("emails", {"nodes": {"id": {}, "address": {}}}),
    ("phones", {"nodes": {"id": {}, "number": {}}}),
    ("location", {"id": {}, "address": {}}),
    ("locations", {"nodes": {"id": {}, "address": {}}}),
    ("tags", {"nodes": {"id": {}, "name": {}}}),
    ("contactType", {"id": {}, "name": {}}),
]

for field, sub in more_fields:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                "contacts": {
                    "$": {"size": 2},
                    "nodes": {
                        "id": {},
                        "name": {},
                        field: sub
                    }
                }
            }
        }
    })
    if status == 200:
        data = json.loads(text)
        nodes = data.get("organization", {}).get("contacts", {}).get("nodes", [])
        print(f"  OK: {field}")
        for n in nodes:
            print(f"    {n['name']}: {json.dumps(n.get(field, 'N/A'))[:150]}")
    else:
        print(f"  ERR: {field} -> {text[:80]}")

# Check if there's a separate vendors endpoint or contactTypes
print("\n=== Organization-level vendor/type fields ===")
org_fields = [
    ("contactTypes", {"nodes": {"id": {}, "name": {}}}),
    ("vendors", {"nodes": {"id": {}, "name": {}}}),
    ("subcontractors", {"nodes": {"id": {}, "name": {}}}),
]
for field, sub in org_fields:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                field: sub
            }
        }
    })
    if status == 200:
        data = json.loads(text)
        val = data.get("organization", {}).get(field, "N/A")
        print(f"  OK: {field} = {json.dumps(val)[:300]}")
    else:
        print(f"  ERR: {field} -> {text[:80]}")
