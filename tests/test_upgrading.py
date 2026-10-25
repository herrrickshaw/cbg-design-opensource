import pytest

from cbg_design import upgrading as U


def test_default_upgrade_meets_is_16087():
    r = U.upgrade_biogas(raw_biogas_flow_nm3_s=1.0, raw_ch4_mole_frac=0.60)
    assert r.meets_is_16087 is True
    assert r.product_ch4_mole_frac >= U.IS_16087_MIN_CH4_MOLE_FRAC


def test_ch4_slip_reduces_product_flow_below_raw_ch4():
    r = U.upgrade_biogas(raw_biogas_flow_nm3_s=1.0, raw_ch4_mole_frac=0.60, technology="psa")
    raw_ch4_flow = 1.0 * 0.60
    assert r.product_ch4_flow_nm3_s < raw_ch4_flow
    assert r.ch4_slip_nm3_s > 0


def test_power_scales_linearly_with_flow():
    r1 = U.upgrade_biogas(raw_biogas_flow_nm3_s=1.0, raw_ch4_mole_frac=0.60)
    r2 = U.upgrade_biogas(raw_biogas_flow_nm3_s=2.0, raw_ch4_mole_frac=0.60)
    assert r2.power_kW == pytest.approx(2 * r1.power_kW)


def test_rejects_unknown_technology():
    with pytest.raises(ValueError):
        U.upgrade_biogas(raw_biogas_flow_nm3_s=1.0, raw_ch4_mole_frac=0.60, technology="cryogenic")


def test_rejects_implausible_raw_ch4_fraction():
    with pytest.raises(ValueError):
        U.upgrade_biogas(raw_biogas_flow_nm3_s=1.0, raw_ch4_mole_frac=1.2)


def test_all_three_technologies_have_published_ranges():
    assert set(U.TECHNOLOGY_SPECIFIC_POWER_KWH_PER_NM3) == {"water_scrubbing", "psa", "membrane"}
    for lo, hi in U.TECHNOLOGY_SPECIFIC_POWER_KWH_PER_NM3.values():
        assert 0 < lo < hi < 1.0


def test_water_scrubbing_hand_computed():
    # 1 Nm3/s raw at 55 % CH4, 2 % slip, 98 % CO2 removal:
    # CH4 out 0.55*0.98 = 0.539; CO2 left 0.45*0.02 = 0.009; y = 0.539/0.548 = 0.98358
    # power = midpoint(0.24, 0.33) = 0.285 kWh/Nm3 x 3600 Nm3/h = 1026 kW
    r = U.upgrade_biogas(1.0, 0.55, "water_scrubbing")
    assert r.product_ch4_flow_nm3_s == pytest.approx(0.539)
    assert r.ch4_slip_nm3_s == pytest.approx(0.011)
    assert r.product_ch4_mole_frac == pytest.approx(0.539 / 0.548)
    assert r.power_kW == pytest.approx(1026.0)


def test_poor_co2_removal_fails_is_16087():
    # 50 % CO2 removal: 0.539 / (0.539 + 0.225) = 0.7055 < 0.90
    assert not U.upgrade_biogas(1.0, 0.55, co2_removal_frac=0.5).meets_is_16087
