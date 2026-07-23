"""Kit-driven image-rich carousel builder (static, swipeable), 4:5 (1080x1350) PNGs.

Reads the SAME authored reel kit the Studio shows (`reels_<date>_kit.md`) and renders the
current cycle's carousel: one 3-slide post (hook / data-bars / takeaway) per stock CFG block,
plus the congress card. Numbers are filled live from web/public/data/{site,quantum}.json; copy,
picks and hero refs come from the kit. Composites AI hero art + real ticker logos + BIG ticker
via headless Playwright. Voice: confident body; disclaimers THIN on the footer only.

    python higgs/_build_v4.py                       # newest reels_<date>_kit.md
    python higgs/_build_v4.py --date 2026-06-27
    python higgs/_build_v4.py --kit higgs/reels_2026-06-27_kit.md

Hero/logo art missing (Phase-1 not run yet) -> render on the solid dark background + warn.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import pathlib
import re
import sys

HIGGS = pathlib.Path(__file__).resolve().parent
ROOT = HIGGS.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))
from aiinvest.kit_md import parse_cfg, parse_congress_card  # noqa: E402

W, H = 1080, 1350

# Compliance footer for computed-screen-result slides (halal-screen cards and any
# ordinary slide that carries a verdict badge). Single source of truth — used at
# every slide/footer site below instead of a repeated literal.
NOT_FATWA_FOOT = "Computed methodology result — not a fatwa · not financial advice"

FONTS = "@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600;700;800&display=swap');"
BASE = f"""*{{margin:0;padding:0;box-sizing:border-box}}{FONTS}
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


def page(body):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}</style></head><body><div class='slide'>{body}</div></body></html>"


def header(tk, ex, logo_b64=None, badge=None):
    inner = f'<img src="{logo_b64}">' if logo_b64 else ""
    b = ""
    if badge:
        b = (f"<div style=\"margin-left:auto;font-family:'JetBrains Mono';font-weight:700;"
             f"font-size:22px;letter-spacing:2px;color:#0A0D12;background:{badge['color']};"
             f"padding:12px 20px;border-radius:12px\">{badge['text']}</div>")
    return f"""<div class='hdr'><div class='logochip'>{inner}</div>
    <div><div class='tkr'>{tk}</div><div class='ex'>{ex}</div></div>{b}</div>"""


def slide_define(hero, topbar, descriptor, teaser, foot=NOT_FATWA_FOOT):
    """The carousel's dedicated company-definition slide (first slide when the
    kit's CFG carries a non-empty `company_def`). Full-bleed hero + a dark
    scrim (heavier than slide_hook's — this slide's text sits over the image
    top-to-bottom, not just the lower half) so the descriptor stays legible
    regardless of what's underneath. `teaser` is an optional one-line
    leverage/context line (kit's `screen_head`, or ""); omitted when empty."""
    scrim = "linear-gradient(180deg,rgba(10,13,18,.70) 0%,rgba(10,13,18,.32) 34%,rgba(10,13,18,.48) 60%,rgba(10,13,18,.93) 100%)"
    teaser_html = (
        f"<div style=\"font-size:29px;line-height:1.4;color:#7FE9C2;margin-top:22px;"
        f"max-width:850px;text-shadow:0 2px 14px rgba(0,0,0,.75)\">{teaser}</div>"
        if teaser else "")
    return page(f"""<div class='hero' style="background-image:url('{hero}')"></div>
    <div class='scrim' style="background:{scrim}"></div>
    <div class='pad'>{topbar}
      <div style='margin-top:28px' class='kick'>WHAT THEY DO</div>
      <div class='head' style="margin-top:auto;font-size:64px">{descriptor}</div>
      {teaser_html}
      <div class='foot' style='margin-top:32px'>{foot}</div></div>""")


