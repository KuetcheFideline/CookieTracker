
import sys
import os
sys.path.append(os.getcwd())
from treatement.helpers import create_birthdate_variants, create_phone_variants, detect_suspicious_tokens

print("=== VÉRIFICATION DES OPTIMISATIONS ===")

# 1. Vérification Dates
date = "12/02/2000"
variants_date = create_birthdate_variants(date)
print(f"\n[DATES] Pour '{date}':")
print(f"Avant: ~40 variantes")
print(f"Maintenant: {len(variants_date)} variantes")
print(f"Liste: {variants_date}")

# 2. Vérification Téléphone
phone = "+33612345678"
variants_phone = create_phone_variants(phone)
print(f"\n[TÉLÉPHONE] Pour '{phone}':")
print(f"Avant: ~15 variantes")
print(f"Maintenant: {len(variants_phone)} variantes")
print(f"Liste: {variants_phone}")

# 3. Vérification Nouveaux Patterns
print(f"\n[NOUVEAUX PATTERNS]")
test_values = [
    ("user_id=12345", "user_id"),
    ("device_id:a1b2-c3d4", "device_id"),
    ("timezone=Europe/Paris", "timezone"),
    ("theme=dark", "theme")
]

for val, name in test_values:
    results = detect_suspicious_tokens(val, "test_cookie")
    found = any(item['subtype'] == name for item in results)
    status = "✅ DÉTECTÉ" if found else "❌ ÉCHEC"
    print(f"Test '{name}': {status}")
