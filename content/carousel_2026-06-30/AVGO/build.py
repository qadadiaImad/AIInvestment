# -*- coding: utf-8 -*-
# AVGO (Broadcom) carousel — dual-mode soft/dark. Date 2026-06-30.
# Self-contained: reads price series, hardcodes verbatim ground-truth data.
# Renders each slide to PNG via standalone playwright.sync_api (NOT any shared MCP browser).
import json, os, datetime
from playwright.sync_api import sync_playwright

ROOT = "C:/Users/yassi/Documents/projects/AIInvestment"
OUT  = ROOT + "/content/carousel_2026-06-30/AVGO"
W, H = 1080, 1350
def dt(s): return datetime.datetime.strptime(s[:10], "%Y-%m-%d")
today = dt("2026-06-30")

# ---- design system reused verbatim from higgs/_build_v2.py ----
FONTS="<style>@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');*{margin:0;padding:0;box-sizing:border-box}.slide{width:1080px;height:1350px;position:relative;overflow:hidden}</style>"
SOFT_CSS=""".soft{background:radial-gradient(120% 100% at 15% 0%,#FAF7F0 0%,#F1EBDD 55%,#E7DECB 100%);color:#1A1C22;font-family:Inter}
.soft:before{content:"";position:absolute;inset:0;opacity:.05;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='0.9'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.pad{padding:96px 88px;height:100%;display:flex;flex-direction:column;position:relative}
.kick{font-family:'JetBrains Mono';font-weight:600;font-size:26px;letter-spacing:4px;color:#0E9F6E}
.dot{display:inline-block;width:11px;height:11px;border-radius:50%;background:#0E9F6E;margin-right:14px;vertical-align:middle}
.wm{position:absolute;top:96px;right:88px;font-family:'JetBrains Mono';font-size:22px;color:#B6AE9C;letter-spacing:2px}
.foot{font-family:'JetBrains Mono';font-size:19px;color:#9AA0AC;letter-spacing:1px}"""
DARK_CSS=""".dk{background:#0A0D12;color:#E8EDF2;font-family:Inter}
.dk:before{content:"";position:absolute;inset:0;background:radial-gradient(90% 70% at 78% 8%,rgba(16,185,129,.14) 0%,rgba(16,185,129,0) 60%)}
.dk:after{content:"";position:absolute;inset:0;opacity:.05;background-image:linear-gradient(#2A3340 1px,transparent 1px),linear-gradient(90deg,#2A3340 1px,transparent 1px);background-size:60px 60px}
.pad{position:relative;padding:90px 80px;height:100%;display:flex;flex-direction:column;z-index:1}
.kick{font-family:'JetBrains Mono';font-weight:600;font-size:24px;letter-spacing:4px;color:#34D399}
.wm{position:absolute;top:90px;right:80px;font-family:'JetBrains Mono';font-size:22px;color:#3A4250;letter-spacing:2px}
.foot{font-family:'JetBrains Mono';font-size:18px;color:#5A6472;letter-spacing:.5px}"""
def page(body,css,cls):
    return f"<!doctype html><html><head><meta charset='utf-8'>{FONTS}<style>{css}</style></head><body><div class='slide {cls}'>{body}</div></body></html>"

# ---- ground-truth data (verbatim) ----
FN = 312.62                 # fundamental value
GF_PULL = 370.07            # model pull price 2026-07-01
PREMIUM_MODEL = 18.38       # 370.07 vs 312.62
medps = [("2026-10-31",386.14),("2027-10-31",633.48),("2028-10-31",856.95)]

# price series
px = json.load(open(ROOT+"/web/public/data/prices/AVGO.json",encoding="utf-8"))["series"]
px = [(dt(p["date"]),p["close"]) for p in px if p.get("close")]
pser = [(d,v) for d,v in px if d >= dt("2024-07-01")]
SPOT = pser[-1][1]                 # 2026-06-30 close = 377.75
PREMIUM_SPOT = (SPOT/FN-1)*100      # premium at slide close

