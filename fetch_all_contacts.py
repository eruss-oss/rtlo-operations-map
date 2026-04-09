#!/usr/bin/env python3.11
"""
Fetch ALL contacts from JobTread and explore their fields to find vendors
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

# First, get a single contact with all possible fields to see what's available
print("=== Exploring contact fields ===")
result = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "contacts": {
                "$": {"size": 1},
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
                    "notes": {},
                    "isVendor": {},
                    "isCustomer": {},
                    "isSubcontractor": {},
                    "isEmployee": {}
                }
            }
        }
    }
})
print(json.dumps(result, indent=2)[:2000])
