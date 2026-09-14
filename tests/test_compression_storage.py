import pytest

from cbg_design import compression_storage as CS
from cbg_design import properties as P


def test_stage_pressure_ratios_multiply_to_the_overall_ratio():
    cbg = P.cbg_product(0.95)
    r = CS.compress_to_cbg_pressure(cbg, mass_flow_kg_s=0.1, P_in_Pa=2e5, P_out_Pa=250e5, n_stages=4)
    product_of_ratios = 1.0
    for s in r.stages:
        product_of_ratios *= s.P_out_Pa / s.P_in_Pa
    assert product_of_ratios == pytest.approx(250e5 / 2e5, rel=1e-6)
    assert r.stages[-1].P_out_Pa == pytest.approx(250e5, rel=1e-6)


def test_total_power_is_sum_of_stage_powers():
    cbg = P.cbg_product(0.95)
    r = CS.compress_to_cbg_pressure(cbg, mass_flow_kg_s=0.1, P_in_Pa=2e5)
    assert r.total_power_kW == pytest.approx(sum(s.power_kW for s in r.stages))


def test_rejects_non_increasing_pressure():
    cbg = P.cbg_product(0.95)
    with pytest.raises(ValueError):
        CS.compress_to_cbg_pressure(cbg, mass_flow_kg_s=0.1, P_in_Pa=250e5, P_out_Pa=2e5)


def test_storage_volume_uses_real_gas_density_not_ideal():
    cbg = P.cbg_product(0.95)
    result = CS.cascade_storage_volume(cbg, mass_to_store_kg=1000.0)
    assert result["compressibility_factor_Z"] < 0.95
    assert result["real_density_kg_m3"] > result["ideal_gas_density_kg_m3"]
    expected_volume = 1000.0 / result["real_density_kg_m3"]
    assert result["storage_volume_m3"] == pytest.approx(expected_volume)


def test_more_stages_reduces_per_stage_pressure_ratio():
    cbg = P.cbg_product(0.95)
    r3 = CS.compress_to_cbg_pressure(cbg, mass_flow_kg_s=0.1, P_in_Pa=2e5, n_stages=3)
    r5 = CS.compress_to_cbg_pressure(cbg, mass_flow_kg_s=0.1, P_in_Pa=2e5, n_stages=5)
    ratio3 = r3.stages[0].P_out_Pa / r3.stages[0].P_in_Pa
    ratio5 = r5.stages[0].P_out_Pa / r5.stages[0].P_in_Pa
    assert ratio5 < ratio3
