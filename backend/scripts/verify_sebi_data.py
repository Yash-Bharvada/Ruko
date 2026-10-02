import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from app.modules.registry.service import RegistryService

df = pd.read_csv('data/registry/sebi_registry_snapshot.csv')

print("=" * 75)
print("SEBI SNAPSHOT VERIFICATION REPORT")
print("=" * 75)
print(f"Total Intermediaries in Database: {len(df)}")
print(f"Sample breakdown: {df['is_sample'].value_counts().to_dict()}")
print(f"Categories included:")
for cat, count in df['category'].value_counts().items():
    print(f"  - {cat:<25}: {count:>5} records")

print("\n" + "-" * 75)
print("1. VERIFYING ACTUAL REGISTERED INDIAN INSTITUTIONS IN CSV:")
print("-" * 75)
test_firms = ["ZERODHA", "ICICI SECURITIES", "HDFC SECURITIES", "MOTILAL OSWAL", "AXIS SECURITIES", "KOTAK SECURITIES"]
for firm in test_firms:
    matches = df[df['name'].str.contains(firm, case=False, na=False)]
    if not matches.empty:
        rec = matches.iloc[0]
        print(f"[CONFIRMED] {rec['name']}")
        print(f"   SEBI Reg No : {rec['reg_no']}")
        print(f"   Category    : {rec['category']}")
        print(f"   Status      : {rec['status']}")
        print(f"   Real Data   : {rec['is_sample'] == False}\n")

print("-" * 75)
print("2. RUNNING LIVE RUKO REGISTRY SERVICE LOOKUPS:")
print("-" * 75)
service = RegistryService()

# A: Real Reg No lookup (ICICI Securities INA000000094)
info_real, _ = service.check({"registration_numbers": ["INA000000094"]})
print(f"Lookup real reg 'INA000000094':")
print(f"  -> Status  : {info_real.status}")
print(f"  -> Matches : {info_real.matches}")

# B: Fake Reg No lookup (Scammer fake registration number)
info_fake, _ = service.check({"registration_numbers": ["INA000099999"]})
print(f"\nLookup fake scammer reg 'INA000099999':")
print(f"  -> Status  : {info_fake.status}")
print(f"  -> Matches : {info_fake.matches}")

# C: Real Name fuzzy lookup
info_name, _ = service.check({"entity_names": ["Zerodha Broking"]})
print(f"\nLookup real name 'Zerodha Broking':")
print(f"  -> Status  : {info_name.status}")
print(f"  -> Top match: {info_name.matches[0]['name'] if info_name.matches else 'None'}")
print("=" * 75)
