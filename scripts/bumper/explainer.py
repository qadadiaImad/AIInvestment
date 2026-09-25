"""Narrated explainer video for the bumper study.

    cd scripts && python -m bumper.narration      # writes narration.json (numbers from the study)
    (grok-cli tts per segment -> data/bumper/voice/<id>.mp3)
    cd scripts && python -m bumper.explainer      # renders references/bumper-report/fig/bumper_explainer.mp4

One 1920x1080 scene per narration segment, sized to that segment's audio, with a burned
caption band that steps through the spoken sentences. Frames are piped raw to ffmpeg and
muxed with the segment's mp3 (audio padded to the video); segments are concatenated
stream-copy at the end. Every number on screen comes from data/bumper/2026-09-25/*.
"""
from __future__ import annotations

import json
import pathlib
import re
import statistics
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedFormatter, FixedLocator

from . import report_figs as R

ROOT = R.ROOT
D = R.D
VOICE = ROOT / "data" / "bumper" / "voice"
WORK = ROOT / "data" / "bumper" / "explainer"
WORK.mkdir(parents=True, exist_ok=True)
FINAL = R.OUT / "bumper_explainer.mp4"
FPS = 24
DPI = 150
FIGSIZE = (12.8, 7.2)  # x150 dpi = 1920x1080
PAD_S = 0.9            # silence after each segment
C = R.C
FF = "ffmpeg"

plt.rcParams.update({"font.family": "Segoe UI", "font.size": 13})


# ------------------------------------------------------------------ helpers
def duration(mp3: pathlib.Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def ease(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def seg(t, start, length):
    """progress 0..1 of a sub-beat that starts at `start` seconds and lasts `length`."""
    return ease((t - start) / length) if length > 0 else 1.0


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?;:])\s+", text.strip())
    out = []
    for p in parts:
        if not p:
            continue
        while len(p) > 150:  # a long list sentence: break at a comma near the middle
            cut = p.rfind(", ", 60, 150)
            if cut < 0:
                break
            out.append(p[:cut + 1])
            p = p[cut + 2:]
        out.append(p)
    return out


def caption_schedule(text: str, total: float):
    """(start, end, sentence) with time proportional to character count."""
    ss = sentences(text)
    n = sum(len(s) for s in ss)
    out, t = [], 0.0
    for s in ss:
        d = total * len(s) / n
        out.append((t, t + d, s))
        t += d
    return out


def wrap(s: str, width: int) -> str:
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return "\n".join(lines)


class Scene:
    """Owns a figure; subclasses build static art once and expose update(t)."""
    title = ""

    def __init__(self, segment, audio_s):
        self.segment = segment
        self.audio_s = audio_s
        self.total = audio_s + PAD_S
        self.fig = plt.figure(figsize=FIGSIZE, dpi=DPI)
        self.fig.patch.set_facecolor(C["bg"])
        self.caps = caption_schedule(segment["text"], audio_s)
        self.cap_txt = self.fig.text(0.5, 0.062, "", ha="center", va="center", fontsize=14, color=C["ink"],
                                     bbox=dict(boxstyle="round,pad=0.6", fc="#0e131dee", ec="#1f2937"), zorder=50)
        self.fig.text(0.985, 0.988, "Bumper study · 2026-09-25 · educational, not advice", ha="right", va="top",
                      fontsize=9, color=C["muted"], zorder=50)
        self.build()

    def build(self):
        pass

    def update(self, t):
        pass

    def caption(self, t):
        for a, b, s in self.caps:
            if a <= t < b:
                self.cap_txt.set_text(wrap(s, 125))
                return
        self.cap_txt.set_text("")

    def frame(self, t):
        self.update(t)
        self.caption(t)
        self.fig.canvas.draw()
        return np.asarray(self.fig.canvas.buffer_rgba())

    def close(self):
        plt.close(self.fig)


