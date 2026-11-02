"""Characterisation test: every public numeric output must match the values
captured from the original (pre-refactor) code in tests/golden_baseline.json."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from cbg_design import anaerobic_digestion as AD
from cbg_design import compression_storage as CS
from cbg_design import digestate as DG
from cbg_design import feedstock as F
from cbg_design import properties as P
from cbg_design import upgrading as U

GOLDEN = json.loads((Path(__file__).parent / "golden_baseline.json").read_text())


def _flat(o):
    return dataclasses.asdict(o) if dataclasses.is_dataclass(o) else o


def _current() -> dict:
    out = {}
    feeds = {"paddy_straw": F.paddy_straw(2.6), "press_mud": F.press_mud(2.6), "cattle_dung": F.cattle_dung(2.6)}
    feeds["mix"] = F.co_digestion_mix([F.paddy_straw(1.0), F.cattle_dung(1.5)], [0.4, 0.6])
    for k, f in feeds.items():
        out[f"feed.{k}"] = _flat(f)
        out[f"bus.{k}"] = AD.buswell_theoretical_yield(f.elemental_composition)
        dg = AD.digest(f)
        out[f"dig.{k}"] = _flat(dg)
        out[f"dig_override.{k}"] = _flat(AD.digest(f, 0.4))
        out[f"vol.{k}"] = AD.digester_working_volume(f, f.mass_flow_kg_s * 2)
        out[f"vol_hrt.{k}"] = AD.digester_working_volume(f, 1.0, hrt_days=20.0, slurry_density_kg_m3=1050.0)
        out[f"dgs.{k}"] = _flat(DG.characterize_digestate(f, dg, f.mass_flow_kg_s * 2))
        for t in U.TECHNOLOGY_SPECIFIC_POWER_KWH_PER_NM3:
            out[f"up.{k}.{t}"] = _flat(U.upgrade_biogas(dg.biogas_flow_nm3_s, dg.biogas_ch4_mole_frac, technology=t))
    out["up_custom"] = _flat(U.upgrade_biogas(0.5, 0.6, "psa", 0.25, 0.01, 0.95))
    gases = {"raw": P.raw_biogas(), "raw55": P.raw_biogas(0.55), "cbg": P.cbg_product(), "cbg92": P.cbg_product(0.92)}
    for name, g in gases.items():
        out[f"prop.{name}"] = {"mw": g.molecular_weight(), "rho": g.density(313.15, 250e5),
                               "Z": g.compressibility(313.15, 250e5), "rho1": g.density(300.0, 1.5e5)}
        out[f"comp.{name}"] = _flat(CS.compress_to_cbg_pressure(g, 0.25, 1.5e5))
        out[f"comp3.{name}"] = _flat(CS.compress_to_cbg_pressure(g, 0.1, 2e5, 200e5, 300.0, 3, 0.8))
        out[f"store.{name}"] = CS.cascade_storage_volume(g, 1000.0)
        out[f"store2.{name}"] = CS.cascade_storage_volume(g, 500.0, 200e5, 300.0)
    out["consts"] = [P.MW_METHANE, P.MW_CO2, P.MW_AIR, AD.MOLAR_VOLUME_NM3_PER_KMOL,
                     DG.MW_CH4_KG_KMOL, U.IS_16087_MIN_CH4_MOLE_FRAC]
    return json.loads(json.dumps(out))


def _assert_same(path: str, got, want) -> None:
    if isinstance(want, dict):
        assert got.keys() == want.keys(), path
        for k in want:
            _assert_same(f"{path}.{k}", got[k], want[k])
    elif isinstance(want, list):
        assert len(got) == len(want), path
        for i, (g, w) in enumerate(zip(got, want)):
            _assert_same(f"{path}[{i}]", g, w)
    elif isinstance(want, float):
        assert got == pytest.approx(want, rel=1e-9), path
    else:
        assert got == want, path


def test_outputs_identical_to_pre_refactor_baseline():
    _assert_same("root", _current(), GOLDEN)
