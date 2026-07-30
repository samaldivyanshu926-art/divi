"""Tests for the minimal DXF exporter."""

from pathlib import Path

from jetx.fixture.dxf_export import build_bracket_dxf, export_bracket_dxf
from jetx.fixture.geometry import BracketGeometry


def test_dxf_string_has_valid_section_structure():
    geom = BracketGeometry()
    writer = build_bracket_dxf(geom)
    text = writer.to_string()
    assert text.startswith("0\nSECTION\n2\nENTITIES\n")
    assert text.rstrip().endswith("0\nENDSEC\n0\nEOF")
    assert text.count("0\nLINE\n") == 4  # four straight edges
    assert text.count("0\nARC\n") == 4  # four corner fillets
    assert text.count("0\nCIRCLE\n") == 5  # four bolt holes + one clevis bore


def test_export_bracket_dxf_writes_file(tmp_path: Path):
    geom = BracketGeometry()
    output_path = tmp_path / "bracket.dxf"
    result_path = export_bracket_dxf(geom, output_path)
    assert result_path.exists()
    content = result_path.read_text()
    assert "ENTITIES" in content
    assert "EOF" in content