# ------------------------------------------------------------------ scenes
class TitleScene(Scene):
    def build(self):
        fig = self.fig
        ax = fig.add_axes([0.08, 0.30, 0.84, 0.42])
        ax.axis("off")
        pw, pc = R.paths_winners_controls()
        self.x = np.arange(-24, 13)
        self.pw, self.pc = pw, pc
        rng = np.random.default_rng(3)
        self.lines = []
        for p in pc[rng.choice(len(pc), 24, replace=False)]:
            self.lines.append((ax.plot([], [], color=C["ctl"], lw=1.0, alpha=0.35)[0], p))
        for p in pw[rng.choice(len(pw), 24, replace=False)]:
            self.lines.append((ax.plot([], [], color=C["win"], lw=1.2, alpha=0.55)[0], p))
        ax.set_yscale("log")
        ax.set_xlim(-24, 12)
        ax.set_ylim(0.25, 8)
        intro = self.segment["id"].startswith("01")
        self.h1 = fig.text(0.5, 0.80, "BUMPER RADAR" if intro else "READ THE CONTRACT,\nNOT THE PRESS RELEASE",
                           ha="center", va="center", fontsize=40 if intro else 30, fontweight="bold", color=C["win"], alpha=0)
        self.h2 = fig.text(0.5, 0.20, "Can the next sector leaders be found before the run?\n336 winners · 300 look-alikes · 18 rebuilt case files · 16 collapses" if intro
                           else "Full report and code: github.com/qadadiaImad/AIInvestment · references/bumper-report",
                           ha="center", va="center", fontsize=16, color=C["muted"], alpha=0)

    def update(self, t):
        k = int(37 * seg(t, 0.3, self.total * 0.75))
        for ln, p in self.lines:
            ln.set_data(self.x[:k], p[:k])
        self.h1.set_alpha(seg(t, 0.2, 1.2))
        self.h2.set_alpha(seg(t, 1.2, 1.2))


class CohortScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "Who counts as a winner, and who are the look-alikes", ha="center", fontsize=22, fontweight="bold")
        self.ax1 = fig.add_axes([0.07, 0.20, 0.36, 0.62])
        self.ax2 = fig.add_axes([0.52, 0.20, 0.42, 0.62])
        S = R.SUM
        self.n_w, self.n_c = S["winners_total"], S["controls_total"]
        self.b1 = self.ax1.bar(["winners\n≥5× in 5y or ≥3× in 3y\ncap ≥ $1B", "look-alikes\nsame industries,\nno run"], [0, 0], color=[C["win"], C["ctl"]], width=0.55)
        self.ax1.set_ylim(0, max(self.n_w, self.n_c) * 1.18)
        self.ax1.set_title("US-listed cohort", fontsize=15)
        self.t1 = [self.ax1.text(i, 0, "", ha="center", va="bottom", fontsize=18, fontweight="bold") for i in range(2)]
        self.yrs = sorted(S["run_start_years"].items())
        self.b2 = self.ax2.bar([y for y, _ in self.yrs], [0] * len(self.yrs), color=C["win"])
        self.ax2.set_ylim(0, max(n for _, n in self.yrs) * 1.2)
        self.ax2.set_title("When the runs started (first 12-month window ≥ 2.5×)", fontsize=15)
        self.t2 = [self.ax2.text(y, 0, "", ha="center", va="bottom", fontsize=12) for y, _ in self.yrs]

    def update(self, t):
        g1, g2 = seg(t, 0.5, 2.2), seg(t, 2.6, 2.2)
        for b, txt, n, g in zip(self.b1, self.t1, [self.n_w, self.n_c], [g1, g2]):
            b.set_height(n * g)
            txt.set_y(n * g)
            txt.set_text(f"{int(round(n * g))}" if g > 0 else "")
        g3 = seg(t, self.audio_s * 0.62, 2.5)
        for b, txt, (y, n) in zip(self.b2, self.t2, self.yrs):
            b.set_height(n * g3)
            txt.set_y(n * g3 + 1)
            txt.set_text(str(n) if g3 > 0.99 else "")


class PathsScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "The shape of a bumper: two flat years, then the run", ha="center", fontsize=22, fontweight="bold")
        ax = fig.add_axes([0.08, 0.17, 0.86, 0.70])
        self.ax = ax
        pw, pc = R.paths_winners_controls()
        self.x = np.arange(-24, 13)
        rng = np.random.default_rng(7)
        self.sw = pw[rng.choice(len(pw), min(40, len(pw)), replace=False)]
        self.sc = pc[rng.choice(len(pc), min(40, len(pc)), replace=False)]
        self.lc = [ax.plot([], [], color=C["ctl"], lw=0.9, alpha=0.4)[0] for _ in self.sc]
        self.lw = [ax.plot([], [], color=C["win"], lw=1.0, alpha=0.55)[0] for _ in self.sw]
        self.mw, = ax.plot([], [], color=C["win"], lw=3.5, label=f"winners, median (n={len(pw)})")
        self.mc, = ax.plot([], [], color=C["ctl"], lw=3.5, label=f"look-alikes, median (n={len(pc)})")
        self.med_w, self.med_c = np.median(pw, axis=0), np.median(pc, axis=0)
        ax.set_yscale("log")
        ax.set_xlim(-24, 12)
        ax.set_ylim(0.2, 8)
        ax.yaxis.set_major_locator(FixedLocator([0.25, 0.5, 1, 2, 4, 8]))
        ax.yaxis.set_major_formatter(FixedFormatter(["0.25×", "0.5×", "1×", "2×", "4×", "8×"]))
        ax.yaxis.set_minor_formatter(FixedFormatter([]))
        self.vline = ax.axvline(0, color=C["amber"], ls="--", lw=1.5, alpha=0)
        self.vtxt = ax.text(0.5, 6.2, "run start", color=C["amber"], fontsize=13, alpha=0)
        self.q = ax.axvline(-3, color=C["blue"], ls=":", lw=2, alpha=0)
        self.qtxt = ax.text(-3.4, 0.24, "features read here\n(3 months before)", color=C["blue"], fontsize=12, ha="right", alpha=0)
        ax.set_xlabel("months relative to run start")
        ax.set_ylabel("price relative to one month before the run (log)")
        ax.legend(loc="upper left", fontsize=12)

    def update(self, t):
        k = int(37 * seg(t, 0.4, self.audio_s * 0.6)) if t > 0.4 else 0
        for ln, p in zip(self.lc, self.sc):
            ln.set_data(self.x[:k], p[:k])
        for ln, p in zip(self.lw, self.sw):
            ln.set_data(self.x[:k], p[:k])
        self.mw.set_data(self.x[:k], self.med_w[:k])
        self.mc.set_data(self.x[:k], self.med_c[:k])
        a = seg(t, self.audio_s * 0.42, 0.8)
        self.vline.set_alpha(a)
        self.vtxt.set_alpha(a)
        b = seg(t, self.audio_s * 0.78, 0.8)
        self.q.set_alpha(b)
        self.qtxt.set_alpha(b)


class AucScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "Three months before the run, the filings say nothing", ha="center", fontsize=22, fontweight="bold")
        ax = fig.add_axes([0.30, 0.17, 0.64, 0.70])
        self.ax = ax
        keys = list(R.LABELS)
        self.a = [R.SEP["tech_small"][k]["auc"] for k in keys]
        self.order = np.argsort(self.a)[::-1]
        self.keys = keys
        y = np.arange(len(keys))
        self.bars = ax.barh(y, [0] * len(keys), color=[C["win"] if self.a[j] >= 0.5 else C["red"] for j in self.order], height=0.62)
        ax.set_yticks(y)
        ax.set_yticklabels([R.LABELS[keys[j]] for j in self.order], fontsize=13)
        ax.invert_yaxis()
        ax.set_xlim(0, 0.85)
        ax.axvline(0.5, color=C["ink"], ls="--", lw=1.5)
        ax.text(0.505, -0.75, "0.5 = coin flip", fontsize=12)
        ax.axvspan(0.6, 0.85, color=C["win"], alpha=0.06)
        ax.text(0.725, len(keys) - 0.4, "would be useful (> 0.6)", ha="center", fontsize=11, color=C["muted"])
        ax.set_xlabel("AUC: chance a random winner scores higher than a random look-alike · tech names, cap < $2B at the run")
        self.vals = [ax.text(0, i, "", va="center", fontsize=13, fontweight="bold") for i in range(len(keys))]

    def update(self, t):
        for i, (b, j) in enumerate(zip(self.bars, self.order)):
            g = seg(t, 1.0 + i * 0.35, 1.2)
            b.set_width(self.a[j] * g)
            self.vals[i].set_x(self.a[j] * g + 0.01)
            self.vals[i].set_text(f"{self.a[j]:.2f}" if g > 0.99 else "")


class DistScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "Same shape: research intensity does not sort winners from look-alikes", ha="center", fontsize=22, fontweight="bold")
        W, K = R.W, R.K
        def col(rows, k):
            return [r["features"][k] for r in rows if r.get("features") and r["features"].get(k) is not None]
        wf = [w for w in W if w["features"] and w["run_start"] and w["sector"] in R.TECH]
        cf = [c for c in K if c["features"] and c["sector"] in R.TECH]
        self.panels = []
        specs = [("rnd_to_rev", "R&D / revenue (TTM)", (0, 3), [0.07, 0.17, 0.26, 0.66]),
                 ("gross_margin", "Gross margin (TTM)", (-1, 1), [0.39, 0.17, 0.26, 0.66]),
                 ("shares_growth_yoy", "Share-count growth YoY (equity raised)", (-0.2, 1.0), [0.71, 0.17, 0.26, 0.66])]
        for k, lab, clip, rect in specs:
            ax = fig.add_axes(rect)
            pw = np.clip(col(wf, k), *clip)
            pc = np.clip(col(cf, k), *clip)
            parts = ax.violinplot([pc, pw], positions=[0, 1], showmedians=True, widths=0.8)
            for body, colr in zip(parts["bodies"], [C["ctl"], C["win"]]):
                body.set_facecolor(colr)
                body.set_alpha(0.0)
            parts["cmedians"].set_color(C["ink"])
            for key in ("cbars", "cmins", "cmaxes", "cmedians"):
                parts[key].set_alpha(0)
            ax.set_xticks([0, 1])
            ax.set_xticklabels([f"look-alikes\n(n={len(pc)})", f"winners\n(n={len(pw)})"], fontsize=12)
            ax.set_title(lab, fontsize=15)
            auc = R.SEP["tech"][k]["auc"]
            txt = ax.text(0.5, 0.97, f"AUC {auc:.2f}", transform=ax.transAxes, ha="center", va="top", fontsize=15, fontweight="bold",
                          color=C["win"] if auc >= 0.5 else C["red"], alpha=0)
            self.panels.append((parts, txt))

    def update(self, t):
        for i, (parts, txt) in enumerate(self.panels):
            g = seg(t, 0.8 + i * (self.audio_s * 0.28), 1.5)
            for body in parts["bodies"]:
                body.set_alpha(0.6 * g)
            for key in ("cbars", "cmins", "cmaxes", "cmedians"):
                parts[key].set_alpha(g)
            txt.set_alpha(g)


class FamiliesScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "Where the early information lived: filing text and relationships", ha="center", fontsize=22, fontweight="bold")
        ax = fig.add_axes([0.30, 0.17, 0.62, 0.70])
        cat = {}
        for c in R.WF["cases"]:
            for s in c["signals"]:
                if s["months_before_run"] > 0:
                    cat.setdefault(s["category"], []).append(s["months_before_run"])
        items = sorted(cat.items(), key=lambda kv: -len(kv[1]))
        names = {"revenue_inflection": "Revenue inflection", "anchor_customer_or_contract": "Anchor customer / contract", "capex_or_capacity": "Capex / capacity build",
                 "insider_or_institutional": "Insider / institutional buying", "attention_and_narrative": "New narrative in filings", "financing_and_dilution": "Financing / dilution",
                 "price_and_flow": "Price & flow (short interest)", "other": "Other", "supply_chain_link": "Supply-chain link", "policy_or_regulation": "Policy / regulation", "hiring_or_patents": "Hiring / patents"}
        self.items = items
        y = np.arange(len(items))
        self.bars = ax.barh(y, [0] * len(items), color=C["blue"], height=0.62)
        ax.set_yticks(y)
        ax.set_yticklabels([names.get(k, k) for k, _ in items], fontsize=13)
        ax.invert_yaxis()
        ax.set_xlim(0, max(len(v) for _, v in items) * 1.35)
        ax.set_xlabel(f"leading-signal instances across {len(R.WF['cases'])} rebuilt winner case files")
        self.lead = [ax.text(0, i, "", va="center", fontsize=12, color=C["amber"]) for i in range(len(items))]

    def update(self, t):
        for i, (b, (k, v)) in enumerate(zip(self.bars, self.items)):
            g = seg(t, 1.5 + i * 0.5, 1.2)
            b.set_width(len(v) * g)
            self.lead[i].set_x(len(v) * g + 0.4)
            self.lead[i].set_text(f"median lead {statistics.median(v):.0f} months" if g > 0.99 else "")


class GraveyardScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "The graveyard had the same signals", ha="center", fontsize=22, fontweight="bold", color=C["red"])
        cases = [(c["ticker"], c["company"].split(" (")[0].replace(" Corporation", "").replace(", Inc.", "").replace(" Inc.", "").replace(" Corp.", "").replace(" Corp", "").replace(" Holdings", ""))
                 for g in R.WF["graveyard"] for c in g["cases"]]
        seen, self.cases = set(), []
        for tk, nm in cases:
            if tk not in seen:
                seen.add(tk)
                self.cases.append((tk, nm))
        self.tiles = []
        cols, w, h = 4, 0.20, 0.065
        for i, (tk, nm) in enumerate(self.cases[:16]):
            r, c_ = divmod(i, cols)
            x, y = 0.06 + c_ * 0.225, 0.80 - r * 0.085
            box = fig.text(x, y, f"{tk}   {nm}", fontsize=12.5, va="center", color=C["ink"], alpha=0,
                           bbox=dict(boxstyle="round,pad=0.5", fc="#1a0f12", ec=C["red"], lw=1.2))
            self.tiles.append(box)
        self.checks = ["binding contracts with delivered units, not letters of intent",
                       "a disclosed runway number, and how fast it shrinks",
                       "share count trajectory: who is buying the dilution",
                       "customers that are also financiers (related-party demand)",
                       "going-concern or material-weakness language in the 10-K/10-Q",
                       "executive departures tied to a funding gap (Item 5.02)",
                       "exchange compliance notices"]
        fig.text(0.06, 0.43, "What separated the collapses from the survivors, and was checkable at the time:", fontsize=15, fontweight="bold", color=C["amber"])
        self.ctxt = [fig.text(0.08, 0.38 - i * 0.037, "", fontsize=13.5, color=C["ink"]) for i in range(len(self.checks))]

    def update(self, t):
        for i, box in enumerate(self.tiles):
            box.set_alpha(seg(t, 0.8 + i * 0.28, 0.6))
        t0 = self.audio_s * 0.55
        for i, txt in enumerate(self.ctxt):
            g = seg(t, t0 + i * 1.6, 0.5)
            txt.set_text(("›  " + self.checks[i]) if g > 0 else "")
            txt.set_alpha(g)


class BaseRateScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "The base rate: the bumper outcome is the thin right tail", ha="center", fontsize=22, fontweight="bold")
        ax = fig.add_axes([0.06, 0.42, 0.88, 0.30])
        self.buckets = [("< −50%", 38.5, C["red"]), ("−50% to +100%", 100 - 38.5 - 15.7, C["ctl"]), ("+100% to +200%", 15.7 - 7.7, C["blue"]),
                        ("+200% to +500%", 7.7 - 1.7, C["win"]), ("> +500%", 1.7, C["amber"])]
        self.bars, self.labels, left, small = [], [], 0, 0
        for lab, pct, colr in self.buckets:
            self.bars.append((ax.barh(0, 0, left=left, color=colr, edgecolor=C["bg"], height=0.7)[0], left, pct))
            if pct < 8:  # thin slices: staggered labels above the bar, each in its own colour
                y = [0.6, 0.95, 1.3][small]
                small += 1
                ax.plot([left + pct / 2, left + pct / 2], [0.36, y - 0.14], color=colr, lw=1, alpha=0.7)
                self.labels.append(ax.text(left + pct / 2, y, f"{lab}  {pct:.1f}%", ha="right", va="center", fontsize=12.5, alpha=0, color=colr))
            else:
                self.labels.append(ax.text(left + pct / 2, 0, f"{lab}" + chr(10) + f"{pct:.1f}%", ha="center", va="center", fontsize=12.5, alpha=0, color="white"))
            left += pct
        ax.set_xlim(0, 100)
        ax.set_ylim(-0.6, 1.5)
        ax.set_yticks([])
        ax.set_xlabel("share of 9,195 US IPOs (1975–2021) by 3-year buy-and-hold return · Ritter, University of Florida tables", fontsize=12)
        self.notes = [fig.text(0.06, 0.30 - i * 0.055, "", fontsize=14, color=C["ink"]) for i in range(3)]
        self.note_text = ["Unprofitable-at-IPO issuers (n = 3,926): −30.7% market-adjusted over three years",
                          "De-SPAC mergers (n = 447): −74.7%",
                          "Attention, hype and retail crowding predict the WRONG tail (Bali 2011, Barber–Odean, Robinhood herding)"]

    def update(self, t):
        for i, ((b, left, pct), lab) in enumerate(zip(self.bars, self.labels)):
            g = seg(t, 0.6 + i * 0.9, 1.4)
            b.set_width(pct * g)
            lab.set_alpha(g)
        t0 = self.audio_s * 0.5
        for i, n in enumerate(self.notes):
            g = seg(t, t0 + i * 2.6, 0.6)
            n.set_text(self.note_text[i] if g > 0 else "")
            n.set_alpha(g)


class FunnelScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "Bumper Radar: disqualify first, promote only on delivered evidence, narrate last", ha="center", fontsize=21, fontweight="bold")
        ax = fig.add_axes([0.05, 0.12, 0.90, 0.76])
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        self.ax = ax
        stages = [("1 · Point-in-time universe", "US filers · " + chr(92) + "$50M–" + chr(92) + "$3B · pre-profit · quantum, physical AI, AI infrastructure", 1.0, C["ctl"]),
                  ("2 · Disqualifying gates", "going-concern · runway compression · governance self-dealing · exchange notices · funding-gap departures", 0.78, C["red"]),
                  ("3 · Binding-demand check", "an announced contract counts only when a later filing shows delivered units or recognised revenue", 0.58, C["amber"]),
                  ("4 · Capped supporting signals", "dilution by who bought it · distressed-but-funded · 13D stakes · capital-web edge gain (triage only)", 0.42, C["blue"]),
                  ("5 · Devil's advocate + judge", "band: abstain · avoid-pattern · watch (thin) · watch (favourable, unvalidated) — three cited reasons, never a tip", 0.28, C["win"])]
        self.items = []
        for i, (title, sub, w, colr) in enumerate(stages):
            y = 0.97 - i * 0.195
            rect = plt.Rectangle((0.5 - w / 2, y - 0.12), w, 0.12, color=colr, alpha=0)
            ax.add_patch(rect)
            t1 = ax.text(0.5, y - 0.06, title, ha="center", va="center", fontsize=17, fontweight="bold", color="white", alpha=0)
            t2 = ax.text(0.5, y - 0.135, sub, ha="center", va="top", fontsize=12, color=C["muted"], alpha=0)
            self.items.append((rect, t1, t2))

    def update(self, t):
        step = self.audio_s / 6.2
        for i, (rect, t1, t2) in enumerate(self.items):
            g = seg(t, 0.6 + i * step, 0.9)
            rect.set_alpha(0.88 * g)
            t1.set_alpha(g)
            t2.set_alpha(g)


