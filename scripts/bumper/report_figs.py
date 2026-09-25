"""Figures and the animated companion for the bumper report.

    cd scripts && python -m bumper.report_figs

Every number is read from data/bumper/2026-09-25/* (the study outputs) and the cached
price files; nothing is typed in by hand except the Ritter base rates, which are quoted
with their source in the report.
"""
from __future__ import annotations

import json
import pathlib
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.animation as anim
import matplotlib.pyplot as plt
import numpy as np

from . import features as F

ROOT = pathlib.Path(__file__).resolve().parents[2]
DAY = "2026-09-25"
D = ROOT / "data" / "bumper" / DAY
CACHE = ROOT / "data" / "bumper" / "cache" / "prices"
OUT = ROOT / "references" / "bumper-report" / "fig"
OUT.mkdir(parents=True, exist_ok=True)

TECH = {"Electronic Technology", "Technology Services", "Producer Manufacturing", "Industrial Services", "Utilities", "Transportation"}
C = {"win": "#22e07e", "ctl": "#8a94a6", "bg": "#0b0f17", "panel": "#0e131d", "ink": "#e5e7eb", "muted": "#9ca3af",
     "red": "#ff3b30", "amber": "#f59e0b", "blue": "#3b82f6", "purple": "#a855f7"}

plt.rcParams.update({
    "figure.facecolor": C["bg"], "axes.facecolor": C["panel"], "savefig.facecolor": C["bg"],
    "axes.edgecolor": "#1f2937", "axes.labelcolor": C["ink"], "xtick.color": C["muted"], "ytick.color": C["muted"],
    "text.color": C["ink"], "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.spines.top": False, "axes.spines.right": False, "grid.color": "#1f2937", "axes.grid": True, "grid.alpha": 0.6,
    "savefig.dpi": 200, "legend.frameon": False,
})

W = json.load(open(D / "winners.json", encoding="utf-8"))
K = json.load(open(D / "controls.json", encoding="utf-8"))
SEP = json.load(open(D / "separation_matched.json", encoding="utf-8"))
SUM = json.load(open(D / "summary.json", encoding="utf-8"))
WF = json.load(open(D / "workflow_result.json", encoding="utf-8"))
SCAN = json.load(open(ROOT / "data" / "bumper_scan_2026-09-25.json", encoding="utf-8"))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png")
    fig.savefig(OUT / f"{name}.svg")
    plt.close(fig)


# 1. cohort -----------------------------------------------------------------------------------
def fig_cohort():
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6), gridspec_kw={"width_ratios": [1, 1.4]})
    yrs = sorted(SUM["run_start_years"].items())
    axs[0].bar([y for y, _ in yrs], [n for _, n in yrs], color=C["win"])
    axs[0].set_title("When the runs started")
    axs[0].set_ylabel("winners (first 12-month window ≥ 2.5×)")
    for y, n in yrs:
        axs[0].text(y, n + 1, str(n), ha="center", fontsize=9)
    sec = list(SUM["winners_by_sector"].items())[:10][::-1]
    axs[1].barh([s for s, _ in sec], [n for _, n in sec], color=[C["win"] if s in TECH else C["ctl"] for s, _ in sec])
    axs[1].set_title(f"{SUM['winners_total']} winners by sector (green = 'emerging-tech' subset)")
    axs[1].set_xlabel("names")
    save(fig, "r01_cohort")


# 2. AUC dumbbell --------------------------------------------------------------------------------
LABELS = {"rev_growth_yoy": "Revenue growth YoY", "rev_acceleration": "Revenue acceleration", "rnd_to_rev": "R&D / revenue",
          "runway_years": "Cash runway (years)", "shares_growth_yoy": "Share count growth (dilution)", "gross_margin": "Gross margin",
          "ocf_ttm": "Operating cash flow", "mom_6m_pre": "6-month prior momentum", "mom_12m_pre": "12-month prior momentum",
          "drawdown_3y": "Drawdown from 3-year high"}


