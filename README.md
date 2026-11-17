# CBG Design (open-source)

Conceptual sizing tools for a Compressed Biogas (CBG) plant under India's SATAT scheme. Given a feedstock
(paddy straw, press mud, cattle dung or a co-digestion mix) it estimates biogas yield with the Buswell equation,
digester volume, upgrading power to the IS 16087 spec, multistage compression to 250 bar with CoolProp real-gas
storage sizing, and the digestate (Fermented Organic Manure) mass balance. Outputs are Python dataclasses/dicts, a
printed worked example and a Streamlit app.

> Status: maintained. Literature-only and generic: nothing here derives from proprietary vendor, licensor or client
> engineering data. Educational use only; not a substitute for a process simulator or vendor-certified data.

<!-- how-to-use-with-ai -->
New here? See [How to use this repo with AI (Claude, Gemini, ChatGPT)](HOW_TO_USE_WITH_AI.md).

**Real-world motivation**: SATAT (launched 2018-10-01) has 133 commissioned CBG plants as of India Energy Week 2026
(926 TPD combined output, 83 more under construction). The worked example runs at the publicly disclosed scale of
Adani Total Gas's Barsana plant (225 TPD feedstock, 10 TPD CBG Phase I); see `docs/VALIDATION.md` for the honest,
unresolved gap that comparison surfaced.

## What it does
- Characterises feedstocks (VS content, elemental composition, published specific yield, calibrated biodegradability, HRT).
- Evaluates the Buswell equation for theoretical methane yield, corrected by a per-substrate biodegradability factor.
- Sizes the digester working volume from hydraulic retention time (cattle dung defaults to a vendor-sourced 85 days).
- Upgrades raw biogas (water scrubbing / PSA / membrane) using published specific-power ranges and checks IS 16087 (>= 90% CH4).
- Compresses to 250 bar (GPSA-style polytropic, equal ratio per stage) and sizes cascade storage from CoolProp real density.
- Computes the digestate / Fermented Organic Manure mass balance by exact VS destruction.

## Quick start
```bash
git clone https://github.com/herrrickshaw/cbg-design-opensource.git
cd cbg-design-opensource
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python examples/full_chain_worked_example.py     # feedstock -> CBG, end to end
streamlit run streamlit_app.py                   # interactive app
```

## How it works
```
feedstock.py -> anaerobic_digestion.py -> upgrading.py -> compression_storage.py
                      \-> digestate.py                          ^
                                         properties.py (CoolProp mixtures) -+
```

| Stage | Module | Method | Key outputs |
|---|---|---|---|
| Feedstock | `cbg_design/feedstock.py` | Published India specific-yield ranges; per-substrate calibrated biodegradability | Paddy straw, press mud, cattle dung, co-digestion mixes |
| Digestion | `cbg_design/anaerobic_digestion.py` | Buswell equation + biodegradability correction; HRT sizing | Biogas flow/composition, digester working volume |
| Upgrading | `cbg_design/upgrading.py` | Published specific-power ranges per technology | Product CH4 fraction, CH4 slip, power, IS 16087 compliance |
| Compression/storage | `cbg_design/compression_storage.py` | Polytropic multistage compression; real-gas storage | Per-stage power, storage volume at 250 bar |
| Digestate | `cbg_design/digestate.py` | VS-destruction mass balance | FOM flow, solids content |
| Properties | `cbg_design/properties.py` | CoolProp HEOS CH4/CO2 mixtures | Real density, compressibility Z |

Design decisions: CoolProp real-gas properties rather than the ideal-gas law, because methane at 250 bar has Z ~ 0.86;
biodegradability is back-solved per substrate against published yields (press mud 0.273 and cattle dung 0.292 are
lower than paddy straw 0.533, since they are already-processed residues); methods and citations are in
`docs/METHODOLOGY.md`, calibration derivations in `docs/VALIDATION.md`, vendor cross-checks (Evonik SEPURAN Green,
KPO Group, WELTEC BIOPOWER, Greenlane Renewables) in `docs/VENDOR_REFERENCE.md`.

## Repository layout
| Path | Purpose |
|---|---|
| `cbg_design/` | The six calculation modules above |
| `streamlit_app.py` | Interactive tabs for each stage |
| `examples/full_chain_worked_example.py` | End-to-end run at Barsana Phase I scale across straw:dung mixes |
| `tests/` | Unit tests per module, a golden-baseline characterisation test, an example smoke test |
| `docs/` | Methodology, validation and vendor reference |
| `HOW_TO_USE_WITH_AI.md` | Prompting guide for AI assistants |

## Data sources
No data is downloaded at run time. All inputs are literature values cited in the module docstrings and
`docs/METHODOLOGY.md` (e.g. Buswell/Deublein & Steinhauser for stoichiometry and elemental compositions; a 2025
ScienceDirect review of CBG from agricultural residues in India for yields; IS 16087:2016 as summarised by IOCL's
SATAT FAQ and PNGRB; GPSA Engineering Data Book for compression).

## Configuration
No environment variables or secrets. All parameters are function arguments with documented defaults (for example
`P_out_Pa=250e5`, `T_suction_K=313.15`, `n_stages=4`, `polytropic_efficiency=0.75`).

## Testing
```bash
pytest -q          # 34 tests
ruff check .
```
`tests/test_golden_baseline.py` pins every public numeric output to values captured from the pre-refactor code.

## Limitations and known issues
- Conceptual, early-stage screening only; upgrading uses published specific-power ranges, not mass-transfer or adsorption models.
- Real co-digestion synergies (up to ~20% yield uplift reported) are not modelled; blends are linear.
- Only a feed close to 100% cattle dung reproduces Barsana's published 10 TPD CBG; any straw-inclusive mix overshoots.
  The actual feedstock split is undisclosed (see `docs/VALIDATION.md`).
- The Streamlit digestion tab's HRT slider only drives the displayed digester volume.

## Related repositories
[lng-design-opensource](https://github.com/herrrickshaw/lng-design-opensource),
[biomass-to-syngas-opensource](https://github.com/herrrickshaw/biomass-to-syngas-opensource),
[coal-to-urea-design-opensource](https://github.com/herrrickshaw/coal-to-urea-design-opensource),
[ethanol-design-opensource](https://github.com/herrrickshaw/ethanol-design-opensource) share the same discipline.
Related open-source work: [DWSIM](https://github.com/DanWBR/dwsim5), [IDAES](https://github.com/IDAES/idaes-pse),
[QSDsan](https://github.com/QSD-Group/QSDsan) / [EXPOsan](https://github.com/QSD-Group/EXPOsan) (consulted for context, not a dependency).

## Licence
MIT; see [LICENSE](LICENSE).
