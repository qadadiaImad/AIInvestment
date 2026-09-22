"""Tests for the physics helpers behind the physical-AI magnet lesson figures."""
import math

import numpy as np
import pytest

from lesson import magnetics as m

MU0 = 4 * math.pi * 1e-7


def test_ideal_energy_product_is_br_squared_over_4mu0():
    # Br = 1.4 T -> 1.96 / (4 * 1.2566e-6) = 389.97 kJ/m3
    assert m.bh_max_ideal(1.4) == pytest.approx(389_968, rel=1e-3)


def test_energy_product_curve_never_exceeds_ideal_bound():
    br = 1.3
    h, b, bh = m.demag_curve(br, hcb=900e3, mu_r=1.05)
    assert bh.max() <= m.bh_max_ideal(br) * (1 + 1e-9)
    assert bh.max() > 0.9 * m.bh_max_ideal(br)  # near-ideal linear magnet


def test_anisotropy_field_matches_hirosawa_2017_nd2fe14b():
    # K1 = 4.3 MJ/m3, Ms = 1.28 MA/m  ->  HA = 5.33 MA/m (Hirosawa et al. 2017, Table 1)
    ha = m.anisotropy_field(k1=4.3e6, ms=1.28e6)
    assert ha == pytest.approx(5.33e6, rel=0.01)
    assert m.tesla(ha) == pytest.approx(6.7, rel=0.02)


def test_koe_conversion():
    assert m.koe_to_am(1.0) == pytest.approx(79_577, rel=1e-4)
    assert m.am_to_koe(m.koe_to_am(12.0)) == pytest.approx(12.0)


def test_operating_point_on_load_line():
    # Pc = 1, mu_r = 1: B = Br/2, H = -Br/(2 mu0)
    b, h = m.operating_point(br=1.2, pc=1.0, mu_r=1.0)
    assert b == pytest.approx(0.6)
    assert h == pytest.approx(-0.6 / MU0)


def test_temperature_scaling_signs_and_magnitude():
    # alpha = -0.12 %/K, beta = -0.6 %/K, +100 K
    assert m.at_temperature(1.4, -0.0012, 120, t_ref=20) == pytest.approx(1.4 * 0.88)
    assert m.at_temperature(1.6e6, -0.006, 120, t_ref=20) == pytest.approx(1.6e6 * 0.40)


def test_kronmuller_coercivity_linear_form():
    # Hc = alpha * HA - Neff * Ms
    assert m.kronmuller_hc(ha=5.33e6, ms=1.28e6, alpha=0.4, neff=0.8) == pytest.approx(
        0.4 * 5.33e6 - 0.8 * 1.28e6
    )


def test_fenske_minimum_stages():
    # beta = 1.17 (Pr/Nd, EHEHPA), 99.9 % both ends -> ln(999^2)/ln(1.17) = 87.9
    n = m.fenske_stages(beta=1.17, x_top=0.999, x_bottom=0.001)
    assert n == pytest.approx(87.9, rel=0.01)
    # higher separation factor -> fewer stages
    assert m.fenske_stages(1.62, 0.999, 0.001) < n


def test_erfc_profile_boundary_conditions():
    x = np.array([0.0, 1e-3, 1e-2])
    c = m.erfc_profile(x, d=1e-13, t=3600 * 10, c0=1.0)
    assert c[0] == pytest.approx(1.0)
    assert c[-1] < 1e-6
    assert np.all(np.diff(c) < 0)


def test_shear_stress_torque_scales_with_radius_squared():
    t1 = m.torque_from_shear(rg=0.02, length=0.03, sigma=20e3)
    t2 = m.torque_from_shear(rg=0.04, length=0.03, sigma=20e3)
    assert t2 / t1 == pytest.approx(4.0)


def test_magnet_mass_falls_with_gear_ratio():
    m6 = m.magnet_mass_for_joint(joint_torque=100.0, gear_ratio=6, kg_per_nm_motor=0.01)
    m50 = m.magnet_mass_for_joint(joint_torque=100.0, gear_ratio=50, kg_per_nm_motor=0.01)
    assert m6 / m50 == pytest.approx(50 / 6)


def test_max_temperature_before_knee():
    # A magnet whose room-temperature Hcj is 12 kOe (N grade) on a Pc = 2 load line
    # should lose its safety margin well before 150 C; an SH-like 20 kOe one should not.
    t_n = m.max_safe_temperature(br=1.4, hcj_ref=m.koe_to_am(12), pc=2.0, beta=-0.006, margin=1.2)
    t_sh = m.max_safe_temperature(br=1.3, hcj_ref=m.koe_to_am(20), pc=2.0, beta=-0.0055, margin=1.2)
    assert t_n < 150 < t_sh