# ================= CHART BUILDERS (viewBox 940x560) =================
SVW,SVH=940,560; PADL,PADR,PADT,PADB=12,66,16,32
def mkXY(t0,t1,vmin,vmax):
    span=(t1-t0).days
    def X(d): return PADL+(d-t0).days/span*(SVW-PADL-PADR)
    def Y(v): return PADT+(1-(v-vmin)/(vmax-vmin))*(SVH-PADT-PADB)
    return X,Y
def pth(s,X,Y): return "M "+" L ".join(f"{X(d):.1f},{Y(v):.1f}" for d,v in s)

def soft_price_chart():
    t0,t1=pser[0][0],pser[-1][0]
    vmin=min(v for _,v in pser); vmax=max(v for _,v in pser)
    pad=(vmax-vmin)*0.10; vmin-=pad; vmax+=pad
    X,Y=mkXY(t0,t1,vmin,vmax)
    area=pth(pser,X,Y)+f" L {X(pser[-1][0]):.1f},{SVH-PADB} L {X(pser[0][0]):.1f},{SVH-PADB} Z"
    ex,ey=X(pser[-1][0]),Y(pser[-1][1])
    yrs=range(t0.year+1,t1.year+1)
    yt="".join(f"<text x='{X(dt(str(y)+'-01-01')):.0f}' y='{SVH-6}' fill='#B6AE9C' font-family=\"JetBrains Mono\" font-size='15' text-anchor='middle'>{y}</text>" for y in yrs)
    return f"""<svg viewBox='0 0 {SVW} {SVH}' width='100%'><defs>
    <linearGradient id='ars' x1='0' x2='0' y1='0' y2='1'><stop offset='0' stop-color='#0E9F6E' stop-opacity='.22'/><stop offset='1' stop-color='#0E9F6E' stop-opacity='0'/></linearGradient></defs>
    <path d='{area}' fill='url(#ars)'/>
    <path d='{pth(pser,X,Y)}' fill='none' stroke='#0E9F6E' stroke-width='4' stroke-linejoin='round'/>
    <circle cx='{ex:.0f}' cy='{ey:.0f}' r='9' fill='#0E9F6E'/>
    <text x='{SVW-4:.0f}' y='{ey-18:.0f}' fill='#0E7A56' font-family=\"JetBrains Mono\" font-weight='700' font-size='30' text-anchor='end'>${SPOT:.0f}</text>{yt}</svg>"""

def dark_value_chart():
    proj=[(today,FN)]+[(dt(d),v) for d,v in medps]
    t0=pser[0][0]; t1=proj[-1][0]
    fh=[(t0,FN),(today,FN)]                     # flat fundamental historical line
    allv=[v for _,v in pser]+[v for _,v in proj]+[FN]
    vmin=min(allv); vmax=max(allv); pad=(vmax-vmin)*0.06; vmin-=pad; vmax+=pad
    X,Y=mkXY(t0,t1,vmin,vmax)
    area=pth(pser,X,Y)+f" L {X(pser[-1][0]):.1f},{SVH-PADB} L {X(pser[0][0]):.1f},{SVH-PADB} Z"
    pxn=X(today)
    yrs=range(t0.year+1,t1.year+1)
    yt="".join(f"<text x='{X(dt(str(y)+'-01-01')):.0f}' y='{SVH-6}' fill='#5A6472' font-family=\"JetBrains Mono\" font-size='15' text-anchor='middle'>{y}</text>" for y in yrs)
    return f"""<svg viewBox='0 0 {SVW} {SVH}' width='100%'><defs>
    <linearGradient id='ar' x1='0' x2='0' y1='0' y2='1'><stop offset='0' stop-color='#5A6472' stop-opacity='.28'/><stop offset='1' stop-color='#5A6472' stop-opacity='0'/></linearGradient>
    <filter id='gl' x='-20%' y='-20%' width='140%' height='140%'><feGaussianBlur stdDeviation='5' result='b'/><feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs>
    <path d='{area}' fill='url(#ar)'/>
    <line x1='{pxn:.0f}' y1='16' x2='{pxn:.0f}' y2='{SVH-PADB}' stroke='#2A3340' stroke-width='1.5' stroke-dasharray='3 6'/>
    <path d='{pth(pser,X,Y)}' fill='none' stroke='#AEB8C6' stroke-width='3.5' stroke-linejoin='round'/>
    <path d='{pth(fh,X,Y)}' fill='none' stroke='#10B981' stroke-width='4.5' stroke-linejoin='round' filter='url(#gl)'/>
    <path d='{pth(proj,X,Y)}' fill='none' stroke='#38BDF8' stroke-width='4' stroke-dasharray='2 9' stroke-linecap='round' opacity='.9'/>
    <circle cx='{X(pser[-1][0]):.0f}' cy='{Y(SPOT):.0f}' r='8' fill='#AEB8C6'/>
    <circle cx='{pxn:.0f}' cy='{Y(FN):.0f}' r='8' fill='#10B981' filter='url(#gl)'/>
    <text x='6' y='40' fill='#AEB8C6' font-family=\"JetBrains Mono\" font-weight='700' font-size='26' text-anchor='start'>PRICE  ${SPOT:.0f}</text>
    <text x='6' y='78' fill='#34D399' font-family=\"JetBrains Mono\" font-weight='700' font-size='26' text-anchor='start'>VALUE  ${FN:.0f}</text>{yt}</svg>"""

