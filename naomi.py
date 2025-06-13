import streamlit as st
import pandas as pd
import numpy as np
from math import exp
import altair as alt

# -------------------- PAGE CONFIG ---------------------------
st.set_page_config(
    page_title="Rainwater & PVC Simulator",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- STYLES --------------------------------
CUSTOM_CSS = """
<style>
/* Rounded white main container with soft shadow */
section.main > div {
    background-color: #ffffffdd;
    border-radius: 1.2rem;
    padding: 2rem 3rem;
    box-shadow: 0 8px 25px rgba(0,0,0,.07);
}
/* Hide default hamburger icon */
header .st-emotion-cache-18ni7ap {
    display: none;
}
/* Accent headings */
h1, h2, h3, h4 { color: #0066cc; }

/* Center align KPI metrics */
[data-testid="stMetric"] svg {
    display: none !important;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------- HEADER --------------------------------
st.title("💧 Rainwater Harvest & PVC Durability Simulator")
st.markdown(
    "Use this interactive tool to **estimate harvestable rainwater** from your roof and **project PVC structural integrity** under long‑term moisture exposure.  All calculations are **for educational planning only** — always consult a qualified engineer for critical designs."
)

# -------------------- SIDEBAR INPUTS ------------------------
st.sidebar.header("📋 Input Parameters")

# --- Roof & Collection ---
roof_area = st.sidebar.number_input(
    "Roof Surface Area (m²)",
    min_value=10.0,
    max_value=10000.0,
    value=250.0,
    step=10.0,
    format="%0.1f",
)

efficiency = st.sidebar.slider(
    "Overall Collection Efficiency (run‑off × filter) %",
    min_value=50,
    max_value=100,
    value=85,
    step=1,
    help="Accounts for roof run‑off (typ. 90–95 %) and first‑flush / filter losses.",
) / 100.0

# --- PVC Degradation ---
deg_coeff = st.sidebar.slider(
    "PVC Moisture‑Degradation Coefficient  (per metre of cumulative rainfall)",
    min_value=0.005,
    max_value=0.10,
    value=0.04,
    step=0.005,
    format="%0.3f",
    help="Higher = faster decay; typical empirical range 0.02–0.06.  Integrity = 100 % · e^(‑k·Σrain).",
)

service_years = st.sidebar.slider(
    "Projection Period (years)",
    min_value=1,
    max_value=40,
    value=25,
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Tip:**  You can **edit the rainfall table** below to model other locations or climate‑change scenarios.  "
    "Values are automatically used in calculations."
)

# -------------------- DEFAULT RAINFALL TABLE ---------------
DEFAULT_RAIN = [
    {"Month": "Jan", "Rainfall_mm": 8, "Rainy_Days": 1.8},
    {"Month": "Feb", "Rainfall_mm": 23, "Rainy_Days": 3.0},
    {"Month": "Mar", "Rainfall_mm": 46, "Rainy_Days": 7.5},
    {"Month": "Apr", "Rainfall_mm": 89, "Rainy_Days": 13},
    {"Month": "May", "Rainfall_mm": 137, "Rainy_Days": 17.8},
    {"Month": "Jun", "Rainfall_mm": 193, "Rainy_Days": 20.2},
    {"Month": "Jul", "Rainfall_mm": 155, "Rainy_Days": 16.5},
    {"Month": "Aug", "Rainfall_mm": 127, "Rainy_Days": 15.4},
    {"Month": "Sep", "Rainfall_mm": 183, "Rainy_Days": 20.6},
    {"Month": "Oct", "Rainfall_mm": 140, "Rainy_Days": 17.4},
    {"Month": "Nov", "Rainfall_mm": 33, "Rainy_Days": 5.1},
    {"Month": "Dec", "Rainfall_mm": 10, "Rainy_Days": 2.0},
]

rain_df = st.data_editor(
    pd.DataFrame(DEFAULT_RAIN),
    use_container_width=True,
    num_rows="fixed",
    hide_index=True,
    key="rain_editor",
)

# -------------------- RAINWATER COLLECTION CALC -------------
rain_df["Rainfall_m"] = rain_df["Rainfall_mm"] / 1000.0
rain_df["Collected_L"] = roof_area * rain_df["Rainfall_m"] * efficiency * 1000  # L per month

annual_volume_l = rain_df["Collected_L"].sum()
annual_volume_m3 = annual_volume_l / 1000

st.subheader("📈 Annual Harvestable Water")
st.metric("Estimated Annual Volume", f"{annual_volume_l:,.0f} L", f"{annual_volume_m3:,.1f} m³")

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Monthly Rainfall vs. Collection")
    chart_data = rain_df.melt(id_vars="Month", value_vars=["Rainfall_mm", "Collected_L"], var_name="Type", value_name="Value")
    bar = (
        alt.Chart(chart_data)
        .mark_bar()
        .encode(
            x=alt.X("Month:N", title="Month"),
            y=alt.Y("Value:Q", title="Rainfall (mm) / Collection (L)", axis=alt.Axis(format=",")),
            color="Type:N",
            tooltip=["Type", "Value"]
        )
        .properties(height=350)
    )
    st.altair_chart(bar, use_container_width=True)

with col2:
    # ---------------- PVC DEGRADATION SIM -------------------
    monthly_rain_m = rain_df["Rainfall_m"].values  # length 12
    cumulative_rain_m_per_year = np.cumsum(np.tile(monthly_rain_m, service_years)).reshape(service_years, 12)[:, -1]
    integrity = 100 * np.exp(-deg_coeff * cumulative_rain_m_per_year)
    years = np.arange(1, service_years + 1)

    pvc_df = pd.DataFrame({"Year": years, "PVC Integrity %": integrity})

    st.markdown("#### Projected PVC Structural Integrity")
    line = (
        alt.Chart(pvc_df)
        .mark_line(point=True)
        .encode(x="Year:Q", y=alt.Y("PVC Integrity %:Q", scale=alt.Scale(domain=[0, 100])), tooltip=["Year", "PVC Integrity %"])
        .properties(height=350)
    )
    st.altair_chart(line, use_container_width=True)

# -------------------- TANK SIZE RECOMMENDATION --------------
st.markdown("---")
REC_MIN_L, REC_MAX_L = 140_000, 280_000
state = (
    "✅ **Within** recommended range" if REC_MIN_L <= annual_volume_l <= REC_MAX_L
    else ("⬆️ **Above** recommended range" if annual_volume_l > REC_MAX_L else "⬇️ **Below** recommended range")
)

st.header("🏷️ Tank Sizing Guidance")
left, right = st.columns([3,2])
with left:
    st.write(
        f"**Recommended storage**: 140 – 280 m³ (140 000 – 280 000 L)\n\n"
        f"**Your estimated requirement**: **{annual_volume_l:,.0f} L** / {annual_volume_m3:,.1f} m³ — {state}."
    )
    st.write(
        "*Tip: choose a tank that balances budget, space, and expected dry‑season demand.  Modular tanks or multiple "
        "smaller units can also be considered.*"
    )
with right:
    st.image(
        "https://images.unsplash.com/photo-1581093588401-8a1a0acdc0e2?auto=format&fit=crop&w=600&q=60",
        caption="Polyethylene rainwater tank (illustrative)",
    )

# -------------------- FOOTER --------------------------------
st.markdown("""<small>© praise_adeyeye2025 — Streamlit demo app generated for educational purposes.</small>""", unsafe_allow_html=True)
