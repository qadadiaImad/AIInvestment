"""Image-rich carousel kit (static, swipeable) — 3 posts: ADBE (AI software), IONQ (quantum), Congress.
Composites AI-generated hero art + real ticker logos + BIG ticker + story/data -> PNG via headless Playwright.
Voice: confident body; disclaimers THIN on the footer only (no cringe / no stacked NFAs in the story).
"""
import json, base64, math, datetime
from playwright.sync_api import sync_playwright
W,H=1080,1350
site=json.load(open('web/public/data/site.json',encoding='utf-8'))['stocks']
qs=json.load(open('web/public/data/quantum.json',encoding='utf-8'))['stocks']
cg=json.load(open('web/public/data/congress.json',encoding='utf-8'))

def b64(p): return "data:image/png;base64,"+base64.b64encode(open(p,'rb').read()).decode()
HERO={'adbe':b64('higgs/hero_software_2026-06-21.png'),
      'ionq':b64('higgs/hero_quantum_2026-06-21.png'),
      'cong':b64('higgs/hero_congress_2026-06-21.png')}
LOGO={'ADBE':b64('higgs/logo_ADBE.png'),'IONQ':b64('higgs/logo_IONQ.png')}

FONTS="@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600;700;800&display=swap');"
BASE=f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;background:#0A0D12;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:0;background-size:cover;background-position:center}}
.scrim{{position:absolute;inset:0}}
.pad{{position:absolute;inset:0;padding:78px 74px;display:flex;flex-direction:column;z-index:2}}
.hdr{{display:flex;align-items:center;gap:22px}}
.logochip{{width:94px;height:94px;border-radius:22px;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 28px rgba(0,0,0,.45)}}
.logochip img{{width:66px;height:66px;object-fit:contain}}
.tkr{{font-family:'JetBrains Mono';font-weight:800;font-size:72px;line-height:.9;letter-spacing:-1px;color:#fff}}
.ex{{font-family:'JetBrains Mono';font-weight:600;font-size:20px;letter-spacing:3px;color:#34D399;margin-top:6px}}
.pill{{display:inline-flex;align-items:center;gap:14px;font-family:'JetBrains Mono';font-weight:700;font-size:26px;letter-spacing:3px;color:#0A0D12;background:#E0A23B;padding:16px 26px;border-radius:14px}}
.foot{{font-family:'JetBrains Mono';font-size:17px;color:#8893A4;letter-spacing:.5px}}
.kick{{font-family:'JetBrains Mono';font-weight:700;font-size:23px;letter-spacing:4px;color:#34D399}}
.head{{font-family:Fraunces;font-weight:600;line-height:1.03;letter-spacing:-2px;text-shadow:0 4px 30px rgba(0,0,0,.6)}}
"""
def page(body): return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{body}</div></body></html>"
def header(tk,ex):
    return f"""<div class='hdr'><div class='logochip'><img src="{LOGO[tk]}"></div>
    <div><div class='tkr'>{tk}</div><div class='ex'>{ex}</div></div></div>"""

def slide_hook(hero,kick,head,sub,foot="Educational · not financial advice   ·   swipe →",topbar=None,big_head=80):
    scrim="linear-gradient(180deg,rgba(10,13,18,.74) 0%,rgba(10,13,18,.28) 36%,rgba(10,13,18,.45) 60%,rgba(10,13,18,.93) 100%)"
    bar=topbar if topbar else ""
    return page(f"""<div class='hero' style="background-image:url('{hero}')"></div>
    <div class='scrim' style="background:{scrim}"></div>
    <div class='pad'>{bar}
      <div style='margin-top:28px' class='kick'>{kick}</div>
      <div class='head' style="margin-top:auto;font-size:{big_head}px">{head}</div>
      <div style="font-size:31px;line-height:1.4;color:#D7DEE8;margin-top:24px;max-width:850px;text-shadow:0 2px 16px rgba(0,0,0,.75)">{sub}</div>
      <div class='foot' style='margin-top:32px'>{foot}</div></div>""")

def slide_bars(hero,topbar,kick,title,rows,caption,mode,onex_label=None,foot=""):
    # rows: [(label,value)] ; mode 'mult' -> value=multiple ; mode 'disc' -> value=pct below
    if mode=='mult':
        def w(m): return 9+(math.log10(m)-math.log10(0.5))/(math.log10(40)-math.log10(0.5))*72
        def lab(m): return f"{m:.1f}x"
        def col(m): return "#10B981" if m<=1.05 else ("#E0A23B" if m<5 else "#6B7787")
    else:
        mx=max(abs(v) for _,v in rows)
        def w(m): return 11+abs(m)/mx*70
        def lab(m): return f"{m:.0f}%"
        def col(m): return "#10B981"
    bars=""
    for s,v in rows:
        bars+=f"""<div style='display:flex;align-items:center;margin:22px 0'>
        <div style="width:152px;font-family:'JetBrains Mono';font-weight:700;font-size:31px;color:#E8EDF2">{s}</div>
        <div style='flex:1;position:relative;height:36px'>
        <div style='position:absolute;left:0;top:0;height:36px;width:{w(v):.1f}%;background:{col(v)};border-radius:7px'></div>
        <div style="position:absolute;left:calc({w(v):.1f}% + 16px);top:2px;font-family:'JetBrains Mono';font-weight:700;font-size:27px;color:#E8EDF2">{lab(v)}</div></div></div>"""
    dash=""
    if mode=='mult':
        ox=9+(math.log10(1.0)-math.log10(0.5))/(math.log10(40)-math.log10(0.5))*72
        dash=f"<div style='position:absolute;left:calc(152px + {ox:.1f}%);top:-12px;bottom:-12px;border-left:2px dashed #E8EDF2;opacity:.5'></div>"
    return page(f"""<div class='hero' style="background-image:url('{hero}');opacity:.15;transform:scale(1.1)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,#0A0D12 28%,rgba(10,13,18,.5) 100%)"></div>
    <div class='pad'>{topbar}
      <div style='margin-top:24px' class='kick'>{kick}</div>
      <div style="font-family:Fraunces;font-weight:600;font-size:54px;line-height:1.04;letter-spacing:-1px;margin-top:10px">{title}</div>
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div style='position:relative'>{dash}{bars}</div>
        <div style="color:#34D399;font-weight:600;font-size:29px;margin-top:38px">{caption}</div></div>
      <div class='foot'>{foot}</div></div>""")

def slide_takeaway(hero,topbar,kick,big,unit,label,body,foot="Educational · not financial advice"):
    scrim="linear-gradient(180deg,rgba(10,13,18,.80) 0%,rgba(10,13,18,.42) 45%,rgba(10,13,18,.93) 100%)"
    return page(f"""<div class='hero' style="background-image:url('{hero}')"></div>
    <div class='scrim' style="background:{scrim}"></div>
    <div class='pad'>{topbar}
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div class='kick'>{kick}</div>
        <div style="font-family:Fraunces;font-weight:700;font-size:228px;line-height:.86;letter-spacing:-6px;margin-top:16px;background:linear-gradient(180deg,#fff,#7FE9C2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 6px 40px rgba(0,0,0,.5)">{big}<span style='font-size:118px'>{unit}</span></div>
        <div style="font-family:'JetBrains Mono';font-size:26px;letter-spacing:2px;color:#CFE8DD;margin-top:14px">{label}</div>
        <div style="font-size:32px;line-height:1.42;color:#D7DEE8;margin-top:38px;max-width:860px;text-shadow:0 2px 14px rgba(0,0,0,.7)">{body}</div></div>
      <div class='foot'>{foot}</div></div>""")

def slide_basket(hero,tickers,meta,note):
    chips="".join(f"<div style=\"font-family:'JetBrains Mono';font-weight:700;font-size:27px;color:#fff;background:rgba(255,255,255,.08);border:1.5px solid rgba(255,255,255,.18);border-radius:11px;padding:12px 18px\">{t}</div>" for t in tickers)
    mr="".join(f"<div style='display:flex;margin:10px 0'><div style=\"width:150px;font-family:'JetBrains Mono';font-size:21px;color:#9FB0A8\">{k}</div><div style='font-family:Inter;font-weight:600;font-size:25px;color:#fff'>{v}</div></div>" for k,v in meta)
    return page(f"""<div class='hero' style="background-image:url('{hero}');opacity:.22;transform:scale(1.1)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,#0A0D12 22%,rgba(10,13,18,.55) 100%)"></div>
    <div class='pad'><div class='pill'>● PUBLIC RECORD</div>
      <div style="font-family:Fraunces;font-weight:600;font-size:50px;line-height:1.04;letter-spacing:-1px;margin-top:22px">Rep. Matthew Van Epps</div>
      <div style="font-size:25px;color:#E0A23B;margin-top:8px">House Committee on Science, Space &amp; Technology</div>
      <div style='display:flex;flex-wrap:wrap;gap:14px;margin-top:30px'>{chips}</div>
      <div style='background:rgba(255,255,255,.05);border:1.5px solid rgba(255,255,255,.14);border-radius:18px;padding:26px 36px;margin-top:30px'>{mr}</div>
      <div style='font-size:26px;color:#D7DEE8;margin-top:auto'>{note}</div>
      <div class='foot' style='margin-top:22px'>public record · not an accusation · educational</div></div>""")

# ===== numbers =====
ADBE_DC=site['ADBE']['valuation']['fundamental_discount_pct']
cheap=[(s,site[s]['valuation']['fundamental_discount_pct']) for s in ('TEAM','ADBE','INTU','WDAY','NOW')]
IONQ_DC=qs['IONQ']['valuation']['fundamental_discount_pct']
MULT={s:qs[s]['valuation']['price']/qs[s]['valuation']['fundamental_value'] for s in ('IONQ','QUBT','QBTS','RGTI')}
ve=[t for t in cg['trades'] if 'van epps' in (t.get('politician') or '').lower() and t.get('txn_date')=='06/16/2026' and t.get('txn_type')=='S']
ve_syms=[t['ticker'] for t in ve]

H_ADBE=header('ADBE',"AI SOFTWARE LAYER · NASDAQ")
H_IONQ=header('IONQ',"QUANTUM COMPUTING · NYSE")

SL={
 # ---- ADBE ----
 "v4_adbe_1_hook.png":slide_hook(HERO['adbe'],"AI · THE OVERLOOKED LAYER",
   "Wall Street bought<br>the chip. It forgot<br>who <em style='font-style:italic;color:#34D399'>sells the AI.</em>",
   "Adobe just slid to ~68% below what analysts think it&rsquo;s worth &mdash; and the smart money is starting to circle.",topbar=H_ADBE),
 "v4_adbe_2_data.png":slide_bars(HERO['adbe'],H_ADBE,"THE AI SOFTWARE LAYER · ON SALE","Every one of them, marked down",
   cheap,"The whole layer that runs on the chips is on sale.","disc",foot="% below analysts' fundamental value · model estimate · NFA"),
 "v4_adbe_3_takeaway.png":slide_takeaway(HERO['adbe'],H_ADBE,"ADOBE",f"~{abs(ADBE_DC):.0f}","%","BELOW ANALYSTS' FUNDAMENTAL VALUE",
   "The hype went to the chips. The discount&rsquo;s on the software that runs on them &mdash; just as the AI-software thesis starts to turn."),
 # ---- IONQ ----
 "v4_ionq_1_hook.png":slide_hook(HERO['ionq'],"QUANTUM · THE ODD ONE OUT",
   "Quantum, priced like<br>a lottery ticket.<br><em style='font-style:italic;color:#34D399'>One name isn&rsquo;t.</em>",
   "Same hype label, opposite math &mdash; and this week IonQ shipped real product while the rest ran on the story.",topbar=H_IONQ),
 "v4_ionq_2_data.png":slide_bars(HERO['ionq'],H_IONQ,"PRICE vs ANALYSTS' FUNDAMENTAL VALUE","How many times above fair value",
   [(s,MULT[s]) for s in ('IONQ','QUBT','QBTS','RGTI')],"IonQ is the only one trading below the model.","mult",
   foot="dashed line = price equals fundamental value · analysts' model · NFA"),
 "v4_ionq_3_takeaway.png":slide_takeaway(HERO['ionq'],H_IONQ,"THE OUTLIER",f"~{abs(IONQ_DC):.0f}","%",
   f"BELOW MODEL — RIGETTI ~{MULT['RGTI']:.0f}x · D-WAVE ~{MULT['QBTS']:.0f}x ABOVE",
   "Most of quantum is priced on the story. One name is priced below analysts&rsquo; model."),
 # ---- CONGRESS ----
 "v4_cong_1_hook.png":slide_hook(HERO['cong'],"PUBLIC RECORD · STOCK ACT",
   "He helps oversee<br>Big Tech. Then he<br><em style='font-style:italic;color:#E0A23B'>sold all of it.</em>",
   "A House Science-Committee member exited Nvidia, Microsoft, Meta, Apple &amp; more &mdash; eight tech names, in one day.",
   foot="public record · not an accusation   ·   swipe →"),
 "v4_cong_2_card.png":slide_basket(HERO['cong'],ve_syms,
   [("Committee","Science, Space &amp; Technology"),("Action","Sold — all one day"),("Amount","$1,001 – $50,000 each"),("Traded","Jun 16, 2026"),("Filed","Jun 17, 2026")],
   "His committee&rsquo;s job is to oversee the U.S. tech &amp; research sector &mdash; the same sector he exited."),
 "v4_cong_3_takeaway.png":slide_takeaway(HERO['cong'],"<div class='pill'>● PUBLIC RECORD</div>","TECH NAMES, ONE DAY","8","","SOLD FROM THE SECTOR HIS COMMITTEE OVERSEES",
   "Members are allowed to trade. The public record simply shows who sold what, when &mdash; and the committee they sit on.",
   foot="public record · not an accusation · educational"),
}
with sync_playwright() as p:
    b=p.chromium.launch(args=["--no-sandbox"]); pg=b.new_page(viewport={"width":W,"height":H})
    for name,html in SL.items():
        pg.set_content(html,wait_until="networkidle"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(900)
        pg.screenshot(path="higgs/"+name,clip={"x":0,"y":0,"width":W,"height":H}); print("rendered",name)
    b.close()
print(f"DONE  ADBE_DC={ADBE_DC} IONQ_DC={IONQ_DC} mult={ {k:round(v,1) for k,v in MULT.items()} } van_epps={len(ve_syms)}")
