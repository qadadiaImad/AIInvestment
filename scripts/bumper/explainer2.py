"""Explainer 2: "The screen". Grok illustration clips as backgrounds, code-drawn data on top.

    cd scripts && python -m bumper.narration2                      # script (numbers from the screen outputs)
    (grok-cli tts -> data/bumper/voice2/<id>.mp3 ; grok-cli video -> data/bumper/clips/<id>.mp4)
    cd scripts && python -m bumper.explainer2 [ids...] [--force]   # -> references/bumper-report/fig/bumper_screen.mp4

Clip scenes: the 10 s grok clip is baked once into a forward+reverse palindrome (seamless
loop), then ffmpeg loops it under an RGBA overlay stream rendered here frame by frame
(title, data panel, captions). Chart scenes are opaque as in explainer.py. Every number on
screen is read from data/bumper/2026-09-25/*; the clips carry no text by prompt.
"""
from __future__ import annotations

import json
import pathlib
import statistics
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Circle, Rectangle

from . import explainer as E
from . import report_figs as R
from .explainer import Scene, seg, duration, FPS, C, FF, WORK, VOICE

D = R.D
VOICE2 = R.ROOT / "data" / "bumper" / "voice2"
CLIPS = R.ROOT / "data" / "bumper" / "clips"
WORK2 = R.ROOT / "data" / "bumper" / "explainer2"
WORK2.mkdir(parents=True, exist_ok=True)
FINAL = R.OUT / "bumper_screen.mp4"
PANEL = "#0b0f17"

WIDE = json.load(open(D / "screen_wide.json", encoding="utf-8"))
TODAY = json.load(open(D / "screen_today.json", encoding="utf-8"))
ROWS = WIDE["rows"]
BY = {r["ticker"].split(":")[1]: r for r in ROWS}
WF = R.WF


def panel(fig, rect, alpha=0.86, pad=0.02):
    """translucent dark panel so data stays legible over a moving clip.
    Drawn as a figure-level patch so it survives ax.axis("off")."""
    x, y, w, h = rect
    fig.patches.append(Rectangle((x - pad, y - pad), w + 2 * pad, h + 2 * pad, transform=fig.transFigure,
                                 facecolor=(0.043, 0.059, 0.09, alpha), edgecolor="#1f2937", lw=1, zorder=-0.5))
    ax = fig.add_axes(rect)
    ax.set_facecolor((0, 0, 0, 0))
    for s in ax.spines.values():
        s.set_edgecolor("#1f2937")
    return ax


class ClipScene(Scene):
    """Transparent figure: only overlays are drawn; the clip is composited by ffmpeg."""

    def __init__(self, segment, audio_s):
        super().__init__(segment, audio_s)
        self.fig.patch.set_alpha(0.0)
        # readability gradient top and bottom
        g = np.zeros((64, 1, 4))
        g[:, 0, 3] = np.linspace(0.85, 0.0, 64)
        self.fig.figimage(np.tile(g, (1, 1920, 1)) * [0.04, 0.06, 0.09, 1], xo=0, yo=1080 - 64 * 3, origin="upper", zorder=-1, resize=False)
        self.fig.figimage(np.tile(g[::-1], (1, 1920, 1)) * [0.04, 0.06, 0.09, 1], xo=0, yo=0, origin="upper", zorder=-1, resize=False)

    def title(self, text, y=0.93, size=24, color=None):
        return self.fig.text(0.04, y, text, fontsize=size, fontweight="bold", color=color or C["ink"], va="center",
                             bbox=dict(boxstyle="round,pad=0.45", fc=(0.043, 0.059, 0.09, 0.75), ec="none"))