def slide_hook(hero, kick, head, sub, foot="Educational · not financial advice   ·   swipe →", topbar=None, big_head=80):
    scrim = "linear-gradient(180deg,rgba(10,13,18,.74) 0%,rgba(10,13,18,.28) 36%,rgba(10,13,18,.45) 60%,rgba(10,13,18,.93) 100%)"
    bar = topbar if topbar else ""
    return page(f"""<div class='hero' style="background-image:url('{hero}')"></div>
    <div class='scrim' style="background:{scrim}"></div>
    <div class='pad'>{bar}
      <div style='margin-top:28px' class='kick'>{kick}</div>
      <div class='head' style="margin-top:auto;font-size:{big_head}px">{head}</div>
      <div style="font-size:31px;line-height:1.4;color:#D7DEE8;margin-top:24px;max-width:850px;text-shadow:0 2px 16px rgba(0,0,0,.75)">{sub}</div>
      <div class='foot' style='margin-top:32px'>{foot}</div></div>""")


def slide_bars(hero, topbar, kick, title, rows, caption, mode, foot=""):
    # rows: [(label,value)] ; mode 'mult' -> value=multiple ; mode 'disc' -> value=pct below
    if mode == 'mult':
        def w(m): return 9 + (math.log10(m) - math.log10(0.5)) / (math.log10(40) - math.log10(0.5)) * 72
        def lab(m): return f"{m:.1f}x"
        def col(m): return "#10B981" if m <= 1.05 else ("#E0A23B" if m < 5 else "#6B7787")
    else:
        mx = max((abs(v) for _, v in rows), default=1) or 1
        def w(m): return 11 + abs(m) / mx * 70
        def lab(m): return f"{m:.0f}%"
        def col(m): return "#10B981"
    bars = ""
    for s, v in rows:
        bars += f"""<div style='display:flex;align-items:center;margin:22px 0'>
        <div style="width:152px;font-family:'JetBrains Mono';font-weight:700;font-size:31px;color:#E8EDF2">{s}</div>
        <div style='flex:1;position:relative;height:36px'>
        <div style='position:absolute;left:0;top:0;height:36px;width:{w(v):.1f}%;background:{col(v)};border-radius:7px'></div>
        <div style="position:absolute;left:calc({w(v):.1f}% + 16px);top:2px;font-family:'JetBrains Mono';font-weight:700;font-size:27px;color:#E8EDF2">{lab(v)}</div></div></div>"""
    dash = ""
    if mode == 'mult':
        ox = 9 + (math.log10(1.0) - math.log10(0.5)) / (math.log10(40) - math.log10(0.5)) * 72
        dash = f"<div style='position:absolute;left:calc(152px + {ox:.1f}%);top:-12px;bottom:-12px;border-left:2px dashed #E8EDF2;opacity:.5'></div>"
    return page(f"""<div class='hero' style="background-image:url('{hero}');opacity:.15;transform:scale(1.1)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,#0A0D12 28%,rgba(10,13,18,.5) 100%)"></div>
    <div class='pad'>{topbar}
      <div style='margin-top:24px' class='kick'>{kick}</div>
      <div style="font-family:Fraunces;font-weight:600;font-size:54px;line-height:1.04;letter-spacing:-1px;margin-top:10px">{title}</div>
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div style='position:relative'>{dash}{bars}</div>
        <div style="color:#34D399;font-weight:600;font-size:29px;margin-top:38px">{caption}</div></div>
      <div class='foot'>{foot}</div></div>""")


def slide_takeaway(hero, topbar, kick, big, unit, label, body, foot="Educational · not financial advice"):
    scrim = "linear-gradient(180deg,rgba(10,13,18,.80) 0%,rgba(10,13,18,.42) 45%,rgba(10,13,18,.93) 100%)"
    return page(f"""<div class='hero' style="background-image:url('{hero}')"></div>
    <div class='scrim' style="background:{scrim}"></div>
    <div class='pad'>{topbar}
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div class='kick'>{kick}</div>
        <div style="font-family:Fraunces;font-weight:700;font-size:228px;line-height:.86;letter-spacing:-6px;margin-top:16px;background:linear-gradient(180deg,#fff,#7FE9C2);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 6px 40px rgba(0,0,0,.5)">{big}<span style='font-size:118px'>{unit}</span></div>
        <div style="font-family:'JetBrains Mono';font-size:26px;letter-spacing:2px;color:#CFE8DD;margin-top:14px">{label}</div>
        <div style="font-size:32px;line-height:1.42;color:#D7DEE8;margin-top:38px;max-width:860px;text-shadow:0 2px 14px rgba(0,0,0,.7)">{body}</div></div>
      <div class='foot'>{foot}</div></div>""")