def fig_auc():
    keys = list(LABELS)
    a = [SEP["all"][k]["auc"] for k in keys]
    t = [SEP["tech_small"][k]["auc"] for k in keys]
    order = np.argsort(a)
    fig, ax = plt.subplots(figsize=(9, 5))
    y = np.arange(len(keys))
    for i, j in enumerate(order):
        ax.plot([a[j], t[j]], [i, i], color="#374151", lw=2, zorder=1)
        ax.scatter(a[j], i, color=C["blue"], s=60, zorder=3, label="all winners vs controls" if i == 0 else None)
        ax.scatter(t[j], i, color=C["win"], s=60, zorder=3, label="tech, cap < $2B at run" if i == 0 else None)
    ax.axvline(0.5, color=C["red"], ls="--", lw=1.2)
    ax.text(0.505, len(keys) - 0.6, "0.5 = coin flip", color=C["red"], fontsize=9)
    ax.set_yticks(y)
    ax.set_yticklabels([LABELS[keys[j]] for j in order])
    ax.set_xlim(0.2, 0.8)
    ax.set_xlabel("AUC: probability a random winner scores higher than a random look-alike, 3 months before the run")
    ax.set_title("Nothing in the filings separates future winners from look-alikes")
    fig.text(0.5, 0.005, "below 0.5 = winners were LOWER on this feature (lower margin, more burn, deeper drawdown)", ha="center", color=C["muted"], fontsize=8.5)
    ax.legend(loc="lower right")
    fig.subplots_adjust(bottom=0.2)
    save(fig, "r02_auc")


# 3. distributions -----------------------------------------------------------------------------------
def fig_distributions():
    def col(rows, k):
        return [r["features"][k] for r in rows if r.get("features") and r["features"].get(k) is not None]
    wf = [w for w in W if w["features"] and w["run_start"] and w["sector"] in TECH]
    cf = [c for c in K if c["features"] and c["sector"] in TECH]
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.6))
    for ax, k, lab, clip in [(axs[0], "gross_margin", "Gross margin (TTM)", (-1, 1)), (axs[1], "rnd_to_rev", "R&D / revenue (TTM)", (0, 3)), (axs[2], "shares_growth_yoy", "Share-count growth YoY", (-0.2, 1.0))]:
        pw = np.clip(col(wf, k), *clip)
        pc = np.clip(col(cf, k), *clip)
        parts = ax.violinplot([pc, pw], positions=[0, 1], showmedians=True, widths=0.8)
        for body, colr in zip(parts["bodies"], [C["ctl"], C["win"]]):
            body.set_facecolor(colr)
            body.set_alpha(0.55)
        parts["cmedians"].set_color(C["ink"])
        ax.set_xticks([0, 1])
        ax.set_xticklabels([f"look-alikes\n(n={len(pc)})", f"winners\n(n={len(pw)})"])
        ax.set_title(lab)
        ax.text(0.5, 0.95, f"AUC {SEP['tech']['gross_margin' if k == 'gross_margin' else k]['auc']:.2f}", transform=ax.transAxes, ha="center", va="top", fontsize=9, color=C["muted"])
    fig.suptitle("Tech names three months before the run: winners were lower-margin and raised more equity", fontsize=11, fontweight="bold")
    save(fig, "r03_distributions")


# 4. price paths ---------------------------------------------------------------------------------------
def closes(sym):
    p = CACHE / f"{sym}.json"
    return [(k, v) for k, v in json.load(open(p))] if p.exists() else None


def path(sym, month, before=24, after=12):
    c = closes(sym)
    if not c or not month:
        return None
    idx = {k: i for i, (k, _) in enumerate(c)}
    if month not in idx:
        return None
    i = idx[month]
    if i - before < 0 or i + after >= len(c) or not c[i - 1][1]:
        return None
    base = c[i - 1][1]
    return [c[j][1] / base for j in range(i - before, i + after + 1)]


def paths_winners_controls():
    months = sorted(w["run_start"] for w in W if w["run_start"])
    pw = [p for w in W if w["run_start"] and w["sector"] in TECH for p in [path(w["symbol"], w["run_start"])] if p]
    pc = []
    for i, c in enumerate(K):
        if c["sector"] not in TECH:
            continue
        p = path(c["symbol"], months[(i * 7) % len(months)])
        if p:
            pc.append(p)
    return np.array(pw), np.array(pc)


