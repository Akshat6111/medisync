import re
from app.services.salt_dictionary import SALT_DICTIONARY

def detect_dosage_form(name: str, default: str = "tablet") -> str:
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
    return default

# Check how many brands exist in SALT_DICTIONARY
total_brands = 0
for k, v in SALT_DICTIONARY.items():
    brands = v.get("brands", [])
    total_brands += len(brands)

print(f"Total salts: {len(SALT_DICTIONARY)}, Total brands: {total_brands}")
