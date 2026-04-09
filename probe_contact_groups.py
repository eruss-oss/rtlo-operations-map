#!/usr/bin/env python3.11
"""
Try to find contact groups/categories in JobTread
Also try fetching all contacts and looking at ALL available fields on each node
"""
import requests
import json

GRANT_KEY = "22TLym9AtViwP98AJWhWKBFTmPQb4dXBhB"
API_URL = "https://api.jobtread.com/pave"
ORG_ID = "22PFyR85uqXr"

def query(payload):
    resp = requests.post(API_URL, json=payload)
    return resp.status_code, resp.text

# Try contact groups
print("=== Contact groups ===")
for field in ["groups", "contactGroups", "categories", "labels", "segments"]:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "organization": {
                "$": {"id": ORG_ID},
                field: {
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
        val = data.get("organization", {}).get(field)
        print(f"  OK: {field} = {json.dumps(val)[:300]}")
    else:
        print(f"  ERR: {field}")

# Try getting ALL fields on a contact node by fetching with every possible scalar
print("\n=== All scalar fields on contact ===")
scalars = [
    "id", "name", "firstName", "lastName", "createdAt",
    "displayName", "fullName", "title", "description", "bio",
    "status", "active", "archived", "deleted",
    "source", "origin", "channel",
    "number", "code", "reference",
    "balance", "credit",
    "rating", "score",
    "color", "icon", "avatar",
    "externalId", "integrationId",
    "quickbooksId", "xeroId",
    "isArchived", "isDeleted", "isActive",
    "isVendor", "isCustomer", "isEmployee", "isSubcontractor", "isSupplier",
    "vendorType", "customerType", "contactType",
    "type", "kind", "class",
    "group", "segment", "category", "label",
    "tag", "tags",
    "notes", "memo", "comment",
    "website", "url",
    "taxId", "ein", "ssn",
    "currency", "language", "timezone",
    "preferredContact", "contactMethod",
    "leadSource", "referral",
    "accountNumber", "customerNumber",
    "creditLimit", "paymentTerms",
    "discount", "markup",
    "license", "insurance", "bond",
    "certifications", "specialties",
    "serviceArea", "territory",
    "priority", "tier", "level",
    "companyId", "parentId",
    "ownerId", "managerId", "salesRepId",
]

working = []
for field in scalars:
    status, text = query({
        "query": {
            "$": {"grantKey": GRANT_KEY},
            "contact": {
                "$": {"id": "22PGgX9Hm7Q5"},
                "id": {},
                field: {}
            }
        }
    })
    if status == 200:
        data = json.loads(text)
        val = data.get("contact", {}).get(field)
        working.append((field, val))
        print(f"  OK: {field} = {val}")

print(f"\nWorking scalar fields: {[f for f,v in working]}")
