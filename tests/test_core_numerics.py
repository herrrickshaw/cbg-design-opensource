"""Hand-computed values, invariants and error paths for the CBG design modules.

Expected numbers are derived on paper from the formulas in each module
docstring. Compression/storage are driven through fake gas objects with
fixed k, Z and molar mass (the modules take any object with the
`GasProperties` interface), so no real CoolProp mixture output (e.g. near
250 bar) is asserted anywhere in this file.
"""
import pytest

from cbg_design import anaerobic_digestion as AD
from cbg_design import compression_storage as CS
from cbg_design import digestate as DG
from cbg_design import feedstock as F
from cbg_design import properties as P
from cbg_design import upgrading as U

# glucose C6H12O6 elemental mass fractions, built from the module's own atomic weights
_GLUCOSE = {"C": 6 * 12.011 / 180.156, "H": 12 * 1.008 / 180.156, "O": 6 * 15.999 / 180.156, "N": 0.0, "S": 0.0}


def _glucose_feed(mass_flow=10.0, vs=0.8, biodeg=0.5, hrt=30.0):
    return F.FeedstockAnalysis("glucose-like", mass_flow, vs, dict(_GLUCOSE), 300.0, biodeg, hrt)


# ----------------------------------------------------------------- feedstock


def test_presets_carry_their_calibrated_defaults():
    s, m, d = F.paddy_straw(1.0), F.press_mud(1.0), F.cattle_dung(1.0)
    assert (s.name, s.vs_mass_frac, s.specific_biogas_yield_nm3_per_tonne_fresh) == ("paddy straw", 0.80, 350.0)
    assert (s.default_biodegradability_fraction, s.default_hrt_days) == (0.533, 30.0)
    assert (m.name, m.vs_mass_frac, m.specific_biogas_yield_nm3_per_tonne_fresh) == ("press mud", 0.70, 150.0)
    assert (m.default_biodegradability_fraction, m.default_hrt_days) == (0.273, 30.0)
    assert (d.name, d.vs_mass_frac, d.specific_biogas_yield_nm3_per_tonne_fresh) == ("cattle dung", 0.55, 120.0)
    assert (d.default_biodegradability_fraction, d.default_hrt_days) == (0.292, 85.0)


def test_preset_arguments_override_defaults():
    s = F.paddy_straw(2.5, vs_mass_frac=0.7, specific_yield_nm3_per_tonne=400.0)
    assert (s.mass_flow_kg_s, s.vs_mass_frac, s.specific_biogas_yield_nm3_per_tonne_fresh) == (2.5, 0.7, 400.0)
    assert F.press_mud(1.0, 0.6, 100.0).vs_mass_frac == 0.6
    assert F.cattle_dung(1.0, 0.5, 90.0).specific_biogas_yield_nm3_per_tonne_fresh == 90.0


def test_co_digestion_mix_hand_computed_linear_blends():
    straw, dung = F.paddy_straw(3.0), F.cattle_dung(1.0)
    mix = F.co_digestion_mix([straw, dung], [0.5, 0.5])
    assert mix.name == "co-digestion mix"
    assert mix.mass_flow_kg_s == pytest.approx(4.0)                       # sum of stream flows
    assert mix.vs_mass_frac == pytest.approx((0.80 + 0.55) / 2)
    assert mix.specific_biogas_yield_nm3_per_tonne_fresh == pytest.approx((350.0 + 120.0) / 2)
    assert mix.default_hrt_days == pytest.approx((30.0 + 85.0) / 2)
    # carbon blends on VS mass: (0.44*0.40 + 0.40*0.275) / 0.675
    assert mix.elemental_composition["C"] == pytest.approx((0.44 * 0.40 + 0.40 * 0.275) / 0.675)


def test_co_digestion_mix_of_identical_streams_reproduces_the_stream():
    straw = F.paddy_straw(2.0)
    mix = F.co_digestion_mix([straw, F.paddy_straw(2.0)], [0.3, 0.7])
    for el, v in straw.elemental_composition.items():
        assert mix.elemental_composition[el] == pytest.approx(v)
    assert mix.default_biodegradability_fraction == pytest.approx(0.533)
    assert mix.vs_mass_frac == pytest.approx(0.80)