def fig_paths():
    pw, pc = paths_winners_controls()
    x = np.arange(-24, 13)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for arr, colr, lab in [(pc, C["ctl"], f"look-alikes (n={len(pc)})"), (pw, C["win"], f"winners (n={len(pw)})")]:
        med = np.median(arr, axis=0)
        lo, hi = np.percentile(arr, 25, axis=0), np.percentile(arr, 75, axis=0)
        ax.fill_between(x, lo, hi, color=colr, alpha=0.18)
        ax.plot(x, med, color=colr, lw=2.4, label=lab + ", median and middle half")
    ax.axvline(0, color=C["amber"], ls="--", lw=1.2)
    ax.text(0.4, 0.06, "run start\n(first 12-month window ≥ 2.5×)", color=C["amber"], fontsize=8.5, transform=ax.get_xaxis_transform())
    ax.set_yscale("log")
    from matplotlib.ticker import FixedLocator, FixedFormatter
    ax.yaxis.set_major_locator(FixedLocator([0.5, 0.75, 1, 1.5, 2, 3]))
    ax.yaxis.set_major_formatter(FixedFormatter(["0.5×", "0.75×", "1×", "1.5×", "2×", "3×"]))
    ax.yaxis.set_minor_formatter(FixedFormatter([]))
    ax.set_xlabel("months relative to run start")
    ax.set_ylabel("price relative to one month before run start")
    ax.set_title("The shape of a bumper: two flat-to-down years, then the run")
    ax.legend(loc="upper left")
    save(fig, "r04_paths")
    return x, pw, pc


# 5. signal families ---------------------------------------------------------------------------------------
def fig_families():
    cat = {}
    for c in WF["cases"]:
        for s in c["signals"]:
            if s["months_before_run"] > 0:
                cat.setdefault(s["category"], []).append(s["months_before_run"])
    items = sorted(cat.items(), key=lambda kv: len(kv[1]))
    names = {"revenue_inflection": "Revenue inflection", "anchor_customer_or_contract": "Anchor customer / contract", "capex_or_capacity": "Capex / capacity build",
             "insider_or_institutional": "Insider / institutional", "attention_and_narrative": "Narrative in filings", "financing_and_dilution": "Financing / dilution",
             "price_and_flow": "Price & flow (short interest)", "other": "Other", "supply_chain_link": "Supply-chain link", "policy_or_regulation": "Policy / regulation", "hiring_or_patents": "Hiring / patents"}
    fig, ax = plt.subplots(figsize=(9, 4.8))
    y = np.arange(len(items))
    ax.barh(y, [len(v) for _, v in items], color=C["blue"], alpha=0.85)
    for i, (k, v) in enumerate(items):
        ax.text(len(v) + 0.3, i, f"median lead {statistics.median(v):.0f} mo", va="center", fontsize=8.5, color=C["muted"])
    ax.set_yticks(y)
    ax.set_yticklabels([names.get(k, k) for k, _ in items])
    ax.set_xlabel("leading signal instances across 18 case studies (opened filings)")
    ax.set_title("Where the early information lived: filing text and relationships, not ratios")
    ax.set_xlim(0, 33)
    save(fig, "r05_families")


# 6. base rates ---------------------------------------------------------------------------------------------
def fig_base_rates():
    # Ritter IPO tables (opened in the workflow, 2026-09-25): 3-year buy-and-hold outcome buckets, 9,195 IPOs 1975-2021
    buckets = [("< −50%", 38.5), ("−50% to +100%", 100 - 38.5 - 15.7), ("+100% to +200%", 15.7 - 7.7), ("+200% to +500%", 7.7 - 1.7), ("> +500%", 1.7)]
    fig, ax = plt.subplots(figsize=(9, 3.4))
    left = 0
    cols = [C["red"], C["ctl"], C["blue"], C["win"], C["amber"]]
    for (lab, pct), colr in zip(buckets, cols):
        ax.barh(0, pct, left=left, color=colr, edgecolor=C["bg"])
        ax.text(left + pct / 2, 0, f"{lab}\n{pct:.1f}%", ha="center", va="center", fontsize=8.5, color="white" if pct > 8 else C["ink"])
        left += pct
    ax.set_xlim(0, 100)
    ax.set_yticks([])
    ax.set_xlabel("share of 9,195 US IPOs (1975–2021) by 3-year buy-and-hold return · Ritter, U. Florida tables")
    ax.set_title("Base rate: the 'bumper' outcome is the thin right tail")
    ax.text(0, -0.75, "Unprofitable-at-IPO issuers (n=3,926): −30.7% market-adjusted over 3 years · de-SPACs (n=447): −74.7%", fontsize=8.5, color=C["muted"], transform=ax.get_xaxis_transform())
    save(fig, "r06_base_rates")


