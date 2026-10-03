import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("\n--- TEST 1: First Search for 'dolo 650' ---")
    t0 = time.time()
    resp1 = client.get("/generic-finder/search?query=dolo 650")
    t1 = time.time()
    print(f"Status: {resp1.status_code} | Duration: {t1 - t0:.2f}s")
    assert resp1.status_code == 200, f"Expected 200 but got {resp1.status_code}"
    data1 = resp1.json()
    print("Matched To:", data1.get("query_matched_to"))
    print("Generic Name:", data1.get("generic_name"))
    print("Category:", data1.get("category"))
    print("How to use:", data1.get("how_to_use"))
    print("PMBJP Benchmark:", data1.get("pmbjp_reference"))
    print("Substitutes in Catalog:", len(data1.get("all_generic_substitutes", [])))
    print("Results Found:", len(data1.get("results", [])))
    print("Cheapest Option:", data1.get("cheapest_option"))
    print("Estimated Savings %:", data1.get("estimated_savings_percent"))
    print("Sources Succeeded:", data1.get("sources_checked"))
    assert len(data1.get("results", [])) > 0, "Expected at least 1 price result"

    print("\n--- TEST 2: Second Search for 'dolo 650' (Instant Cache Test) ---")
    t2 = time.time()
    resp2 = client.get("/generic-finder/search?query=dolo 650")
    t3 = time.time()
    print(f"Status: {resp2.status_code} | Duration: {t3 - t2:.2f}s")
    assert resp2.status_code == 200
    data2 = resp2.json()
    print("Results Count:", len(data2.get("results", [])))

    print("\n--- TEST 3: Typo Search for 'augmntin' ---")
    resp3 = client.get("/generic-finder/search?query=augmntin")
    assert resp3.status_code == 200
    data3 = resp3.json()
    print("Query: 'augmntin' -> Matched To:", data3.get("query_matched_to"), "| Generic:", data3.get("generic_name"))
    assert data3.get("is_salt_dictionary_match") is True
    assert "amoxicillin" in data3.get("generic_name", "").lower()

    print("\n--- TEST 4: Unknown Medicine Search ('xyz123randomdrug') ---")
    resp4 = client.get("/generic-finder/search?query=xyz123randomdrug")
    assert resp4.status_code == 200
    data4 = resp4.json()
    print("Status:", resp4.status_code)
    print("Match:", data4.get("is_salt_dictionary_match"), "| Generic:", data4.get("generic_name"))
    assert data4.get("is_salt_dictionary_match") is False, "Expected false for random gibberish"

    print("\n--- TEST 5: Savings Calculator Endpoint ---")
    calc_payload = {
        "medicine_name": "Augmentin 625 Duo",
        "doses_per_day": 2.0,
        "duration_days": 14,
    }
    resp5 = client.post("/generic-finder/calculate-savings", json=calc_payload)
    print("Status:", resp5.status_code)
    assert resp5.status_code == 200
    data5 = resp5.json()
    print("Brand Cost:", data5.get("brand_total_cost"))
    print("Generic Cost:", data5.get("generic_total_cost"))
    print("Total Savings (INR):", data5.get("total_savings_inr"))
    print("Savings %:", data5.get("savings_percent"))
    print("Annual Projected Savings (INR):", data5.get("annual_projected_savings_inr"))
    assert data5.get("total_savings_inr") > 0

    print("\n--- TEST 6: Popular Categories ---")
    resp6 = client.get("/generic-finder/popular")
    assert resp6.status_code == 200
    data6 = resp6.json()
    print("Categories count:", len(data6.get("categories", [])))
    assert len(data6.get("categories", [])) >= 6

    print("\n ALL GENERIC FINDER BACKEND TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