# ------------------------------------------------------------------ scenes
class HookScene(ClipScene):
    def build(self):
        self.h1 = self.fig.text(0.5, 0.60, "BUMPER RADAR", ha="center", va="center", fontsize=54, fontweight="bold", color=C["win"], alpha=0)
        self.h2 = self.fig.text(0.5, 0.50, "part two: the screen", ha="center", va="center", fontsize=24, color=C["ink"], alpha=0)
        n_in, n_out = WIDE["scanner_total"], sum(r["stage"] == "not disqualified" for r in ROWS)
        self.c1 = self.fig.text(0.35, 0.30, "", ha="center", va="center", fontsize=44, fontweight="bold", color=C["ink"])
        self.c1s = self.fig.text(0.35, 0.235, "pre-profit small caps in", ha="center", fontsize=15, color=C["muted"], alpha=0)
        self.c2 = self.fig.text(0.65, 0.30, "", ha="center", va="center", fontsize=44, fontweight="bold", color=C["win"])
        self.c2s = self.fig.text(0.65, 0.235, "not disqualified out", ha="center", fontsize=15, color=C["muted"], alpha=0)
        self.n_in, self.n_out = n_in, n_out

    def update(self, t):
        self.h1.set_alpha(seg(t, 0.3, 1.2))
        self.h2.set_alpha(seg(t, 1.0, 1.0))
        g1, g2 = seg(t, 3.0, 2.0), seg(t, 5.0, 2.0)
        self.c1.set_text(f"{int(self.n_in * g1):,}" if g1 > 0 else "")
        self.c1s.set_alpha(g1)
        self.c2.set_text(f"{int(self.n_out * g2):,}" if g2 > 0 else "")
        self.c2s.set_alpha(g2)


class CapDistScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "What 'low cap' means, from the winners themselves", ha="center", fontsize=22, fontweight="bold")
        ax = fig.add_axes([0.08, 0.20, 0.84, 0.62])
        caps = np.array([w["cap_at_run_usd"] for w in R.W if w.get("cap_at_run_usd")]) / 1e6
        self.capvals = np.sort(caps)
        bins = np.logspace(np.log10(30), np.log10(30000), 36)
        self.n, _ = np.histogram(caps, bins=bins)
        self.bars = ax.bar(bins[:-1], [0] * len(self.n), width=np.diff(bins) * 0.9, align="edge", color=C["win"], alpha=0.85)
        ax.set_xscale("log")
        ax.set_xlim(30, 30000)
        ax.set_ylim(0, self.n.max() * 1.25)
        ax.set_xlabel("market cap at run start, $ millions (log)", fontsize=13)
        ax.set_ylabel(f"winners (n={len(caps)})", fontsize=13)
        self.marks = []
        for q, lab, colr in [(10, "10th pct", C["muted"]), (25, "25th", C["blue"]), (50, "median", C["amber"]), (75, "75th", C["red"])]:
            v = np.percentile(caps, q)
            ln = ax.axvline(v, color=colr, ls="--", lw=1.6, alpha=0)
            tx = ax.text(v, self.n.max() * 1.18, f"{lab}\n${v:,.0f}M", ha="center", va="top", fontsize=12, color=colr, alpha=0)
            self.marks.append((ln, tx))
        self.band = ax.axvspan(50, 3000, color=C["win"], alpha=0)
        self.bandtxt = ax.text(390, self.n.max() * 0.05, "screen universe " + chr(92) + "$50M–" + chr(92) + "$3B", ha="center", fontsize=12, color=C["win"], alpha=0)

    def update(self, t):
        g = seg(t, 0.8, 2.5)
        for b, n in zip(self.bars, self.n):
            b.set_height(n * g)
        for i, (ln, tx) in enumerate(self.marks):
            a = seg(t, 5.0 + i * 3.2, 0.8)
            ln.set_alpha(a)
            tx.set_alpha(a)
        a = seg(t, self.audio_s * 0.82, 1.0)
        self.band.set_alpha(0.08 * a)
        self.bandtxt.set_alpha(a)


