"""Smoke test: the worked example runs end to end and prints its headline table."""
from __future__ import annotations

import runpy
from pathlib import Path

EXAMPLE = Path(__file__).parent.parent / "examples" / "full_chain_worked_example.py"


def test_full_chain_example_runs(capsys):
    runpy.run_path(str(EXAMPLE), run_name="__main__")
    out = capsys.readouterr().out
    assert "Barsana Phase I scale" in out
    assert "Digestate (Fermented Organic Manure)" in out