def test_co_digestion_mix_shares_decide_which_stream_dominates():
    straw, dung = F.paddy_straw(1.0), F.cattle_dung(1.0)
    mostly_dung = F.co_digestion_mix([straw, dung], [0.1, 0.9])
    mostly_straw = F.co_digestion_mix([straw, dung], [0.9, 0.1])
    assert mostly_dung.default_hrt_days > mostly_straw.default_hrt_days
    assert mostly_dung.default_biodegradability_fraction < mostly_straw.default_biodegradability_fraction
    assert 0.292 < mostly_dung.default_biodegradability_fraction < 0.533


def test_co_digestion_mix_input_validation():
    s = F.paddy_straw(1.0)
    with pytest.raises(ValueError, match="equal-length"):
        F.co_digestion_mix([s, s], [1.0])
    with pytest.raises(ValueError, match="equal-length"):
        F.co_digestion_mix([], [])
    with pytest.raises(ValueError, match="sum to 1.0"):
        F.co_digestion_mix([s, s], [0.5, 0.49])
    F.co_digestion_mix([s, s], [0.5, 0.4999995])          # inside the 1e-6 tolerance


# ------------------------------------------------------- anaerobic digestion


def test_buswell_glucose_gives_three_methane_three_co2_per_mole():
    r = AD.buswell_theoretical_yield(_GLUCOSE)
    assert r["mol_ch4_per_kg_vs"] == pytest.approx(3000.0 / 180.156, rel=1e-6)
    assert r["mol_co2_per_kg_vs"] == pytest.approx(3000.0 / 180.156, rel=1e-6)


def test_buswell_nitrogen_diverts_carbon_from_methane_to_ammonia():
    with_n = AD.buswell_theoretical_yield({"C": 0.4, "H": 0.06, "O": 0.5, "N": 0.04})
    without = AD.buswell_theoretical_yield({"C": 0.4, "H": 0.06, "O": 0.5, "N": 0.0})
    assert with_n["mol_ch4_per_kg_vs"] < without["mol_ch4_per_kg_vs"]
    assert with_n["mol_co2_per_kg_vs"] > without["mol_co2_per_kg_vs"]
    # hand: methane = (4a + b - 2c - 3d)/8 with a = 400/12.011, b = 60/1.008, c = 500/15.999, d = 40/14.007
    a, b, c, d = 400 / 12.011, 60 / 1.008, 500 / 15.999, 40 / 14.007
    assert with_n["mol_ch4_per_kg_vs"] == pytest.approx((4 * a + b - 2 * c - 3 * d) / 8)
    assert with_n["mol_co2_per_kg_vs"] == pytest.approx((4 * a - b + 2 * c + 3 * d) / 8)


def test_buswell_rejects_a_substrate_too_oxidised_to_make_methane():
    with pytest.raises(ValueError, match="non-positive"):
        AD.buswell_theoretical_yield({"C": 0.1, "H": 0.0, "O": 0.9, "N": 0.0})


def test_digest_hand_computed_for_glucose_like_feed():
    r = AD.digest(_glucose_feed())
    theo = 3000.0 / 180.156 * 22.414                     # Nm3 CH4 / tonne VS
    assert r.theoretical_ch4_nm3_per_tonne_vs == pytest.approx(theo, rel=1e-6)
    assert r.practical_ch4_nm3_per_tonne_vs == pytest.approx(theo * 0.5, rel=1e-6)
    assert r.biogas_ch4_mole_frac == pytest.approx(0.5, rel=1e-6)          # 3 CH4 : 3 CO2
    assert r.ch4_flow_nm3_s == pytest.approx(theo * 0.5 * (10.0 * 0.8 / 1000.0), rel=1e-6)
    assert r.biogas_flow_nm3_s == pytest.approx(2 * r.ch4_flow_nm3_s, rel=1e-6)
    assert r.biodegradability_fraction == 0.5 and r.feedstock_name == "glucose-like"