# 7. detector funnel --------------------------------------------------------------------------------------------
def fig_funnel():
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.axis("off")
    stages = [("Point-in-time universe", "US filers · $50M–$3B · pre-profit · quantum, physical AI, AI infra", 1.0, C["ctl"]),
              ("Disqualifying gates", "going-concern · runway compression · governance self-dealing · exchange notices · funding-gap departures", 0.7, C["red"]),
              ("Binding-demand check", "an announced contract counts only when a later filing shows delivered units or recognised revenue", 0.5, C["amber"]),
              ("Capped supporting signals", "dilution by who bought it · distressed-but-funded ensemble · 13D stakes · capital-web edge gain (triage only)", 0.36, C["blue"]),
              ("Devil's advocate + judge", "band: abstain · avoid-pattern · watch (thin) · watch (favourable, unvalidated) — three cited reasons, never a tip", 0.22, C["win"])]
    for i, (t, sub, w, colr) in enumerate(stages):
        y = 1 - i * 0.215
        ax.add_patch(plt.Rectangle((0.5 - w / 2, y - 0.11), w, 0.11, color=colr, alpha=0.85))
        ax.text(0.5, y - 0.055, t, ha="center", va="center", fontsize=11, fontweight="bold", color="white")
        ax.text(0.5, y - 0.125, sub, ha="center", va="top", fontsize=8.2, color=C["muted"])
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.12, 1.02)
    ax.set_title("Bumper Radar: disqualify first, promote only on delivered evidence, narrate last")
    save(fig, "r07_funnel")


# 8. today's screen ----------------------------------------------------------------------------------------------
def fig_today():
    groups = {"quantum": ["IONQ", "RGTI", "QUBT", "ARQQ", "LAES", "INFQ", "XNDU", "HQ", "BTQ"],
              "physical AI": ["USAR", "UUUU", "NB", "CRML", "EMAT", "ALNT", "SERV", "ALGM", "NOVT"],
              "AI infra": ["NBIS", "IREN", "APLD", "CORZ", "WULF", "ALAB", "CRDO", "SOUN", "AI", "RZLV", "CRWV"]}
    cols = {"quantum": C["purple"], "physical AI": C["win"], "AI infra": C["blue"]}
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    for g, syms in groups.items():
        for s in syms:
            v = next((r for k, r in SCAN.items() if k.split(":")[-1] == s), None)
            if not v:
                continue
            rev, rd, fcf, cash, mc = v["total_revenue_ttm"], v["research_and_dev_ttm"], v["free_cash_flow_ttm"], v["cash_n_short_term_invest_fq"], v["market_cap_basic"]
            rdr = abs(rd) / rev if rev and rd is not None else None
            runway = cash / -fcf if (fcf is not None and fcf < 0 and cash) else (25 if fcf is not None and fcf >= 0 else None)
            if rdr is None or runway is None or not mc:
                continue
            ax.scatter(max(rdr, 0.02), min(runway, 25), s=max(30, (mc / 1e9) ** 0.5 * 40), color=cols[g], alpha=0.75, edgecolor="white", lw=0.5)
            dy = {"ALGM": -11, "CRDO": 6, "ALNT": -11}.get(s, 3)
            ax.annotate(s, (max(rdr, 0.02), min(runway, 25)), xytext=(4, dy), textcoords="offset points", fontsize=8)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("R&D / revenue (TTM)  →  more research per dollar of sales")
    ax.set_ylabel("cash runway, years (cash ÷ free-cash burn; 25 = FCF positive)")
    ax.axhline(2, color=C["red"], ls="--", lw=1)
    ax.text(0.09, 2.15, "runway gate (< 2 years)", color=C["red"], fontsize=8.5)
    for g, colr in cols.items():
        ax.scatter([], [], color=colr, label=g)
    ax.legend(loc="lower right")
    ax.set_title("Today's screen (2026-09-25): where the candidates sit, bubble = market cap")
    save(fig, "r08_today")


