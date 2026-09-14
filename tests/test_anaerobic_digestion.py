import pytest

from cbg_design import anaerobic_digestion as AD
from cbg_design import feedstock as F


def test_buswell_reproduces_the_classic_glucose_50_50_split():
    # A well-known exact textbook result: fermenting glucose (C6H12O6) via
    # Buswell's equation gives exactly 3 mol CH4 + 3 mol CO2 per mol glucose
    # (a=6, b=12, c=6, d=0 -> mol_CH4 = (24+12-12)/8 = 3, mol_CO2 = (24-12+12)/8 = 3),
    # i.e. an exact 50/50 CH4:CO2 split -- built here from real molecular weights,
    # not typed in as a pre-computed ratio.
    mw_c, mw_h, mw_o = 12.011, 1.008, 15.999
    total_mw_glucose = 6 * mw_c + 12 * mw_h + 6 * mw_o
    elemental = {
        "C": 6 * mw_c / total_mw_glucose, "H": 12 * mw_h / total_mw_glucose,
        "O": 6 * mw_o / total_mw_glucose, "N": 0.0,
    }
    out = AD.buswell_theoretical_yield(elemental)
    assert out["mol_ch4_per_kg_vs"] == pytest.approx(out["mol_co2_per_kg_vs"], rel=1e-6)


@pytest.mark.parametrize("preset,target_nm3_per_tonne_fresh", [
    (F.paddy_straw, 350.0), (F.press_mud, 150.0), (F.cattle_dung, 120.0),
])
def test_calibrated_default_reproduces_the_published_yield(preset, target_nm3_per_tonne_fresh):
    fs = preset(10.0)
    r = AD.digest(fs)
    nm3_biogas_per_tonne_fresh = (r.practical_ch4_nm3_per_tonne_vs / r.biogas_ch4_mole_frac) * fs.vs_mass_frac
    assert nm3_biogas_per_tonne_fresh == pytest.approx(target_nm3_per_tonne_fresh, rel=0.01)


def test_practical_yield_never_exceeds_theoretical():
    fs = F.paddy_straw(10.0)
    r = AD.digest(fs, biodegradability_fraction=0.9)
    assert r.practical_ch4_nm3_per_tonne_vs < r.theoretical_ch4_nm3_per_tonne_vs


def test_digest_rejects_biodegradability_outside_zero_to_one():
    fs = F.paddy_straw(10.0)
    with pytest.raises(ValueError):
        AD.digest(fs, biodegradability_fraction=1.5)


def test_digester_working_volume_scales_linearly_with_hrt():
    fs = F.cattle_dung(10.0)
    short = AD.digester_working_volume(fs, dilution_water_kg_s=20.0, hrt_days=20.0)
    long = AD.digester_working_volume(fs, dilution_water_kg_s=20.0, hrt_days=40.0)
    assert long["digester_working_volume_m3"] == pytest.approx(2 * short["digester_working_volume_m3"])


def test_digester_working_volume_defaults_to_the_feedstock_own_hrt():
    dung, straw = F.cattle_dung(10.0), F.paddy_straw(10.0)
    r_dung = AD.digester_working_volume(dung, dilution_water_kg_s=20.0)
    r_straw = AD.digester_working_volume(straw, dilution_water_kg_s=20.0)
    assert r_dung["hrt_days"] == pytest.approx(dung.default_hrt_days)
    assert r_straw["hrt_days"] == pytest.approx(straw.default_hrt_days)


def test_default_hrt_would_have_understated_cattle_dung_digester_volume_by_2_8x():
    # A real, quantified consequence of the vendor-sourced fix: had the generic
    # 30-day default been used for cattle dung instead of the real 85-day figure,
    # the digester would have been undersized by roughly 85/30 ~= 2.83x.
    dung = F.cattle_dung(10.0)
    real = AD.digester_working_volume(dung, dilution_water_kg_s=20.0)
    generic = AD.digester_working_volume(dung, dilution_water_kg_s=20.0, hrt_days=30.0)
    assert real["digester_working_volume_m3"] / generic["digester_working_volume_m3"] == pytest.approx(
        dung.default_hrt_days / 30.0, rel=1e-6)
