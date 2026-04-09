#!/usr/bin/env python3.11
"""
Look at jobs and their contacts/subcontractors to find vendor type info
Also try fetching bills/purchase orders which reference vendors
"""
import requests
import json

GRANT_KEY = "22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB"
API_URL = "https://api.jobtread.com/pave"
ORG_ID = "22PFyR85uqXr"

def query(payload):
    resp = requests.post(API_URL, json=payload)
    return resp.status_code, resp.text

# Check what fields are available on a job's contacts
print("=== Job contacts ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "jobs": {
                "$": {"size": 3},
                "nodes": {
                    "id": {},
                    "name": {},
                    "contacts": {
                        "nodes": {
                            "id": {},
                            "name": {},
                            "type": {}
                        }
                    }
                }
            }
        }
    }
})
print(f"Status: {status}")
if status == 200:
    print(text[:1000])
else:
    print(text[:200])

# Try bills/purchase orders
print("\n=== Bills ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "bills": {
                "$": {"size": 5},
                "nodes": {
                    "id": {},
                    "vendor": {
                        "id": {},
                        "name": {}
                    }
                }
            }
        }
    }
})
print(f"Status: {status}, Response: {text[:500]}")

# Try purchase orders
print("\n=== Purchase Orders ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "purchaseOrders": {
                "$": {"size": 5},
                "nodes": {
                    "id": {},
                    "vendor": {
                        "id": {},
                        "name": {}
                    }
                }
            }
        }
    }
})
print(f"Status: {status}, Response: {text[:500]}")

# Try the contact node directly with "type" as a scalar
print("\n=== Contact node direct - type scalar ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "contact": {
            "$": {"id": "22PGgX9Hm7Q5"},
            "id": {},
            "name": {},
            "type": {}
        }
    }
})
print(f"Status: {status}, Response: {text[:300]}")

# Try searching for "All In All" contact
print("\n=== Search for All In All ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "contacts": {
                "$": {"size": 100, "search": "All In All"},
                "nodes": {
                    "id": {},
                    "name": {}
                }
            }
        }
    }
})
print(f"Status: {status}, Response: {text[:500]}")

# Try name filter
print("\n=== Name filter ===")
status, text = query({
    "query": {
        "$": {"grantKey": GRANT_KEY},
        "organization": {
            "$": {"id": ORG_ID},
            "contacts": {
                "$": {"size": 100, "name": "All In All"},
                "nodes": {
                    "id": {},
                    "name": {}
                }
            }
        }
    }
})
print(f"Status: {status}, Response: {text[:500]}")