class TodayScene(Scene):
    def build(self):
        fig = self.fig
        fig.text(0.5, 0.905, "Today's screen (2026-09-25): research intensity against cash runway, bubble = market cap", ha="center", fontsize=20, fontweight="bold")
        ax = fig.add_axes([0.08, 0.17, 0.86, 0.70])
        groups = {"quantum": ["IONQ", "RGTI", "QUBT", "ARQQ", "LAES", "INFQ", "XNDU", "HQ", "BTQ"],
                  "physical AI": ["USAR", "UUUU", "NB", "CRML", "EMAT", "ALNT", "SERV", "ALGM", "NOVT"],
                  "AI infra": ["NBIS", "IREN", "APLD", "CORZ", "WULF", "ALAB", "CRDO", "SOUN", "AI", "RZLV", "CRWV"]}
        cols = {"quantum": C["purple"], "physical AI": C["win"], "AI infra": C["blue"]}
        self.pts = []
        for gi, (g, syms) in enumerate(groups.items()):
            for s in syms:
                v = next((r for k, r in R.SCAN.items() if k.split(":")[-1] == s), None)
                if not v:
                    continue
                rev, rd, fcf, cash, mc = v["total_revenue_ttm"], v["research_and_dev_ttm"], v["free_cash_flow_ttm"], v["cash_n_short_term_invest_fq"], v["market_cap_basic"]
                rdr = abs(rd) / rev if rev and rd is not None else None
                runway = cash / -fcf if (fcf is not None and fcf < 0 and cash) else (25 if fcf is not None and fcf >= 0 else None)
                if rdr is None or runway is None or not mc:
                    continue
                x, y = max(rdr, 0.02), min(runway, 25)
                sc = ax.scatter([x], [y], s=max(60, (mc / 1e9) ** 0.5 * 70), color=cols[g], alpha=0, edgecolor="white", lw=0.6)
                dy = {"ALGM": -14, "CRDO": 8, "ALNT": -14}.get(s, 5)
                an = ax.annotate(s, (x, y), xytext=(6, dy), textcoords="offset points", fontsize=12, alpha=0)
                self.pts.append((gi, sc, an))
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("R&D / revenue (TTM)  →  more research per dollar of sales", fontsize=13)
        ax.set_ylabel("cash runway, years (cash ÷ free-cash burn; 25 = FCF positive)", fontsize=13)
        self.gate = ax.axhline(2, color=C["red"], ls="--", lw=1.5, alpha=0)
        self.gtxt = ax.text(0.01, 2.15, "runway gate (< 2 years)", color=C["red"], fontsize=13, alpha=0, transform=ax.get_yaxis_transform())
        for g, colr in cols.items():
            ax.scatter([], [], color=colr, label=g, s=80)
        ax.legend(loc="lower right", fontsize=13)

    def update(self, t):
        for gi, sc, an in self.pts:
            g = seg(t, 0.8 + gi * 2.2, 1.2)
            sc.set_alpha(0.8 * g)
            an.set_alpha(g)
        a = seg(t, self.audio_s * 0.5, 0.8)
        self.gate.set_alpha(a)
        self.gtxt.set_alpha(a)


SCENES = {"title": TitleScene, "r01": CohortScene, "r04": PathsScene, "r02": AucScene, "r03": DistScene, "r05": FamiliesScene,
          "graveyard": GraveyardScene, "r06": BaseRateScene, "r07": FunnelScene, "r08": TodayScene}


# ------------------------------------------------------------------ render
def render_segment(segment, force=False) -> pathlib.Path:
    mp3 = VOICE / f"{segment['id']}.mp3"
    out = WORK / f"{segment['id']}.mp4"
    if out.exists() and not force and out.stat().st_mtime > mp3.stat().st_mtime:
        return out
    scene = SCENES[segment["chart"]](segment, duration(mp3))
    n = int(round(scene.total * FPS))
    cmd = [FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", "1920x1080", "-r", str(FPS), "-i", "-",
           "-i", str(mp3), "-af", "apad", "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        buf = scene.frame(f / FPS)
        assert buf.shape[:2] == (1080, 1920), buf.shape
        p.stdin.write(buf.tobytes())
    p.stdin.close()
    p.wait()
    scene.close()
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {segment['id']}")
    print(f"{segment['id']}: {n} frames, {scene.total:.1f}s -> {out.name}", flush=True)
    return out


def concat(parts, final=FINAL):
    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(final)], check=True)
    return final


def main(argv):
    segs = json.load(open(D / "narration.json", encoding="utf-8"))
    only = [a for a in argv if not a.startswith("-")]
    force = "--force" in argv
    parts = []
    for s in segs:
        if only and s["id"] not in only:
            continue
        parts.append(render_segment(s, force=force))
    if not only:
        final = concat(parts)
        print("final:", final, f"{final.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1:])
