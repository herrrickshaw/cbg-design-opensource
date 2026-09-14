import pytest

from cbg_design import feedstock as F


def test_presets_carry_their_published_yield_and_calibrated_biodegradability():
    straw = F.paddy_straw(10.0)
    assert straw.specific_biogas_yield_nm3_per_tonne_fresh == pytest.approx(350.0)
    assert 0.4 < straw.default_biodegradability_fraction < 0.6

    dung = F.cattle_dung(10.0)
    press = F.press_mud(10.0)
    # The real, counter-to-naive-intuition finding: already-processed residues
    # (press mud, cattle dung) calibrate to LOWER biodegradability than fresh straw.
    assert dung.default_biodegradability_fraction < straw.default_biodegradability_fraction
    assert press.default_biodegradability_fraction < straw.default_biodegradability_fraction


def test_co_digestion_mix_is_mass_weighted():
    straw = F.paddy_straw(10.0)
    dung = F.cattle_dung(10.0)
    mix = F.co_digestion_mix([straw, dung], [0.5, 0.5])
    assert mix.vs_mass_frac == pytest.approx(0.5 * straw.vs_mass_frac + 0.5 * dung.vs_mass_frac)
    assert mix.default_biodegradability_fraction == pytest.approx(
        0.5 * straw.default_biodegradability_fraction + 0.5 * dung.default_biodegradability_fraction)


def test_co_digestion_mix_rejects_shares_not_summing_to_one():
    straw = F.paddy_straw(10.0)
    dung = F.cattle_dung(10.0)
    with pytest.raises(ValueError):
        F.co_digestion_mix([straw, dung], [0.5, 0.6])


def test_co_digestion_mix_rejects_mismatched_lengths():
    straw = F.paddy_straw(10.0)
    with pytest.raises(ValueError):
        F.co_digestion_mix([straw], [0.5, 0.5])