class CounterScene(ClipScene):
    def build(self):
        self.title("Two universes")
        ax = panel(self.fig, [0.52, 0.22, 0.44, 0.60])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        self.n1, self.n2 = len(TODAY["rows"]), WIDE["scanner_total"]
        self.b1 = ax.barh(0.68, 0, height=0.16, color=C["ctl"])[0]
        self.b2 = ax.barh(0.32, 0, height=0.16, color=C["win"])[0]
        ax.text(0.02, 0.86, "curated sector lists (first screen)", fontsize=14, color=C["ink"])
        ax.text(0.02, 0.50, "scanner-built: every US common stock, " + chr(92) + "$50M–" + chr(92) + "$3B, FCF < 0", fontsize=14, color=C["ink"])
        self.t1 = ax.text(0.02, 0.68, "", va="center", fontsize=26, fontweight="bold", color="white")
        self.t2 = ax.text(0.02, 0.32, "", va="center", fontsize=26, fontweight="bold", color="white")
        self.note = ax.text(0.02, 0.08, "a bumper is, by definition, not on anyone's list yet", fontsize=13, color=C["amber"], alpha=0)

    def update(self, t):
        g1, g2 = seg(t, 1.0, 1.5), seg(t, self.audio_s * 0.55, 2.5)
        self.b1.set_width(self.n1 / self.n2 * g1 * 0.95)
        self.t1.set_text(f"{int(self.n1 * g1)}" if g1 > 0 else "")
        self.b2.set_width(0.95 * g2)
        self.t2.set_text(f"{int(self.n2 * g2):,}" if g2 > 0 else "")
        self.note.set_alpha(seg(t, self.audio_s * 0.35, 1))


class FunnelScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "The screen, gate by gate", ha="center", fontsize=22, fontweight="bold")
        ax = fig.add_axes([0.05, 0.12, 0.90, 0.76])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        n_total, n_scope = WIDE["scanner_total"], len(ROWS)
        n_runway = sum(1 for r in ROWS if any(x.startswith("runway") for x in r["reasons"]))
        n_notice = sum(1 for r in ROWS if any("listing notice" in x for x in r["reasons"]))
        n_flag = sum(r["stage"] == "FLAGGED" for r in ROWS)
        n_clean = sum(r["stage"] == "not disqualified" for r in ROWS)
        n_low = sum(r["stage"] == "not disqualified" and r["market_cap_usd"] < 8e8 for r in ROWS)
        stages = [(f"{n_total:,}", "US common stocks · " + chr(92) + "$50M–" + chr(92) + "$3B · free cash flow < 0", 1.0, C["ctl"]),
                  (f"{n_scope}", f"minus biotech, finance, retail, consumer, shells  (−{n_total - n_scope})", 0.72, C["blue"]),
                  (f"{n_scope - n_runway}", f"runway ≥ 2 years  (−{n_runway})", 0.50, C["red"]),
                  (f"{n_scope - n_runway - n_notice}", f"no exchange listing notice  (−{n_notice})", 0.40, C["amber"]),
                  (f"{n_clean}", f"not disqualified  ·  {n_flag} flagged for reading  ·  {n_low} below the median winner's cap", 0.30, C["win"])]
        self.items = []
        for i, (num, sub, w, colr) in enumerate(stages):
            y = 0.97 - i * 0.195
            rect = Rectangle((0.5 - w / 2, y - 0.12), w, 0.12, color=colr, alpha=0)
            ax.add_patch(rect)
            t1 = ax.text(0.5, y - 0.06, num, ha="center", va="center", fontsize=24, fontweight="bold", color="white", alpha=0)
            t2 = ax.text(0.5, y - 0.135, sub, ha="center", va="top", fontsize=13, color=C["muted"], alpha=0)
            self.items.append((rect, t1, t2))

    def update(self, t):
        step = self.audio_s / 6.0
        for i, (rect, t1, t2) in enumerate(self.items):
            g = seg(t, 0.5 + i * step, 0.9)
            rect.set_alpha(0.88 * g)
            t1.set_alpha(g)
            t2.set_alpha(g)


