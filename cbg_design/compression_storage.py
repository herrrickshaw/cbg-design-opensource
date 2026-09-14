"""CBG compression to 250 bar (IS 16087:2016) and cascade storage sizing.

Compression: the same polytropic head/efficiency method as the sibling
lng-design-opensource repo's `compressor.py` and coal-to-urea-design-
opensource's `ammonia_synthesis.py` makeup-gas compressor -- GPSA
Engineering Data Book, 14th ed., Section 13 ("Compressors"), also
standard in Boyce, "Gas Turbine Engineering Handbook". The polytropic
exponent n is derived from the isentropic exponent k (evaluated from
CoolProp's real-gas Cp/Cv at each stage's inlet, not an ideal-gas
assumption) via (n-1)/n = (k-1)/(k*eta_p). Multistage sizing splits the
overall pressure ratio evenly on a log basis across stages (GPSA's
standard first-pass frame-selection heuristic) with intercooling back to
a fixed suction temperature between stages -- necessary here because the
overall ratio (raw/upgraded biogas at a few bar, up to 250 bar) is far
too large for one stage.

Storage: CBG at 250 bar deviates substantially from ideal-gas behaviour
(real-gas compressibility factor Z ~ 0.86 at 250 bar/25 C for methane,
verified in this module's own test suite against CoolProp's HEOS methane
equation of state -- an ideal-gas estimate would overstate the storage
volume needed by roughly that same margin). Cascade storage (a bank of
high-pressure cylinders, the IS 16087 term for CBG's standard storage
format) is sized directly from CoolProp's real density at 250 bar rather
than PV = nRT."""
from __future__ import annotations

import math
from dataclasses import dataclass

import CoolProp.CoolProp as CP


@dataclass
class CompressorStageResult:
    stage: int
    P_in_Pa: float
    P_out_Pa: float
    T_out_K: float
    polytropic_head_kJ_kg: float
    power_kW: float


@dataclass
class CompressionResult:
    n_stages: int
    stages: list
    total_power_kW: float


def _isentropic_exponent(gas_mixture, T_K: float, P_Pa: float) -> float:
    cp = gas_mixture.prop("Cpmass", T_K, P_Pa)
    cv = gas_mixture.prop("Cvmass", T_K, P_Pa)
    return cp / cv


def _compress_one_stage(gas_mixture, T_in_K: float, P_in_Pa: float, P_out_Pa: float,
                        mass_flow_kg_s: float, polytropic_efficiency: float) -> CompressorStageResult:
    k = _isentropic_exponent(gas_mixture, T_in_K, P_in_Pa)
    n = 1.0 / (1.0 - (k - 1.0) / (k * polytropic_efficiency))
    Z = gas_mixture.compressibility(T_in_K, P_in_Pa)
    M = gas_mixture.molecular_weight() / 1000.0  # kg/mol
    R_specific = 8.314462618 / M  # J/kg-K

    pressure_ratio = P_out_Pa / P_in_Pa
    head_J_kg = Z * R_specific * T_in_K * (n / (n - 1.0)) * (pressure_ratio ** ((n - 1.0) / n) - 1.0)
    power_kW = mass_flow_kg_s * head_J_kg / polytropic_efficiency / 1000.0
    T_out_K = T_in_K * pressure_ratio ** ((n - 1.0) / n)

    return CompressorStageResult(stage=0, P_in_Pa=P_in_Pa, P_out_Pa=P_out_Pa, T_out_K=T_out_K,
                                 polytropic_head_kJ_kg=head_J_kg / 1000.0, power_kW=power_kW)


def compress_to_cbg_pressure(gas_mixture, mass_flow_kg_s: float, P_in_Pa: float,
                             P_out_Pa: float = 250e5, T_suction_K: float = 313.15,
                             n_stages: int = 4, polytropic_efficiency: float = 0.75) -> CompressionResult:
    """Splits P_out/P_in evenly (log-mean) across `n_stages`, with
    intercooling back to `T_suction_K` before every stage after the
    first -- the standard GPSA equal-pressure-ratio-per-stage heuristic.
    250 bar / a few bar of suction pressure typically needs 3-5 stages
    to keep each stage's discharge temperature and pressure ratio within
    normal centrifugal/reciprocating compressor frame limits; this
    module defaults to 4 and lets the caller override."""
    if P_out_Pa <= P_in_Pa:
        raise ValueError("P_out_Pa must exceed P_in_Pa")
    overall_ratio = P_out_Pa / P_in_Pa
    stage_ratio = overall_ratio ** (1.0 / n_stages)

    stages = []
    P_stage_in = P_in_Pa
    total_power = 0.0
    for i in range(1, n_stages + 1):
        P_stage_out = P_stage_in * stage_ratio
        result = _compress_one_stage(gas_mixture, T_suction_K, P_stage_in, P_stage_out,
                                     mass_flow_kg_s, polytropic_efficiency)
        result.stage = i
        stages.append(result)
        total_power += result.power_kW
        P_stage_in = P_stage_out

    return CompressionResult(n_stages=n_stages, stages=stages, total_power_kW=total_power)


def cascade_storage_volume(gas_mixture, mass_to_store_kg: float, P_Pa: float = 250e5,
                           T_K: float = 313.15) -> dict:
    """Storage volume from CoolProp's real density at storage conditions
    (not the ideal-gas law) -- see module docstring for why this matters
    at 250 bar."""
    rho_real = gas_mixture.density(T_K, P_Pa)
    rho_ideal = P_Pa * (gas_mixture.molecular_weight() / 1000.0) / (8.314462618 * T_K)
    volume_m3 = mass_to_store_kg / rho_real
    return {"real_density_kg_m3": rho_real, "ideal_gas_density_kg_m3": rho_ideal,
            "compressibility_factor_Z": gas_mixture.compressibility(T_K, P_Pa),
            "storage_volume_m3": volume_m3}
