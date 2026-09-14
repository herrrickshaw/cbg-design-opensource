"""Biogas upgrading: raw biogas (55-65% CH4) -> CBG product meeting India's
IS 16087:2016 spec (minimum 90% CH4, compressed to 250 bar -- see the
Bureau of Indian Standards specification as summarized in IOCL's public
SATAT FAQ and the PNGRB's "Compressed Biogas Integration in India's Gas
Economy" report).

Three commercial upgrading technologies are compared, each with a
published specific-power range (electricity consumed per Nm3 of RAW
biogas processed):

- **Water scrubbing**: 0.24-0.33 kWh/Nm3 (a ScienceDirect 2018 paper,
  "Process selection, modelling and optimization of a water scrubbing
  process for energy-self-sufficient biogas upgrading plants" -- the low
  end for a near-atmospheric-pressure design without water regeneration,
  the high end for high-pressure/regenerated configurations).
- **Pressure Swing Adsorption (PSA)**: 0.18-0.30 kWh/Nm3 (biogas-industry
  technical-comparison sources; best-in-class units with heat recovery
  can go as low as ~0.18).
- **Membrane separation**: 0.20-0.40 kWh/Nm3 (same source family).

This module does not derive these from first-principles mass-transfer or
adsorption-isotherm models (a real, much larger scope each technology's
own dedicated literature covers) -- it takes the published specific-
power range as a direct input, the same "real published range as
overridable default" pattern the sibling repos use for e.g. LNG's amine-
absorber K_SB or ethanol's molecular-sieve working capacity. CH4 slip
(methane lost to the off-gas/permeate rather than recovered in the
product) is a second real, technology-dependent loss this module tracks
explicitly rather than assuming zero."""
from __future__ import annotations

from dataclasses import dataclass

IS_16087_MIN_CH4_MOLE_FRAC = 0.90

# (low, high) kWh per Nm3 of RAW biogas processed, and a representative
# CH4 slip fraction -- see module docstring for sourcing.
TECHNOLOGY_SPECIFIC_POWER_KWH_PER_NM3 = {
    "water_scrubbing": (0.24, 0.33),
    "psa": (0.18, 0.30),
    "membrane": (0.20, 0.40),
}
TECHNOLOGY_CH4_SLIP_FRAC = {
    "water_scrubbing": 0.02,  # typical with water regeneration/recycle
    "psa": 0.03,
    "membrane": 0.02,
}


@dataclass
class UpgradingResult:
    technology: str
    raw_biogas_flow_nm3_s: float
    raw_ch4_mole_frac: float
    product_ch4_flow_nm3_s: float
    product_ch4_mole_frac: float
    ch4_slip_nm3_s: float
    power_kW: float
    meets_is_16087: bool


def upgrade_biogas(raw_biogas_flow_nm3_s: float, raw_ch4_mole_frac: float,
                   technology: str = "water_scrubbing", specific_power_kwh_per_nm3: float | None = None,
                   ch4_slip_frac: float | None = None, co2_removal_frac: float = 0.98) -> UpgradingResult:
    if technology not in TECHNOLOGY_SPECIFIC_POWER_KWH_PER_NM3:
        raise ValueError(f"technology must be one of {list(TECHNOLOGY_SPECIFIC_POWER_KWH_PER_NM3)}")
    if not 0 < raw_ch4_mole_frac < 1:
        raise ValueError("raw_ch4_mole_frac must be strictly between 0 and 1")

    if specific_power_kwh_per_nm3 is None:
        lo, hi = TECHNOLOGY_SPECIFIC_POWER_KWH_PER_NM3[technology]
        specific_power_kwh_per_nm3 = (lo + hi) / 2  # midpoint of the published range
    if ch4_slip_frac is None:
        ch4_slip_frac = TECHNOLOGY_CH4_SLIP_FRAC[technology]

    raw_ch4_nm3_s = raw_biogas_flow_nm3_s * raw_ch4_mole_frac
    raw_co2_nm3_s = raw_biogas_flow_nm3_s * (1 - raw_ch4_mole_frac)

    product_ch4_nm3_s = raw_ch4_nm3_s * (1 - ch4_slip_frac)
    slipped_ch4_nm3_s = raw_ch4_nm3_s * ch4_slip_frac
    remaining_co2_nm3_s = raw_co2_nm3_s * (1 - co2_removal_frac)

    product_total_nm3_s = product_ch4_nm3_s + remaining_co2_nm3_s
    product_ch4_frac = product_ch4_nm3_s / product_total_nm3_s if product_total_nm3_s > 0 else 0.0

    # kWh/Nm3 (energy per volume) x Nm3/s (volume per second) x 3600 s/h = kW:
    # e.g. 0.28 kWh/Nm3 x 1 Nm3/s means 0.28 kWh is spent every 1/3600 h, i.e. 0.28*3600 = 1008 kW.
    power_kW = specific_power_kwh_per_nm3 * raw_biogas_flow_nm3_s * 3600.0

    return UpgradingResult(
        technology=technology,
        raw_biogas_flow_nm3_s=raw_biogas_flow_nm3_s,
        raw_ch4_mole_frac=raw_ch4_mole_frac,
        product_ch4_flow_nm3_s=product_ch4_nm3_s,
        product_ch4_mole_frac=product_ch4_frac,
        ch4_slip_nm3_s=slipped_ch4_nm3_s,
        power_kW=power_kW,
        meets_is_16087=product_ch4_frac >= IS_16087_MIN_CH4_MOLE_FRAC,
    )