class RunwayScene(ClipScene):
    def build(self):
        self.title("Gate 1 · cash runway = cash ÷ yearly burn")
        ax = panel(self.fig, [0.50, 0.20, 0.46, 0.64])
        names = ["SERV", "XTND", "PDYN", "ARBE", "AEVA", "INVZ", "RR", "UMAC"]
        self.rows = [(n, BY[n]) for n in names if n in BY]
        y = np.arange(len(self.rows))
        self.bars = ax.barh(y, [0] * len(self.rows), height=0.6, color=[C["red"] if r["runway_years"] < 2 else C["win"] for _, r in self.rows])
        ax.set_yticks(y)
        ax.set_yticklabels([f"{n}  ({r['name'].split(' ')[0]})" for n, r in self.rows], fontsize=13)
        ax.invert_yaxis()
        for lab in ax.get_yticklabels():
            lab.set_bbox(dict(boxstyle="round,pad=0.25", fc=(0.043, 0.059, 0.09, 0.85), ec="none"))
        ax.set_xlim(0, 22)
        ax.axvline(2, color=C["red"], ls="--", lw=1.8)
        ax.text(2.3, -0.75, "gate: 2 years", color=C["red"], fontsize=12, va="center")
        ax.set_xlabel("years of cash at the current burn", fontsize=13)
        ax.grid(True, axis="x", alpha=0.3)
        self.vals = [ax.text(0, i, "", va="center", fontsize=13, fontweight="bold", color="white") for i in range(len(self.rows))]

    def update(self, t):
        for i, (b, (n, r), v) in enumerate(zip(self.bars, self.rows, self.vals)):
            g = seg(t, 2.0 + i * 1.3, 1.0)
            w = min(r["runway_years"], 15.5) * g
            b.set_width(w)
            v.set_x(w + 0.2)
            v.set_text((f"{r['runway_years']:.1f} y · rev {r['rev_growth_yoy']:+.0f}%" if r["rev_growth_yoy"] is not None else f"{r['runway_years']:.1f} y") if g > 0.99 else "")


class DilutionScene(ClipScene):
    """Illustration only: how an emergency raise re-slices ownership. No company numbers claimed."""

    def build(self):
        self.title("Why runway is gate one: the second raise")
        ax = panel(self.fig, [0.52, 0.26, 0.42, 0.52], pad=0.035)
        ax.set_xlim(0, 20)
        ax.set_ylim(0, 12)
        ax.axis("off")
        self.old = [Rectangle((c, r), 0.9, 0.9, color=C["win"], alpha=0.75) for r in range(5) for c in range(20)]
        self.new = [Rectangle((c, r), 0.9, 0.9, color=C["amber"], alpha=0) for r in range(5, 12) for c in range(20)]
        for p in self.old + self.new:
            ax.add_patch(p)
        self.l1 = ax.text(0, -1.0, "existing shareholders", fontsize=13, color=C["win"], clip_on=False)
        self.l2 = ax.text(0, 12.4, "", fontsize=13, color=C["amber"])
        self.note = ax.text(10, 5.6, "", ha="center", fontsize=13, color="white", fontweight="bold",
                            bbox=dict(boxstyle="round,pad=0.4", fc=PANEL, ec=C["amber"]))
        self.ax = ax

    def update(self, t):
        g = seg(t, self.audio_s * 0.35, self.audio_s * 0.35)
        k = int(len(self.new) * g)
        for i, p in enumerate(self.new):
            p.set_alpha(0.75 if i < k else 0)
        if g > 0:
            self.l2.set_text("new shares sold at a discount, warrants attached")
        if g > 0.99:
            self.note.set_text("same company · more owners · who bought, and at what price?")


