# CBG Design (open-source)

Interactive, open-source conceptual sizing tools for a Compressed Biogas
(CBG) plant under India's SATAT scheme — feedstock characterization,
Buswell-equation anaerobic digestion with a per-substrate calibrated
biodegradability factor, biogas upgrading (water scrubbing / PSA /
membrane) to IS 16087 spec, multistage compression to 250 bar with
CoolProp real-gas storage sizing, and digestate (Fermented Organic
Manure) mass balance. Sibling project to
[lng-design-opensource](https://github.com/herrrickshaw/lng-design-opensource),
[biomass-to-syngas-opensource](https://github.com/herrrickshaw/biomass-to-syngas-opensource),
[coal-to-urea-design-opensource](https://github.com/herrrickshaw/coal-to-urea-design-opensource)
and [ethanol-design-opensource](https://github.com/herrrickshaw/ethanol-design-opensource):
same discipline — public-domain/textbook correlations only, CoolProp for
real thermodynamic properties, every method cited, every module tested,
every worked example actually run end to end.

**Real-world motivation**: SATAT (launched 2018-10-01) has 133
commissioned CBG plants as of India Energy Week 2026 (926 TPD combined
output, 83 more under construction). This repo's worked example runs at
the real, publicly disclosed scale of Adani Total Gas's Barsana plant
(225 TPD feedstock, 10 TPD CBG Phase I) — see `docs/VALIDATION.md` for
an honest, unresolved gap the comparison surfaced.

**Scope**: fully generic and literature-only. Nothing here derives from
any proprietary vendor, licensor, or client engineering data.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q                                        # 29 tests
python examples/full_chain_worked_example.py     # feedstock -> CBG, end to end
streamlit run streamlit_app.py                   # interactive app
```

## Modules

| Module | Method | Key outputs |
|---|---|---|
| `cbg_design/feedstock.py` | Published India specific-yield ranges + per-substrate calibrated biodegradability | Paddy straw, press mud, cattle dung, co-digestion mixes |
| `cbg_design/anaerobic_digestion.py` | Buswell equation (theoretical methane ceiling) + biodegradability correction; HRT digester sizing | Biogas composition/flow, digester working volume |
| `cbg_design/upgrading.py` | Water scrubbing / PSA / membrane, published specific-power ranges | CBG product composition, CH4 slip, power, IS 16087 compliance |
| `cbg_design/compression_storage.py` | GPSA-style polytropic multistage compression + CoolProp real-gas storage | Per-stage power, cascade storage volume at 250 bar |
| `cbg_design/digestate.py` | Exact VS-destruction mass balance | Fermented Organic Manure flow, solids content |
| `cbg_design/properties.py` | CoolProp HEOS methane/CO2 mixtures | Real density, compressibility factor Z |

## Validated against real, independently published figures

`examples/full_chain_worked_example.py` runs Barsana Phase I's published
225 TPD feedstock scale across a range of straw:cattle-dung mixes,
reporting each one against the published 10 TPD CBG output honestly —
only a feed close to 100% cattle dung matches, a real, unresolved
finding this project surfaces rather than hides (see
`docs/VALIDATION.md`). Separately, the digestion module's calibration
against three independently published feedstock yield figures produced
a genuine, counter-to-naive-intuition result: already-processed residues
(press mud, cattle dung) calibrate to LOWER biodegradability than fresh
straw, not higher. `docs/VENDOR_REFERENCE.md` cross-checks real CBG
technology providers (Evonik's SEPURAN® Green membrane, KPO Group's CSTR
digester operating parameters) against this project's own method set.

## Related open-source work

[DWSIM](https://github.com/DanWBR/dwsim5), [IDAES](https://github.com/IDAES/idaes-pse) —
general open-source process simulators, same as every sibling repo cites.
[QSDsan](https://github.com/QSD-Group/QSDsan) / [EXPOsan](https://github.com/QSD-Group/EXPOsan)
(Quantitative Sustainable Design Group, UIUC) — the closest existing
open-source prior art for anaerobic digestion / resource-recovery
modeling (consulted for context, not a dependency; every correlation
here is independently sourced and cited in `docs/METHODOLOGY.md`).

## Disclaimer

This tool implements textbook/public-domain conceptual sizing methods
for early-stage screening only. It is not a substitute for a rigorous
process simulator, digestion kinetics model, or vendor-certified
equipment data for detailed design. Always validate against a licensed
simulator and vendor data before committing to equipment specifications.

## License

MIT — see [LICENSE](LICENSE).