# ================= RATIO CARDS =================
def ratio_card(label, comp, med, badge, bcol):
    return f"""<div style='background:#10151C;border:1px solid #1C2530;border-radius:16px;padding:26px 28px'>
    <div style="font-family:'JetBrains Mono';font-size:21px;letter-spacing:2px;color:#8A95A5">{label}</div>
    <div style="display:flex;align-items:baseline;gap:16px;margin-top:12px">
      <div style="font-family:Fraunces;font-weight:700;font-size:62px;line-height:1;color:#F4F8FC">{comp}</div>
      <div style='margin-left:auto;background:{bcol}22;border:1px solid {bcol}66;color:{bcol};border-radius:999px;padding:8px 16px;font-family:"JetBrains Mono";font-weight:700;font-size:20px'>{badge}</div>
    </div>
    <div style="font-family:'JetBrains Mono';font-size:22px;color:#6B7688;margin-top:14px">industry median {med}</div></div>"""

# ================= SLIDES =================
def slide1():
    b=f"""<div class='wm'>2026&middot;06&middot;30</div><div class='pad'>
    <div class='kick'><span class='dot'></span>SEMIS &nbsp;&middot;&nbsp; BROADCOM</div>
    <div style="font-family:Fraunces;font-weight:600;font-size:82px;line-height:1.03;letter-spacing:-2px;margin-top:26px">Up <em style='font-style:italic;color:#0E9F6E'>37.5%</em> in a year&mdash;<br>then reportedly shed<br><em style='font-style:italic;color:#B4690E'>~16% in a month.</em></div>
    <div style='margin-top:34px'>{soft_price_chart()}</div>
    <div style="font-size:31px;line-height:1.42;color:#5C6270;margin-top:26px;max-width:900px">One drawdown, two camps: <b>sell the rip, or buy more?</b> The $377 close sits well above where an analyst model reads fair &mdash; the next slides walk the numbers. <span style='color:#8A8170'>(price move reported 2026-06-30)</span></div>
    <div class='foot' style='margin-top:22px'>educational &middot; not financial advice &middot; swipe &rarr;</div></div>"""
    return page(b,SOFT_CSS,"soft")

