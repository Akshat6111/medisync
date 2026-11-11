"""
MediSync CSP Scheduler Benchmark Suite
======================================
This standalone script benchmarks the performance, correctness, and conflict
diagnosis of the Constraint Satisfaction Problem (CSP) scheduler located in
`app/scheduling/scheduler.py` without modifying any application code.

Evaluates:
- Regimens with 3, 5, 8, 10, and 15 medications
- Varied frequencies: OD (1x/day), BD (2x/day), TDS (3x/day), QID (4x/day)
- Dietary/timing constraints: with_food, empty_stomach, bedtime_only, standard
- Known clinical drug-drug interaction separation constraints
- 20 benchmark iterations per regimen size
- Metrics: Median time (ms), Max time (ms), Validity, and Independent Constraint Violations
- Deliberately unsolvable case tested against `diagnose_conflict`
"""

import os
import sys
import time
import statistics
from datetime import time as dt_time
from typing import List, Dict, Any, Optional

# Ensure backend root is on sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.scheduling.scheduler import (
    solve_schedule,
    diagnose_conflict,
    get_candidate_slots,
    get_min_gap_slots,
    SLOT_MINUTES,
)


class MockPatient:
    """Lightweight patient representation fulfilling scheduler requirements."""
    def __init__(
        self,
        wake_up_time: dt_time,
        breakfast_time: dt_time,
        lunch_time: dt_time,
        dinner_time: dt_time,
        sleep_time: dt_time,
    ):
        self.wake_up_time = wake_up_time
        self.breakfast_time = breakfast_time
        self.lunch_time = lunch_time
        self.dinner_time = dinner_time
        self.sleep_time = sleep_time


class MockMedication:
    """Lightweight medication representation fulfilling scheduler requirements."""
    def __init__(
        self,
        med_id: str,
        name: str,
        frequency_per_day: int,
        with_food: bool = False,
        empty_stomach: bool = False,
        bedtime_only: bool = False,
    ):
        self.id = med_id
        self.name = name
        self.frequency_per_day = frequency_per_day
        self.with_food = with_food
        self.empty_stomach = empty_stomach
        self.bedtime_only = bedtime_only


def verify_schedule_constraints(
    solution: List[Dict[str, Any]],
    medications: List[MockMedication],
    patient: MockPatient,
    interactions: List[Dict[str, Any]],
) -> List[str]:
    """
    Independently inspects every scheduled dose in the solution against all constraints:
    1. Domain constraints (meal proximity, empty stomach, bedtime only, waking window)
    2. Same-medication minimum spacing (patient waking window / frequency)
    3. Drug-interaction separation gaps (minimum gap hours converted to slots)
    Returns a list of violation descriptions (empty if perfectly valid).
    """
    violations: List[str] = []
    med_by_id = {m.id: m for m in medications}
    med_by_name = {m.name.strip().lower(): m for m in medications}

    def time_to_minutes(t_str: str) -> int:
        h, m = map(int, t_str.split(":"))
        return h * 60 + m

    # 1. Verify Domain Constraints
    doses_by_med: Dict[str, List[Dict[str, Any]]] = {}
    for dose in solution:
        doses_by_med.setdefault(dose["medication_id"], []).append(dose)
        med = med_by_id.get(dose["medication_id"])
        if not med:
            violations.append(f"Unknown medication_id {dose['medication_id']} in schedule")
            continue

        slot = time_to_minutes(dose["scheduled_time"]) // SLOT_MINUTES
        candidate_slots = get_candidate_slots(med, patient)
        if slot not in candidate_slots:
            violations.append(
                f"Domain violation: {med.name} (dose {dose['dose_index']}) at {dose['scheduled_time']} "
                f"is not in candidate slots"
            )

    # 2. Verify Same-Medication Spacing Constraints
    for med_id, doses in doses_by_med.items():
        med = med_by_id[med_id]
        if med.frequency_per_day > 1:
            req_min_gap_slots = get_min_gap_slots(med, patient)
            for i in range(len(doses)):
                for j in range(i + 1, len(doses)):
                    s1 = time_to_minutes(doses[i]["scheduled_time"]) // SLOT_MINUTES
                    s2 = time_to_minutes(doses[j]["scheduled_time"]) // SLOT_MINUTES
                    actual_gap = abs(s1 - s2)
                    if actual_gap < req_min_gap_slots:
                        violations.append(
                            f"Same-med spacing violation: {med.name} dose {i} and {j} "
                            f"have gap {actual_gap * SLOT_MINUTES}m < required {req_min_gap_slots * SLOT_MINUTES}m"
                        )

    # 3. Verify Drug-Drug Interaction Constraints
    for inter in interactions:
        med_a = med_by_name.get(inter["drug_a"].strip().lower())
        med_b = med_by_name.get(inter["drug_b"].strip().lower())
        if med_a and med_b:
            req_gap_slots = int((inter["minimum_gap_hours"] * 60) / SLOT_MINUTES)
            doses_a = doses_by_med.get(med_a.id, [])
            doses_b = doses_by_med.get(med_b.id, [])
            for da in doses_a:
                for db in doses_b:
                    sa = time_to_minutes(da["scheduled_time"]) // SLOT_MINUTES
                    sb = time_to_minutes(db["scheduled_time"]) // SLOT_MINUTES
                    actual_gap = abs(sa - sb)
                    if actual_gap < req_gap_slots:
                        violations.append(
                            f"Drug-interaction violation: {med_a.name} ({da['scheduled_time']}) and "
                            f"{med_b.name} ({db['scheduled_time']}) gap {actual_gap * SLOT_MINUTES}m "
                            f"< required {req_gap_slots * SLOT_MINUTES}m"
                        )

    return violations