def test_digest_override_boundaries_and_default_selection():
    f = _glucose_feed(biodeg=0.5)
    assert AD.digest(f, 1.0).biodegradability_fraction == 1.0
    assert AD.digest(f, 0.25).biodegradability_fraction == 0.25
    assert AD.digest(f).biodegradability_fraction == 0.5
    assert AD.digest(f, 1.0).ch4_flow_nm3_s == pytest.approx(2 * AD.digest(f).ch4_flow_nm3_s)
    for bad in (0.0, -0.1, 1.0001):
        with pytest.raises(ValueError, match="biodegradability_fraction"):
            AD.digest(f, bad)


def test_digest_methane_fraction_is_independent_of_biodegradability():
    f = F.paddy_straw(5.0)
    assert AD.digest(f, 0.3).biogas_ch4_mole_frac == pytest.approx(AD.digest(f, 0.9).biogas_ch4_mole_frac)


def test_digester_volume_hand_computed():
    f = _glucose_feed(hrt=30.0)
    r = AD.digester_working_volume(f, dilution_water_kg_s=20.0)
    assert r["hrt_days"] == 30.0
    assert r["daily_feed_m3"] == pytest.approx(30.0 * 86400.0 / 1000.0)           # 2592 m3/day
    assert r["digester_working_volume_m3"] == pytest.approx(2592.0 * 30.0)
    r2 = AD.digester_working_volume(f, 20.0, hrt_days=20.0, slurry_density_kg_m3=1050.0)
    assert r2["hrt_days"] == 20.0
    assert r2["daily_feed_m3"] == pytest.approx(30.0 * 86400.0 / 1050.0)
    assert r2["digester_working_volume_m3"] == pytest.approx(30.0 * 86400.0 / 1050.0 * 20.0)


def test_cattle_dung_needs_a_larger_digester_than_straw_for_equal_feed():
    straw = AD.digester_working_volume(F.paddy_straw(1.0), 1.0)["digester_working_volume_m3"]
    dung = AD.digester_working_volume(F.cattle_dung(1.0), 1.0)["digester_working_volume_m3"]
    assert dung / straw == pytest.approx(85.0 / 30.0)


# ----------------------------------------------------------------- digestate


def _digestion(ch4_flow=2.2414, ch4_frac=0.5, biodeg=0.5):
    return AD.DigestionResult("x", 0.0, 0.0, ch4_frac, ch4_flow / ch4_frac, ch4_flow, biodeg)


def test_digestate_hand_computed_mass_balance():
    f = _glucose_feed()                           # 10 kg/s, VS 0.8
    r = DG.characterize_digestate(f, _digestion(), dilution_water_kg_s=20.0)
    # CH4 = 2.2414/22.414 = 0.1 kmol/s ; CO2 equal (50:50) ; biogas = 0.1*16.043 + 0.1*44.01
    biogas = 0.1 * 16.043 + 0.1 * 44.01
    assert r.digestate_mass_flow_kg_s == pytest.approx(30.0 - biogas)
    assert r.vs_destroyed_kg_s == pytest.approx(4.0)                    # 10 * 0.8 * 0.5
    assert r.solids_content_mass_frac == pytest.approx((10.0 - 4.0) / (30.0 - biogas))
    assert r.digestate_flow_m3_day == pytest.approx((30.0 - biogas) * 86.4)
    dense = DG.characterize_digestate(f, _digestion(), 20.0, digestate_density_kg_m3=1100.0)
    assert dense.digestate_flow_m3_day == pytest.approx((30.0 - biogas) * 86400.0 / 1100.0)


def test_digestate_co2_follows_the_biogas_methane_fraction():
    f = _glucose_feed()
    r = DG.characterize_digestate(f, _digestion(ch4_flow=2.2414, ch4_frac=0.6), 20.0)
    biogas = 0.1 * 16.043 + 0.1 * (0.4 / 0.6) * 44.01
    assert r.digestate_mass_flow_kg_s == pytest.approx(30.0 - biogas)


def test_digestate_rejects_biogas_exceeding_feed():
    with pytest.raises(ValueError, match="non-positive"):
        DG.characterize_digestate(_glucose_feed(), _digestion(), dilution_water_kg_s=-10.0)


# ----------------------------------------------------------------- upgrading


