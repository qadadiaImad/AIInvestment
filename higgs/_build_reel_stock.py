"""9:16 reel frames for a stock reel (IONQ / ADBE). Outputs per ticker:
  reel_<tk>_hook.png (TRANSPARENT overlay for the animated hero), reel_<tk>_data.png, reel_<tk>_takeaway.png
Run: python higgs/_build_reel_stock.py IONQ   (or ADBE)
"""
import json, base64, math, sys
from playwright.sync_api import sync_playwright
W,H=1080,1920
site=json.load(open('web/public/data/site.json',encoding='utf-8'))['stocks']
qs=json.load(open('web/public/data/quantum.json',encoding='utf-8'))['stocks']

def b64(p): return "data:image/png;base64,"+base64.b64encode(open(p,'rb').read()).decode()

CFG={
 "IONQ":{"hero":"hero_quantum_2026-06-21.png","logo":"logo_IONQ.png","ex":"QUANTUM COMPUTING · NYSE",
   "kick":"QUANTUM · THE ODD ONE OUT",
   "head":"Quantum, priced like<br>a lottery ticket.<br><em style='font-style:italic;color:#34D399'>One name isn&rsquo;t.</em>",
   "sub":"Same hype label, opposite math &mdash; and this week IonQ shipped real product while the rest ran on the story.",
   "data_kick":"PRICE vs ANALYSTS' FUNDAMENTAL VALUE","data_title":"How many times above fair value",
   "mode":"mult","rows":[("IONQ",None),("QUBT",None),("QBTS",None),("RGTI",None)],
   "data_cap":"IonQ is the only one trading <em style='font-style:normal;color:#fff'>below</em> the model.",
   "data_foot":"dashed line = price equals fundamental value · analysts' model · NFA",
   "tk_kick":"THE OUTLIER","big":None,"unit":"%","tk_label":None,
   "tk_body":"Most of quantum is priced on the story. One name is priced below analysts&rsquo; model.",
   "src":"quantum"},
 "NVDA":{"hero":"hero_nvda_2026-06-22.png","logo":"logo_NVDA.png","ex":"AI CHIPS · NASDAQ",
   "kick":"AI CHIPS · THE ONE OUTLIER",
   "head":"Every AI chip looks<br>expensive. The<br><em style='font-style:italic;color:#34D399'>biggest one doesn&rsquo;t.</em>",
   "sub":"Nvidia is the only chip leader still trading below analysts&rsquo; model &mdash; even after a ~46% run this past year.",
   "data_kick":"AI CHIP LEADERS · PRICE vs MODEL","data_title":"How many times above fair value",
   "mode":"mult","rows":[("NVDA",None),("AVGO",None),("TSM",None),("AMD",None),("MU",None)],
   "data_cap":"Nvidia is the only one trading <em style='font-style:normal;color:#fff'>below</em> the model.",
   "data_foot":"dashed line = price equals fundamental value · analysts' model · NFA",
   "tk_kick":"THE OUTLIER","big":None,"unit":"%","tk_label":"BELOW MODEL — WHILE EVERY MAJOR PEER TRADES ABOVE",
   "tk_body":"The most crowded trade in tech &mdash; and by this measure, the cheapest of the bunch. One name is priced on the model, not the hype.",
   "src":"site"},
 "ADBE":{"hero":"hero_software_2026-06-21.png","logo":"logo_ADBE.png","ex":"AI SOFTWARE LAYER · NASDAQ",
   "kick":"AI · THE OVERLOOKED LAYER",
   "head":"Wall Street bought<br>the chip. It forgot<br>who <em style='font-style:italic;color:#34D399'>sells the AI.</em>",
   "sub":"Adobe just slid to ~68% below what analysts think it&rsquo;s worth &mdash; and the smart money is starting to circle.",
   "data_kick":"THE AI SOFTWARE LAYER · ON SALE","data_title":"Every one of them, marked down",
   "mode":"disc","rows":[("TEAM",None),("ADBE",None),("INTU",None),("WDAY",None),("NOW",None)],
   "data_cap":"The whole layer that runs on the chips is on sale.",
   "data_foot":"% below analysts' fundamental value · model estimate · NFA",
   "tk_kick":"ADOBE","big":None,"unit":"%","tk_label":"BELOW ANALYSTS' FUNDAMENTAL VALUE",
   "tk_body":"The hype went to the chips. The discount&rsquo;s on the software that runs on them &mdash; just as the AI-software thesis starts to turn.",
   "src":"site"},
}

