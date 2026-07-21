from aiinvest.kit_md import parse_cfg

KIT = '''
## REEL 1 — WULF
```python
"WULF":{ "hero":"hero_wulf_2026-07-21.png", "logo":"logo_WULF.png", "ex":"NASDAQ",
  "kick":"HALAL SCREEN", "head":"Bitcoin money, screened", "sub":"38 percent of revenue is mining.",
  "data_kick":"THE MATH", "data_title":"AAOIFI screen", "data_cap":"", "data_foot":"", "mode":"disc",
  "rows":[], "tk_kick":"TAKEAWAY", "big":"38", "unit":"%", "tk_label":"MINING REVENUE",
  "tk_body":"Purification, estimated.", "src":"site",
  "halal_script":"TeraWulf makes real money... but thirty-eight percent of it is bitcoin mining.
The AAOIFI screen flags it. Purification, estimated, about thirteen cents a share.
Educational, not financial or religious advice." }
```
'''

def test_halal_script_parsed_multiline():
    c = parse_cfg(KIT, "WULF")
    assert c["halal_script"].startswith("TeraWulf makes real money")
    assert "thirteen cents a share" in c["halal_script"]
    assert c["halal_script"].rstrip().endswith("religious advice.")

def test_halal_script_absent_is_none():
    md = '"NVDA":{ "hero":"h.png", "kick":"K" }'
    assert parse_cfg(md, "NVDA")["halal_script"] is None

def test_legacy_fields_unchanged():
    c = parse_cfg(KIT, "WULF")
    assert c["hook"]["kick"] == "HALAL SCREEN"
    assert c["data"]["mode"] == "disc"
