# External validation

## Real-world motivation and public source

India's SATAT (Sustainable Alternative Towards Affordable Transportation)
scheme, launched 2018-10-01 by the Ministry of Petroleum and Natural Gas,
is the direct policy driver behind this repo. As of India Energy Week
2026 there were 133 commissioned CBG plants totaling 926 TPD output and
83 more under construction. Adani Total Gas's Barsana plant (Mathura
district, Uttar Pradesh) is a real, publicly disclosed example: Phase I
processes ~225 TPD of agricultural waste and cattle dung to produce a
reported 10 TPD of CBG; the full Phase III design processes 600 TPD
feedstock into 42+ TPD CBG and 217 TPD organic fertilizer.

## Anaerobic digestion biodegradability -- a real, counter-to-intuition calibration finding

`anaerobic_digestion.py`'s Buswell-equation theoretical methane ceiling,
applied at a single generic "typical" biodegradability fraction, does
NOT reproduce all three published feedstock yield figures at once. Back-
solving the biodegradability fraction separately against each published
Nm3-per-tonne-fresh yield (see `feedstock.py`) gives:

| Feedstock | Published yield (Nm3 biogas/tonne fresh) | Back-solved biodegradability |
|---|---|---|
| Paddy straw | 350 | 0.533 |
| Press mud | 150 | 0.273 |
| Cattle dung | 120 | 0.292 |

This was a genuine finding, not designed in advance: the naive
expectation (manure "digests more easily" than fibrous crop residue)
predicts the OPPOSITE ordering. The calibration instead shows press mud
and cattle dung both need a markedly LOWER biodegradability fraction
than fresh straw to reproduce their own published yields -- consistent
with a real, documented AD mechanism: both substrates have already had
their easily fermentable fraction removed before ever reaching a CBG
digester (press mud, by sugar extraction; cattle dung, by the animal's
own rumen digestion), leaving a VS pool that is proportionally MORE
recalcitrant, not less. Each `feedstock.py` preset now carries its own
calibrated default rather than one shared constant.

**Honest caveat**: because these three defaults are each individually
back-solved to exactly reproduce their own single published figure, this
is a calibration exercise, not a blind prediction -- real value would
come from validating against a substrate's own BMP (Biochemical Methane
Potential) test result, the actual real-world measurement this factor
stands in for. The ORDERING finding (straw > press mud ~ cattle dung)
is the genuinely informative result; the exact third-decimal-place
values are fitted, not independently measured.

## Real-gas storage sizing -- CoolProp vs. ideal gas at 250 bar

`compression_storage.cascade_storage_volume()` computes methane/CO2
mixture density from CoolProp's real equation of state. At CBG storage
conditions (250 bar, 25 C) the compressibility factor Z comes out to
roughly 0.86-0.87 -- confirmed in this module's own test suite -- meaning
an ideal-gas (PV=nRT) volume estimate would be wrong by a comparable
margin at this pressure. This is the same justification the sibling
repos give for using CoolProp instead of a shortcut correlation
wherever real-fluid behaviour matters.

## Full-chain worked example -- an honest, unresolved gap against Barsana's published output

`examples/full_chain_worked_example.py` runs the full chain at Barsana
Phase I's published scale (225 TPD feedstock) across a range of
straw:cattle-dung mixes, since Adani Total Gas's own public disclosures
describe the feedstock only as "agricultural waste and cattle dung"
without the exact split:

| Feedstock mix | Computed CBG output | vs. published 10 TPD |
|---|---|---|
| 100% paddy straw | 29.3 TPD | 2.93x |
| 50/50 straw/dung | 18.4 TPD | 1.84x |
| 85% dung / 15% straw | 12.3 TPD | 1.23x |
| 100% cattle dung | 10.1 TPD | 1.01x |

**This is reported honestly, not massaged to fit**: only a feed close to
100% cattle dung reproduces Barsana's published output; any meaningful
inclusion of straw overshoots it substantially, since straw's calibrated
per-tonne yield is roughly 3x cattle dung's. Three possible explanations,
none of which this conceptual model can distinguish between with the
information publicly available: (1) Barsana's real feedstock mix leans
far more heavily toward cattle dung than "agricultural waste and cattle
dung" suggests to a reader; (2) a real mixed-feedstock CSTR digester's
actual co-digestion performance for straw falls well below this
project's straw-specific calibration (itself back-solved against a
DIFFERENT, straw-only published figure, not a mixed-feed one); or (3)
the plant is not yet running at its full theoretical biogas potential
during the reporting period the 10 TPD figure describes. This is exactly
the kind of finding worth publishing as a genuine open question rather
than silently tuning a parameter until the numbers agree.

## What was deliberately not modeled in this first pass

- Rate-based/kinetic digestion models (Monod-type substrate-utilization
  kinetics, or the full ADM1 standard) -- this module uses the Buswell
  mass-balance ceiling plus an empirical biodegradability correction,
  not a dynamic biological model.
- H2S removal as a separate process step (real CBG upgrading trains
  remove H2S before or alongside CO2 -- `upgrading.py` handles CO2
  removal and CH4 slip only, at the same conceptual level as the
  sibling repos' own acid-gas modules).
- Real digester heating/insulation duty for mesophilic operation --
  digester_working_volume() sizes volume from HRT only, not the thermal
  energy needed to maintain 32-38 C (see docs/VENDOR_REFERENCE.md).
