"""Tests for the parametric bracket geometry model."""

import pytest

from jetx.fixture.geometry import AL_6061_T6, BracketGeometry


def test_default_geometry_is_valid():
    geom = BracketGeometry()
    assert geom.plate_area_mm2 > 0.0
    assert geom.mass_kg > 0.0


def test_bolt_hole_edge_margin_below_diameter_raises():
    with pytest.raises(ValueError):
        BracketGeometry(bolt_hole_diameter_mm=10.0, bolt_hole_edge_margin_mm=5.0)


def test_fillet_radius_too_large_raises():
    with pytest.raises(ValueError):
        BracketGeometry(length_mm=50.0, width_mm=40.0, corner_fillet_radius_mm=25.0)


def test_bolt_hole_centers_are_symmetric_about_origin():
    geom = BracketGeometry()
    centers = geom.bolt_hole_centers_mm
    assert len(centers) == 4
    xs = sorted({round(c[0], 6) for c in centers})
    ys = sorted({round(c[1], 6) for c in centers})
    assert xs[0] == pytest.approx(-xs[1])
    assert ys[0] == pytest.approx(-ys[1])


def test_mass_scales_with_thickness():
    thin = BracketGeometry(thickness_mm=6.0)
    thick = BracketGeometry(thickness_mm=12.0)
    assert thick.mass_kg == pytest.approx(2.0 * thin.mass_kg, rel=1e-9)


def test_mass_uses_material_density():
    al = BracketGeometry(material=AL_6061_T6)
    from jetx.fixture.geometry import STEEL_4130

    steel = BracketGeometry(material=STEEL_4130)
    assert steel.mass_kg > al.mass_kg


def test_bearing_stress_and_safety_factor_are_consistent():
    geom = BracketGeometry()
    stress = geom.bearing_stress_mpa(applied_load_n=5000.0)
    sf = geom.safety_factor(applied_load_n=5000.0)
    assert stress > 0.0
    assert sf == pytest.approx(geom.material.yield_strength_mpa / stress)


def test_higher_load_reduces_safety_factor():
    geom = BracketGeometry()
    sf_low_load = geom.safety_factor(2000.0)
    sf_high_load = geom.safety_factor(8000.0)
    assert sf_high_load < sf_low_load