def build_test_regimens() -> Dict[int, Dict[str, Any]]:
    """Builds realistic medication regimens for 3, 5, 8, 10, and 15 medications."""
    # 3 Medications (OD, BD, Bedtime)
    meds_3 = [
        MockMedication("m1", "Levothyroxine 50mcg", 1, empty_stomach=True), # OD
        MockMedication("m2", "Metformin 500mg", 2, with_food=True),        # BD
        MockMedication("m3", "Atorvastatin 20mg", 1, bedtime_only=True),   # OD (bedtime)
    ]
    inter_3: List[Dict[str, Any]] = []

    # 5 Medications (Adds TDS + known interaction: Levothyroxine & Calcium)
    meds_5 = meds_3 + [
        MockMedication("m4", "Amoxicillin 500mg", 3, with_food=False),     # TDS
        MockMedication("m5", "Calcium Carbonate 500mg", 1, with_food=True), # OD
    ]
    inter_5 = [
        {"drug_a": "levothyroxine 50mcg", "drug_b": "calcium carbonate 500mg", "minimum_gap_hours": 4.0}
    ]

    # 8 Medications (Adds QID + Empty Stomach + Antacid interaction)
    meds_8 = meds_5 + [
        MockMedication("m6", "Paracetamol 650mg", 4, with_food=False),     # QID
        MockMedication("m7", "Pantoprazole 40mg", 1, empty_stomach=True),  # OD
        MockMedication("m8", "Amlodipine 5mg", 1, with_food=False),        # OD
    ]
    inter_8 = inter_5 + [
        {"drug_a": "amoxicillin 500mg", "drug_b": "pantoprazole 40mg", "minimum_gap_hours": 2.0}
    ]

    # 10 Medications (Adds Fluoroquinolone interaction with polyvalent cations)
    meds_10 = meds_8 + [
        MockMedication("m9", "Ciprofloxacin 500mg", 2, with_food=False),   # BD
        MockMedication("m10", "Multivitamin Complex", 1, with_food=True),   # OD
    ]
    inter_10 = inter_8 + [
        {"drug_a": "ciprofloxacin 500mg", "drug_b": "calcium carbonate 500mg", "minimum_gap_hours": 2.0}
    ]

    # 15 Medications (Polypharmacy regimen with 23 doses across full day)
    meds_15 = meds_10 + [
        MockMedication("m11", "Losartan 50mg", 1, with_food=False),        # OD
        MockMedication("m12", "Cetirizine 10mg", 1, bedtime_only=True),    # OD
        MockMedication("m13", "Vitamin D3 60k", 1, with_food=True),        # OD
        MockMedication("m14", "Ibuprofen 400mg", 2, with_food=True),       # BD
        MockMedication("m15", "B-Complex Forte", 1, with_food=False),      # OD
    ]
    inter_15 = inter_10

    return {
        3: {"medications": meds_3, "interactions": inter_3},
        5: {"medications": meds_5, "interactions": inter_5},
        8: {"medications": meds_8, "interactions": inter_8},
        10: {"medications": meds_10, "interactions": inter_10},
        15: {"medications": meds_15, "interactions": inter_15},
    }