class GcScene(ClipScene):
    def build(self):
        self.title("Gate 2 · 'substantial doubt … going concern' in a 10-K / 10-Q")
        ax = panel(self.fig, [0.50, 0.20, 0.46, 0.64])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        n_flag = sum(r["stage"] == "FLAGGED" for r in ROWS)
        ax.text(0.03, 0.92, f"{n_flag} names flagged by full-text search this year", fontsize=15, color=C["amber"], fontweight="bold")
        ax.text(0.03, 0.84, "the search cannot tell an explicit statement from boilerplate: read, then decide", fontsize=12, color=C["muted"])
        ex = [("NNE", "Nano Nuclear Energy"), ("EMAT", "Evolution Metals & Tech")]
        self.lines = []
        for i, (tk, nm) in enumerate(ex):
            # the wide screen only ran the text gates on runway survivors; the curated screen ran them on all
            cands = [BY.get(tk), {x["ticker"].split(":")[1]: x for x in TODAY["rows"]}.get(tk)]
            r = next((c for c in cands if c and c.get("going_concern_hits") is not None), cands[0] or cands[1])
            hits = r.get("going_concern_hits") or 0
            rw = r.get("runway_years")
            verdict = "boilerplate risk language" if (rw or 0) > 5 else "real: cash for months, not years"
            colr = C["win"] if (rw or 0) > 5 else C["red"]
            y = 0.66 - i * 0.30
            a = ax.text(0.03, y, f"{tk}  {nm}", fontsize=15, fontweight="bold", color="white", alpha=0)
            b = ax.text(0.03, y - 0.08, f"{hits} filings with the phrase · runway {rw:.1f} years", fontsize=13, color=C["ink"], alpha=0)
            c = ax.text(0.03, y - 0.16, "→ " + verdict, fontsize=13, color=colr, fontweight="bold", alpha=0)
            self.lines.append((a, b, c))

    def update(self, t):
        t0 = self.audio_s * 0.62
        for i, trio in enumerate(self.lines):
            for j, tx in enumerate(trio):
                tx.set_alpha(seg(t, t0 + i * 3.4 + j * 0.6, 0.5))


class NoticeScene(ClipScene):
    def build(self):
        self.title("Gate 3 · the exchange letter (8-K: bid price / listing rule)")
        ax = panel(self.fig, [0.50, 0.20, 0.46, 0.64])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        names = [(r["ticker"].split(":")[1], r["name"], r["listing_notice_hits"]) for r in ROWS if any("listing notice" in x for x in r["reasons"])]
        self.items = []
        ax.text(0.03, 0.92, f"{len(names)} names carry a notice in the last 12 months", fontsize=15, color=C["red"], fontweight="bold")
        for i, (tk, nm, n) in enumerate(names[:7]):
            tx = ax.text(0.03, 0.80 - i * 0.11, f"{tk}   {nm[:30]}   ·   {n} 8-K{'s' if n > 1 else ''}", fontsize=14, color="white", alpha=0,
                         bbox=dict(boxstyle="round,pad=0.35", fc="#1a0f12", ec=C["red"], lw=1))
            self.items.append(tx)

    def update(self, t):
        for i, tx in enumerate(self.items):
            tx.set_alpha(seg(t, 2.5 + i * 1.4, 0.5))


class GraveyardTableScene(ClipScene):
    def build(self):
        self.title("Same signals as the winners", color=C["red"])
        ax = panel(self.fig, [0.40, 0.18, 0.56, 0.66])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        rows = [("Nikola", "General Motors stake + pre-orders", "orders had no deposits; demo footage staged"),
                ("Lordstown", "Foxconn plant deal, 100k 'pre-orders'", "pre-orders were non-binding; $0 deposits"),
                ("Canoo", "Walmart order for 4,500 vans", "customer-as-financier; runway months; raise after raise"),
                ("Arrival", "UPS LOI for 10,000 vans", "LOI: no deposit, no cancellation penalty (20-F risk factor)")]
        self.items = []
        ax.text(0.02, 0.94, "name", fontsize=12, color=C["muted"])
        ax.text(0.20, 0.94, "the winner-looking signal", fontsize=12, color=C["muted"])
        ax.text(0.58, 0.94, "what the filing said", fontsize=12, color=C["muted"])
        for i, (a, b, c) in enumerate(rows):
            y = 0.82 - i * 0.21
            t1 = ax.text(0.02, y, a, fontsize=15, fontweight="bold", color="white", alpha=0)
            t2 = ax.text(0.20, y, E.wrap(b, 30), fontsize=12.5, color=C["win"], va="center", alpha=0)
            t3 = ax.text(0.58, y, E.wrap(c, 34), fontsize=12.5, color=C["red"], va="center", alpha=0)
            self.items.append((t1, t2, t3))

    def update(self, t):
        for i, (t1, t2, t3) in enumerate(self.items):
            a = seg(t, 2.0 + i * 3.2, 0.6)
            t1.set_alpha(a)
            t2.set_alpha(a)
            t3.set_alpha(seg(t, 3.4 + i * 3.2, 0.6))


