import json, datetime
from playwright.sync_api import sync_playwright
W,H=1080,1350
def dt(s): return datetime.datetime.strptime(s[:10],"%Y-%m-%d")
today=dt("2026-06-20")
site=json.load(open('web/public/data/site.json',encoding='utf-8'))
qs=json.load(open('web/public/data/quantum.json',encoding='utf-8'))['stocks']
cg=json.load(open('web/public/data/congress.json',encoding='utf-8'))

FONTS="<style>@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');*{margin:0;padding:0;box-sizing:border-box}.slide{width:1080px;height:1350px;position:relative;overflow:hidden}</style>"

SOFT_CSS=""".soft{background:radial-gradient(120% 100% at 15% 0%,#FAF7F0 0%,#F1EBDD 55%,#E7DECB 100%);color:#1A1C22;font-family:Inter}
.soft:before{content:"";position:absolute;inset:0;opacity:.05;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='0.9'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
.pad{padding:96px 88px;height:100%;display:flex;flex-direction:column;position:relative}
.kick{font-family:'JetBrains Mono';font-weight:600;font-size:26px;letter-spacing:4px;color:#0E9F6E}
.dot{display:inline-block;width:11px;height:11px;border-radius:50%;background:#0E9F6E;margin-right:14px;vertical-align:middle}
.wm{position:absolute;top:96px;right:88px;font-family:'JetBrains Mono';font-size:22px;color:#B6AE9C;letter-spacing:2px}
.foot{font-family:'JetBrains Mono';font-size:19px;color:#9AA0AC;letter-spacing:1px}"""
DARK_CSS=""".dk{background:#0A0D12;color:#E8EDF2;font-family:Inter}
.pad{position:relative;padding:90px 80px;height:100%;display:flex;flex-direction:column}
.kick{font-family:'JetBrains Mono';font-weight:600;font-size:24px;letter-spacing:4px;color:#34D399}
.wm{position:absolute;top:90px;right:80px;font-family:'JetBrains Mono';font-size:22px;color:#3A4250;letter-spacing:2px}
.foot{font-family:'JetBrains Mono';font-size:18px;color:#5A6472;letter-spacing:.5px}"""

def page(body,css,cls):
    return f"<!doctype html><html><head><meta charset='utf-8'>{FONTS}<style>{css}</style></head><body><div class='slide {cls}'>{body}</div></body></html>"

def soft_hook(kick,head,sub,foot="not financial advice  ·  swipe &rarr;"):
    b=f"""<div class='wm'>&nbsp;</div><div class='pad'>
    <div class='kick'><span class='dot'></span>{kick}</div>
    <div style="font-family:Fraunces;font-weight:600;font-size:86px;line-height:1.04;letter-spacing:-2px;margin-top:30px">{head}</div>
    <div style="font-size:33px;line-height:1.42;color:#5C6270;margin-top:auto;max-width:820px">{sub}</div>
    <div class='foot' style='margin-top:30px'>{foot}</div></div>"""
    return page(b,SOFT_CSS,"soft")

def soft_takeaway(kick,big,sub):
    b=f"""<div class='pad'>
    <div style='width:120px;height:5px;border-radius:3px;background:#0E9F6E'></div>
    <div class='kick' style='margin-top:24px'>{kick}</div>
    <div style="font-family:Fraunces;font-weight:700;font-size:80px;line-height:1.04;letter-spacing:-2px;margin-top:18px;color:#15171C">{big}</div>
    <div style="font-size:33px;line-height:1.42;color:#5C6270;margin-top:auto;max-width:840px">{sub}</div>
    <div class='foot' style='margin-top:28px'>educational · not financial advice · public, date-stamped sources</div></div>"""
    return page(b,SOFT_CSS,"soft")