def slide2():
    b=f"""<div class='wm'>AVGO &middot; VALUE</div><div class='pad'>
    <div class='kick'>PRICE vs FUNDAMENTAL VALUE</div>
    <div style="font-family:Fraunces;font-weight:600;font-size:56px;line-height:1.05;letter-spacing:-1px;margin-top:16px">A <span style='color:#F4B740'>~18% premium</span> to an<br>analyst fundamental-value model</div>
    <div style="font-size:24px;color:#8A95A5;margin-top:10px;white-space:nowrap">price <b style='color:#AEB8C6'>${SPOT:.0f}</b> vs fundamental value <b style='color:#34D399'>${FN:.0f}</b> &middot; model read ${GF_PULL:.0f} (2026-07-01)</div>
    <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>{dark_value_chart()}
    <div style="display:flex;gap:30px;flex-wrap:wrap;font-family:'JetBrains Mono';font-size:22px;margin:14px 4px 0">
    <span><i style='display:inline-block;width:30px;height:5px;border-radius:3px;background:#AEB8C6;margin-right:10px;vertical-align:middle'></i>Share price</span>
    <span><i style='display:inline-block;width:30px;height:5px;border-radius:3px;background:#10B981;margin-right:10px;vertical-align:middle'></i>Fundamental value</span>
    <span><i style='display:inline-block;width:30px;height:5px;border-radius:3px;background:#38BDF8;margin-right:10px;vertical-align:middle'></i>Model projection</span></div></div>
    <div style="font-size:29px;line-height:1.4;color:#C2CAD6;max-width:900px;margin-top:4px">Honest read: <b>modestly overvalued today.</b> The dashed line is the model&rsquo;s own projected value rising toward $857 by 2028 &mdash; an estimate, not a forecast.</div>
    <div class='foot' style='margin-top:20px'>public fundamentals &middot; analyst model estimate, not a forecast &middot; NFA</div></div>"""
    return page(b,DARK_CSS,"dk")

def slide3():
    cards="".join([
        ratio_card("P / E TTM","62.9x","63.3x","IN LINE","#8A95A5"),
        ratio_card("P / S","24.1x","6.8x","3.5&times; RICHER","#B4690E"),
        ratio_card("GROSS MARGIN","65.7%","35.9%","ELITE","#10B981"),
        ratio_card("ROIC","20.8%","&minus;2.1%","FAR ABOVE","#10B981"),
        ratio_card("REV GROWTH YoY","32.3%","14.4%","2.2&times;","#10B981"),
        ratio_card("NET MARGIN","38.8%","&mdash;","STRONG","#10B981"),
    ])
    b=f"""<div class='wm'>AVGO &middot; RATIOS</div><div class='pad'>
    <div class='kick'>FUNDAMENTALS vs SEMICONDUCTOR MEDIAN</div>
    <div style="font-family:Fraunces;font-weight:600;font-size:54px;line-height:1.04;letter-spacing:-1px;margin-top:14px">Elite margins, ordinary multiple</div>
    <div style="font-size:26px;color:#8A95A5;margin-top:8px">company vs live Semiconductor industry median (TradingView scan, 2026-07-01)</div>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:30px'>{cards}</div>
    <div style="background:#0E1A16;border:1px solid #10B98155;border-radius:16px;padding:26px 30px;margin-top:auto">
    <div style="font-family:'JetBrains Mono';font-size:20px;letter-spacing:2px;color:#34D399">THE ONE FACTOR</div>
    <div style="font-size:29px;line-height:1.4;color:#DCE3EC;margin-top:10px">The whole debate is <b>elite fundamentals vs a rich multiple.</b> A 62.9x P/E is basically the sector median &mdash; but AVGO pairs it with margins, ROIC and growth far above peers, on a custom-ASIC / AI franchise. The market pays up for that; the model still reads it modestly rich because 62.9x already prices in years of growth.</div></div>
    <div class='foot' style='margin-top:20px'>industry medians: live &middot; educational &middot; NFA</div></div>"""
    return page(b,DARK_CSS,"dk")