class InteractionScene(Scene):
    """Company / customer / financier graph: LOI dashed -> contract solid on delivery; customer==financier warning."""

    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "The binding-demand check: who is really paying whom", ha="center", fontsize=22, fontweight="bold")
        ax = fig.add_axes([0.05, 0.12, 0.90, 0.76])
        ax.axis("off")
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        self.ax = ax
        self.nodes = {}
        for key, (x, y, lab, colr) in {"co": (5, 3, "COMPANY\n(pre-profit)", C["win"]), "cu": (1.3, 3, "CUSTOMER", C["blue"]), "fi": (8.7, 3, "FINANCIER", C["amber"])}.items():
            c = Circle((x, y), 0.9, color=colr, alpha=0.0)
            ax.add_patch(c)
            tx = ax.text(x, y, lab, ha="center", va="center", fontsize=14, fontweight="bold", color="white", alpha=0)
            self.nodes[key] = (c, tx)
        self.loi = FancyArrowPatch((2.2, 3.35), (4.1, 3.35), arrowstyle="-|>", mutation_scale=22, lw=2.5, ls="--", color=C["ctl"], alpha=0)
        self.loi_t = ax.text(3.15, 3.75, "letter of intent · no deposit", ha="center", fontsize=12, color=C["ctl"], alpha=0)
        self.con = FancyArrowPatch((2.2, 2.65), (4.1, 2.65), arrowstyle="-|>", mutation_scale=22, lw=3.5, color=C["win"], alpha=0)
        self.con_t = ax.text(3.15, 2.2, "contract · delivered units\nrecognised revenue in a later filing", ha="center", va="top", fontsize=12, color=C["win"], alpha=0)
        self.fin = FancyArrowPatch((7.8, 3.0), (5.9, 3.0), arrowstyle="-|>", mutation_scale=22, lw=3, color=C["amber"], alpha=0)
        self.fin_t = ax.text(6.85, 3.4, "equity / convertible / loan", ha="center", fontsize=12, color=C["amber"], alpha=0)
        self.same = FancyArrowPatch((1.6, 2.2), (8.4, 2.2), connectionstyle="arc3,rad=0.32", arrowstyle="<|-|>", mutation_scale=22, lw=3, ls=":", color=C["red"], alpha=0)
        self.same_t = ax.text(5, 0.12, "customer = financier → demand that finances itself is a warning, not a validation", ha="center", fontsize=14, color=C["red"], fontweight="bold", alpha=0)
        for a in (self.loi, self.con, self.fin, self.same):
            ax.add_patch(a)

    def update(self, t):
        a = self.audio_s
        for i, key in enumerate(["co", "cu", "fi"]):
            c, tx = self.nodes[key]
            g = seg(t, 0.5 + i * 0.9, 0.8)
            c.set_alpha(0.85 * g)
            tx.set_alpha(g)
        g = seg(t, a * 0.28, 0.8)
        self.loi.set_alpha(g)
        self.loi_t.set_alpha(g)
        g = seg(t, a * 0.45, 0.8)
        self.con.set_alpha(g)
        self.con_t.set_alpha(g)
        self.loi.set_alpha(max(0, 0.9 - g))
        self.loi_t.set_alpha(max(0, 0.9 - g))
        g = seg(t, a * 0.62, 0.8)
        self.fin.set_alpha(g)
        self.fin_t.set_alpha(g)
        g = seg(t, a * 0.72, 1.0)
        self.same.set_alpha(g)
        self.same_t.set_alpha(g)


