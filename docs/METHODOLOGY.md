# Methodology & citations

## Feedstock (`cbg_design/feedstock.py`)

Specific biogas yield ranges — paddy/rice straw >350 Nm3/tonne fresh
mass, press mud 140-160 m3/tonne, cattle dung 100-140 m3/tonne — are
from a 2025 ScienceDirect techno-enviro-economic review of compressed
biogas production from agricultural residues in India, cross-referenced
against India's own national CBG feedstock-potential estimates (cattle
dung ~25 MMT/year, agricultural residues ~20 MMT/year, press mud/spent
wash ~2 MMT/year — the same source). Elemental (C, H, O, N) composition
presets are representative literature values for each substrate class
(Deublein & Steinhauser, "Biogas from Waste and Renewable Resources",
2nd ed., Wiley-VCH, 2011).

## Anaerobic digestion (`cbg_design/anaerobic_digestion.py`)

Buswell's equation (Buswell & Mueller, 1952; Buswell & Hatfield, 1936)
gives the theoretical methane-yield ceiling from a substrate's elemental
composition, evaluated here directly from a `FeedstockAnalysis`'s
measurable C/H/O/N mass fractions rather than looked up per-substrate.
Real digestion never reaches that ceiling; this module's
`biodegradability_fraction` closes the gap. Rather than assume one
"typical" biodegradability figure, this project back-solved it
separately for each `feedstock.py` preset against the published Nm3-
per-tonne-fresh yield ranges above — see docs/VALIDATION.md for the
full calibration and the real, counter-to-naive-intuition finding it
produced (press mud and cattle dung calibrate to markedly LOWER
biodegradability than fresh straw, not higher).

## Upgrading (`cbg_design/upgrading.py`)

India's IS 16087:2016 CBG specification requires a minimum of 90% CH4,
compressed to 250 bar (Bureau of Indian Standards, summarized in IOCL's
public SATAT FAQ and PNGRB's "Compressed Biogas Integration in India's
Gas Economy" report). Specific-power ranges for the three commercial
upgrading technologies compared — water scrubbing (0.24-0.33 kWh/Nm3),
PSA (0.18-0.30 kWh/Nm3), membrane (0.20-0.40 kWh/Nm3) — are from a
ScienceDirect 2018 water-scrubbing process-optimization paper and
biogas-industry technical-comparison sources for PSA/membrane.

## Compression & storage (`cbg_design/compression_storage.py`)

Same polytropic head/efficiency compressor method as the sibling
lng-design-opensource repo's `compressor.py` and coal-to-urea-design-
opensource's ammonia makeup-gas compressor (GPSA Engineering Data Book,
14th ed., Section 13), reused here for the same reason: it is the
standard first-pass conceptual sizing method for any multistage gas
compression train, not something specific to natural gas or ammonia
service. Storage sizing uses CoolProp's real methane/CO2 equation of
state rather than the ideal gas law — methane's compressibility factor
Z is roughly 0.86-0.87 at 250 bar/25 C (verified in this module's own
test suite), so an ideal-gas estimate would understate the storage
density (and overstate the vessel volume needed) by a comparable margin.

## Digestate (`cbg_design/digestate.py`)

A direct mass-balance consequence of `anaerobic_digestion.py`'s VS-
destruction fraction (whatever solids mass isn't converted to biogas,
plus dilution water, leaves as digestate) — not a separately fitted
"typical FOM yield" ratio. India's SATAT scheme markets this Fermented
Organic Manure co-product explicitly alongside CBG (see
docs/VALIDATION.md's Barsana example).

## Related open-source work

[DWSIM](https://github.com/DanWBR/dwsim5), [IDAES](https://github.com/IDAES/idaes-pse) —
general open-source process simulators, same as every sibling repo.
[QSDsan](https://github.com/QSD-Group/QSDsan) and its companion
[EXPOsan](https://github.com/QSD-Group/EXPOsan) (Quantitative
Sustainable Design Group, University of Illinois Urbana-Champaign) —
Python tools for quantitative sustainable design of sanitation and
resource-recovery systems, including ADM1-based anaerobic digestion and
biogas recovery modeling — the closest existing open-source prior art
for this repo's core process (consulted for context, not a dependency;
every correlation here is independently sourced and cited per-module
above).

No dedicated open-source repository was found covering CBG/biomethane
upgrading (water scrubbing, PSA, membrane) sizing specifically — the
same "no existing project" gap the coal-to-urea-design-opensource
sibling repo found for its own niche.