def _receipts_strip(card):
    """Compact one-strip proof line: per-standard ratio/cap + mark, plus the data stamp."""
    parts = []
    for r in card["standards_rows"]:
        mark = "✓" if r["ok"] else "✕"
        mcol = "#10B981" if r["ok"] else "#C25E5E"
        parts.append(f"{r['name']} {r['ratio']}<span style='color:#8893A4'>/{r['threshold']}</span> "
                     f"<span style='color:{mcol}'>{mark}</span>")
    body = " <span style='color:#3A4652'>·</span> ".join(parts)
    return (f"<div style='border-top:1.5px solid rgba(255,255,255,.14);padding-top:20px;margin-top:34px'>"
            f"<div style=\"font-family:'JetBrains Mono';font-size:19px;letter-spacing:3px;color:#8893A4\">THE RECEIPTS</div>"
            f"<div style=\"font-family:'JetBrains Mono';font-weight:700;font-size:24px;color:#E8EDF2;margin-top:12px\">{body}</div>"
            f"<div style=\"font-family:'JetBrains Mono';font-size:18px;color:#8893A4;margin-top:10px\">data as of {card['inputs_asof'][:10]}</div></div>")


def _screen_body(hero, topbar, card, foot=NOT_FATWA_FOOT, human=None):
    if human and human.get("head"):
        body2 = (f"<div style='font-size:33px;line-height:1.45;color:#D7DEE8;margin-top:26px;max-width:880px'>{human['body2']}</div>"
                 if human.get("body2") else "")
        return f"""<div class='hero' style="background-image:url('{hero}');opacity:.12;transform:scale(1.1)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,#0A0D12 30%,rgba(10,13,18,.55) 100%)"></div>
    <div class='pad'>{topbar}
      <div style='margin-top:22px' class='kick'>THE SCREEN — IN PLAIN WORDS</div>
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div style="font-family:Fraunces;font-weight:700;font-size:92px;line-height:1.0;letter-spacing:-2px">{human['head']}</div>
        <div style='font-size:33px;line-height:1.45;color:#E8EDF2;margin-top:34px;max-width:880px'>{human.get('body') or ''}</div>
        {body2}
        {_receipts_strip(card)}</div>
      <div class='foot'>{foot}</div></div>"""
    rows = ""
    for r in card["standards_rows"]:
        mark = "✓" if r["ok"] else "✕"
        mcol = "#10B981" if r["ok"] else "#C25E5E"
        rows += f"""<div style='display:flex;align-items:center;margin:20px 0;gap:18px'>
        <div style="width:120px;font-family:'JetBrains Mono';font-weight:700;font-size:28px">{r['name']}</div>
        <div style='font-size:34px;color:{mcol};width:44px'>{mark}</div>
        <div style='flex:1'>
          <div style='font-size:24px;color:#9FB0A8'>{r['binding_label']}</div>
          <div style="font-family:'JetBrains Mono';font-weight:700;font-size:28px;color:#E8EDF2">
            {r['ratio']} <span style='color:#8893A4'>vs cap {r['threshold']}</span>
            <span style='color:{mcol}'>({r['margin']})</span></div></div></div>"""
    return f"""<div class='hero' style="background-image:url('{hero}');opacity:.12;transform:scale(1.1)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,#0A0D12 30%,rgba(10,13,18,.55) 100%)"></div>
    <div class='pad'>{topbar}
      <div style='margin-top:22px' class='kick'>THE SCREEN — WORKED MATH</div>
      <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
        <div style='background:rgba(255,255,255,.04);border:1.5px solid rgba(255,255,255,.12);border-radius:18px;padding:30px 36px'>{rows}</div>
        <div style='font-size:27px;color:#D7DEE8;margin-top:26px'>{card['business_line']}</div>
        <div style='font-size:27px;color:#7FE9C2;margin-top:10px'>{card['purification_line']}</div>
        <div class='foot' style='margin-top:18px'>inputs as of {card['inputs_asof'][:10]}</div></div>
      <div class='foot'>{foot}</div></div>"""