class RobotScatterScene(ClipScene):
    def build(self):
        self.title("Robotics & perception, pre-profit, " + chr(92) + "$50M–" + chr(92) + "$3B")
        ax = panel(self.fig, [0.49, 0.25, 0.47, 0.58], pad=0.06)
        names = ["SERV", "XTND", "PDYN", "ARBE", "RR", "AEVA", "INVZ", "UMAC", "DPRO", "RCAT"]
        self.pts = []
        for n in names:
            r = BY.get(n)
            if not r or r["runway_years"] is None:
                continue
            x, y = max(r["rev_growth_yoy"] or 0, -20), r["runway_years"]
            colr = C["red"] if r["stage"] == "DISQUALIFIED" else (C["amber"] if r["stage"] == "FLAGGED" else C["win"])
            sc = ax.scatter([x], [y], s=max(80, (r["market_cap_usd"] / 1e9) ** 0.5 * 220), color=colr, alpha=0, edgecolor="white", lw=0.8)
            an = ax.annotate(n, (x, y), xytext=(7, 6), textcoords="offset points", fontsize=13, color="white", alpha=0)
            self.pts.append((sc, an))
        ax.set_yscale("log")
        ax.set_ylim(0.3, 30)
        ax.set_xlim(-30, 760)
        ax.axhline(2, color=C["red"], ls="--", lw=1.8)
        ax.text(-25, 2.2, "runway gate", color=C["red"], fontsize=12)
        ax.set_xlabel("revenue growth, trailing 12 months (%)", fontsize=13)
        ax.set_ylabel("cash runway, years (log)", fontsize=13)
        ax.grid(True, alpha=0.3)
        for colr, lab in [(C["red"], "disqualified"), (C["amber"], "flagged"), (C["win"], "not disqualified")]:
            ax.scatter([], [], color=colr, label=lab, s=80)
        ax.legend(loc="upper right", fontsize=12)

    def update(self, t):
        for i, (sc, an) in enumerate(self.pts):
            g = seg(t, 2.0 + i * 1.1, 0.8)
            sc.set_alpha(0.85 * g)
            an.set_alpha(g)


class SurvivorScene(ClipScene):
    def build(self):
        self.title("Not disqualified ≠ bumper")
        ax = panel(self.fig, [0.40, 0.16, 0.56, 0.70])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        TECH = R.TECH
        low = [r for r in ROWS if r["stage"] == "not disqualified" and r["market_cap_usd"] < 8e8 and r["sector"] in TECH and r["rnd_ttm"] and (r["rev_growth_yoy"] or 0) >= 30]
        low = sorted(low, key=lambda r: r["market_cap_usd"])
        hdr = ["ticker", "cap $M", "runway y", "rev growth", "1y", "binding demand"]
        xs = [0.02, 0.24, 0.40, 0.56, 0.72, 0.84]
        for x, h in zip(xs, hdr):
            ax.text(x, 0.95, h, fontsize=12, color=C["muted"])
        self.items = []
        for i, r in enumerate(low[:9]):
            y = 0.86 - i * 0.092
            vals = [r["ticker"].split(":")[1], f"{r['market_cap_usd'] / 1e6:.0f}", f"{r['runway_years']:.1f}", f"{r['rev_growth_yoy']:+.0f}%", f"{r['perf_1y']:+.0f}%", "UNVERIFIED"]
            cols = ["white", C["ink"], C["ink"], C["win"], C["red"] if r["perf_1y"] < 0 else C["win"], C["amber"]]
            self.items.append([ax.text(x, y, v, fontsize=13.5, color=c, alpha=0, fontweight="bold" if j in (0, 5) else "normal") for j, (x, v, c) in enumerate(zip(xs, vals, cols))])
        self.foot = ax.text(0.02, 0.04, "low-cap tech names with an R&D line and revenue growth ≥ 30% · gates remove, they do not rank", fontsize=11.5, color=C["muted"], alpha=0)

    def update(self, t):
        for i, row in enumerate(self.items):
            a = seg(t, 2.0 + i * 1.2, 0.5)
            for tx in row:
                tx.set_alpha(a)
        self.foot.set_alpha(seg(t, self.audio_s * 0.6, 1))


