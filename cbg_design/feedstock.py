"""Feedstock characterization for a CBG plant: elemental/VS composition and
specific biogas yield for the substrates India's SATAT scheme actually
uses. Yield ranges (paddy/rice straw >350 Nm3 biogas per tonne fresh mass;
press mud 140-160 m3/tonne; cattle dung 100-140 m3/tonne) are from a
2025 ScienceDirect techno-enviro-economic review of compressed biogas
production from agricultural residues in India, cross-referenced against
India's own feedstock-potential figures (cattle dung ~25 MMT/year CBG
potential, agricultural residues ~20 MMT/year, press mud/spent wash
~2 MMT/year -- the same source). Elemental (C, H, O, N, S) composition
presets, needed by `anaerobic_digestion.py`'s Buswell-equation methane
yield, are representative literature values for each substrate class
(Deublein & Steinhauser, "Biogas from Waste and Renewable Resources",
2nd ed., Wiley-VCH, 2011, the standard reference biogas-engineering
text) -- overridable with a feedstock's own lab analysis."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FeedstockAnalysis:
    name: str
    mass_flow_kg_s: float
    vs_mass_frac: float  # Volatile Solids, kg VS / kg fresh (as-received) mass
    elemental_composition: dict  # {"C": frac, "H": frac, "O": frac, "N": frac, "S": frac} of VS, mass basis
    specific_biogas_yield_nm3_per_tonne_fresh: float  # literature range midpoint, Nm3 biogas / tonne fresh mass
    default_biodegradability_fraction: float  # see anaerobic_digestion.py -- back-solved per substrate, not asserted
    default_hrt_days: float  # see anaerobic_digestion.digester_working_volume() -- real, cited, substrate-dependent


# Representative elemental composition of the volatile-solids fraction (mass basis),
# Deublein & Steinhauser table values for these substrate classes.
_PADDY_STRAW_ELEMENTAL = {"C": 0.44, "H": 0.055, "O": 0.42, "N": 0.008, "S": 0.001}
_PRESS_MUD_ELEMENTAL = {"C": 0.42, "H": 0.058, "O": 0.40, "N": 0.020, "S": 0.003}
_CATTLE_DUNG_ELEMENTAL = {"C": 0.40, "H": 0.055, "O": 0.38, "N": 0.024, "S": 0.003}


def paddy_straw(mass_flow_kg_s: float, vs_mass_frac: float = 0.80,
                specific_yield_nm3_per_tonne: float = 350.0) -> FeedstockAnalysis:
    """>350 Nm3/tonne fresh mass average specific biogas yield (ScienceDirect
    2025 India review); this module defaults to that reported floor as a
    conservative planning figure rather than an unverified higher point
    estimate. `default_biodegradability_fraction` (0.53) is back-solved so
    that `anaerobic_digestion.digest()`'s Buswell-based practical yield
    reproduces this same 350 Nm3/tonne figure exactly -- see
    docs/VALIDATION.md for the full derivation and why it differs sharply
    from press mud/cattle dung's calibrated values below."""
    return FeedstockAnalysis("paddy straw", mass_flow_kg_s, vs_mass_frac,
                             _PADDY_STRAW_ELEMENTAL, specific_yield_nm3_per_tonne, 0.533, default_hrt_days=30.0)


def press_mud(mass_flow_kg_s: float, vs_mass_frac: float = 0.70,
             specific_yield_nm3_per_tonne: float = 150.0) -> FeedstockAnalysis:
    """140-160 m3/tonne (midpoint 150); a sugar-mill byproduct, distinct
    from `ethanol-design-opensource`'s spent wash/vinasse (a liquid
    stream) though both are sugar-industry AD feedstocks in practice.
    `default_biodegradability_fraction` (0.273) is back-solved the same
    way as paddy_straw's -- notably lower, consistent with press mud
    already having had its readily fermentable sugars stripped out
    during juice extraction, leaving a more recalcitrant VS pool."""
    return FeedstockAnalysis("press mud", mass_flow_kg_s, vs_mass_frac,
                             _PRESS_MUD_ELEMENTAL, specific_yield_nm3_per_tonne, 0.273, default_hrt_days=30.0)


