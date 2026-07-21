"""One-off script to identify verdict flips between v1 (no-xbrl) and xbrl-enhanced."""
import json, pathlib, sys, glob
sys.path.insert(0, pathlib.Path(__file__).parent.as_posix())
from aiinvest import halal

# Load the batch (latest halal tradingview batch)
data_root = pathlib.Path(__file__).parent.parent / "data"
paths = sorted(glob.glob(str(data_root / "halal" / "*" / "tradingview_halal_*.json")))
batch = json.loads(pathlib.Path(paths[-1]).read_text(encoding="utf-8"))
activity = halal.load_business_activity()

# Build WITHOUT xbrl = v1 baseline
v1_verdicts = {}
for sym, rec in (batch.get("financial_data") or {}).items():
    metrics = rec.get("metrics", {}) or {}
    v = halal.verdict(sym, metrics, activity.get(sym), xbrl_facts=None, avg_mcap_36m=None, avg_mcap_24m=None)
    v1_verdicts[sym] = v

# Load the new bundle (with xbrl)
new_b = json.loads((pathlib.Path(__file__).parent.parent / "web" / "public" / "data" / "halal.json").read_text(encoding="utf-8"))
new_verdicts = new_b["verdicts"]

# Find overall flips
flips = []
for sym in new_verdicts:
    old_v = v1_verdicts.get(sym, {}).get("overall", "MISSING")
    new_v = new_verdicts[sym]["overall"]
    if old_v != new_v:
        flips.append((sym, old_v, new_v))

print(f"Flips (v1 no-xbrl baseline vs xbrl-enhanced):")
for sym, old, new in sorted(flips):
    old_verdict = v1_verdicts.get(sym, {})
    new_verdict = new_verdicts.get(sym, {})
    print(f"  {sym}: {old} -> {new}")

    # Print inputs from both
    old_inp = old_verdict.get("inputs", {})
    new_inp = new_verdict.get("inputs", {})
    ii_key = "interest_income"
    rev_key = "revenue_ttm"
    imp_key = "impermissible_revenue_pct"
    rec_key = "receivables"
    rec_basis_key = "receivables_basis"

    print(f"    OLD interest_income: {old_inp.get(ii_key)}")
    print(f"    NEW interest_income: {new_inp.get(ii_key)}")
    print(f"    OLD impermissible_revenue_pct: {old_inp.get(imp_key)}")
    print(f"    NEW impermissible_revenue_pct: {new_inp.get(imp_key)}")
    print(f"    revenue_ttm: {new_inp.get(rev_key)}")
    print(f"    OLD receivables ({old_inp.get(rec_basis_key)}): {old_inp.get(rec_key)}")
    print(f"    NEW receivables ({new_inp.get(rec_basis_key)}): {new_inp.get(rec_key)}")

    # Per-standard activity status
    for std_name, std_data in new_verdict.get("standards", {}).items():
        old_std = old_verdict.get("standards", {}).get(std_name, {})
        old_act = old_std.get("activity_status")
        new_act = std_data.get("activity_status")
        if old_act != new_act:
            print(f"    {std_name} activity_status: {old_act} -> {new_act}")

    # Also check test-level changes
    for std_name, std_data in new_verdict.get("standards", {}).items():
        old_std = old_verdict.get("standards", {}).get(std_name, {})
        for test in std_data.get("tests", []):
            tid = test.get("id")
            old_test = next((t for t in old_std.get("tests", []) if t.get("id") == tid), None)
            if old_test and old_test.get("status") != test.get("status"):
                print(f"    {std_name}/{tid}: {old_test.get('status')} -> {test.get('status')} "
                      f"(ratio {old_test.get('ratio')} -> {test.get('ratio')}, threshold {test.get('threshold')})")

if not flips:
    print("  (none)")
print(f"\nTotal overall flips: {len(flips)}")
print(f"Delta: halal {sum(1 for _,o,n in flips if o=='halal' and n!='halal')} lost; "
      f"not_halal {sum(1 for _,o,n in flips if o!='halal' and n=='halal')} gained")