def test_upgrading_hand_computed_water_scrubbing():
    r = U.upgrade_biogas(1.0, 0.60)
    assert r.technology == "water_scrubbing"
    assert r.product_ch4_flow_nm3_s == pytest.approx(0.6 * 0.98)             # 2 % slip
    assert r.ch4_slip_nm3_s == pytest.approx(0.6 * 0.02)
    # remaining CO2 = 0.4 * (1 - 0.98) = 0.008 -> purity 0.588 / 0.596
    assert r.product_ch4_mole_frac == pytest.approx(0.588 / 0.596)
    assert r.power_kW == pytest.approx(0.285 * 3600.0)                      # midpoint of 0.24-0.33 kWh/Nm3
    assert r.meets_is_16087 is True
    assert (r.raw_biogas_flow_nm3_s, r.raw_ch4_mole_frac) == (1.0, 0.60)


def test_upgrading_technology_defaults():
    psa = U.upgrade_biogas(2.0, 0.6, "psa")
    assert psa.power_kW == pytest.approx(0.24 * 2.0 * 3600.0)               # midpoint 0.18-0.30
    assert psa.ch4_slip_nm3_s == pytest.approx(2.0 * 0.6 * 0.03)
    mem = U.upgrade_biogas(1.0, 0.6, "membrane")
    assert mem.power_kW == pytest.approx(0.30 * 3600.0)                     # midpoint 0.20-0.40
    assert mem.ch4_slip_nm3_s == pytest.approx(0.6 * 0.02)


def test_upgrading_explicit_overrides_beat_technology_defaults():
    r = U.upgrade_biogas(1.0, 0.6, "psa", specific_power_kwh_per_nm3=0.25, ch4_slip_frac=0.01, co2_removal_frac=0.95)
    assert r.power_kW == pytest.approx(0.25 * 3600.0)
    assert r.ch4_slip_nm3_s == pytest.approx(0.006)
    assert r.product_ch4_mole_frac == pytest.approx(0.594 / (0.594 + 0.4 * 0.05))
    # a zero override is a real value, not "unset"
    z = U.upgrade_biogas(1.0, 0.6, ch4_slip_frac=0.0)
    assert z.ch4_slip_nm3_s == 0.0
    assert z.product_ch4_flow_nm3_s == pytest.approx(0.6)


def test_upgrading_input_validation():
    with pytest.raises(ValueError, match="technology must be one of"):
        U.upgrade_biogas(1.0, 0.6, "cryogenic")
    for bad in (0.0, 1.0, -0.2, 1.2):
        with pytest.raises(ValueError, match="strictly between"):
            U.upgrade_biogas(1.0, bad)


def test_upgrading_purity_threshold_is_inclusive(monkeypatch):
    r = U.upgrade_biogas(1.0, 0.6)
    monkeypatch.setattr(U, "IS_16087_MIN_CH4_MOLE_FRAC", r.product_ch4_mole_frac)
    assert U.upgrade_biogas(1.0, 0.6).meets_is_16087 is True
    monkeypatch.setattr(U, "IS_16087_MIN_CH4_MOLE_FRAC", r.product_ch4_mole_frac + 1e-9)
    assert U.upgrade_biogas(1.0, 0.6).meets_is_16087 is False


def test_upgrading_fails_is_16087_with_poor_co2_removal():
    r = U.upgrade_biogas(1.0, 0.55, co2_removal_frac=0.60)
    assert r.product_ch4_mole_frac < 0.90
    assert r.meets_is_16087 is False


def test_upgrading_with_nothing_left_reports_zero_purity():
    r = U.upgrade_biogas(1.0, 0.5, ch4_slip_frac=1.0, co2_removal_frac=1.0)
    assert r.product_ch4_mole_frac == 0.0
    assert r.meets_is_16087 is False


def test_is_16087_constant_and_technology_tables():
    assert U.IS_16087_MIN_CH4_MOLE_FRAC == 0.90
    assert set(U.TECHNOLOGY_SPECIFIC_POWER_KWH_PER_NM3) == set(U.TECHNOLOGY_CH4_SLIP_FRAC) == {
        "water_scrubbing", "psa", "membrane"}
    for lo, hi in U.TECHNOLOGY_SPECIFIC_POWER_KWH_PER_NM3.values():
        assert 0 < lo < hi