TK=sys.argv[1].upper() if len(sys.argv)>1 else "IONQ"
c=CFG[TK]
store=qs if c["src"]=="quantum" else site
HERO=b64('higgs/'+c["hero"]); LOGO=b64('higgs/'+c["logo"])

# fill numbers
if c["mode"]=="mult":
    rows=[(s, store[s]['valuation']['price']/store[s]['valuation']['fundamental_value']) for s,_ in c["rows"]]
    prim_dc=store[TK]['valuation']['fundamental_discount_pct']; c["big"]=f"~{abs(prim_dc):.0f}"
    if TK=="IONQ":   # quantum-specific peer callout; others keep their config tk_label
        rgti=qs['RGTI']['valuation']['price']/qs['RGTI']['valuation']['fundamental_value']
        qbts=qs['QBTS']['valuation']['price']/qs['QBTS']['valuation']['fundamental_value']
        c["tk_label"]=f"BELOW MODEL — RIGETTI ~{rgti:.0f}x · D-WAVE ~{qbts:.0f}x ABOVE"
else:
    rows=[(s, site[s]['valuation']['fundamental_discount_pct']) for s,_ in c["rows"]]
    c["big"]=f"~{abs(site['ADBE']['valuation']['fundamental_discount_pct']):.0f}"

FONTS="@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600;700;800&display=swap');"
BASE=f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:0;background-size:cover;background-position:center}}
.scrim{{position:absolute;inset:0}}
.pad{{position:absolute;inset:0;padding:104px 80px;display:flex;flex-direction:column;z-index:2}}
.hdr{{display:flex;align-items:center;gap:24px}}
.logochip{{width:104px;height:104px;border-radius:24px;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 30px rgba(0,0,0,.45)}}
.logochip img{{width:74px;height:74px;object-fit:contain}}
.tkr{{font-family:'JetBrains Mono';font-weight:800;font-size:80px;line-height:.9;letter-spacing:-1px;color:#fff}}
.ex{{font-family:'JetBrains Mono';font-weight:600;font-size:22px;letter-spacing:3px;color:#34D399;margin-top:8px}}
.foot{{font-family:'JetBrains Mono';font-size:20px;color:#9AA6B6;letter-spacing:.5px}}
.kick{{font-family:'JetBrains Mono';font-weight:700;font-size:26px;letter-spacing:4px;color:#34D399}}
.head{{font-family:Fraunces;font-weight:600;line-height:1.04;letter-spacing:-2px;text-shadow:0 4px 30px rgba(0,0,0,.65)}}
"""
def page(b): return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{b}</div></body></html>"
def header(): return f"""<div class='hdr'><div class='logochip'><img src="{LOGO}"></div><div><div class='tkr'>{TK}</div><div class='ex'>{c['ex']}</div></div></div>"""

def hook():  # transparent overlay (no hero baked) — sits over the animated hero
    scrim="linear-gradient(180deg,rgba(10,13,18,.66) 0%,rgba(10,13,18,.12) 34%,rgba(10,13,18,.40) 64%,rgba(10,13,18,.93) 100%)"
    return page(f"""<div class='scrim' style="background:{scrim}"></div>
    <div class='pad'>{header()}
      <div style='margin-top:34px' class='kick'>{c['kick']}</div>
      <div class='head' style="margin-top:auto;font-size:94px">{c['head']}</div>
      <div style="font-size:35px;line-height:1.4;color:#DCE3ED;margin-top:28px;max-width:900px;text-shadow:0 2px 16px rgba(0,0,0,.8)">{c['sub']}</div>
      <div class='foot' style='margin-top:40px'>Educational · not financial advice</div></div>""")

def data():
    if c["mode"]=="mult":
        def w(m): return 9+(math.log10(m)-math.log10(0.5))/(math.log10(40)-math.log10(0.5))*70
        def lab(m): return f"{m:.1f}x"
        def col(m): return "#10B981" if m<=1.05 else ("#E0A23B" if m<5 else "#6B7787")
    else:
        mx=max(abs(v) for _,v in rows)
        def w(m): return 11+abs(m)/mx*68
        def lab(m): return f"{m:.0f}%"
        def col(m): return "#10B981"
    bars=""
    for s,v in rows:
        bars+=f"""<div style='display:flex;align-items:center;margin:26px 0'>
        <div style="width:168px;font-family:'JetBrains Mono';font-weight:700;font-size:36px;color:#E8EDF2">{s}</div>
        <div style='flex:1;position:relative;height:42px'>
        <div style='position:absolute;left:0;top:0;height:42px;width:{w(v):.1f}%;background:{col(v)};border-radius:8px'></div>
        <div style="position:absolute;left:calc({w(v):.1f}% + 18px);top:3px;font-family:'JetBrains Mono';font-weight:700;font-size:32px;color:#E8EDF2">{lab(v)}</div></div></div>"""
    dash=""
    if c["mode"]=="mult":
        ox=9+(math.log10(1.0)-math.log10(0.5))/(math.log10(40)-math.log10(0.5))*70
        dash=f"<div style='position:absolute;left:calc(168px + {ox:.1f}%);top:-14px;bottom:-14px;border-left:2px dashed #E8EDF2;opacity:.5'></div>"
    return page(f"""<div class='hero' style="background-image:url('{HERO}');opacity:.16;transform:scale(1.1)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,#0A0D12 26%,rgba(10,13,18,.5) 100%)"></div>
    <div class='pad'>{header()}
      <div style='margin-top:30px' class='kick'>{c['data_kick']}</div>
      <div style="font-family:Fraunces;font-weight:600;font-size:60px;line-height:1.04;letter-spacing:-1px;margin-top:12px">{c['data_title']}</div>
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div style='position:relative'>{dash}{bars}</div>
        <div style="color:#34D399;font-weight:600;font-size:33px;margin-top:46px">{c['data_cap']}</div></div>
      <div class='foot'>{c['data_foot']}</div></div>""")

def takeaway():
    scrim="linear-gradient(180deg,rgba(10,13,18,.80) 0%,rgba(10,13,18,.42) 45%,rgba(10,13,18,.93) 100%)"
    lab=f"<div style=\"font-family:'JetBrains Mono';font-size:27px;letter-spacing:2px;color:#CFE8DD;margin-top:18px;max-width:900px\">{c['tk_label']}</div>" if c['tk_label'] else ""
    return page(f"""<div class='hero' style="background-image:url('{HERO}')"></div>
    <div class='scrim' style="background:{scrim}"></div>
    <div class='pad'>{header()}
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div class='kick'>{c['tk_kick']}</div>
        <div style="font-family:Fraunces;font-weight:700;font-size:300px;line-height:.84;letter-spacing:-6px;margin-top:16px;background:linear-gradient(180deg,#fff,#7FE9C2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 6px 40px rgba(0,0,0,.5)">{c['big']}<span style='font-size:150px'>{c['unit']}</span></div>{lab}
        <div style="font-size:35px;line-height:1.42;color:#DCE3ED;margin-top:44px;max-width:900px;text-shadow:0 2px 14px rgba(0,0,0,.7)">{c['tk_body']}</div></div>
      <div class='foot'>educational · not financial advice · public, date-stamped sources</div></div>""")

JOBS=[(f"reel_{TK.lower()}_hook.png",hook(),True),(f"reel_{TK.lower()}_data.png",data(),False),(f"reel_{TK.lower()}_takeaway.png",takeaway(),False)]
with sync_playwright() as p:
    b=p.chromium.launch(args=["--no-sandbox"]); pg=b.new_page(viewport={"width":W,"height":H})
    for name,html,transparent in JOBS:
        pg.set_content(html,wait_until="networkidle"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
        pg.screenshot(path="higgs/"+name,omit_background=transparent,clip={"x":0,"y":0,"width":W,"height":H}); print("rendered",name)
    b.close()
print(f"DONE {TK}  big={c['big']}{c['unit']}  rows={[(s,round(v,1)) for s,v in rows]}")
