#!/usr/bin/env python3.11
"""
Probe contact type fields - looking for subcontractor/vendor type
"""
import requests
import json

GRANT_KEY = "22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB"
API_URL = "https://api.jobtread.com/pave"
ORG_ID = "22PFyR85uqXr"

def query(payload):
    resp = requests.post(API_URL, json=payload)
    return resp.status_code, resp.text

# Try contact type as nested object
print("=== Contact type as nested object ===")
nested_tests = [
    ("type", {"id": {}, "name": {}}),
    ("contactType", {"id": {}, "name": {}}),
    ("category", {"id": {}, "name": {}}),
    ("role", {"id": {}, "name": {}}),
    ("roles", {"nodes": {"id": {}, "name": {}}}),
    ("types", {"nodes": {"id": {}, "name": {}}}),
]

for field, sub in nested_tests:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                "contacts": {
                    "$": {"size": 3},
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
            print(f"    {n['name']}: {json.dumps(n.get(field))[:100]}")
    else:
        print(f"  ERR: {field} -> {text[:100]}")

# Try filtering contacts by type
print("\n=== Filter contacts by type/role ===")
filter_tests = [
    {"type": "subcontractor"},
    {"type": "vendor"},
    {"type": "supplier"},
    {"role": "subcontractor"},
    {"isVendor": True},
    {"isSubcontractor": True},
]

for filt in filter_tests:
    key = list(filt.keys())[0]
    val = list(filt.values())[0]
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                "contacts": {
                    "$": {"size": 5, **filt},
                    "nodes": {
                        "id": {},
                        "name": {}
                    }
                }
            }
        }
    })
    if status == 200:
        data = json.loads(text)
        nodes = data.get("organization", {}).get("contacts", {}).get("nodes", [])
        print(f"  OK filter {key}={val}: {[n['name'] for n in nodes]}")
    else:
        print(f"  ERR filter {key}={val}: {text[:100]}")

# Try looking at the contact object's available fields via introspection
print("\n=== Try __typename on contact ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "contacts": {
                "$": {"size": 5},
                "nodes": {
                    "id": {},
                    "name": {},
                    "__typename": {}
                }
            }
        }
    }
})
print(f"Status: {status}, Response: {text[:300]}")
