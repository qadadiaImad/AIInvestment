"""Generate every figure in references/physical-ai-lesson/fig from the tested helpers.

Run:  cd scripts && python -m lesson.figures
Every curve is computed by lesson.magnetics; the only hand-typed numbers are the
literature constants collected in CONSTANTS below, each with its source key.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from lesson import magnetics as m

OUT = Path(__file__).resolve().parents[2] / "references" / "physical-ai-lesson" / "fig"
OUT.mkdir(parents=True, exist_ok=True)

# ---- literature constants (source key -> lesson bibliography) -------------------------------
CONSTANTS = {
    # Hirosawa, Nishino, Miyashita 2017, Table 1 (Nd2Fe14B, room temperature)
    "Js_Nd2Fe14B_T": 1.60,
    "Ms_Nd2Fe14B_Am": 1.28e6,
    "K1_Nd2Fe14B_Jm3": 4.3e6,
    "BHmax_theo_kJm3": 509,
    # Wikipedia, Neodymium magnet: sintered range
    "BHmax_sintered_range_kJm3": (200, 440),
    # Radial Magnets class table (nominal): grade -> (min Hcj kOe, max operating C)
    "grades": {"N": (12, 80), "M": (14, 100), "H": (17, 120), "SH": (20, 150),
               "UH": (25, 180), "EH": (30, 200), "AH": (33, 230)},
    # Bunting (magnetapplications.com): reversible coefficients, %/C
    "alpha_beta": {"NdFeB": (-0.12, -0.60), "SmCo": (-0.04, -0.30), "Ferrite": (-0.20, +0.27),
                   "Alnico": (-0.02, -0.01)},
    # Ismail et al. 2019 (IJRTE), Table 4 (EHEHPA / P507) and Table 3 (D2EHPA), adjacent pairs
    "beta_P507": {"Pr/Nd": 1.17, "Nd/Sm": 2.00, "Sm/Eu": 1.96, "Eu/Gd": 1.46, "Gd/Tb": 2.35,
                  "Tb/Dy": 1.62, "Dy/Ho": 2.58, "Ho/Er": 1.25, "Er/Tm": 1.33, "Tm/Yb": 1.12,
                  "Yb/Lu": 1.13},
    "beta_D2EHPA": {"Pr/Nd": 1.06, "Nd/Sm": 4.86, "Sm/Eu": 2.23, "Eu/Gd": 1.69, "Gd/Tb": 1.60,
                    "Tb/Dy": 1.42, "Dy/Ho": 1.24, "Ho/Er": 1.70, "Er/Tm": 1.50, "Tm/Yb": 1.30,
                    "Yb/Lu": 1.03},
    # FAI 2026: magnet per humanoid by architecture; Dy per robot
    "kg_magnet_high_ratio": 2.0, "kg_magnet_qdd": 4.5, "g_Dy_per_robot": (35, 79),
    # Energy Fuels / FAI: dysprosium tonnes per year (oxide capacity vs metal demand)
    "dy_rows": [("1M humanoids/yr need (metal)", 35, 79), ("Energy Fuels target Q4 2026 (oxide)", 48, 48),
                ("Energy Fuels phase 1, 2027-28", 120, 120), ("Energy Fuels phase 2, 2028-29", 288, 288),
                ("EVs consumed 2025 (Dy-eq.)", 1470, 1470), ("World Dy sold 2024", 2700, 2700)],
    # Wensing et al. 2017: empirical torque-density exponent vs gap radius
    "torque_density_exponent": 0.8,
}

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "legend.fontsize": 8, "figure.dpi": 150, "savefig.dpi": 200, "svg.fonttype": "path",
    "axes.spines.top": False, "axes.spines.right": False,
})
C = ["#1f4e79", "#c0392b", "#2e8b57", "#8e44ad", "#e67e22", "#7f8c8d"]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.svg")
    fig.savefig(OUT / f"{name}.png")
    plt.close(fig)


# 1. Energy product: ideal bound vs remanence, with Nd2Fe14B and sintered ranges ------------
def fig_energy_product():
    br = np.linspace(0.2, 1.7, 200)
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    ax.plot(br, m.bh_max_ideal(br) / 1e3, color=C[0], lw=2, label=r"ideal square loop: $B_r^2/4\mu_0$")
    js = CONSTANTS["Js_Nd2Fe14B_T"]
    ax.scatter([js], [m.bh_max_ideal(js) / 1e3], color=C[1], zorder=5)
    ax.annotate(f"Nd$_2$Fe$_{{14}}$B, $J_s$ = {js} T\n{m.bh_max_ideal(js)/1e3:.0f} kJ/m$^3$ (theory 509)",
                (js, m.bh_max_ideal(js) / 1e3), xytext=(0.55, 470), fontsize=8,
                arrowprops=dict(arrowstyle="->", color=C[1]))
    lo, hi = CONSTANTS["BHmax_sintered_range_kJm3"]
    ax.axhspan(lo, hi, color=C[2], alpha=0.12)
    ax.text(0.25, (lo + hi) / 2, "commercial sintered NdFeB\n200 to 440 kJ/m$^3$", color=C[2], fontsize=8, va="center")
    ax.set_xlabel("remanence $B_r$ (T)")
    ax.set_ylabel("$(BH)_{max}$ (kJ/m$^3$)")
    ax.set_title("The energy-product ceiling is set by remanence squared")
    ax.legend(loc="upper left")
    save(fig, "f01_energy_product")


# 2. Demagnetisation curves with temperature and load lines ---------------------------------
def j_curve(h, br, hcj, sharp=6.0):
    """Smooth intrinsic curve J(H): flat at Br, falling to 0 around H = -Hcj."""
    return br * 0.5 * (1 + np.tanh(sharp * (h + hcj) / hcj))


def fig_demag_temperature():
    br0, hcj0 = 1.40, m.koe_to_am(CONSTANTS["grades"]["N"][0])
    a, b = CONSTANTS["alpha_beta"]["NdFeB"]
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    h = np.linspace(-1.3e6, 0, 600)
    for t, col in zip([20, 80, 120, 150], [C[0], C[2], C[4], C[1]]):
        br = m.at_temperature(br0, a / 100, t)
        hcj = m.at_temperature(hcj0, b / 100, t)
        j = j_curve(h, br, hcj)
        bfield = j + m.MU0 * h
        ax.plot(m.tesla(h), np.clip(bfield, 0, None), color=col, lw=1.8, label=f"B(H) at {t} °C")
        ax.plot(m.tesla(h), j, color=col, lw=0.9, ls="--")
    for pc in [1, 2, 5]:
        # load line B = -mu0 Pc H, drawn only up to B = 1.5 T so it stays inside the axes
        h_end = -1.5 / (m.MU0 * pc)
        hh = np.linspace(max(h_end, -1.3e6), 0, 10)
        ax.plot(m.tesla(hh), -m.MU0 * pc * hh, color="k", lw=0.8, alpha=0.5)
        x_lab = m.tesla(hh[0]); y_lab = -m.MU0 * pc * hh[0]
        ax.text(x_lab - 0.02, min(y_lab, 1.45), f"$P_c$={pc}", fontsize=7, alpha=0.8, ha="right", va="bottom")
    ax.set_xlim(-1.6, 0); ax.set_ylim(0, 1.55)
    ax.set_xlabel(r"$\mu_0 H$ (T)  [second quadrant]")
    ax.set_ylabel("B, J (T)")
    ax.set_title("An N-grade magnet loses its knee margin as it heats")
    ax.legend(loc="upper left", fontsize=7)
    ax.text(-1.55, 0.08, "dashed = intrinsic J(H); solid = B(H); grey = load lines", fontsize=7)
    save(fig, "f02_demag_temperature")


# 3. Maximum safe temperature vs permeance coefficient, by grade -------------------------------
def fig_safe_temperature():
    pcs = np.linspace(0.5, 6, 60)
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    a, _ = CONSTANTS["alpha_beta"]["NdFeB"]
    for (g, (hcj_koe, t_nom)), col in zip(list(CONSTANTS["grades"].items())[:5], C):
        beta = -0.60 if g == "N" else -0.55  # Radial Magnets: higher classes ~ -0.50 to -0.55 %/C
        br = {"N": 1.40, "M": 1.37, "H": 1.35, "SH": 1.32, "UH": 1.28}[g]
        ts = [m.max_safe_temperature(br, m.koe_to_am(hcj_koe), pc, beta / 100, alpha=a / 100, margin=1.2)
              for pc in pcs]
        ax.plot(pcs, ts, color=col, lw=1.8, label=f"{g}: $H_{{cj}}$ ≥ {hcj_koe} kOe (nominal {t_nom} °C)")
    ax.set_xlabel("permeance coefficient $P_c$ of the magnetic circuit")
    ax.set_ylabel("highest safe temperature (°C), 20 % knee margin")
    ax.set_title("Grade and circuit design together set the thermal ceiling")
    ax.set_ylim(20, 260)
    ax.legend(fontsize=7, loc="lower right")
    save(fig, "f03_safe_temperature")


# 4. Reversible temperature coefficients by material ---------------------------------------------
def fig_temp_coefficients():
    t = np.linspace(20, 200, 100)
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 3.0), sharex=True)
    for (mat, (a, b)), col in zip(CONSTANTS["alpha_beta"].items(), C):
        axs[0].plot(t, m.at_temperature(1.0, a / 100, t), color=col, lw=1.8, label=mat)
        axs[1].plot(t, m.at_temperature(1.0, b / 100, t), color=col, lw=1.8, label=mat)
    axs[0].set_title(r"remanence $B_r(T)/B_r(20)$"); axs[1].set_title(r"coercivity $H_{cj}(T)/H_{cj}(20)$")
    for ax in axs:
        ax.set_xlabel("temperature (°C)"); ax.axhline(1, color="k", lw=0.5, alpha=0.4)
    axs[0].set_ylim(0.6, 1.02); axs[1].set_ylim(0, 1.6)
    axs[1].legend(fontsize=7)
    save(fig, "f04_temp_coefficients")


# 5. Kronmuller: coercivity vs anisotropy field, the Brown paradox ------------------------------
def fig_kronmuller():
    ha_nd = m.anisotropy_field(CONSTANTS["K1_Nd2Fe14B_Jm3"], CONSTANTS["Ms_Nd2Fe14B_Am"])
    ms = CONSTANTS["Ms_Nd2Fe14B_Am"]
    ha = np.linspace(2e6, 14e6, 100)
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.plot(ha / 1e6, ha / 1e6, color="k", ls=":", lw=1, label="ideal nucleation: $H_c = H_A$ (Stoner-Wohlfarth)")
    for alpha, neff, col in [(0.42, 1.0, C[0]), (0.6, 1.0, C[2]), (0.3, 1.0, C[4])]:
        hc = m.kronmuller_hc(ha, ms, alpha, neff)
        ax.plot(ha / 1e6, hc / 1e6, color=col, lw=1.8, label=rf"$\alpha$={alpha}, $N_{{eff}}$={neff}")
    hcj_n = m.koe_to_am(12)
    ax.scatter([ha_nd / 1e6], [hcj_n / 1e6], color=C[1], zorder=5)
    ax.annotate(f"sintered N grade:\n$H_A$ = {ha_nd/1e6:.2f} MA/m, $H_{{cj}}$ ≈ 12 kOe = {hcj_n/1e6:.2f} MA/m\n"
                f"ratio {hcj_n/ha_nd:.2f}", (ha_nd / 1e6, hcj_n / 1e6), xytext=(2.0, 7.9), fontsize=7.5,
                arrowprops=dict(arrowstyle="->", color=C[1]),
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C[1], lw=0.6))
    ax.axvline(ha_nd / 1e6 * 2.3, color=C[3], lw=0.8, ls="--")
    ax.text(ha_nd / 1e6 * 2.3 + 0.1, 8, "Tb-rich shell\n(~2.3× $H_A$ by the\nsame 1984 method)", fontsize=7, color=C[3])
    ax.set_xlabel("anisotropy field $H_A$ (MA/m)"); ax.set_ylabel("coercivity $H_c$ (MA/m)")
    ax.set_title("Real coercivity is a fraction of $H_A$: raise $H_A$ where nucleation starts")
    ax.set_ylim(0, 10)
    ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False)
    fig.set_size_inches(5.2, 4.0)
    save(fig, "f05_kronmuller")


# 6. Grain-boundary diffusion: erfc profiles and the thickness limit -------------------------
def fig_gbd_profile():
    x = np.linspace(0, 3e-3, 300)
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    d = 2.5e-13  # m^2/s, illustrative effective grain-boundary diffusivity
    for hours, col in zip([1, 4, 16], [C[0], C[2], C[1]]):
        c = m.erfc_profile(x, d, hours * 3600)
        ax.plot(x * 1e3, c, color=col, lw=1.8, label=f"$t$ = {hours} h")
    ax.axvspan(0.3, 1.0, color=C[3], alpha=0.12)
    ax.text(0.32, 0.85, "Lu et al. 2019: uniform\ncore-shell layer 300 to 1000 µm", fontsize=7, color=C[3])
    ax.set_xlabel("depth from coated surface (mm)"); ax.set_ylabel("$C/C_0$ of heavy rare earth along grain boundaries")
    ax.set_title(r"Diffusion depth grows as $\sqrt{Dt}$: GBD suits thin magnets")
    ax.legend(fontsize=7)
    ax.text(1.6, 0.55, "erfc solution, constant surface source;\n$D$ illustrative (2.5e-13 m²/s)", fontsize=7, alpha=0.8)
    save(fig, "f06_gbd_profile")


# 7. Motor scaling: magnet mass vs gear ratio; torque density vs gap radius --------------------
def fig_motor_scaling():
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.1))
    n = np.linspace(4, 100, 200)
    joint_torque = 100.0  # N m, a hip-class joint
    mass = np.array([m.magnet_mass_for_joint(joint_torque, g, kg_per_nm_motor=0.006) for g in n])
    axs[0].plot(n, mass * 1e3, color=C[0], lw=2)
    for g, lab in [(6, "quasi-direct drive"), (50, "harmonic / cycloidal")]:
        mm = m.magnet_mass_for_joint(joint_torque, g, 0.006) * 1e3
        axs[0].scatter([g], [mm], color=C[1], zorder=5); axs[0].annotate(f"{lab}\nN={g}: {mm:.0f} g", (g, mm), xytext=(g + 6, mm + 15), fontsize=7)
    axs[0].set_xlabel("gear ratio N"); axs[0].set_ylabel("magnet mass per joint (g), 100 N m joint")
    axs[0].set_title("Magnet mass ∝ 1/N at fixed shear stress")
    r = np.linspace(10, 60, 100)
    axs[1].plot(r, (r / 10) ** CONSTANTS["torque_density_exponent"], color=C[2], lw=2, label=r"empirical $\propto r_g^{0.8}$ (Wensing 2017)")
    axs[1].plot(r, (r / 10) ** 1.0, color="k", ls=":", lw=1, label=r"dimensional $\propto r_g$")
    axs[1].set_xlabel("gap radius $r_g$ (mm)"); axs[1].set_ylabel("torque density (relative)")
    axs[1].set_title("Bigger gap radius, more torque per kg"); axs[1].legend(fontsize=7)
    save(fig, "f07_motor_scaling")


# 8. Fenske stage count vs separation factor with the P507 / D2EHPA pairs ------------------------
def fig_fenske():
    beta = np.linspace(1.04, 3.0, 300)
    fig, ax = plt.subplots(figsize=(5.6, 3.5))
    for purity, col, ls in [(0.999, C[0], "-"), (0.99, C[2], "--")]:
        ax.plot(beta, [m.fenske_stages(b, purity, 1 - purity) for b in beta], color=col, lw=1.8, ls=ls,
                label=f"{purity*100:.1f} % purity both ends")
    items = sorted(CONSTANTS["beta_P507"].items(), key=lambda kv: kv[1])
    for i, (pair, b) in enumerate(items):
        n = m.fenske_stages(b, 0.999, 0.001)
        ax.scatter([b], [n], color=C[1], s=14, zorder=5)
        dx, dy = (4, 4) if i % 2 == 0 else (4, -9)
        ax.annotate(pair, (b, n), xytext=(dx, dy), textcoords="offset points", fontsize=6.5, color=C[1])
    ax.set_yscale("log"); ax.set_ylim(5, 400)
    ax.set_xlabel("separation factor β, adjacent pairs (P507 / EHEHPA in HCl; Ismail et al. 2019)")
    ax.set_ylabel("minimum theoretical stages (Fenske, total reflux)")
    ax.set_title("Why the middle of the lanthanide row costs the most stages")
    ax.legend(fontsize=7)
    save(fig, "f08_fenske")


# 9. Dysprosium tonnes per year: robot demand vs Western supply ------------------------------------
def fig_dy_arithmetic():
    rows = CONSTANTS["dy_rows"]
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    y = np.arange(len(rows))[::-1]
    for yi, (lab, lo, hi) in zip(y, rows):
        mid = (lo + hi) / 2
        col = C[1] if "humanoid" in lab else (C[2] if "Energy Fuels" in lab else C[5])
        ax.plot([lo, hi], [yi, yi], color=col, lw=6, alpha=0.35) if lo != hi else None
        ax.scatter([mid], [yi], color=col, s=40, zorder=5)
        ax.text(hi * 1.15, yi, f"{lo:g}" if lo == hi else f"{lo:g} to {hi:g}", va="center", fontsize=8)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=8)
    ax.set_xscale("log"); ax.set_xlim(20, 8000)
    ax.set_xlabel("dysprosium, tonnes per year (log scale)")
    ax.set_title("The dysprosium arithmetic, tonnes per year")
    save(fig, "f09_dy_arithmetic")


# 10. Hysteresis loop anatomy ---------------------------------------------------------------------
def fig_loop_anatomy():
    h = np.linspace(-2.2e6, 2.2e6, 800)
    br, hcj = 1.3, 1.1e6
    j_up = br * np.tanh(3.0 * (h + hcj) / hcj)
    j_dn = br * np.tanh(3.0 * (h - hcj) / hcj)
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.plot(m.tesla(h), j_up, color=C[0], lw=1.8, label="J(H), intrinsic")
    ax.plot(m.tesla(h), j_dn, color=C[0], lw=1.8)
    ax.plot(m.tesla(h), j_up + m.MU0 * h, color=C[1], lw=1.2, ls="--", label=r"B(H) = J + $\mu_0$H")
    ax.plot(m.tesla(h), j_dn + m.MU0 * h, color=C[1], lw=1.2, ls="--")
    ax.axhline(0, color="k", lw=0.6); ax.axvline(0, color="k", lw=0.6)
    ax.annotate("$B_r$ (remanence)", (0, br), xytext=(0.3, 1.5), fontsize=8, arrowprops=dict(arrowstyle="->"))
    ax.annotate("$H_{cj}$ (intrinsic coercivity)", (-m.tesla(hcj), 0), xytext=(-2.6, -0.8), fontsize=8, arrowprops=dict(arrowstyle="->"))
    b_up = j_up + m.MU0 * h
    i_cb = int(np.argmin(np.abs(b_up[h < 0])))  # numerical zero crossing of B on the descending branch
    ax.annotate("$H_{cb}$ (B crosses zero)", (m.tesla(h[h < 0][i_cb]), 0), xytext=(-2.6, 0.9), fontsize=8, arrowprops=dict(arrowstyle="->"))
    ax.set_xlabel(r"$\mu_0 H$ (T)"); ax.set_ylabel("J, B (T)")
    ax.set_title("Anatomy of a hard magnet's loop")
    ax.legend(fontsize=7, loc="lower right"); ax.set_xlim(-2.8, 2.8); ax.set_ylim(-2.0, 2.0)
    save(fig, "f10_loop_anatomy")


if __name__ == "__main__":
    for f in [fig_energy_product, fig_demag_temperature, fig_safe_temperature, fig_temp_coefficients,
              fig_kronmuller, fig_gbd_profile, fig_motor_scaling, fig_fenske, fig_dy_arithmetic, fig_loop_anatomy]:
        f()
        print("wrote", f.__name__)
    # numbers quoted in the text, printed so the manuscript can be checked against them
    print("BHmax ideal at Js=1.60 T:", m.bh_max_ideal(1.60) / 1e3, "kJ/m3")
    print("HA Nd2Fe14B:", m.anisotropy_field(4.3e6, 1.28e6) / 1e6, "MA/m =", m.tesla(m.anisotropy_field(4.3e6, 1.28e6)), "T")
    print("Fenske Pr/Nd 1.17:", m.fenske_stages(1.17, 0.999, 0.001), " Tb/Dy 1.62:", m.fenske_stages(1.62, 0.999, 0.001),
          " Ho/Er 1.25:", m.fenske_stages(1.25, 0.999, 0.001), " Dy/Ho 2.58:", m.fenske_stages(2.58, 0.999, 0.001))
    for g, (k, _) in CONSTANTS["grades"].items():
        br = {"N": 1.40, "M": 1.37, "H": 1.35, "SH": 1.32, "UH": 1.28, "EH": 1.25, "AH": 1.22}[g]
        print(g, "Pc=2 safe T:", m.max_safe_temperature(br, m.koe_to_am(k), 2.0, (-0.006 if g == "N" else -0.0055), margin=1.2))