def run_benchmark():
    patient = MockPatient(
        wake_up_time=dt_time(7, 0),
        breakfast_time=dt_time(8, 30),
        lunch_time=dt_time(13, 0),
        dinner_time=dt_time(20, 0),
        sleep_time=dt_time(23, 0),
    )

    regimens = build_test_regimens()
    iterations = 20

    print("=" * 88)
    print("        MEDISYNC CSP SCHEDULER PERFORMANCE & VERIFICATION BENCHMARK")
    print("=" * 88)
    print(f"Patient Schedule: Wake 07:00 | Breakfast 08:30 | Lunch 13:00 | Dinner 20:00 | Sleep 23:00")
    print(f"Iterations per regimen: {iterations}\n")

    results_table = []

    for size in [3, 5, 8, 10, 15]:
        regimen = regimens[size]
        meds = regimen["medications"]
        inters = regimen["interactions"]
        total_doses = sum(m.frequency_per_day for m in meds)

        times_ms = []
        all_valid = True
        total_violations = 0
        sample_solution = None

        for _ in range(iterations):
            start = time.perf_counter()
            sol = solve_schedule(meds, patient, inters)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            times_ms.append(elapsed_ms)

            if sol is None:
                all_valid = False
            else:
                sample_solution = sol
                violations = verify_schedule_constraints(sol, meds, patient, inters)
                total_violations += len(violations)

        median_ms = statistics.median(times_ms)
        max_ms = max(times_ms)

        results_table.append({
            "med_count": size,
            "total_doses": total_doses,
            "interactions_count": len(inters),
            "median_ms": median_ms,
            "max_ms": max_ms,
            "valid_found": "YES" if (all_valid and sample_solution is not None) else "NO",
            "violations": total_violations,
        })

    # Print Formatted Results Table
    print(f"{'Meds':<6} | {'Doses':<6} | {'Interactions':<13} | {'Median Time (ms)':<17} | {'Max Time (ms)':<14} | {'Valid?':<7} | {'Violations'}")
    print("-" * 88)
    for r in results_table:
        print(
            f"{r['med_count']:<6} | "
            f"{r['total_doses']:<6} | "
            f"{r['interactions_count']:<13} | "
            f"{r['median_ms']:<17.3f} | "
            f"{r['max_ms']:<14.3f} | "
            f"{r['valid_found']:<7} | "
            f"{r['violations']}"
        )
    print("-" * 88)

    # --------------------------------------------------------------------------
    # UNCOLVABLE CASE BENCHMARK & CONFLICT DIAGNOSIS
    # --------------------------------------------------------------------------
    print("\n" + "=" * 88)
    print("                     DELIBERATELY UNSOLVABLE CASE TEST")
    print("=" * 88)
    unsolvable_meds = [
        MockMedication("unsolv_1", "Zolpidem 10mg", 1, bedtime_only=True),
        MockMedication("unsolv_2", "Clonazepam 0.5mg", 1, bedtime_only=True),
    ]
    unsolvable_interactions = [
        {"drug_a": "zolpidem 10mg", "drug_b": "clonazepam 0.5mg", "minimum_gap_hours": 4.0}
    ]

    print("Configuration:")
    print("  - Medication 1: Zolpidem 10mg (OD, bedtime_only=True)")
    print("  - Medication 2: Clonazepam 0.5mg (OD, bedtime_only=True)")
    print("  - Interaction: 4.0 hour minimum separation required between bedtime-only drugs")
    print("  - Conflict Cause: Both drugs restricted to single slot (22:30), separation impossible.")

    start_unsolv = time.perf_counter()
    unsolvable_res = solve_schedule(unsolvable_meds, patient, unsolvable_interactions)
    unsolv_time_ms = (time.perf_counter() - start_unsolv) * 1000.0

    print(f"\nExecution Result: solve_schedule returned -> {unsolvable_res}")
    print(f"Solve Time: {unsolv_time_ms:.3f} ms")

    # Diagnose conflict
    diag_start = time.perf_counter()
    diagnosis = diagnose_conflict(unsolvable_meds, patient, unsolvable_interactions)
    diag_time_ms = (time.perf_counter() - diag_start) * 1000.0

    print(f"Conflict Diagnosis Time: {diag_time_ms:.3f} ms")
    print("diagnose_conflict Output:")
    print(f"  - conflict: {diagnosis.get('conflict')}")
    print(f"  - reason: {diagnosis.get('reason')}")
    print(f"  - drug_a: {diagnosis.get('drug_a')}")
    print(f"  - drug_b: {diagnosis.get('drug_b')}")
    print(f"  - required_gap_hours: {diagnosis.get('required_gap_hours')}")
    print(f"  - detail: {diagnosis.get('detail')}")
    print("=" * 88)


if __name__ == "__main__":
    run_benchmark()

