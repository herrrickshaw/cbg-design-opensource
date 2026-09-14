"""Thermophysical properties for biogas/CBG components, built on CoolProp.

Same pattern as every sibling repo (lng-design-opensource, biomass-to-
syngas-opensource, coal-to-urea-design-opensource, ethanol-design-
opensource): use CoolProp's real equation of state directly rather than
an ideal-gas assumption. This matters a great deal more here than in most
sibling modules -- CBG is stored at up to 250 bar (IS 16087:2016), where
methane's real-gas compressibility factor deviates from 1.0 by well over
10%, so an ideal-gas storage-volume estimate would be meaningfully wrong
(verified in this module's own test suite: Z ~ 0.86 at 250 bar / 25 C,
vs. Z = 1.0 assumed by an ideal-gas calculation -- see docs/VALIDATION.md)."""
from __future__ import annotations

from dataclasses import dataclass

import CoolProp.CoolProp as CP

MW_METHANE = CP.PropsSI("M", "Methane") * 1000.0    # g/mol, ~16.043
MW_CO2 = CP.PropsSI("M", "CarbonDioxide") * 1000.0  # g/mol, ~44.010
MW_AIR = 28.96  # g/mol, standard reference value, used only for a relative-density check


@dataclass
class GasMixture:
    """A CoolProp HEOS mixture, keyed by CoolProp fluid names."""

    composition: dict[str, float]  # component -> mole fraction (sums to 1)

    def __post_init__(self) -> None:
        total = sum(self.composition.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Mole fractions must sum to 1.0, got {total}")

    def _heos_string(self) -> str:
        return "&".join(f"{name}[{frac}]" for name, frac in self.composition.items())

    def molecular_weight(self) -> float:
        """g/mol"""
        return CP.PropsSI("M", self._heos_string()) * 1000.0

    def prop(self, output: str, T: float, P: float) -> float:
        return CP.PropsSI(output, "T", T, "P", P, self._heos_string())

    def density(self, T: float, P: float) -> float:
        return self.prop("Dmass", T, P)

    def compressibility(self, T: float, P: float) -> float:
        return self.prop("Z", T, P)


def raw_biogas(ch4_mole_frac: float = 0.60) -> GasMixture:
    """Typical raw (pre-upgrading) biogas composition: methane + CO2 only
    (trace H2S/N2/moisture omitted at this conceptual level) -- 55-65%
    CH4 is the commonly cited range for agricultural-residue/manure
    digestion (see docs/METHODOLOGY.md); default 60% is the range's
    midpoint."""
    return GasMixture({"Methane": ch4_mole_frac, "CarbonDioxide": 1 - ch4_mole_frac})


def cbg_product(ch4_mole_frac: float = 0.95) -> GasMixture:
    """Upgraded CBG product composition -- IS 16087:2016 requires a
    minimum of 90% CH4; this module defaults to 95% as a representative
    achievable upgraded-product purity (see `upgrading.py`)."""
    return GasMixture({"Methane": ch4_mole_frac, "CarbonDioxide": 1 - ch4_mole_frac})