def slide_screen(hero, topbar, card, foot=NOT_FATWA_FOOT, human=None):
    return page(_screen_body(hero, topbar, card, foot, human=human))


def slide_basket(hero, name, subhead, pill, tickers, meta, note):
    chips = "".join(f"<div style=\"font-family:'JetBrains Mono';font-weight:700;font-size:27px;color:#fff;background:rgba(255,255,255,.08);border:1.5px solid rgba(255,255,255,.18);border-radius:11px;padding:12px 18px\">{t}</div>" for t in tickers)
    mr = "".join(f"<div style='display:flex;margin:10px 0'><div style=\"width:150px;font-family:'JetBrains Mono';font-size:21px;color:#9FB0A8\">{k}</div><div style='font-family:Inter;font-weight:600;font-size:25px;color:#fff'>{v}</div></div>" for k, v in meta)
    return page(f"""<div class='hero' style="background-image:url('{hero}');opacity:.22;transform:scale(1.1)"></div>
    <div class='scrim' style="background:linear-gradient(180deg,#0A0D12 22%,rgba(10,13,18,.55) 100%)"></div>
    <div class='pad'><div class='pill'>{pill}</div>
      <div style="font-family:Fraunces;font-weight:600;font-size:50px;line-height:1.04;letter-spacing:-1px;margin-top:22px">{name}</div>
      <div style="font-size:25px;color:#E0A23B;margin-top:8px">{subhead}</div>
      <div style='display:flex;flex-wrap:wrap;gap:14px;margin-top:30px'>{chips}</div>
      <div style='background:rgba(255,255,255,.05);border:1.5px solid rgba(255,255,255,.14);border-radius:18px;padding:26px 36px;margin-top:30px'>{mr}</div>
      <div style='font-size:26px;color:#D7DEE8;margin-top:auto'>{note}</div>
      <div class='foot' style='margin-top:22px'>public record · not an accusation · educational</div></div>""")


# --------------------------------------------------------------------------- assembly (pure)

def _cfg_tickers(md):
    """Bare tickers that have a CFG block (``"TK":{``), in document order, de-duplicated."""
    seen = []
    for tk in re.findall(r'"([A-Z0-9.]{1,12})":\{', md):
        if tk not in seen:
            seen.append(tk)
    return seen


def _rows_from_bundle(tickers, stocks, mode):
    rows = []
    for rt in tickers:
        rec = stocks.get(rt)
        if not rec:
            continue
        val = rec.get("valuation", {})
        if mode == "mult":
            pr, fv = val.get("price"), val.get("fundamental_value")
            if pr and fv:
                rows.append((rt, pr / fv))
        else:
            d = val.get("fundamental_discount_pct")
            if d is not None:
                rows.append((rt, d))
    return rows