def dark_number(kick,big,unit,lab,sub):
    b=f"""<div class='wm'>&nbsp;</div><div class='pad'>
    <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
      <div class='kick'>{kick}</div>
      <div style="font-family:Fraunces;font-weight:700;font-size:210px;line-height:.9;letter-spacing:-6px;margin-top:30px;background:linear-gradient(180deg,#FFFFFF,#9FE7C8);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{big}<span style='font-size:112px'>{unit}</span></div>
      <div style="font-family:'JetBrains Mono';font-size:27px;color:#8A95A5;letter-spacing:2px;margin-top:14px">{lab}</div>
      <div style="font-size:33px;line-height:1.42;color:#C2CAD6;margin-top:46px;max-width:850px">{sub}</div>
    </div>
    <div class='foot'>educational · not financial advice · public, date-stamped sources</div></div>"""
    return page(b,DARK_CSS,"dk")

def dark_chart(sym,kick,title,note):
    o=site['stocks'][sym] if sym in site['stocks'] else qs[sym]; val=o['valuation']
    PN=val['price']; FN=val['fundamental_value']
    px=json.load(open('web/public/data/prices/'+sym+'.json',encoding='utf-8'))['series']
    pser=[(dt(p['date']),p['close']) for p in px if p.get('close')]
    fser=[(dt(f['date']),f['value']) for f in o.get('fundamental_value_series',[])]
    t0=min(d for d,_ in pser+fser)
    t1=min(max(d for d,_ in pser+fser), today+datetime.timedelta(days=300))
    pser=[(d,v) for d,v in pser if d<=t1]; fser=[(d,v) for d,v in fser if d<=t1]
    vmin=min(v for _,v in pser+fser); vmax=max(v for _,v in pser+fser)
    SVW,SVH=940,560; PADL,PADR,PADT,PADB=12,66,16,32
    def X(d): return PADL+(d-t0).days/((t1-t0).days)*(SVW-PADL-PADR)
    def Y(v): return PADT+(1-(v-vmin)/(vmax-vmin))*(SVH-PADT-PADB)
    def pth(s): return "M "+" L ".join(f"{X(d):.1f},{Y(v):.1f}" for d,v in s)
    fh=[(d,v) for d,v in fser if d<=today]; fp=[(d,v) for d,v in fser if d>=today]
    area=pth(pser)+f" L {X(pser[-1][0]):.1f},{SVH-PADB} L {X(pser[0][0]):.1f},{SVH-PADB} Z"
    pxn=X(today); pyn=Y(PN); fyn=Y(FN)
    yrs=range(t0.year+1,t1.year,2)
    yt="".join(f"<text x='{X(dt(str(y)+'-01-01')):.0f}' y='{SVH-6}' fill='#5A6472' font-family='JetBrains Mono' font-size='15' text-anchor='middle'>{y}</text>" for y in yrs)
    svg=f"""<svg viewBox='0 0 {SVW} {SVH}' width='100%'><defs>
    <linearGradient id='ar' x1='0' x2='0' y1='0' y2='1'><stop offset='0' stop-color='#5A6472' stop-opacity='.28'/><stop offset='1' stop-color='#5A6472' stop-opacity='0'/></linearGradient>
    <filter id='gl' x='-20%' y='-20%' width='140%' height='140%'><feGaussianBlur stdDeviation='5' result='b'/><feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs>
    <path d='{area}' fill='url(#ar)'/>
    <path d='{pth(pser)}' fill='none' stroke='#AEB8C6' stroke-width='3.5' stroke-linejoin='round'/>
    <path d='{pth(fh)}' fill='none' stroke='#10B981' stroke-width='4.5' stroke-linejoin='round' filter='url(#gl)'/>
    <path d='{pth(fp)}' fill='none' stroke='#38BDF8' stroke-width='3.5' stroke-dasharray='2 9' stroke-linecap='round' opacity='.8'/>
    <line x1='{pxn:.0f}' y1='16' x2='{pxn:.0f}' y2='{SVH-PADB}' stroke='#2A3340' stroke-width='1.5' stroke-dasharray='3 6'/>
    <circle cx='{pxn:.0f}' cy='{pyn:.0f}' r='8' fill='#AEB8C6'/><circle cx='{pxn:.0f}' cy='{fyn:.0f}' r='8' fill='#10B981' filter='url(#gl)'/>
    <text x='{SVW-4:.0f}' y='40' fill='#AEB8C6' font-family='JetBrains Mono' font-weight='700' font-size='26' text-anchor='end'>PRICE  ${PN:.0f}</text>
    <text x='{SVW-4:.0f}' y='78' fill='#34D399' font-family='JetBrains Mono' font-weight='700' font-size='26' text-anchor='end'>VALUE  ${FN:.0f}</text>{yt}</svg>"""
    b=f"""<div class='pad'><div class='kick'>{kick}</div>
    <div style="font-family:Fraunces;font-weight:600;font-size:58px;line-height:1.05;letter-spacing:-1px;margin-top:18px">{title}</div>
    <div style="font-size:28px;color:#8A95A5;margin-top:10px">{note}</div>
    <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>{svg}
    <div style="display:flex;gap:34px;font-family:'JetBrains Mono';font-size:23px;margin:16px 4px 0">
    <span><i style='display:inline-block;width:30px;height:5px;border-radius:3px;background:#AEB8C6;margin-right:12px;vertical-align:middle'></i>Share price</span>
    <span><i style='display:inline-block;width:30px;height:5px;border-radius:3px;background:#10B981;margin-right:12px;vertical-align:middle'></i>Fundamental value</span></div></div>
    <div class='foot' style='margin-top:24px'>public fundamentals · analysts' model estimate, not a forecast · NFA</div></div>"""
    return page(b,DARK_CSS,"dk")