def cattle_dung(mass_flow_kg_s: float, vs_mass_frac: float = 0.55,
                specific_yield_nm3_per_tonne: float = 120.0) -> FeedstockAnalysis:
    """100-140 m3/tonne (midpoint 120); cattle dung has India's largest
    single feedstock potential for CBG (~25 MMT/year) per the same source.
    `default_biodegradability_fraction` (0.292) is back-solved the same
    way -- a real, counter-to-naive-intuition finding this project made
    while calibrating: cattle dung's VS is LESS biodegradable than fresh
    straw's, not more, because a cow's own rumen digestion has already
    consumed the easily fermentable fraction before the dung is ever fed
    to a digester. See docs/VALIDATION.md.

    `default_hrt_days` (85.0) is a real, vendor-sourced figure, not the
    generic 30-day default the other two presets use: WELTEC BIOPOWER's
    own published digester process spec (docs/VENDOR_REFERENCE.md)
    states retention time "can be as long as 80-90 days if the manure
    content is high" -- a real, independent confirmation that the same
    lower-biodegradability finding above shows up again here, in a
    completely different real-world parameter (residence time, not
    yield): manure genuinely needs longer to digest, not just less
    complete digestion. This project's own generic 30-day default would
    have understated a 100%-cattle-dung digester's real required volume
    by roughly 2.8x had this vendor figure not been found."""
    return FeedstockAnalysis("cattle dung", mass_flow_kg_s, vs_mass_frac,
                             _CATTLE_DUNG_ELEMENTAL, specific_yield_nm3_per_tonne, 0.292, default_hrt_days=85.0)


def co_digestion_mix(feedstocks: list, mass_shares: list) -> FeedstockAnalysis:
    """Mass-weighted blend of several feedstocks fed to one digester (e.g.
    the real Adani Total Gas Barsana plant's agricultural-waste + cattle-
    dung mix, see docs/VALIDATION.md) -- a simple linear mass-weighted
    average of VS content, elemental composition and specific yield. Real
    co-digestion synergies (the ScienceDirect review and others report up
    to ~20% yield uplift from cattle-manure/straw co-digestion vs. a
    naive linear blend) are NOT modeled here -- flagged, not assumed."""
    if len(feedstocks) != len(mass_shares) or not feedstocks:
        raise ValueError("feedstocks and mass_shares must be equal-length, non-empty lists")
    total_share = sum(mass_shares)
    if abs(total_share - 1.0) > 1e-6:
        raise ValueError(f"mass_shares must sum to 1.0, got {total_share}")

    total_mass_flow = sum(f.mass_flow_kg_s for f in feedstocks)
    vs = sum(f.vs_mass_frac * s for f, s in zip(feedstocks, mass_shares))
    yield_ = sum(f.specific_biogas_yield_nm3_per_tonne_fresh * s for f, s in zip(feedstocks, mass_shares))
    hrt = sum(f.default_hrt_days * s for f, s in zip(feedstocks, mass_shares))
    # Elemental composition and biodegradability are per-kg-VS quantities, so they
    # blend on VS mass (share x VS fraction), and biodegradability additionally on
    # each stream's theoretical CH4 potential -- the weighting under which digesting
    # the mix gives exactly the CH4 of digesting each stream separately (no synergy).
    from .anaerobic_digestion import buswell_theoretical_yield
    vs_w = [f.vs_mass_frac * s for f, s in zip(feedstocks, mass_shares)]
    elements = {}
    for el in ("C", "H", "O", "N", "S"):
        elements[el] = sum(f.elemental_composition[el] * w for f, w in zip(feedstocks, vs_w)) / sum(vs_w)
    ch4_w = [w * buswell_theoretical_yield(f.elemental_composition)["mol_ch4_per_kg_vs"]
             for f, w in zip(feedstocks, vs_w)]
    biodeg = sum(f.default_biodegradability_fraction * w for f, w in zip(feedstocks, ch4_w)) / sum(ch4_w)

    return FeedstockAnalysis("co-digestion mix", total_mass_flow, vs, elements, yield_, biodeg, hrt)
