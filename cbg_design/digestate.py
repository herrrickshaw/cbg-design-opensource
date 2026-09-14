"""Digestate / Fermented Organic Manure (FOM) mass balance -- the CBG
plant's other saleable co-product besides gas. India's SATAT scheme
markets this explicitly (the real Adani Total Gas Barsana plant's Phase
III design co-produces 217 TPD of organic fertilizer alongside 42 TPD
CBG from 600 TPD feedstock -- see docs/VALIDATION.md), so this module
treats it as a real output stream, not a waste disposal afterthought.

A simple VS-destruction mass balance: whatever volatile-solids mass the
digester actually converts to biogas (feedstock VS x biodegradability
fraction, from `anaerobic_digestion.py`) leaves the total solids mass
balance; everything else -- fixed solids (ash/inerts) plus the
UNDIGESTED VS fraction -- reports out as digestate, diluted by whatever
water was added for digestion. This is a real, exact mass balance (what
doesn't leave as gas must leave as digestate + moisture), not a fitted
"typical FOM yield" ratio."""
from __future__ import annotations

from dataclasses import dataclass

from .anaerobic_digestion import DigestionResult
from .feedstock import FeedstockAnalysis

# Standard molar mass of CH4 (kg/kmol) -- used to convert the Buswell-
# balance's molar CH4 output back into a mass leaving the solids balance.
MW_CH4_KG_KMOL = 16.043


@dataclass
class DigestateResult:
    digestate_mass_flow_kg_s: float
    digestate_flow_m3_day: float
    solids_content_mass_frac: float
    vs_destroyed_kg_s: float


def characterize_digestate(feedstock: FeedstockAnalysis, digestion: DigestionResult,
                           dilution_water_kg_s: float, digestate_density_kg_m3: float = 1000.0) -> DigestateResult:
    total_feed_kg_s = feedstock.mass_flow_kg_s + dilution_water_kg_s
    # CH4 molar flow (Nm3/s -> kmol/s via the standard 22.414 Nm3/kmol molar volume,
    # matching anaerobic_digestion.py's own reference), converted to a mass leaving
    # the solids balance as biogas.
    ch4_kmol_s = digestion.ch4_flow_nm3_s / 22.414
    co2_kmol_s = ch4_kmol_s * (1 - digestion.biogas_ch4_mole_frac) / digestion.biogas_ch4_mole_frac
    biogas_mass_flow_kg_s = ch4_kmol_s * MW_CH4_KG_KMOL + co2_kmol_s * 44.01

    digestate_mass_flow_kg_s = total_feed_kg_s - biogas_mass_flow_kg_s
    if digestate_mass_flow_kg_s <= 0:
        raise ValueError("computed digestate mass flow is non-positive -- biogas output exceeds total feed input")

    vs_total_kg_s = feedstock.mass_flow_kg_s * feedstock.vs_mass_frac
    vs_destroyed_kg_s = vs_total_kg_s * digestion.biodegradability_fraction
    solids_remaining_kg_s = (feedstock.mass_flow_kg_s - vs_destroyed_kg_s)
    solids_content = solids_remaining_kg_s / digestate_mass_flow_kg_s if digestate_mass_flow_kg_s > 0 else 0.0

    return DigestateResult(
        digestate_mass_flow_kg_s=digestate_mass_flow_kg_s,
        digestate_flow_m3_day=digestate_mass_flow_kg_s * 86400.0 / digestate_density_kg_m3,
        solids_content_mass_frac=solids_content,
        vs_destroyed_kg_s=vs_destroyed_kg_s,
    )