def dark_bars_ai(rows,kick,title,note,caption):
    # rows: [(label, discount_pct)] ; positive disc = below model (cheap)
    import math
    mx=max(abs(d) for _,d in rows)
    bars=""
    for s,d in rows:
        w=10+abs(d)/mx*78
        bars+=f"""<div style='display:flex;align-items:center;margin:20px 0'>
        <div style="width:160px;font-family:'JetBrains Mono';font-weight:700;font-size:30px;color:#E8EDF2">{s}</div>
        <div style='flex:1;position:relative;height:34px'>
        <div style='position:absolute;left:0;top:0;height:34px;width:{w:.1f}%;background:#10B981;border-radius:6px'></div>
        <div style="position:absolute;left:calc({w:.1f}% + 14px);top:2px;font-family:'JetBrains Mono';font-weight:700;font-size:26px;color:#34D399">{d:.0f}%</div></div></div>"""
    b=f"""<div class='pad'><div class='kick'>{kick}</div>
    <div style="font-family:Fraunces;font-weight:600;font-size:56px;line-height:1.05;letter-spacing:-1px;margin-top:18px">{title}</div>
    <div style="font-size:28px;color:#8A95A5;margin-top:10px">{note}</div>
    <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>{bars}
    <div style="color:#34D399;font-family:Inter;font-weight:600;font-size:30px;margin-top:40px">{caption}</div></div>
    <div class='foot'>% below analysts' fundamental-value model · model estimate, not a forecast · NFA</div></div>"""
    return page(b,DARK_CSS,"dk")