def build_slides(md, site_stocks, quantum_stocks, hero_map, logo_map, date, halal_map=None):
    """kit md + bundle stocks -> {filename: html}. Pure: hero/logo art injected as
    {filename: data-uri-or-None}; missing art => '' (solid-bg fallback).

    halal_map: optional {ticker: screen_card_data dict} (aiinvest.halal_join). When a
    ticker's kit CFG has a halal_script AND a card is present, slide 2 becomes the
    screen-card (worked-math) slide instead of the ordinary bars slide, and every slide
    for that ticker carries the verdict badge in its header."""
    out = {}
    for tk in _cfg_tickers(md):
        c = parse_cfg(md, tk)
        if not c:
            continue
        card = (halal_map or {}).get(tk)
        if c.get("halal_script") and card is None and halal_map is not None:
            # Bundle loaded (halal_map is a real dict, possibly {}) but this
            # ticker isn't in it: exclude the ticker entirely rather than
            # falling through to a broken ordinary bars slide (IMPORTANT 4).
            # Legacy/no-bundle path (halal_map is None) keeps the old fallback.
            continue
        stocks = quantum_stocks if c.get("src") == "quantum" else site_stocks
        hero = hero_map.get(c.get("hero")) or ""
        is_halal_post = bool(c.get("halal_script")) and card is not None
        badge = card["badge"] if card else None
        hdr = header(tk, c.get("ex") or "", logo_map.get(c.get("logo")), badge=badge)
        mode = c["data"]["mode"] or "disc"
        rows = _rows_from_bundle(c["data"]["rows"], stocks, mode)
        tkl = tk.lower()
        hk = c["hook"]; dt = c["data"]; tkw = c["takeaway"]
        # Company-definition slide: FIRST slide, gated on the kit carrying a
        # non-empty company_def (task-4). The July-21 3-slide kits predate
        # this field -- parse_cfg returns None for them -- so they render
        # unchanged (backward compat). Numbered "_0_" so it sorts before the
        # existing "_1_hook" filename without renumbering anything else (the
        # Studio indexer globs `v4_<tk>_\d_<name>.png` and localeCompare-sorts).
        if c.get("company_def"):
            out[f"v4_{tkl}_0_define.png"] = slide_define(
                hero, hdr, c["company_def"], c.get("screen_head") or "")
        out[f"v4_{tkl}_1_hook.png"] = slide_hook(
            hero, hk["kick"] or "", hk["head"] or "", hk["sub"] or "", topbar=hdr)
        if is_halal_post:
            human = {"head": c.get("screen_head"), "body": c.get("screen_body"), "body2": c.get("screen_body2")}
            out[f"v4_{tkl}_2_data.png"] = slide_screen(hero, hdr, card, human=human)
            out[f"v4_{tkl}_3_takeaway.png"] = slide_takeaway(
                hero, hdr, tkw["kick"] or "", tkw["big"] or "", tkw["unit"] or "",
                tkw["label"] or "", tkw["body"] or "",
                foot=NOT_FATWA_FOOT)
        else:
            # IMPORTANT 5: an ordinary post whose ticker still carries a verdict
            # badge (card present, just not a halal_script post) must carry the
            # compliance footer on its bars/takeaway slides too.
            bars_foot = NOT_FATWA_FOOT if card else (dt["foot"] or "")
            takeaway_foot_kw = {"foot": NOT_FATWA_FOOT} if card else {}
            out[f"v4_{tkl}_2_data.png"] = slide_bars(
                hero, hdr, dt["kick"] or "", dt["title"] or "", rows, dt["cap"] or "", mode, foot=bars_foot)
            out[f"v4_{tkl}_3_takeaway.png"] = slide_takeaway(
                hero, hdr, tkw["kick"] or "", tkw["big"] or "", tkw["unit"] or "", tkw["label"] or "", tkw["body"] or "",
                **takeaway_foot_kw)

    card = parse_congress_card(md)
    if card:
        hero = hero_map.get(f"hero_congress_{date}.png") or ""
        pill = card.get("pill") or "● PUBLIC RECORD"
        kick = pill.replace("●", "").strip()
        out["v4_cong_1_hook.png"] = slide_hook(
            hero, kick, card.get("hook_head") or "", card.get("hook_sub") or "",
            foot="public record · not an accusation   ·   swipe →")
        out["v4_cong_2_card.png"] = slide_basket(
            hero, card.get("name") or "", card.get("subhead") or "", pill,
            card.get("chips") or [], card.get("meta") or [], card.get("hook_sub") or "")
        out["v4_cong_3_takeaway.png"] = slide_takeaway(
            hero, f"<div class='pill'>{pill}</div>", "", card.get("big") or "", "",
            card.get("big_label") or "", card.get("body") or "",
            foot=card.get("footer") or "public record · not an accusation · educational")
    return out


