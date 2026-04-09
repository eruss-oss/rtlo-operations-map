#!/usr/bin/env python3.11
"""
Probe cost items and their vendor associations
Also look at contact's jobs to find type info
"""
import requests
import json

GRANT_KEY = "22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB"
API_URL = "https://api.jobtread.com/pave"
ORG_ID = "22PFyR85uqXr"
JOB_ID = "22PK2vLzgLDC"
COST_ITEM_ID = "22PUKcWvTnBh"

def query(payload):
    resp = requests.post(API_URL, json=payload)
    return resp.status_code, resp.text

# Probe cost item fields
print("=== Cost item fields ===")
cost_fields = [
    "vendor", "contact", "subcontractor", "assignedTo", "assignee",
    "supplier", "source", "category", "type"
]
for field in cost_fields:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "costItem": {
                "$": {"id": COST_ITEM_ID},
                "id": {},
                "name": {},
                field: {"id": {}, "name": {}}
            }
        }
    })
    if status == 200:
        data = json.loads(text)
        val = data.get("costItem", {}).get(field)
        print(f"  OK: {field} = {json.dumps(val)[:200]}")
    else:
        print(f"  ERR: {field} -> {text[:100]}")

# Look at what fields the contact object actually has
# by checking the JobTread API docs approach - try "contactRoles" 
print("\n=== Contact roles/memberships ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "contacts": {
                "$": {"size": 10},
                "nodes": {
                    "id": {},
                    "name": {},
                    "memberships": {
                        "nodes": {
                            "id": {},
                            "role": {}
                        }
                    }
                }
            }
        }
    }
})
print(f"Status: {status}, Response: {text[:500]}")

# Try looking at the contact with "jobs" sub-field
print("\n=== Contact jobs ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "contact": {
            "$": {"id": "22PGgX9Hm7Q5"},
            "id": {},
            "name": {},
            "jobs": {
                "nodes": {
                    "id": {},
                    "name": {}
                }
            }
        }
    }
})
print(f"Status: {status}, Response: {text[:300]}")

# Try the organization's contact list with "role" filter
print("\n=== Contact list with role filter ===")
for role in ["subcontractor", "vendor", "customer", "employee", "supplier"]:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                "contacts": {
                    "$": {"size": 5, "roles": [role]},
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
        print(f"  OK role={role}: {[n['name'] for n in nodes]}")
    else:
        print(f"  ERR role={role}: {text[:100]}")

# Try "contactRoles" on the organization
print("\n=== Organization contactRoles ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "contactRoles": {
                "nodes": {
                    "id": {},
                    "name": {}
                }
            }
        }
    }
})
print(f"Status: {status}, Response: {text[:300]}")
