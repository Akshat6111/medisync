from datetime import time
from typing import List, Dict, Optional, Any

SLOT_MINUTES = 15


def time_to_slot(t: time) -> int:
    return (t.hour * 60 + t.minute) // SLOT_MINUTES


def slot_to_time_str(slot: int) -> str:
    total_minutes = (slot * SLOT_MINUTES) % (24 * 60)
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def get_candidate_slots(medication, patient) -> List[int]:
    wake = time_to_slot(patient.wake_up_time)
    sleep = time_to_slot(patient.sleep_time)
    breakfast = time_to_slot(patient.breakfast_time)
    lunch = time_to_slot(patient.lunch_time)
    dinner = time_to_slot(patient.dinner_time)

    if medication.bedtime_only:
        return [max(sleep - 2, wake)]

    if medication.with_food:
        candidates = []
        for meal in [breakfast, lunch, dinner]:
            candidates.extend(range(meal - 2, meal + 3))
        return sorted(set(c for c in candidates if wake <= c <= sleep))

    if medication.empty_stomach:
        candidates = []
        for meal in [breakfast, lunch, dinner]:
            candidates.append(meal - 4)
            candidates.append(meal + 8)
        return sorted(set(c for c in candidates if wake <= c <= sleep))

    return list(range(wake, sleep))


def build_dose_instances(medications: List[Any]) -> List[Dict]:
    instances = []
    for med in medications:
        for i in range(med.frequency_per_day):
            instances.append({
                "id": f"{med.id}_dose{i}",
                "medication_id": med.id,
                "medication_name": med.name,
                "dose_index": i,
            })
    return instances


def get_min_gap_slots(medication) -> int:
    hours = 24 / medication.frequency_per_day
    return int((hours * 60) / SLOT_MINUTES)


def build_constraint_graph(
    dose_instances,
    med_by_id,
    interactions,
):
    graph: Dict[str, List] = {
        d["id"]: []
        for d in dose_instances
    }

    by_med = {}

    for dose in dose_instances:
        by_med.setdefault(
            dose["medication_id"],
            [],
        ).append(dose["id"])

    # Same medication spacing
    for med_id, dose_ids in by_med.items():
        gap = get_min_gap_slots(
            med_by_id[med_id]
        )

        for i in range(len(dose_ids)):
            for j in range(i + 1, len(dose_ids)):
                graph[dose_ids[i]].append(
                    (dose_ids[j], gap)
                )
                graph[dose_ids[j]].append(
                    (dose_ids[i], gap)
                )

    # Build name lookup
    med_by_name = {
        med.name.strip().lower(): med
        for med in med_by_id.values()
    }

    # Drug interaction spacing
    for interaction in interactions:

        med_a = med_by_name.get(
            interaction["drug_a"]
        )

        med_b = med_by_name.get(
            interaction["drug_b"]
        )

        if med_a is None or med_b is None:
            continue

        gap_slots = int(
            (
                interaction["minimum_gap_hours"]
                * 60
            )
            / SLOT_MINUTES
        )

        doses_a = by_med.get(
            med_a.id,
            [],
        )

        doses_b = by_med.get(
            med_b.id,
            [],
        )

        for da in doses_a:
            for db in doses_b:
                graph[da].append(
                    (db, gap_slots)
                )
                graph[db].append(
                    (da, gap_slots)
                )

    return graph

def is_consistent(dose_id, value, assignment, graph):
    """Check if assigning `value` to `dose_id` conflicts with existing assignments."""
    for neighbor_id, min_gap in graph[dose_id]:
        if neighbor_id in assignment:
            if abs(assignment[neighbor_id] - value) < min_gap:
                return False
    return True


def select_unassigned_variable(domains, assignment):
    """MRV heuristic: pick the unassigned variable with the fewest remaining legal values."""
    unassigned = [v for v in domains if v not in assignment]
    return min(unassigned, key=lambda v: len(domains[v]))


def backtrack(assignment, domains, graph):
    if len(assignment) == len(domains):
        return dict(assignment)  # complete assignment found

    dose_id = select_unassigned_variable(domains, assignment)

    for value in domains[dose_id]:
        if is_consistent(dose_id, value, assignment, graph):
            assignment[dose_id] = value
            result = backtrack(assignment, domains, graph)
            if result is not None:
                return result
            del assignment[dose_id]  # backtrack

    return None  # no valid value found for this variable, trigger backtracking upward


def solve_schedule(
    medications: List[Any],
    patient: Any,
    interactions: List[Dict],
) -> Optional[List[Dict]]:
    if not medications:
        return []

    dose_instances = build_dose_instances(medications)
    med_by_id = {m.id: m for m in medications}

    domains: Dict[str, List[int]] = {}
    for dose in dose_instances:
        med = med_by_id[dose["medication_id"]]
        domain = get_candidate_slots(med, patient)
        if not domain:
            return None
        domains[dose["id"]] = domain

    graph = build_constraint_graph(dose_instances, med_by_id, interactions)

    solution = backtrack({}, domains, graph)
    if solution is None:
        return None

    dose_by_id = {d["id"]: d for d in dose_instances}
    result = []
    for dose_id, slot in solution.items():
        dose = dose_by_id[dose_id]
        result.append({
            "medication_id": dose["medication_id"],
            "medication_name": dose["medication_name"],
            "dose_index": dose["dose_index"],
            "scheduled_time": slot_to_time_str(slot),
        })

    result.sort(key=lambda x: x["scheduled_time"])
    return result


def diagnose_conflict(
    medications: List[Any],
    patient: Any,
    interactions: List[Dict],
) -> Dict:
    for i, interaction in enumerate(interactions):
        remaining = interactions[:i] + interactions[i + 1:]
        if solve_schedule(medications, patient, remaining) is not None:
            return {
                "conflict": True,
                "reason": "interaction_gap",
                "drug_a": interaction["drug_a"],
                "drug_b": interaction["drug_b"],
                "required_gap_hours": interaction["minimum_gap_hours"],
                "detail": None,
            }

    return {
    "conflict": True,
    "reason": "insufficient_time_windows",
    "drug_a": None,
    "drug_b": None,
    "required_gap_hours": None,
    "detail": "Patient's meal/sleep routine doesn't provide enough valid time windows for all medications.",
}