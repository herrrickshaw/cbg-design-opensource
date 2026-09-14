import pytest

from cbg_design import anaerobic_digestion as AD
from cbg_design import digestate as DG
from cbg_design import feedstock as F


def test_digestate_plus_biogas_mass_conserves_total_feed():
    fs = F.cattle_dung(10.0)
    r = AD.digest(fs)
    dilution = 20.0
    dg = DG.characterize_digestate(fs, r, dilution_water_kg_s=dilution)

    ch4_kmol_s = r.ch4_flow_nm3_s / 22.414
    co2_kmol_s = ch4_kmol_s * (1 - r.biogas_ch4_mole_frac) / r.biogas_ch4_mole_frac
    biogas_mass_kg_s = ch4_kmol_s * 16.043 + co2_kmol_s * 44.01

    total_feed = fs.mass_flow_kg_s + dilution
    assert dg.digestate_mass_flow_kg_s + biogas_mass_kg_s == pytest.approx(total_feed, rel=1e-6)


def test_solids_content_is_between_zero_and_one():
    fs = F.paddy_straw(10.0)
    r = AD.digest(fs)
    dg = DG.characterize_digestate(fs, r, dilution_water_kg_s=30.0)
    assert 0 < dg.solids_content_mass_frac < 1


def test_vs_destroyed_matches_biodegradability_fraction():
    fs = F.press_mud(10.0)
    r = AD.digest(fs)
    dg = DG.characterize_digestate(fs, r, dilution_water_kg_s=25.0)
    expected = fs.mass_flow_kg_s * fs.vs_mass_frac * r.biodegradability_fraction
    assert dg.vs_destroyed_kg_s == pytest.approx(expected, rel=1e-6)