# --------------------------------------------------- compression and storage


class _FakeGas:
    """k = 1.4, Z = 1.0 (override), M = 16 g/mol, density = ideal gas times `rho_scale`."""

    def __init__(self, k=1.4, Z=1.0, M_g_mol=16.0, rho_scale=1.0):
        self.k, self.Z, self.M, self.rho_scale = k, Z, M_g_mol, rho_scale
        self.suction_temperatures = []

    def prop(self, output, T, P):
        if output == "Cpmass":
            return self.k * 1000.0
        if output == "Cvmass":
            return 1000.0
        raise KeyError(output)

    def compressibility(self, T, P):
        self.suction_temperatures.append(T)
        return self.Z

    def density(self, T, P):
        return self.rho_scale * P * (self.M / 1000.0) / (8.314462618 * T)

    def molecular_weight(self):
        return self.M


def test_isentropic_exponent_is_cp_over_cv():
    assert CS._isentropic_exponent(_FakeGas(k=1.31), 300.0, 1e5) == pytest.approx(1.31)


def test_single_stage_polytropic_hand_computed():
    g = _FakeGas()
    r = CS.compress_to_cbg_pressure(g, 1.0, 1.0e5, 4.0e5, T_suction_K=300.0, n_stages=1, polytropic_efficiency=1.0)
    ratio_term = 4.0 ** (0.4 / 1.4)
    head = (8.314462618 / 0.016) * 300.0 * (1.4 / 0.4) * (ratio_term - 1.0)
    assert r.n_stages == 1 and len(r.stages) == 1
    st = r.stages[0]
    assert st.stage == 1 and (st.P_in_Pa, st.P_out_Pa) == (1.0e5, 4.0e5)
    assert st.polytropic_head_kJ_kg == pytest.approx(head / 1000.0)
    assert st.power_kW == pytest.approx(head / 1000.0)         # 1 kg/s, eta 1
    assert st.T_out_K == pytest.approx(300.0 * ratio_term)
    assert head / 1000.0 == pytest.approx(265.18, abs=0.01)    # hand arithmetic: 519.65 * 300 * 3.5 * 0.48599


def test_efficiency_raises_power_and_polytropic_exponent():
    g = _FakeGas()
    eta1 = CS.compress_to_cbg_pressure(g, 1.0, 1e5, 4e5, 300.0, 1, 1.0).total_power_kW
    eta75 = CS.compress_to_cbg_pressure(g, 1.0, 1e5, 4e5, 300.0, 1, 0.75).total_power_kW
    k, eta = 1.4, 0.75
    n = 1.0 / (1.0 - (k - 1.0) / (k * eta))
    head = (8.314462618 / 0.016) * 300.0 * (n / (n - 1.0)) * (4.0 ** ((n - 1.0) / n) - 1.0)
    assert eta75 == pytest.approx(head / eta / 1000.0)
    assert eta75 > eta1


def test_multi_stage_splits_the_ratio_evenly_and_intercools():
    g = _FakeGas()
    r = CS.compress_to_cbg_pressure(g, 2.0, 1.5e5, 250e5)
    assert r.n_stages == 4 and [s.stage for s in r.stages] == [1, 2, 3, 4]
    ratio = (250e5 / 1.5e5) ** 0.25
    for s in r.stages:
        assert s.P_out_Pa / s.P_in_Pa == pytest.approx(ratio)
    for a, b in zip(r.stages, r.stages[1:]):
        assert b.P_in_Pa == pytest.approx(a.P_out_Pa)
    assert r.stages[0].P_in_Pa == 1.5e5 and r.stages[-1].P_out_Pa == pytest.approx(250e5)
    assert r.total_power_kW == pytest.approx(sum(s.power_kW for s in r.stages))
    assert g.suction_temperatures == [313.15] * 4            # default suction temperature, every stage
    assert all(s.T_out_K > 313.15 for s in r.stages)
    # equal ratio and constant suction conditions -> identical stages
    assert len({round(s.power_kW, 9) for s in r.stages}) == 1


