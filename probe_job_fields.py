#!/usr/bin/env python3.11
"""
Probe job fields to find vendor/subcontractor connections
"""
import requests
import json

GRANT_KEY = "22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB"
API_URL = "https://api.jobtread.com/pave"
ORG_ID = "22PFyR85uqXr"

def query(payload):
    resp = requests.post(API_URL, json=payload)
    return resp.status_code, resp.text

# Get first job ID
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "jobs": {
                "$": {"size": 1},
                "nodes": {
                    "id": {},
                    "name": {}
                }
            }
        }
    }
})
data = json.loads(text)
job_id = data["organization"]["jobs"]["nodes"][0]["id"]
job_name = data["organization"]["jobs"]["nodes"][0]["name"]
print(f"Testing with job: {job_name} ({job_id})")

# Probe job sub-fields
job_sub_fields = [
    ("contacts", {"nodes": {"id": {}, "name": {}}}),
    ("subcontractors", {"nodes": {"id": {}, "name": {}}}),
    ("vendors", {"nodes": {"id": {}, "name": {}}}),
    ("assignedContacts", {"nodes": {"id": {}, "name": {}}}),
    ("jobContacts", {"nodes": {"id": {}, "name": {}}}),
    ("crew", {"nodes": {"id": {}, "name": {}}}),
    ("members", {"nodes": {"id": {}, "name": {}}}),
    ("tasks", {"nodes": {"id": {}, "name": {}}}),
    ("expenses", {"nodes": {"id": {}, "name": {}}}),
    ("lineItems", {"nodes": {"id": {}, "name": {}}}),
    ("costItems", {"nodes": {"id": {}, "name": {}}}),
    ("bills", {"nodes": {"id": {}, "vendor": {"id": {}, "name": {}}}}),
]

print("\n=== Job sub-fields ===")
for field, sub in job_sub_fields:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "job": {
                "$": {"id": job_id},
                "id": {},
                "name": {},
                field: sub
            }
        }
    })
    if status == 200:
        data = json.loads(text)
        val = data.get("job", {}).get(field)
        print(f"  OK: {field} = {json.dumps(val)[:200]}")
    else:
        print(f"  ERR: {field} -> {text[:100]}")

# Try the organization-level with different entity types
print("\n=== Organization entity types ===")
org_entities = [
    "subcontractors", "employees", "suppliers", "vendors", 
    "crews", "teams", "members", "users", "staff"
]
for entity in org_entities:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                entity: {
                    "$": {"size": 3},
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
        nodes = data.get("organization", {}).get(entity, {}).get("nodes", [])
        print(f"  OK: {entity} = {[n['name'] for n in nodes]}")
    else:
        print(f"  ERR: {entity}")
