"""Tests for BOM generation."""

from pathlib import Path

from jetx.fixture.bom import build_bom, save_bom_csv
from jetx.fixture.geometry import BracketGeometry


def test_bom_has_expected_columns_and_bracket_line_item():
    geom = BracketGeometry()
    df = build_bom(geom)
    assert {"item", "part_number", "description", "qty", "material", "unit_mass_kg", "extended_mass_kg"}.issubset(
        df.columns
    )
    bracket_row = df[df["part_number"] == "JX-FIX-001"].iloc[0]
    assert bracket_row["unit_mass_kg"] > 0.0
    assert bracket_row["qty"] == 1


def test_extended_mass_equals_qty_times_unit_mass():
    df = build_bom(BracketGeometry())
    for _, row in df.iterrows():
        assert row["extended_mass_kg"] == round(row["qty"] * row["unit_mass_kg"], 4)


def test_save_bom_csv_writes_file(tmp_path: Path):
    output_path = tmp_path / "bom.csv"
    result_path = save_bom_csv(BracketGeometry(), output_path)
    assert result_path.exists()
    assert "part_number" in result_path.read_text()