RW, RH = 1080, 1920


def _page916(body, transparent=False):
    bg = "background:transparent" if transparent else ""
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}"
            f".slide{{width:{RW}px;height:{RH}px;{bg}}}</style></head>"
            f"<body style='{bg}'><div class='slide' style='width:{RW}px;height:{RH}px;{bg}'>{body}</div></body></html>")


def build_halal_frames(md, hero_map, halal_map):
    """Halal entries -> 9:16 reel frames {reel_<tkl>_{hook,data,takeaway}.png: html}.
    Hook frame is transparent (make_reel.py overlays it on the animated hero)."""
    out = {}
    for tk in _cfg_tickers(md):
        c = parse_cfg(md, tk)
        card = (halal_map or {}).get(tk)
        if not c or not c.get("halal_script") or not card:
            continue
        tkl = tk.lower()
        hdr = header(tk, c.get("ex") or "", badge=card["badge"])
        hk = c["hook"]; tkw = c["takeaway"]
        hero = hero_map.get(c.get("hero")) or ""
        out[f"reel_{tkl}_hook.png"] = _page916(f"""<div class='pad'>{hdr}
          <div style='margin-top:34px' class='kick'>{hk['kick'] or ''}</div>
          <div class='head' style='margin-top:auto;font-size:96px'>{hk['head'] or ''}</div>
          <div style='font-size:38px;line-height:1.4;color:#D7DEE8;margin-top:28px'>{hk['sub'] or ''}</div>
          <div class='foot' style='margin-top:40px'>Educational · not financial or religious advice</div></div>""",
          transparent=True)
        human = {"head": c.get("screen_head"), "body": c.get("screen_body"), "body2": c.get("screen_body2")}
        out[f"reel_{tkl}_data.png"] = _page916(_screen_body(hero, hdr, card, human=human))
        out[f"reel_{tkl}_takeaway.png"] = _page916(f"""<div class='pad'>{hdr}
          <div style='flex:1;display:flex;flex-direction:column;justify-content:center'>
            <div class='kick'>{tkw['kick'] or ''}</div>
            <div style="font-family:Fraunces;font-weight:700;font-size:260px;line-height:.86;letter-spacing:-6px;margin-top:16px;background:linear-gradient(180deg,#fff,#7FE9C2);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{tkw['big'] or ''}<span style='font-size:130px'>{tkw['unit'] or ''}</span></div>
            <div style="font-family:'JetBrains Mono';font-size:30px;letter-spacing:2px;color:#CFE8DD;margin-top:16px">{tkw['label'] or ''}</div>
            <div style='font-size:36px;line-height:1.42;color:#D7DEE8;margin-top:40px'>{tkw['body'] or ''}</div></div>
          <div class='foot'>{NOT_FATWA_FOOT}</div></div>""")
    return out


# --------------------------------------------------------------------------- kit selection / io

def pick_kit(higgs_dir, date=None, kit_path=None):
    """Resolve the kit file: explicit --kit, else reels_<date>_kit.md, else the newest by date."""
    if kit_path:
        return pathlib.Path(kit_path)
    higgs_dir = pathlib.Path(higgs_dir)
    if date:
        return higgs_dir / f"reels_{date}_kit.md"

    def dkey(p):
        m = re.search(r"reels_(\d{4}-\d{2}-\d{2})_kit\.md", p.name)
        return m.group(1) if m else ""
    cands = sorted(higgs_dir.glob("reels_*_kit.md"), key=dkey)
    return cands[-1] if cands else None


