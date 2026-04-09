#!/usr/bin/env python3.11
"""
Explore JobTread API to find vendor/contact fields
"""
import requests
import json

GRANT_KEY = "22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB"
API_URL = "https://api.jobtread.com/pave"
ORG_ID = "22PFyR85uqXr"

def query(payload):
    resp = requests.post(API_URL, json=payload)
    print(f"Status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Response: {resp.text[:500]}")
        return None
    return resp.json()

# Try minimal contact fetch
print("=== Test 1: Minimal contacts ===")
result = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "contacts": {
                "$": {"size": 5},
                "nextPage": {},
                "nodes": {
                    "id": {},
                    "name": {}
                }
            }
        }
    }
})
if result:
    print(json.dumps(result, indent=2)[:2000])

print("\n=== Test 2: Vendors specifically ===")
result2 = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "vendors": {
                "$": {"size": 50},
                "nextPage": {},
                "nodes": {
                    "id": {},
                    "name": {}
                }
            }
        }
    }
})
if result2:
    print(json.dumps(result2, indent=2)[:2000])

print("\n=== Test 3: Customers ===")
result3 = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "customers": {
                "$": {"size": 5},
                "nextPage": {},
                "nodes": {
                    "id": {},
                    "name": {}
                }
            }
        }
    }
})
if result3:
    print(json.dumps(result3, indent=2)[:1000])