def test_more_stages_use_less_power_for_the_same_duty_and_power_scales_with_flow():
    g = _FakeGas()
    two = CS.compress_to_cbg_pressure(g, 1.0, 1e5, 100e5, n_stages=2).total_power_kW
    four = CS.compress_to_cbg_pressure(g, 1.0, 1e5, 100e5, n_stages=4).total_power_kW
    assert four < two
    double = CS.compress_to_cbg_pressure(g, 2.0, 1e5, 100e5, n_stages=2).total_power_kW
    assert double == pytest.approx(2 * two)
    assert CS.compress_to_cbg_pressure(g, 1.0, 1e5, 100e5, n_stages=3, T_suction_K=290.0).total_power_kW < \
        CS.compress_to_cbg_pressure(g, 1.0, 1e5, 100e5, n_stages=3, T_suction_K=330.0).total_power_kW


def test_compression_requires_a_pressure_rise():
    with pytest.raises(ValueError, match="P_out_Pa must exceed P_in_Pa"):
        CS.compress_to_cbg_pressure(_FakeGas(), 1.0, 1e5, 1e5)
    with pytest.raises(ValueError):
        CS.compress_to_cbg_pressure(_FakeGas(), 1.0, 2e5, 1e5)


def test_cascade_storage_uses_real_density_not_ideal():
    g = _FakeGas(Z=0.86, rho_scale=1 / 0.86)               # real gas denser than ideal by 1/Z
    out = CS.cascade_storage_volume(g, 1000.0)
    ideal = 250e5 * 0.016 / (8.314462618 * 313.15)
    assert out["ideal_gas_density_kg_m3"] == pytest.approx(ideal)
    assert out["real_density_kg_m3"] == pytest.approx(ideal / 0.86)
    assert out["storage_volume_m3"] == pytest.approx(1000.0 / (ideal / 0.86))
    assert out["compressibility_factor_Z"] == 0.86
    assert out["storage_volume_m3"] < 1000.0 / ideal          # the ideal-gas estimate overstates volume
    small = CS.cascade_storage_volume(g, 500.0, P_Pa=200e5, T_K=300.0)
    ideal2 = 200e5 * 0.016 / (8.314462618 * 300.0)
    assert small["storage_volume_m3"] == pytest.approx(500.0 / (ideal2 / 0.86))


# ---------------------------------------------------------------- properties


def test_gas_mixture_sum_tolerance():
    P.GasMixture({"Methane": 0.6, "CarbonDioxide": 0.4})
    P.GasMixture({"Methane": 0.6, "CarbonDioxide": 0.4000005})
    with pytest.raises(ValueError, match="sum to 1.0"):
        P.GasMixture({"Methane": 0.6, "CarbonDioxide": 0.4001})
    with pytest.raises(ValueError):
        P.GasMixture({"Methane": 0.5, "CarbonDioxide": 0.4})


def test_biogas_presets_and_heos_string():
    raw, cbg = P.raw_biogas(), P.cbg_product()
    assert raw.composition == {"Methane": 0.60, "CarbonDioxide": pytest.approx(0.40)}
    assert cbg.composition == {"Methane": 0.95, "CarbonDioxide": pytest.approx(0.05)}
    assert P.raw_biogas(0.55).composition["Methane"] == 0.55
    assert P.cbg_product(0.92).composition["Methane"] == 0.92
    assert raw._heos_string().startswith("Methane[0.6]&CarbonDioxide[0.4")


def test_molecular_weight_is_the_mole_weighted_mean():
    assert P.MW_METHANE == pytest.approx(16.043, abs=0.01)
    assert P.MW_CO2 == pytest.approx(44.010, abs=0.01)
    assert P.raw_biogas().molecular_weight() == pytest.approx(0.6 * 16.043 + 0.4 * 44.010, rel=1e-3)
    assert P.cbg_product().molecular_weight() < P.raw_biogas().molecular_weight()