def slide4():
    cards="".join([
        ratio_card("EPS GROWTH YoY","125.8%","&mdash;","EXPLOSIVE","#10B981"),
        ratio_card("GROSS MARGIN","65.7%","35.9%","+30 pts","#10B981"),
        ratio_card("DEBT / EQUITY","0.74","n/a","MODEST","#8A95A5"),
        ratio_card("5Y EARNINGS GROWTH","17.7%","&mdash;","DURABLE","#10B981"),
    ])
    b=f"""<div class='wm'>AVGO &middot; ENGINE</div><div class='pad'>
    <div class='kick'>WHAT JUSTIFIES THE MULTIPLE</div>
    <div style="font-family:Fraunces;font-weight:600;font-size:54px;line-height:1.04;letter-spacing:-1px;margin-top:14px">The growth doing the<br>heavy lifting</div>
    <div style="font-size:26px;color:#8A95A5;margin-top:8px">the numbers a 62.9x multiple is leaning on</div>
    <div style='display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:34px'>{cards}</div>
    <div style="font-size:30px;line-height:1.44;color:#C2CAD6;max-width:920px;margin-top:44px">EPS up <b style='color:#34D399'>125.8%</b> year-on-year and a <b style='color:#34D399'>65.7%</b> gross margin, carried on modest <b>0.74</b> debt-to-equity. That is the case for the premium &mdash; and also why the reported drawdown reignited the &ldquo;sell or add?&rdquo; debate. <span style='color:#8A95A5'>D/E has no clean live sector median, shown as n/a.</span></div>
    <div class='foot' style='margin-top:auto'>public fundamentals &middot; educational &middot; not financial advice</div></div>"""
    return page(b,DARK_CSS,"dk")

def slide5():
    def row(tag,tcol,txt):
        return f"""<div style='display:flex;gap:20px;margin:22px 0;align-items:flex-start'>
        <div style='flex:none;margin-top:4px;background:{tcol}22;border:1px solid {tcol}66;color:{tcol};border-radius:999px;padding:7px 16px;font-family:"JetBrains Mono";font-weight:700;font-size:19px;letter-spacing:1px'>{tag}</div>
        <div style='font-size:29px;line-height:1.4;color:#2A2C33'>{txt}</div></div>"""
    news=(
        row("REPORTED","#0E7A56","A reported custom-ASIC face-off pits <b>Broadcom against Marvell</b> for the merchant-silicon crown (reported 2026-06-30).")+
        row("RUMORED","#B4690E","A <b>rumored</b> &ldquo;biggest three-year upside in AI inference&rdquo; angle is circulating &mdash; unconfirmed framing, treat as narrative (rumored 2026-06-30).")+
        row("FILED","#6B6250","Public record: a congressional purchase of AVGO worth <b>$15,001&ndash;50,000</b> filed Sep 2025 (Rep. Cleo Fields, LA-06). Dated disclosure &mdash; <b>not a signal, not an accusation.</b>")
    )
    b=f"""<div class='wm'>2026&middot;06&middot;30</div><div class='pad'>
    <div class='kick'><span class='dot' style='background:#B4690E'></span>THE CHATTER &nbsp;&middot;&nbsp; STAY SKEPTICAL</div>
    <div style="font-family:Fraunces;font-weight:600;font-size:60px;line-height:1.03;letter-spacing:-1.5px;margin-top:24px">What&rsquo;s being said &mdash;<br>and how sure it is</div>
    <div style='margin-top:20px'>{news}</div>
    <div style="background:#FFFCF6;border:1.5px solid #E4DCCB;border-radius:18px;padding:30px 34px;margin-top:auto">
    <div style="font-size:30px;line-height:1.42;color:#1A1C22"><b>Bottom line:</b> a great business at a full price. Analysts read a ~18% premium to fundamental value; the reported dip narrowed it, not erased it. <b>Do your own research.</b></div></div>
    <div class='foot' style='margin-top:24px'>educational, not financial advice &middot; certainty labels shown &middot; DYOR</div></div>"""
    return page(b,SOFT_CSS,"soft")

SLIDES={"slide_1":slide1(),"slide_2":slide2(),"slide_3":slide3(),"slide_4":slide4(),"slide_5":slide5()}

if __name__=="__main__":
    for name,html in SLIDES.items():
        open(os.path.join(OUT,name+".html"),"w",encoding="utf-8").write(html)
    with sync_playwright() as p:
        b=p.chromium.launch(args=["--no-sandbox"]); pg=b.new_page(viewport={"width":W,"height":H})
        for name,html in SLIDES.items():
            pg.set_content(html,wait_until="networkidle"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
            pg.screenshot(path=os.path.join(OUT,name+".png"),clip={"x":0,"y":0,"width":W,"height":H}); print("rendered",name)
        b.close()
    print(f"DONE spot={SPOT} premium_spot={PREMIUM_SPOT:.2f}% premium_model={PREMIUM_MODEL}%")
