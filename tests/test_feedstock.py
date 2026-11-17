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


def test_cattle_dung_uses_the_real_vendor_sourced_longer_hrt():
    # WELTEC BIOPOWER's own published digester spec: retention "can be as long
    # as 80-90 days if the manure content is high" -- see docs/VENDOR_REFERENCE.md.
    # Confirms the same finding as the biodegradability calibration, independently,
    # in a second real design parameter: manure needs longer, not just less complete, digestion.
    dung, straw, press = F.cattle_dung(10.0), F.paddy_straw(10.0), F.press_mud(10.0)
    assert dung.default_hrt_days > straw.default_hrt_days
    assert dung.default_hrt_days > press.default_hrt_days
    assert 80.0 <= dung.default_hrt_days <= 90.0
    assert straw.default_hrt_days == pytest.approx(30.0)
    assert press.default_hrt_days == pytest.approx(30.0)


def test_co_digestion_mix_is_mass_weighted():
    straw = F.paddy_straw(10.0)
    dung = F.cattle_dung(10.0)
    mix = F.co_digestion_mix([straw, dung], [0.5, 0.5])
    assert mix.vs_mass_frac == pytest.approx(0.5 * straw.vs_mass_frac + 0.5 * dung.vs_mass_frac)
    # Biodegradability is a fraction of each stream's CH4 potential, so it blends on
    # VS mass x theoretical CH4 per kg VS, not on fresh mass (the earlier fresh-mass
    # expectation here contradicted methane conservation -- see the sum-of-parts test).
    from cbg_design.anaerobic_digestion import buswell_theoretical_yield as B
    w_s = 0.5 * straw.vs_mass_frac * B(straw.elemental_composition)["mol_ch4_per_kg_vs"]
    w_d = 0.5 * dung.vs_mass_frac * B(dung.elemental_composition)["mol_ch4_per_kg_vs"]
    assert mix.default_biodegradability_fraction == pytest.approx(
        (w_s * straw.default_biodegradability_fraction + w_d * dung.default_biodegradability_fraction) / (w_s + w_d))
    assert mix.default_hrt_days == pytest.approx(0.5 * straw.default_hrt_days + 0.5 * dung.default_hrt_days)


def test_co_digestion_mix_rejects_shares_not_summing_to_one():
    straw = F.paddy_straw(10.0)
    dung = F.cattle_dung(10.0)
    with pytest.raises(ValueError):
        F.co_digestion_mix([straw, dung], [0.5, 0.6])


def test_co_digestion_mix_rejects_mismatched_lengths():
    straw = F.paddy_straw(10.0)
    with pytest.raises(ValueError):
        F.co_digestion_mix([straw], [0.5, 0.5])


# --- Co-digestion blending must conserve methane. The mix model explicitly does
# NOT add co-digestion synergy, so digesting a straw+dung mix must give exactly
# the CH4 of digesting each stream on its own (sum of parts). Elemental
# composition and biodegradability are per-kg-VS quantities, so they have to be
# blended on VS mass (and biodegradability on methane potential), not on fresh mass.

from cbg_design import anaerobic_digestion as AD  # noqa: E402


@pytest.mark.parametrize("straw_share", [0.2, 0.5, 0.8])
def test_co_digestion_mix_conserves_methane_sum_of_parts(straw_share):
    total = 2.6  # kg/s fresh, ~225 t/day
    straw = F.paddy_straw(total * straw_share)
    dung = F.cattle_dung(total * (1 - straw_share))
    mix = F.co_digestion_mix([straw, dung], [straw_share, 1 - straw_share])
    parts = AD.digest(straw).ch4_flow_nm3_s + AD.digest(dung).ch4_flow_nm3_s
    assert AD.digest(mix).ch4_flow_nm3_s == pytest.approx(parts, rel=1e-9)


def test_co_digestion_mix_biogas_matches_its_own_blended_specific_yield():
    # Each preset's biodegradability is calibrated to its published Nm3 biogas / t fresh,
    # so a 50/50 mix must produce the 50/50 blend of those yields (235 Nm3/t) to within
    # the small CH4:CO2-split mixing effect (<1 %).
    straw, dung = F.paddy_straw(0.5), F.cattle_dung(0.5)
    mix = F.co_digestion_mix([straw, dung], [0.5, 0.5])
    per_t = AD.digest(mix).biogas_flow_nm3_s / mix.mass_flow_kg_s * 1000.0
    assert per_t == pytest.approx(0.5 * 350.0 + 0.5 * 120.0, rel=0.01)


def test_co_digestion_mix_elements_are_vs_weighted():
    straw, dung = F.paddy_straw(0.5), F.cattle_dung(0.5)
    mix = F.co_digestion_mix([straw, dung], [0.5, 0.5])
    # C: (0.5*0.80*0.44 + 0.5*0.55*0.40) / (0.5*0.80 + 0.5*0.55) = 0.286/0.675 = 0.42370
    assert mix.elemental_composition["C"] == pytest.approx(0.286 / 0.675, rel=1e-9)
