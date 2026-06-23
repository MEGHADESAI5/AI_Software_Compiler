from stage1_intent import extract_intent
from stage2_design import design_system
from stage3_generate import generate_all_schemas
from repair_engine import validate_and_repair
from runtime import validate_config

print("=" * 60)
print("Testing pipeline with: 'Build a CRM with login and contacts'")
print("=" * 60)

# Run the full pipeline
intent = extract_intent('Build a CRM with login and contacts')
design = design_system(intent)
schemas = generate_all_schemas(design)

db = schemas['db']
api = schemas['api']
ui = schemas['ui']
auth = schemas['auth']

# Repair
repaired_db, repaired_api, repaired_ui, repaired_auth, repairs = validate_and_repair(db, api, ui, auth)

# Runtime validation
result = validate_config(repaired_db, repaired_api, repaired_ui, repaired_auth)

# Print detailed results
print("\n" + "=" * 60)
print("📊 DETAILED VALIDATION RESULTS:")
print("=" * 60)

for r in result['results']:
    status = "✅" if r['passed'] else "❌"
    print(f"  {status} {r['check']}: {r['message']}")

print("\n" + "=" * 60)
print(f"📊 FINAL STATUS: {'✅ PASSED' if result['passed'] else '❌ FAILED'}")
print(f"   Checks: {result['passed_checks']}/{result['total_checks']} passed")
print("=" * 60)