def dark_multiples(syms,kick,title,note,caption):
    rows=[(s,qs[s]['valuation']['price']/qs[s]['valuation']['fundamental_value']) for s in syms]
    import math
    def w(m): return 8+ (math.log10(m)-math.log10(0.5))/(math.log10(40)-math.log10(0.5))*78
    bars=""
    for s,m in rows:
        col="#10B981" if m<=1 else ("#B4690E" if m<5 else "#5A6472")
        bars+=f"""<div style='display:flex;align-items:center;margin:22px 0'>
        <div style="width:150px;font-family:'JetBrains Mono';font-weight:700;font-size:30px;color:#E8EDF2">{s}</div>
        <div style='flex:1;position:relative;height:34px'>
        <div style='position:absolute;left:0;top:0;height:34px;width:{w(m):.1f}%;background:{col};border-radius:6px'></div>
        <div style="position:absolute;left:calc({w(m):.1f}% + 14px);top:2px;font-family:'JetBrains Mono';font-weight:700;font-size:26px;color:#E8EDF2">{m:.1f}x</div></div></div>"""
    onex=w(1.0)
    b=f"""<div class='pad'><div class='kick'>{kick}</div>
    <div style="font-family:Fraunces;font-weight:600;font-size:58px;line-height:1.05;letter-spacing:-1px;margin-top:18px">{title}</div>
    <div style="font-size:28px;color:#8A95A5;margin-top:10px">{note}</div>
    <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
    <div style='position:relative'>
    <div style='position:absolute;left:calc(150px + {onex:.1f}%);top:-10px;bottom:-10px;border-left:2px dashed #E8EDF2;opacity:.45'></div>
    {bars}</div>
    <div style="color:#34D399;font-family:Inter;font-weight:600;font-size:30px;margin-top:46px">{caption}</div></div>
    <div class='foot'>dashed line = price equals fundamental value · analysts' model · NFA</div></div>"""
    return page(b,DARK_CSS,"dk")

def soft_basket(member,tickers,meta,note):
    chips="".join(f"<div style=\"font-family:'JetBrains Mono';font-weight:700;font-size:30px;color:#1A1C22;background:#FFFCF6;border:1.5px solid #E4DCCB;border-radius:12px;padding:14px 22px\">{t}</div>" for t in tickers)
    mr="".join(f"<div style='display:flex;margin:12px 0'><div style=\"width:150px;font-family:'JetBrains Mono';font-size:22px;color:#8A8170\">{k}</div><div style='font-family:Inter;font-weight:600;font-size:26px;color:#1A1C22'>{v}</div></div>" for k,v in meta)
    b=f"""<div class='pad'><div class='kick' style='color:#B4690E'><span class='dot' style='background:#B4690E'></span>PUBLIC RECORD</div>
    <div style="font-family:Fraunces;font-weight:600;font-size:56px;line-height:1.04;letter-spacing:-1px;margin-top:22px">{member}</div>
    <div style="font-size:26px;color:#8A8170;margin-top:8px">disclosed selling, all on the same day</div>
    <div style='display:flex;flex-wrap:wrap;gap:16px;margin-top:34px'>{chips}</div>
    <div style='background:#FFFCF6;border:1.5px solid #E4DCCB;border-radius:18px;padding:30px 40px;margin-top:34px'>{mr}</div>
    <div style='font-size:27px;color:#5C6270;margin-top:auto'>{note}</div>
    <div class='foot' style='margin-top:24px'>public disclosure for transparency — not an accusation, not a signal · NFA</div></div>"""
    return page(b,SOFT_CSS,"soft")

# ---- compute fresh numbers ----
ADBE_DC=site['stocks']['ADBE']['valuation']['fundamental_discount_pct']
IONQ_DC=qs['IONQ']['valuation']['fundamental_discount_pct']
RGTI_M=qs['RGTI']['valuation']['price']/qs['RGTI']['valuation']['fundamental_value']
QBTS_M=qs['QBTS']['valuation']['price']/qs['QBTS']['valuation']['fundamental_value']
cheap=[('TEAM',site['stocks']['TEAM']['valuation']['fundamental_discount_pct']),
       ('ADBE',ADBE_DC),
       ('INTU',site['stocks']['INTU']['valuation']['fundamental_discount_pct']),
       ('WDAY',site['stocks']['WDAY']['valuation']['fundamental_discount_pct']),
       ('NOW',site['stocks']['NOW']['valuation']['fundamental_discount_pct'])]

