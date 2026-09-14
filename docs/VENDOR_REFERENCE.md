# CBG Technology Provider Reference

Same purpose as the sibling lng-design-opensource/coal-to-urea-design-
opensource repos' `docs/VENDOR_REFERENCE.md`: for each named provider
below, does their own public page publish a genuine, verifiable technical
detail this project's `upgrading.py`/`anaerobic_digestion.py` sizing can
be cross-checked against — not vendor endorsement, not a procurement
recommendation. Every entry was fetched and its content inspected at the
time of writing (September 2026); where a figure could only be confirmed
via a secondary source rather than the vendor's own page, that is stated
explicitly rather than cited as if independently verified.

| Provider | Public resource (verified) | What it confirms | Relevance to this repo |
|---|---|---|---|
| **Evonik Industries** | [Biogas/CNG production in India](https://www.membrane-separation.com/en/biogas-cng-production-in-india) (membrane-separation.com, an Evonik-operated site) | SEPURAN® Green hollow-fibre membrane technology, a real named product: "patented 3 stage membrane-based gas separation", produces gas ">90% methane", "up to 99% methane recovery achievable". No explicit kWh/Nm3 specific-power figure is published on this page. | Directly confirms `upgrading.py`'s "membrane" technology as a real, actively marketed option for the Indian CBG market (not solely a generic literature category), and that IS 16087's 90% CH4 floor is the technology's own stated target purity. |
| **KPO Group** | [Services](https://www.kpogroup.in/services.php) (kpogroup.in) | Real CSTR (Continuous Stirred Tank Reactor) digester operating parameters: **32-38 C, 10-12% organic loading rate**, feeding on press mud/cow dung/poultry/food/vegetable waste — plus separately offered H2S removal, water-scrubber, PSA, and membrane upgrading, matching this project's own `upgrading.py` technology set exactly. | The 32-38 C operating range independently confirms `anaerobic_digestion.py`'s implicit mesophilic-digestion assumption (Buswell's equation itself is temperature-independent, but real digester biology is mesophilic in this range); the loading-rate figure is a real design cross-check this project's `digester_working_volume()` HRT-based sizing does not itself derive. |
| **Green Elephant Engineering** | [greenelephant.in](https://greenelephant.in/) (own site) confirms the company is real and active in CSTR-based anaerobic digestion + biogas upgrading to CBG, but does **not** itself publish the specific plant-capacity figures reported about it. | Secondary sources (environmental-expert.com, theceo.in) report a real Satara, Maharashtra plant processing up to 600 m3/day of spent wash into 7,920 kg/day RNG at 97% methane, financed by IREDA/KfW — a genuine India-specific operating data point, but **not independently confirmed on the company's own site**, so flagged here rather than treated as verified. | If confirmed, would be a real spent-wash-to-CBG operating benchmark directly relevant to this repo's `press_mud`/spent-wash feedstock class and a cross-link to the `ethanol-design-opensource` sibling's own vinasse output (see `stillage.py`'s docstring there). |

## What was checked but didn't clear the verification bar

- **Advance Biofuel (Biotexus Energy Pvt. Ltd.)** and **Organic Recycling
  Systems Limited** are both real, active Indian CBG EPC companies
  (confirmed via search results describing specific project experience),
  but their own sites were not fetched and inspected in the time
  available for this document — a genuine gap, not a claim that they
  lack real capability.

## Note on this document's scope vs. the sibling repos'

The sibling LNG/coal-to-urea `VENDOR_REFERENCE.md` cross-checks named
international equipment manufacturers' published dimensional/pressure-
class catalogs against computed sizing outputs (valve Cv, vessel
diameter, exchanger shell size). This document is intentionally smaller
in scope: the CBG technology landscape in India is dominated by
turnkey EPC/technology-provider firms (KPO Group, Green Elephant,
Evonik) rather than a standardized component-catalog market the way
valves or shell-and-tube exchangers are, so there is less of a numeric
size-table tradition to cross-check against in the first place.
