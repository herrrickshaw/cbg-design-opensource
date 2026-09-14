import pytest

from cbg_design import properties as P


def test_molecular_weights_match_known_reference_values():
    assert P.MW_METHANE == pytest.approx(16.043, abs=0.01)
    assert P.MW_CO2 == pytest.approx(44.010, abs=0.01)


def test_raw_biogas_and_cbg_product_are_valid_mixtures():
    raw = P.raw_biogas(0.60)
    cbg = P.cbg_product(0.95)
    assert raw.composition["Methane"] == pytest.approx(0.60)
    assert cbg.composition["Methane"] == pytest.approx(0.95)


def test_mixture_rejects_fractions_not_summing_to_one():
    with pytest.raises(ValueError):
        P.GasMixture({"Methane": 0.5, "CarbonDioxide": 0.3})


def test_methane_deviates_substantially_from_ideal_gas_at_250_bar():
    # Real-gas justification for compression_storage.py's storage sizing:
    # Z should be meaningfully below 1.0 at CBG storage conditions.
    cbg = P.cbg_product(0.95)
    Z = cbg.compressibility(298.15, 250e5)
    assert 0.75 < Z < 0.95