class NextScene(ClipScene):
    def build(self):
        self.title("Three reads per survivor")
        ax = panel(self.fig, [0.50, 0.20, 0.46, 0.64])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        steps = [("1 · the customer contract", "deposit · cancellation terms · delivered units in a later 10-Q"),
                 ("2 · the last raise", "who bought · discount to market · warrants · registered direct or PIPE"),
                 ("3 · the related parties", "is the customer also the lender or the shareholder? (Item 13, 10-K)")]
        self.items = []
        for i, (h, s) in enumerate(steps):
            y = 0.85 - i * 0.30
            a = ax.text(0.03, y, h, fontsize=17, fontweight="bold", color=C["win"], alpha=0)
            b = ax.text(0.03, y - 0.09, E.wrap(s, 48), fontsize=13, color=C["ink"], va="top", alpha=0)
            self.items.append((a, b))

    def update(self, t):
        step = self.audio_s / 4.2
        for i, (a, b) in enumerate(self.items):
            a.set_alpha(seg(t, 1.0 + i * step, 0.6))
            b.set_alpha(seg(t, 1.6 + i * step, 0.6))


class OutroScene(ClipScene):
    def build(self):
        self.h1 = self.fig.text(0.5, 0.58, "READ THE CONTRACT,\nNOT THE PRESS RELEASE", ha="center", va="center", fontsize=34, fontweight="bold", color=C["win"], alpha=0)
        self.h2 = self.fig.text(0.5, 0.36, "Educational research only · not investment advice\ngithub.com/qadadiaImad/AIInvestment · references/bumper-report", ha="center", va="center", fontsize=15, color=C["ink"], alpha=0)

    def update(self, t):
        self.h1.set_alpha(seg(t, 0.5, 1.2))
        self.h2.set_alpha(seg(t, 2.0, 1.2))


SCENES = {"title": HookScene, "capdist": CapDistScene, "counter": CounterScene, "funnel": FunnelScene, "runway": RunwayScene,
          "dilution": DilutionScene, "gclist": GcScene, "noticelist": NoticeScene, "graveyardtable": GraveyardTableScene,
          "interaction": InteractionScene, "robotscatter": RobotScatterScene, "survivors": SurvivorScene, "nextsteps": NextScene, "outro": OutroScene}


# ------------------------------------------------------------------ render
def palindrome(clip: pathlib.Path) -> pathlib.Path:
    """forward + reverse copy of the 10 s clip: a seamless 20 s loop (baked once, 720p)."""
    out = clip.with_name(clip.stem + "_pal.mp4")
    if out.exists() and out.stat().st_mtime > clip.stat().st_mtime:
        return out
    subprocess.run([FF, "-v", "error", "-y", "-i", str(clip), "-filter_complex", "[0:v]fps=24,split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1[v]",
                    "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", str(out)], check=True)
    return out


def render_segment(segment, force=False) -> pathlib.Path:
    mp3 = VOICE2 / f"{segment['id']}.mp3"
    out = WORK2 / f"{segment['id']}.mp4"
    if out.exists() and not force and out.stat().st_mtime > mp3.stat().st_mtime:
        return out
    scene = SCENES[segment["chart"]](segment, duration(mp3))
    n = int(round(scene.total * FPS))
    if segment["kind"] == "clip":
        bg = palindrome(CLIPS / f"{segment['id']}.mp4")
        cmd = [FF, "-v", "error", "-y", "-stream_loop", "-1", "-i", str(bg),
               "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "1920x1080", "-r", str(FPS), "-i", "-", "-i", str(mp3),
               "-filter_complex", "[0:v]scale=1920:1080:flags=lanczos,setsar=1[bg];[bg][1:v]overlay=shortest=1:format=auto[v]",
               "-map", "[v]", "-map", "2:a", "-af", "apad", "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    else:
        cmd = [FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "1920x1080", "-r", str(FPS), "-i", "-",
               "-i", str(mp3), "-af", "apad", "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(scene.frame(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    scene.close()
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {segment['id']}")
    print(f"{segment['id']}: {n} frames, {scene.total:.1f}s -> {out.name}", flush=True)
    return out


def main(argv):
    segs = json.load(open(D / "narration2.json", encoding="utf-8"))
    only = [a for a in argv if not a.startswith("-")]
    force = "--force" in argv
    parts = [render_segment(s, force=force) for s in segs if not only or s["id"] in only]
    if not only:
        lst = WORK2 / "concat.txt"
        lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
        subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(FINAL)], check=True)
        print("final:", FINAL, f"{FINAL.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1:])