# Van Epps single-day basket (pulled dynamically for accuracy)
ve=[t for t in cg['trades'] if 'van epps' in (t.get('politician') or '').lower() and t.get('txn_date')=='06/16/2026' and t.get('txn_type')=='S']
ve_syms=[t['ticker'] for t in ve]
print("Van Epps 06/16 sells:",ve_syms)

SL={
 "v3_post1_1_hook.png":soft_hook("AI &nbsp;·&nbsp; VALUATION",
   "The chips get the hype.<br>The <em style='font-style:italic;color:#0E9F6E'>software</em> gets the<br>discount.",
   "The layer that actually sells AI &mdash; Adobe, Intuit, ServiceNow &mdash; reportedly trades far below analysts&rsquo; fundamental-value model."),
 "v3_post1_2_graph.png":dark_bars_ai(cheap,"APPLICATION LAYER &nbsp;·&nbsp; vs MODEL","How cheap, by analysts&rsquo; model","gap below fundamental value",
   "Five software names sit 56&ndash;70% below analysts&rsquo; model."),
 "v3_post1_3_takeaway.png":dark_number("THE GAP",f"~{abs(ADBE_DC):.0f}","%","ADOBE BELOW ANALYSTS' FUNDAMENTAL VALUE",
   "Reportedly, even the people who build the chips say software benefits next. The hype and the price are looking in different directions. Not financial advice."),
 "v3_post2_1_hook.png":soft_hook("QUANTUM",
   "&lsquo;Quantum stocks&rsquo;<br>aren&rsquo;t <em style='font-style:italic;color:#0E9F6E'>one trade.</em>",
   "Same hype label. Opposite math &mdash; one name even trades below what analysts model."),
 "v3_post2_2_graph.png":dark_multiples(["IONQ","QUBT","QBTS","RGTI"],"QUANTUM &nbsp;·&nbsp; PRICE vs MODEL","Price vs fundamental value",
   "times the price sits above analysts&rsquo; fundamental value","IonQ is the only one trading below the model."),
 "v3_post2_3_takeaway.png":dark_number("THE OUTLIER",f"~{abs(IONQ_DC):.0f}","%",f"IonQ BELOW MODEL — RIGETTI ~{RGTI_M:.0f}x, D-WAVE ~{QBTS_M:.0f}x ABOVE",
   "Most quantum names are priced on narrative. One is priced below analysts&rsquo; model. Reported, not confirmed. Not a recommendation."),
 "v3_post3_1_hook.png":soft_hook("PUBLIC RECORD",
   "A House member sold<br>13 stocks &mdash;<br><em style='font-style:italic;color:#B4690E'>in a single day.</em>",
   "Seven were AI &amp; Big-Tech names. Straight from the STOCK Act filing &mdash; just the record.","not financial advice  ·  swipe &rarr;"),
 "v3_post3_2_card.png":soft_basket("Rep. Matthew Van Epps",ve_syms,
   [("Type","Sales"),("Amount","$1,001 – $50,000 each"),("Traded","Jun 16, 2026"),("Filed","Jun 17, 2026")],
   "None were from the application-software layer analysts flag ~60% below fundamental value."),
 "v3_post3_3_takeaway.png":soft_takeaway("TRANSPARENCY","Public record —<br>not a signal.",
   "Not an accusation, not insider anything, not advice. Just who disclosed what, and when."),
}
with sync_playwright() as p:
    b=p.chromium.launch(args=["--no-sandbox"]); pg=b.new_page(viewport={"width":W,"height":H})
    for name,html in SL.items():
        pg.set_content(html,wait_until="networkidle"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
        pg.screenshot(path="higgs/"+name,clip={"x":0,"y":0,"width":W,"height":H}); print("rendered",name)
    b.close()
print(f"DONE  ADBE_DC={ADBE_DC} IONQ_DC={IONQ_DC} RGTI={RGTI_M:.1f}x QBTS={QBTS_M:.1f}x  van_epps={len(ve_syms)} names")
