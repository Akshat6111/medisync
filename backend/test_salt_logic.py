import re

def detect_dosage_form(name: str) -> str:
    n = name.lower()
    if re.search(r"\b(syrup|suspension|oral liquid|elixir|liquid)\b", n) or "syrup" in n or "suspension" in n:
        return "syrup"
    if re.search(r"\b(capsule|capsules|cap|caps)\b", n):
        return "capsule"
    if re.search(r"\b(injection|inj|infusion|vial|ampoule)\b", n):
        return "injection"
    if re.search(r"\b(drop|drops|eye drop|ear drop|nasal drop|pediatric drops)\b", n):
        return "drops"
    if re.search(r"\b(gel|ointment|cream|lotion|emulgel)\b", n):
        return "ointment"
    if re.search(r"\b(inhaler|rotacap|respule|inhalation)\b", n):
        return "inhaler"
    return "tablet"

tests = [
    "Dolo 650",
    "Ascoril LS Syrup",
    "Relikast-LC Kid Syrup",
    "Phensedyl DX Syrup",
    "Phensedyl LM Tablet",
    "Montecip LC",
    "Becosules Capsules",
    "Ciplox Eye Drops",
    "Amoxyclav Injection",
    "Montair LC Kid Strawberry Tablet DT"
]

for t in tests:
    print(f"{t} -> {detect_dosage_form(t)}")
