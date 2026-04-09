#!/usr/bin/env python3.11
"""
Probe JobTread contact fields one by one
"""
import requests
import json

GRANT_KEY = "22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB"
API_URL = "https://api.jobtread.com/pave"
ORG_ID = "22PFyR85uqXr"

def query(payload):
    resp = requests.post(API_URL, json=payload)
    return resp.status_code, resp.text

# Test each field individually
fields_to_test = [
    "type", "email", "phone", "address", "city", "state", "zip", 
    "notes", "isVendor", "isCustomer", "isSubcontractor", "isEmployee",
    "tags", "category", "companyName", "company", "website", "customFields"
]

for field in fields_to_test:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                "contacts": {
                    "$": {"size": 1},
                    "nodes": {
                        "id": {},
                        "name": {},
                        field: {}
                    }
                }
            }
        }
    })
    if status == 200:
        data = json.loads(text)
        node = data.get("organization", {}).get("contacts", {}).get("nodes", [{}])[0]
        val = node.get(field, "N/A")
        print(f"  OK: {field} = {val}")
    else:
        print(f"  ERR: {field} -> {text[:100]}")
