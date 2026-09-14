"""End-to-end worked example: feedstock -> anaerobic digestion -> biogas
upgrading -> compression to CBG -> digestate, at the real, publicly
disclosed scale of Adani Total Gas's Barsana CBG plant (Mathura
district, Uttar Pradesh) Phase I: 225 tonnes/day of agricultural waste
and cattle dung feedstock, producing a reported 10 tonnes/day of CBG
(see docs/VALIDATION.md for the source).

Adani Total Gas's own public disclosures describe the feedstock only as
"agricultural waste and cattle dung", without the exact mass split --
this script runs the full chain across a range of straw:dung mixes to
show how sensitive the result is, printing all of them against the
published 10 t/day figure rather than silently picking whichever ratio
happens to match best.

Run: python examples/full_chain_worked_example.py
"""
from __future__ import annotations

import CoolProp.CoolProp as CP

from cbg_design import anaerobic_digestion as AD
from cbg_design import compression_storage as CS
from cbg_design import digestate as DG
from cbg_design import feedstock as F
from cbg_design import properties as P
from cbg_design import upgrading as U

FEEDSTOCK_TPD = 225.0
FEEDSTOCK_KG_S = FEEDSTOCK_TPD * 1000.0 / 86400.0
PUBLISHED_CBG_TPD = 10.0

RHO_CH4_STP = CP.PropsSI("Dmass", "T", 273.15, "P", 101325, "Methane")
RHO_CO2_STP = CP.PropsSI("Dmass", "T", 273.15, "P", 101325, "CarbonDioxide")


def run_mix(dung_share: float) -> dict:
    straw_share = 1.0 - dung_share
    if straw_share <= 0:
        feed = F.cattle_dung(FEEDSTOCK_KG_S)
    elif dung_share <= 0:
        feed = F.paddy_straw(FEEDSTOCK_KG_S)
    else:
        straw = F.paddy_straw(FEEDSTOCK_KG_S * straw_share)
        dung = F.cattle_dung(FEEDSTOCK_KG_S * dung_share)
        feed = F.co_digestion_mix([straw, dung], [straw_share, dung_share])

    digestion = AD.digest(feed)
    upgraded = U.upgrade_biogas(digestion.biogas_flow_nm3_s, digestion.biogas_ch4_mole_frac)

    ch4_mass_kg_s = upgraded.product_ch4_flow_nm3_s * RHO_CH4_STP
    co2_flow_nm3_s = upgraded.product_ch4_flow_nm3_s / upgraded.product_ch4_mole_frac * (1 - upgraded.product_ch4_mole_frac)
    co2_mass_kg_s = co2_flow_nm3_s * RHO_CO2_STP
    cbg_tpd = (ch4_mass_kg_s + co2_mass_kg_s) * 86400.0 / 1000.0

    digestate = DG.characterize_digestate(feed, digestion, dilution_water_kg_s=FEEDSTOCK_KG_S * 2.0)

    return {"dung_share": dung_share, "cbg_tpd": cbg_tpd, "digestate_tpd": digestate.digestate_mass_flow_kg_s * 86.4}


def main() -> None:
    print(f"=== CBG plant: {FEEDSTOCK_TPD:.0f} t/day feedstock (Barsana Phase I scale) ===\n")
    print(f"{'dung share':>12} {'straw share':>12} {'CBG t/day':>12} {'vs. published 10 t/day':>24}")
    for dung_share in [0.0, 0.5, 0.7, 0.85, 0.95, 1.0]:
        r = run_mix(dung_share)
        gap = r["cbg_tpd"] / PUBLISHED_CBG_TPD
        print(f"{dung_share:>12.0%} {1 - dung_share:>12.0%} {r['cbg_tpd']:>12.2f} {gap:>23.2f}x")

    print("\n=== Detail at a 50/50 illustrative mix ===")
    dung_share = 0.5
    straw = F.paddy_straw(FEEDSTOCK_KG_S * (1 - dung_share))
    dung = F.cattle_dung(FEEDSTOCK_KG_S * dung_share)
    feed = F.co_digestion_mix([straw, dung], [1 - dung_share, dung_share])
    digestion = AD.digest(feed)
    upgraded = U.upgrade_biogas(digestion.biogas_flow_nm3_s, digestion.biogas_ch4_mole_frac)
    cbg_gas = P.cbg_product(upgraded.product_ch4_mole_frac)
    compression = CS.compress_to_cbg_pressure(cbg_gas, mass_flow_kg_s=upgraded.product_ch4_flow_nm3_s * RHO_CH4_STP / 0.95,
                                              P_in_Pa=1.5e5)
    digestate = DG.characterize_digestate(feed, digestion, dilution_water_kg_s=FEEDSTOCK_KG_S * 2.0)

    print(f"Digester: {digestion.biogas_flow_nm3_s * 86400:,.0f} Nm3/day raw biogas, "
          f"{digestion.biogas_ch4_mole_frac:.1%} CH4")
    print(f"Upgrading ({upgraded.technology}): {upgraded.product_ch4_mole_frac:.1%} CH4 product, "
          f"meets IS 16087: {upgraded.meets_is_16087}, power {upgraded.power_kW:.0f} kW")
    print(f"Compression to 250 bar: {compression.total_power_kW:.0f} kW, {compression.n_stages} stages")
    print(f"Digestate (Fermented Organic Manure): {digestate.digestate_flow_m3_day:,.0f} m3/day")

    print(f"\n=== Validation: a 100% cattle-dung feed lands within a few percent of the published "
          f"10 t/day; any straw-inclusive mix overshoots it substantially, since straw's calibrated "
          f"per-tonne yield is roughly 3x cattle dung's. See docs/VALIDATION.md for the honest discussion "
          f"of what this does and doesn't prove about Barsana's real (undisclosed) feedstock mix. ===")


if __name__ == "__main__":
    main()