# 9. animation: paths draw in, then the AUC verdict ------------------------------------------------------------------
def animate(x, pw, pc, out=OUT / "bumper_paths.mp4"):
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.8, 7.2), gridspec_kw={"width_ratios": [1.5, 1]})
    fig.subplots_adjust(left=0.06, right=0.98, top=0.86, bottom=0.12, wspace=0.28)
    fig.suptitle("Bumper study, 2026-09-25: what the winners looked like before the run", fontsize=14, fontweight="bold", y=0.96)
    rng = np.random.default_rng(7)
    sample_w = pw[rng.choice(len(pw), size=min(40, len(pw)), replace=False)]
    sample_c = pc[rng.choice(len(pc), size=min(40, len(pc)), replace=False)]
    lines_c = [ax.plot([], [], color=C["ctl"], lw=0.8, alpha=0.45)[0] for _ in sample_c]
    lines_w = [ax.plot([], [], color=C["win"], lw=0.9, alpha=0.6)[0] for _ in sample_w]
    med_w, = ax.plot([], [], color=C["win"], lw=3)
    med_c, = ax.plot([], [], color=C["ctl"], lw=3)
    ax.set_yscale("log")
    ax.set_xlim(-24, 12)
    ax.set_ylim(0.2, 8)
    ax.axvline(0, color=C["amber"], ls="--", lw=1.2)
    ax.set_xlabel("months relative to run start")
    ax.set_ylabel("price relative to one month before the run (log)")
    ax.set_title("winners (green) vs industry look-alikes (grey)")
    keys = list(LABELS)
    a = [SEP["tech_small"][k]["auc"] for k in keys]
    order = np.argsort(a)
    bars = ax2.barh(np.arange(len(keys)), [0] * len(keys), color=[C["win"] if a[j] > 0.5 else C["red"] for j in order])
    ax2.set_yticks(np.arange(len(keys)))
    ax2.set_yticklabels([LABELS[keys[j]] for j in order], fontsize=9)
    ax2.set_xlim(0, 0.8)
    ax2.axvline(0.5, color=C["ink"], ls="--", lw=1)
    ax2.set_xlabel("AUC, tech names with cap < $2B (0.5 = coin flip)")
    ax2.set_title("three months before the run, filings say... nothing")
    n_frames_paths = 37 * 6
    n_frames_bars = 72
    hold = 60
    total = n_frames_paths + n_frames_bars + hold

    def update(f):
        if f < n_frames_paths:
            k = f // 6 + 1
            for ln, p in zip(lines_c, sample_c):
                ln.set_data(x[:k], p[:k])
            for ln, p in zip(lines_w, sample_w):
                ln.set_data(x[:k], p[:k])
            med_w.set_data(x[:k], np.median(pw, axis=0)[:k])
            med_c.set_data(x[:k], np.median(pc, axis=0)[:k])
        else:
            g = min(1.0, (f - n_frames_paths) / n_frames_bars)
            for b, j in zip(bars, order):
                b.set_width(a[j] * g)
        return lines_c + lines_w + [med_w, med_c] + list(bars)

    an = anim.FuncAnimation(fig, update, frames=total, interval=1000 / 24, blit=False)
    an.save(out, writer="ffmpeg", fps=24, dpi=100, extra_args=["-pix_fmt", "yuv420p", "-crf", "24"])
    plt.close(fig)
    return out


if __name__ == "__main__":
    fig_cohort(); print("r01")
    fig_auc(); print("r02")
    fig_distributions(); print("r03")
    x, pw, pc = fig_paths(); print("r04", len(pw), len(pc))
    fig_families(); print("r05")
    fig_base_rates(); print("r06")
    fig_funnel(); print("r07")
    fig_today(); print("r08")
    print("mp4:", animate(x, pw, pc))
