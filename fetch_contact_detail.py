#!/usr/bin/env python3.11
"""
Fetch a single contact by ID and explore all its fields
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

# Try fetching contact directly
print("=== Fetch contact directly ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "contact": {
            "$": {"id": CONTACT_ID},
            "id": {},
            "name": {}
        }
    }
})
print(f"Status: {status}")
print(text[:500])

# Try fetching contact with sub-fields
print("\n=== Contact sub-fields ===")
sub_fields = ["email", "phone", "address", "city", "state", "zip", 
              "notes", "type", "tags", "isVendor", "website",
              "firstName", "lastName", "companyName", "company"]

for field in sub_fields:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "contact": {
                "$": {"id": CONTACT_ID},
                "id": {},
                "name": {},
                field: {}
            }
        }
    })
    if status == 200:
        data = json.loads(text)
        val = data.get("contact", {}).get(field, "N/A")
        print(f"  OK: {field} = {val}")
    else:
        print(f"  ERR: {field} -> {text[:80]}")

# Try the contacts list with different field names
print("\n=== Contacts list - probe node fields ===")
node_fields = ["firstName", "lastName", "email", "phone", "address", 
               "city", "state", "zip", "notes", "type", "isVendor",
               "companyName", "website", "createdAt", "updatedAt"]

for field in node_fields:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                "contacts": {
                    "$": {"size": 1},
                    "nodes": {
                        "id": {},
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
        print(f"  ERR: {field}")