_MIME_BY_SUFFIX = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def _b64(path):
    p = pathlib.Path(path)
    if not p.exists():
        return None
    mime = _MIME_BY_SUFFIX.get(p.suffix.lower(), "image/png")
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Render the current cycle's carousel from a reel kit.")
    ap.add_argument("--date", help="Kit date YYYY-MM-DD (default: newest reels_*_kit.md).")
    ap.add_argument("--kit", help="Explicit path to a reels_<date>_kit.md.")
    args = ap.parse_args(argv)

    kit = pick_kit(HIGGS, args.date, args.kit)
    if not kit or not kit.exists():
        print(f"no kit found ({kit}). Author higgs/reels_<date>_kit.md first.")
        return 2
    md = kit.read_text(encoding="utf-8")
    m = re.search(r"reels_(\d{4}-\d{2}-\d{2})_kit", kit.name)
    date = args.date or (m.group(1) if m else "")

    site = json.loads((ROOT / "web/public/data/site.json").read_text(encoding="utf-8"))["stocks"]
    quantum = json.loads((ROOT / "web/public/data/quantum.json").read_text(encoding="utf-8"))["stocks"]

    halal_map = None
    from aiinvest.halal_join import HalalDataMissing, load_halal, screen_card_data
    tk_list = _cfg_tickers(md)
    wants_halal = any((parse_cfg(md, t) or {}).get("halal_script") for t in tk_list)
    try:
        verdicts, warns = load_halal(ROOT / "web/public/data/halal.json")
        for w in warns:
            print("WARN", w)
        halal_map = {t: screen_card_data(verdicts, t) for t in tk_list}
        halal_map = {t: c for t, c in halal_map.items() if c}
        skipped = [t for t in tk_list if (parse_cfg(md, t) or {}).get("halal_script") and t not in halal_map]
        if skipped:
            print(f"WARN halal_script tickers missing from halal.json (skipped halal mode): {skipped}")
    except HalalDataMissing as e:
        if wants_halal:
            print(f"REFUSED: kit has halal posts but {e}")
            return 3
    except Exception as e:
        # IMPORTANT 3: a malformed halal.json (e.g. json.JSONDecodeError) must
        # not crash carousel builds that don't need it. Refuse only when the
        # kit actually wants halal posts; otherwise degrade to no halal mode.
        if wants_halal:
            print(f"REFUSED: kit has halal posts but halal.json is malformed: {e}")
            return 3
        print(f"WARN halal.json failed to load ({e}) — continuing without halal mode")
        halal_map = None

    hero_map, logo_map = {}, {}
    for tk in _cfg_tickers(md):
        c = parse_cfg(md, tk)
        if not c:
            continue
        if c.get("hero"):
            hero_map[c["hero"]] = _b64(HIGGS / c["hero"])
        if c.get("logo"):
            logo_map[c["logo"]] = _b64(HIGGS / c["logo"])
    chn = f"hero_congress_{date}.png"
    hero_map[chn] = _b64(HIGGS / chn)

    sl = build_slides(md, site, quantum, hero_map, logo_map, date, halal_map=halal_map)
    missing = [k for k, v in {**hero_map, **logo_map}.items() if v is None]
    if missing:
        print(f"WARN missing hero/logo art (solid-bg fallback): {missing}")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        pg = b.new_page(viewport={"width": W, "height": H})
        for name, html in sl.items():
            pg.set_content(html, wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(600)
            pg.screenshot(path=str(HIGGS / name), clip={"x": 0, "y": 0, "width": W, "height": H})
            print("rendered", name)

        frames = build_halal_frames(md, hero_map, halal_map or {})
        if frames:
            pg2 = b.new_page(viewport={"width": RW, "height": RH})
            for name, html in frames.items():
                pg2.set_content(html, wait_until="networkidle")
                pg2.evaluate("document.fonts.ready")
                pg2.wait_for_timeout(600)
                pg2.screenshot(path=str(HIGGS / name), omit_background=name.endswith("_hook.png"),
                               clip={"x": 0, "y": 0, "width": RW, "height": RH})
                print("rendered", name)
        b.close()
    print(f"DONE kit={kit.name} date={date} slides={len(sl)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
