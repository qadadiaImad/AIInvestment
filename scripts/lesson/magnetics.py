"""Small, testable physics helpers for the magnet lesson.

Everything here is textbook magnetostatics and process engineering; the point is that
every number printed in the lesson comes out of a function that has a unit test, not
out of prose. SI units throughout unless a name says otherwise.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import erfc

MU0 = 4 * math.pi * 1e-7  # H/m
KOE_TO_AM = 1e6 / (4 * math.pi)  # 1 kOe = 79.577 kA/m


def koe_to_am(koe: float) -> float:
    return koe * KOE_TO_AM


def am_to_koe(am: float) -> float:
    return am / KOE_TO_AM


def tesla(h_am: float) -> float:
    """mu0 * H, i.e. a field in A/m expressed as a flux density in tesla."""
    return MU0 * h_am


# --- energy product ------------------------------------------------------------------

def bh_max_ideal(br: float) -> float:
    """Upper bound on (BH)max for a square-loop magnet: Br^2 / (4 mu0), in J/m3."""
    return br**2 / (4 * MU0)


def demag_curve(br: float, hcb: float, mu_r: float = 1.05, n: int = 400):
    """Second-quadrant B(H) for a linear magnet with recoil permeability mu_r.

    Returns (H, B, -B*H) arrays with H from -Hcb to 0 (A/m). Hcb is where B crosses zero,
    so B(H) = Br + mu0*mu_r*H is clipped at that point.
    """
    h = np.linspace(-hcb, 0.0, n)
    b = np.clip(br + MU0 * mu_r * h, 0.0, None)
    return h, b, -b * h


# --- anisotropy and coercivity --------------------------------------------------------

def anisotropy_field(k1: float, ms: float) -> float:
    """H_A = 2 K1 / (mu0 Ms) in A/m (K1 in J/m3, Ms in A/m)."""
    return 2 * k1 / (MU0 * ms)


def kronmuller_hc(ha: float, ms: float, alpha: float, neff: float) -> float:
    """Kronmuller nucleation model: Hc = alpha * H_A - N_eff * Ms (all A/m)."""
    return alpha * ha - neff * ms


# --- operating point and temperature ---------------------------------------------------

def operating_point(br: float, pc: float, mu_r: float = 1.05):
    """Intersection of the load line B = -mu0*Pc*H with B = Br + mu0*mu_r*H.

    Returns (B in T, H in A/m). Pc is the permeance coefficient of the circuit.
    """
    h = -br / (MU0 * (pc + mu_r))
    b = br * pc / (pc + mu_r)
    return b, h


def at_temperature(value_ref: float, coeff_per_k: float, t_c: float, t_ref: float = 20.0) -> float:
    """Linear reversible temperature scaling: X(T) = X_ref * (1 + coeff*(T - T_ref))."""
    return value_ref * (1 + coeff_per_k * (t_c - t_ref))


def max_safe_temperature(br: float, hcj_ref: float, pc: float, beta: float,
                         alpha: float = -0.0012, margin: float = 1.2, mu_r: float = 1.05,
                         t_ref: float = 20.0, t_max: float = 300.0) -> float:
    """Highest temperature at which |H_operating| * margin < Hcj(T).

    A crude knee criterion: treats Hcj(T) as the demagnetisation threshold and asks the
    operating field on the load line (which also moves with Br(T)) to stay a `margin`
    below it. Returns t_max if the criterion never fails.
    """
    for t in np.arange(t_ref, t_max, 0.5):
        br_t = at_temperature(br, alpha, t, t_ref)
        hcj_t = at_temperature(hcj_ref, beta, t, t_ref)
        _, h = operating_point(br_t, pc, mu_r)
        if abs(h) * margin >= hcj_t:
            return float(t)
    return float(t_max)


# --- separation ---------------------------------------------------------------------------

def fenske_stages(beta: float, x_top: float, x_bottom: float) -> float:
    """Fenske minimum theoretical stages for a binary split at total reflux.

    N = ln[(x_top/(1-x_top)) * ((1-x_bottom)/x_bottom)] / ln(beta).
    Used here as the counter-current solvent-extraction analogue with beta = separation
    factor between two adjacent lanthanides.
    """
    return math.log((x_top / (1 - x_top)) * ((1 - x_bottom) / x_bottom)) / math.log(beta)


# --- diffusion ----------------------------------------------------------------------------

def erfc_profile(x, d: float, t: float, c0: float = 1.0):
    """Semi-infinite constant-surface-source solution: C(x,t) = C0 erfc(x / (2 sqrt(D t)))."""
    x = np.asarray(x, dtype=float)
    return c0 * erfc(x / (2 * math.sqrt(d * t)))


# --- motors -------------------------------------------------------------------------------

def torque_from_shear(rg: float, length: float, sigma: float) -> float:
    """tau = 2 pi rg^2 l sigma: air-gap shear stress sigma (Pa) on a rotor of radius rg, length l."""
    return 2 * math.pi * rg**2 * length * sigma


def magnet_mass_for_joint(joint_torque: float, gear_ratio: float, kg_per_nm_motor: float) -> float:
    """Magnet mass needed if the motor must supply joint_torque / gear_ratio at constant shear
    stress (magnet volume, and so mass, scales linearly with motor torque)."""
    return joint_torque / gear_ratio * kg_per_nm_motor
