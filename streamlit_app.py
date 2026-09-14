"""Interactive Compressed Biogas (CBG) plant conceptual sizing tool.

Run with: streamlit run streamlit_app.py

All methods are cited public-domain correlations - see README.md and
docs/METHODOLOGY.md for sources.
"""
from __future__ import annotations

import CoolProp.CoolProp as CP
import streamlit as st

from cbg_design import anaerobic_digestion as AD
from cbg_design import compression_storage as CS
from cbg_design import digestate as DG
from cbg_design import feedstock as F
from cbg_design import properties as P
from cbg_design import upgrading as U

st.set_page_config(page_title="CBG Plant Conceptual Sizing", layout="wide")
st.title("Compressed Biogas (CBG) Plant, India SATAT scheme (open-source)")
st.caption(
    "Independent open-source conceptual sizing using public-domain correlations "
    "(Buswell equation, GPSA-style compression) and CoolProp thermodynamics. "
    "Not derived from any proprietary vendor/client data. See README.md and "
    "docs/METHODOLOGY.md for citations, and the disclaimer at the bottom."
)

tab_feed, tab_dig, tab_up, tab_comp, tab_dig2, tab_chain = st.tabs([
    "Feedstock", "Digestion", "Upgrading", "Compression/Storage", "Digestate", "Full Chain",
])

# ---------------------------------------------------------------------
with tab_feed:
    st.header("Feedstock")
    substrate = st.radio("Substrate", ["Paddy straw", "Press mud", "Cattle dung"])
    flow_tpd = st.number_input("Feedstock flow (tonnes/day)", min_value=1.0, value=225.0)
    flow_kg_s = flow_tpd * 1000.0 / 86400.0
    fs = {"Paddy straw": F.paddy_straw, "Press mud": F.press_mud, "Cattle dung": F.cattle_dung}[substrate](flow_kg_s)
    st.session_state["feedstock"] = fs
    colA, colB, colC = st.columns(3)
    colA.metric("VS content", f"{fs.vs_mass_frac:.0%}")
    colB.metric("Published yield", f"{fs.specific_biogas_yield_nm3_per_tonne_fresh:.0f} Nm3/t fresh")
    colC.metric("Calibrated biodegradability", f"{fs.default_biodegradability_fraction:.1%}")

# ---------------------------------------------------------------------
with tab_dig:
    st.header("Anaerobic digestion (Buswell equation)")
    if "feedstock" not in st.session_state:
        st.info("Set up the Feedstock tab first.")
    else:
        fs = st.session_state["feedstock"]
        biodeg = st.slider("Biodegradability fraction", 0.10, 0.90, fs.default_biodegradability_fraction)
        hrt = st.slider("Hydraulic retention time (days)", 15.0, 45.0, 30.0)
        if st.button("Run digestion", type="primary"):
            r = AD.digest(fs, biodeg)
            st.session_state["digestion"] = r
            vol = AD.digester_working_volume(fs, dilution_water_kg_s=fs.mass_flow_kg_s * 2.0, hrt_days=hrt)
            colA, colB, colC = st.columns(3)
            colA.metric("Raw biogas", f"{r.biogas_flow_nm3_s * 86400:,.0f} Nm3/day")
            colB.metric("CH4 content", f"{r.biogas_ch4_mole_frac:.1%}")
            colC.metric("Digester volume", f"{vol['digester_working_volume_m3']:,.0f} m3")

# ---------------------------------------------------------------------
with tab_up:
    st.header("Biogas upgrading")
    if "digestion" not in st.session_state:
        st.info("Run the Digestion tab first.")
    else:
        r = st.session_state["digestion"]
        tech = st.selectbox("Technology", list(U.TECHNOLOGY_SPECIFIC_POWER_KWH_PER_NM3))
        if st.button("Run upgrading", type="primary"):
            u = U.upgrade_biogas(r.biogas_flow_nm3_s, r.biogas_ch4_mole_frac, technology=tech)
            st.session_state["upgraded"] = u
            colA, colB, colC = st.columns(3)
            colA.metric("Product CH4", f"{u.product_ch4_mole_frac:.1%}")
            colB.metric("Power", f"{u.power_kW:.0f} kW")
            colC.metric("Meets IS 16087", str(u.meets_is_16087))

# ---------------------------------------------------------------------
with tab_comp:
    st.header("Compression to 250 bar & storage")
    if "upgraded" not in st.session_state:
        st.info("Run the Upgrading tab first.")
    else:
        u = st.session_state["upgraded"]
        n_stages = st.slider("Number of compressor stages", 2, 6, 4)
        if st.button("Run compression", type="primary"):
            rho_ch4 = CP.PropsSI("Dmass", "T", 273.15, "P", 101325, "Methane")
            mass_flow = u.product_ch4_flow_nm3_s * rho_ch4 / u.product_ch4_mole_frac
            cbg_gas = P.cbg_product(u.product_ch4_mole_frac)
            comp = CS.compress_to_cbg_pressure(cbg_gas, mass_flow, P_in_Pa=1.5e5, n_stages=n_stages)
            store = CS.cascade_storage_volume(cbg_gas, mass_to_store_kg=mass_flow * 3600 * 8)
            colA, colB, colC = st.columns(3)
            colA.metric("Total power", f"{comp.total_power_kW:,.0f} kW")
            colB.metric("Storage Z factor", f"{store['compressibility_factor_Z']:.3f}")
            colC.metric("8h storage volume", f"{store['storage_volume_m3']:,.1f} m3")

# ---------------------------------------------------------------------
with tab_dig2:
    st.header("Digestate (Fermented Organic Manure)")
    if "digestion" not in st.session_state:
        st.info("Run the Digestion tab first.")
    else:
        fs, r = st.session_state["feedstock"], st.session_state["digestion"]
        if st.button("Characterize digestate", type="primary"):
            dg = DG.characterize_digestate(fs, r, dilution_water_kg_s=fs.mass_flow_kg_s * 2.0)
            colA, colB = st.columns(2)
            colA.metric("Digestate flow", f"{dg.digestate_flow_m3_day:,.0f} m3/day")
            colB.metric("Solids content", f"{dg.solids_content_mass_frac:.1%}")

# ---------------------------------------------------------------------
with tab_chain:
    st.header("Full chain: feedstock -> CBG")
    st.caption("Runs every module in sequence - see examples/full_chain_worked_example.py.")
    st.markdown(
        "This mirrors the repo's own worked example, run at Adani Total Gas's real, publicly "
        "disclosed Barsana plant scale (225 t/day feedstock, published 10 t/day CBG). See "
        "`docs/VALIDATION.md` for an honest, unresolved gap the comparison surfaced across "
        "different feedstock mix assumptions. Use the individual tabs above to explore each "
        "unit interactively, or run `python examples/full_chain_worked_example.py` for the full trace."
    )

st.divider()
st.caption(
    "**Disclaimer**: this tool implements textbook/public-domain conceptual sizing "
    "methods for early-stage screening only. It is not a substitute for a rigorous "
    "process simulator, digestion kinetics model, or vendor-certified equipment data "
    "for detailed design."
)