def test_property_accessors_request_the_right_coolprop_output(monkeypatch):
    calls = []

    def fake(out, k1, v1, k2, v2, fluid):
        calls.append((out, k1, v1, k2, v2, fluid))
        return 3.0

    monkeypatch.setattr(P.CP, "PropsSI", fake)
    g = P.raw_biogas(0.5)
    assert g.density(300.0, 2e5) == 3.0 and g.compressibility(310.0, 3e5) == 3.0 and g.prop("Cpmass", 320.0, 4e5) == 3.0
    assert [c[0] for c in calls] == ["Dmass", "Z", "Cpmass"]
    assert calls[0][1:5] == ("T", 300.0, "P", 2e5)
    assert calls[1][1:5] == ("T", 310.0, "P", 3e5)
    assert calls[0][5] == "Methane[0.5]&CarbonDioxide[0.5]"


# ------------------------------------------------- boundary / survivor tests


def test_co_digestion_share_total_tolerance_is_tight():
    s = F.paddy_straw(1.0)
    with pytest.raises(ValueError, match="sum to 1.0"):
        F.co_digestion_mix([s, s], [0.5, 0.4999])        # off by 1e-4


def test_co_digestion_biodegradability_is_weighted_by_theoretical_methane():
    straw, dung = F.paddy_straw(1.0), F.cattle_dung(1.0)
    mix = F.co_digestion_mix([straw, dung], [0.5, 0.5])
    w = [0.5 * straw.vs_mass_frac, 0.5 * dung.vs_mass_frac]
    m = [AD.buswell_theoretical_yield(f.elemental_composition)["mol_ch4_per_kg_vs"] for f in (straw, dung)]
    expected = (0.533 * w[0] * m[0] + 0.292 * w[1] * m[1]) / (w[0] * m[0] + w[1] * m[1])
    assert mix.default_biodegradability_fraction == pytest.approx(expected, rel=1e-12)
    # and it differs from the plain VS-weighted mean, which would ignore methane potential
    vs_only = (0.533 * w[0] + 0.292 * w[1]) / (w[0] + w[1])
    assert mix.default_biodegradability_fraction != pytest.approx(vs_only, rel=1e-6)


def test_co_digestion_mix_yields_the_same_methane_as_digesting_streams_separately():
    straw, dung = F.paddy_straw(3.0), F.cattle_dung(1.0)
    mix = F.co_digestion_mix([straw, dung], [0.75, 0.25])        # shares equal the mass fractions
    separate = AD.digest(straw).ch4_flow_nm3_s + AD.digest(dung).ch4_flow_nm3_s
    # the mix blends VS on mass share while elements/biodegradability blend on VS mass, so the
    # documented "no synergy" property holds only approximately; assert it to 0.5 %
    assert AD.digest(mix).ch4_flow_nm3_s == pytest.approx(separate, rel=5e-3)


def test_buswell_all_zero_composition_has_no_methane():
    with pytest.raises(ValueError, match="non-positive"):
        AD.buswell_theoretical_yield({"C": 0.0, "H": 0.0, "O": 0.0, "N": 0.0})


def test_digestate_exactly_equal_to_biogas_mass_is_rejected():
    ch4_kmol = 2.2414 / AD.MOLAR_VOLUME_NM3_PER_KMOL
    co2_kmol = ch4_kmol * (1 - 0.5) / 0.5
    biogas = ch4_kmol * DG.MW_CH4_KG_KMOL + co2_kmol * DG.MW_CO2_KG_KMOL
    f = _glucose_feed(mass_flow=biogas)
    with pytest.raises(ValueError, match="non-positive"):
        DG.characterize_digestate(f, _digestion(), dilution_water_kg_s=0.0)


def test_upgrading_zero_power_override_is_honoured():
    assert U.upgrade_biogas(1.0, 0.6, specific_power_kwh_per_nm3=0.0).power_kW == 0.0


def test_compression_defaults_are_four_stages_and_075_efficiency():
    g = _FakeGas()
    default = CS.compress_to_cbg_pressure(g, 1.5, 2e5)
    explicit = CS.compress_to_cbg_pressure(g, 1.5, 2e5, 250e5, 313.15, 4, 0.75)
    assert default.n_stages == 4
    assert default.total_power_kW == pytest.approx(explicit.total_power_kW)
    assert default.stages[-1].P_out_Pa == pytest.approx(250e5)
