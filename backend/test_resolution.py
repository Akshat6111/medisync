from app.services.salt_dictionary import resolve_medicine_salt
import json

for q in ["Montecip LC", "Phensedyl LM", "Relikast-LC", "Montiwor-LC"]:
    res = resolve_medicine_salt(q)
    if res:
        print(f"QUERY: {q} -> Matched: {res['query_matched_to']}, Salt: {res['generic_name']}, Brands: {res['brands'][:5]}")
    else:
        print(f"QUERY: {q} -> None")
