"""9:16 reel frames for the Congress (Van Epps) sample video.
Outputs: reel_cong_hook.png (TRANSPARENT overlay for the animated hero), reel_cong_card.png,
reel_cong_takeaway.png (full 1080x1920 frames, Capitol hero baked). Rendered via headless Playwright.
"""
import json, base64, os, pathlib
from playwright.sync_api import sync_playwright
os.chdir(pathlib.Path(__file__).resolve().parent.parent)   # anchor to repo root — runnable from any cwd
W,H=1080,1920
cg=json.load(open('web/public/data/congress.json',encoding='utf-8'))
ve=[t for t in cg['trades'] if 'van epps' in (t.get('politician') or '').lower() and t.get('txn_date')=='06/16/2026' and t.get('txn_type')=='S']
ve_syms=[t['ticker'] for t in ve]
# newest generated Capitol hero — no per-round edit needed when only the date moves
_heroes=sorted(pathlib.Path('higgs').glob('hero_congress_*.png'))
if not _heroes: raise SystemExit("no higgs/hero_congress_*.png found — generate the hero first")
HERO="data:image/png;base64,"+base64.b64encode(_heroes[-1].read_bytes()).decode()

FONTS="@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600;700;800&display=swap');"
BASE=f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
.slide{{width:{W}px;height:{H}px;position:relative;overflow:hidden;font-family:Inter;color:#E8EDF2}}
.hero{{position:absolute;inset:0;background-size:cover;background-position:center}}
.scrim{{position:absolute;inset:0}}
.pad{{position:absolute;inset:0;padding:104px 80px;display:flex;flex-direction:column;z-index:2}}
.pill{{display:inline-flex;align-items:center;gap:14px;font-family:'JetBrains Mono';font-weight:700;font-size:28px;letter-spacing:3px;color:#0A0D12;background:#E0A23B;padding:18px 28px;border-radius:15px;align-self:flex-start}}
.foot{{font-family:'JetBrains Mono';font-size:20px;color:#9AA6B6;letter-spacing:.5px}}
.head{{font-family:Fraunces;font-weight:600;line-height:1.04;letter-spacing:-2px;text-shadow:0 4px 30px rgba(0,0,0,.65)}}
"""
def page(b): return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{b}</div></body></html>"

def hook():  # transparent overlay (scrim + text), no hero
    scrim="linear-gradient(180deg,rgba(10,13,18,.62) 0%,rgba(10,13,18,.10) 34%,rgba(10,13,18,.40) 66%,rgba(10,13,18,.92) 100%)"
    return page(f"""<div class='scrim' style="background:{scrim}"></div>
    <div class='pad'><div class='pill'>● PUBLIC RECORD · STOCK ACT</div>
      <div class='head' style="margin-top:auto;font-size:96px">He helps oversee<br>Big Tech. Then he<br><em style='font-style:italic;color:#E0A23B'>sold all of it.</em></div>
      <div style="font-size:35px;line-height:1.4;color:#DCE3ED;margin-top:30px;max-width:900px;text-shadow:0 2px 16px rgba(0,0,0,.8)">A House Science-Committee member exited Nvidia, Microsoft, Meta, Apple &amp; more &mdash; eight tech names, in one day.</div>
      <div class='foot' style='margin-top:40px'>public record · not an accusation</div></div>""")

def card():
    chips="".join(f"<div style=\"font-family:'JetBrains Mono';font-weight:700;font-size:32px;color:#fff;background:rgba(255,255,255,.08);border:1.6px solid rgba(255,255,255,.20);border-radius:13px;padding:15px 22px\">{t}</div>" for t in ve_syms)
    meta=[("Committee","Science, Space &amp; Technology"),("Action","Sold — all one day"),("Amount","$1,001 – $50,000 each"),("Traded","Jun 16, 2026"),("Filed","Jun 17, 2026")]
    mr="".join(f"<div style='display:flex;margin:13px 0'><div style=\"width:180px;font-family:'JetBrains Mono';font-size:24px;color:#9FB0A8\">{k}</div><div style='font-family:Inter;font-weight:600;font-size:29px;color:#fff'>{v}</div></div>" for k,v in meta)
    return page(f"""<div class='hero' style="background-image:url('{HERO}');opacity:.20;transform:scale(1.1)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,#0A0D12 18%,rgba(10,13,18,.5) 100%)"></div>
    <div class='pad'><div class='pill'>● PUBLIC RECORD</div>
      <div style="font-family:Fraunces;font-weight:600;font-size:62px;line-height:1.04;letter-spacing:-1px;margin-top:30px">Rep. Matthew Van Epps</div>
      <div style="font-size:30px;color:#E0A23B;margin-top:12px">House Committee on Science, Space &amp; Technology</div>
      <div style='display:flex;flex-wrap:wrap;gap:18px;margin-top:42px'>{chips}</div>
      <div style='background:rgba(255,255,255,.05);border:1.6px solid rgba(255,255,255,.15);border-radius:22px;padding:34px 44px;margin-top:44px'>{mr}</div>
      <div style='font-size:31px;line-height:1.4;color:#DCE3ED;margin-top:auto'>His committee&rsquo;s job is to oversee the U.S. tech &amp; research sector &mdash; the same sector he exited.</div>
      <div class='foot' style='margin-top:28px'>public record · not an accusation · educational</div></div>""")

def takeaway():
    scrim="linear-gradient(180deg,rgba(10,13,18,.78) 0%,rgba(10,13,18,.40) 45%,rgba(10,13,18,.93) 100%)"
    return page(f"""<div class='hero' style="background-image:url('{HERO}')"></div>
    <div class='scrim' style="background:{scrim}"></div>
    <div class='pad'><div class='pill'>● PUBLIC RECORD</div>
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div style="font-family:'JetBrains Mono';font-weight:700;font-size:26px;letter-spacing:4px;color:#E0A23B">TECH NAMES · ONE DAY</div>
        <div style="font-family:Fraunces;font-weight:700;font-size:300px;line-height:.84;letter-spacing:-6px;margin-top:18px;background:linear-gradient(180deg,#fff,#F0CF92);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 6px 40px rgba(0,0,0,.5)">8</div>
        <div style="font-family:'JetBrains Mono';font-size:28px;letter-spacing:2px;color:#ECD9B8;margin-top:18px;max-width:880px">SOLD FROM THE SECTOR HIS COMMITTEE OVERSEES</div>
        <div style="font-size:34px;line-height:1.42;color:#DCE3ED;margin-top:42px;max-width:900px;text-shadow:0 2px 14px rgba(0,0,0,.7)">Members are allowed to trade. The record simply shows who sold what, when &mdash; and the committee they sit on.</div></div>
      <div class='foot'>public record · not an accusation · educational</div></div>""")

JOBS=[("reel_cong_hook.png",hook(),True),("reel_cong_card.png",card(),False),("reel_cong_takeaway.png",takeaway(),False)]
with sync_playwright() as p:
    b=p.chromium.launch(args=["--no-sandbox"]); pg=b.new_page(viewport={"width":W,"height":H})
    for name,html,transparent in JOBS:
        pg.set_content(html,wait_until="networkidle"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
        pg.screenshot(path="higgs/"+name,omit_background=transparent,clip={"x":0,"y":0,"width":W,"height":H}); print("rendered",name,"(transparent)" if transparent else "")
    b.close()
print("DONE  van_epps syms:",ve_syms)
