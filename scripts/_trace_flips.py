"""Trace the exact activity_pct computation for flipped symbols."""
import json, pathlib, sys, glob
sys.path.insert(0, pathlib.Path(__file__).parent.as_posix())
from aiinvest import halal

data_root = pathlib.Path(__file__).parent.parent / "data"
paths = sorted(glob.glob(str(data_root / "halal" / "*" / "tradingview_halal_*.json")))
batch = json.loads(pathlib.Path(paths[-1]).read_text(encoding="utf-8"))
activity = halal.load_business_activity()

for sym in ["DDOG", "MRNA", "QBTS", "RGTI", "UEC"]:
    rec = (batch.get("financial_data") or {}).get(sym, {})
    metrics = rec.get("metrics", {}) or {}
    curated = activity.get(sym)

    # Load xbrl from cache
    xf = data_root / "xbrl" / (sym + ".json")
    xbrl_facts = None
    if xf.exists():
        xd = json.loads(xf.read_text())
        xbrl_facts = xd.get("facts", {})

    # v1: no xbrl
    inp_v1 = halal.inputs_from_metrics(metrics, xbrl_facts=None)
    v1 = halal.verdict(sym, metrics, curated, xbrl_facts=None)

    # v1.1: with xbrl
    inp_v11 = halal.inputs_from_metrics(metrics, xbrl_facts=xbrl_facts)
    v11 = halal.verdict(sym, metrics, curated, xbrl_facts=xbrl_facts)

    # Compute effective pct manually for both paths
    if curated:
        ipr = curated.get("impermissible_revenue_pct") or {}
        pct_base = ipr.get("value") if isinstance(ipr, dict) else None
        if pct_base is None and curated.get("status") == "clean":
            pct_base = 0.0
    else:
        pct_base = None

    ii_v1 = inp_v1.get("interest_income")
    ii_v11 = inp_v11.get("interest_income")
    rev = inp_v11.get("revenue_ttm")

    pct_v1 = pct_base
    pct_v11 = pct_base
    if pct_v11 is not None and ii_v11 is not None and rev:
        pct_v11 = min(100.0, pct_v11 + (ii_v11 / rev) * 100.0)

    thr = next(s for s in halal.STANDARDS if s["key"] == "AAOIFI")["activity_threshold_pct"]

    print(f"{sym}:")
    ov1 = v1["overall"]
    ov11 = v11["overall"]
    as_v1 = v1["standards"]["AAOIFI"]["activity_status"]
    as_v11 = v11["standards"]["AAOIFI"]["activity_status"]
    print(f"  v1  overall={ov1} | AAOIFI activity_status={as_v1}")
    print(f"  v11 overall={ov11} | AAOIFI activity_status={as_v11}")
    print(f"  curated status={curated.get('status') if curated else 'None'}")
    print(f"  pct_base={pct_base}  ii_v11={ii_v11}  revenue_ttm={rev}")
    print(f"  effective pct v1={pct_v1}  v11={pct_v11}  threshold={thr}")
    if xbrl_facts:
        ii_data = xbrl_facts.get("interest_income")
        print(f"  xbrl interest_income: {ii_data}")
    else:
        print(f"  No xbrl cache found for {sym}")
    print()
