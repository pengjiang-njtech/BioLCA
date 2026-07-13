
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from defaults import (
    DEFAULT_BACKGROUND,
    DEFAULT_CREDITS,
    DEFAULT_INVENTORY,
    PROCESS_ORDER,
    PROCESS_ICONS,
)
from engine import calculate_lca, build_excel_report, run_sensitivity


st.set_page_config(
    page_title="ThermoLCA",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --green: #2F9E44;
        --green-soft: #ECF8EF;
        --line: #E5E7EB;
        --muted: #64748B;
        --bg: #F8FAFC;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1.5rem;
        max-width: 1700px;
    }
    [data-testid="stSidebar"] {
        background: #FBFCFD;
        border-right: 1px solid var(--line);
    }
    .thermo-title {
        font-size: 2.25rem;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.2rem;
    }
    .thermo-subtitle {
        color: var(--muted);
        margin-bottom: 1rem;
    }
    .process-card {
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px 8px;
        min-height: 128px;
        text-align: center;
        background: white;
        box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
    }
    .process-card.active {
        border: 2px solid #47B35A;
        background: #FBFFFC;
    }
    .process-icon {
        font-size: 2rem;
        margin-bottom: .35rem;
    }
    .process-name {
        font-weight: 750;
    }
    .process-note {
        color: var(--muted);
        font-size: .82rem;
        margin-top: .25rem;
    }
    .summary-box {
        border: 1px solid #CDEBD2;
        background: linear-gradient(180deg, #F4FCF6 0%, #ECF8EF 100%);
        border-radius: 14px;
        padding: 18px;
        text-align: center;
    }
    .summary-value {
        font-size: 3rem;
        color: var(--green);
        font-weight: 800;
        line-height: 1;
    }
    .summary-unit {
        color: var(--green);
        font-weight: 700;
        margin-top: .5rem;
    }
    .panel {
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 16px;
        background: white;
        box-shadow: 0 1px 2px rgba(15, 23, 42, .04);
        margin-bottom: 14px;
    }
    .small-note {
        font-size: .84rem;
        color: var(--muted);
    }
    .pill-ok {
        color: #167D2C;
        background: #EAF8ED;
        border-radius: 999px;
        padding: 2px 8px;
        font-size: .78rem;
        font-weight: 700;
    }
    .footer {
        color: var(--muted);
        font-size: .82rem;
        padding-top: .7rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state() -> None:
    if "inventory" not in st.session_state:
        st.session_state.inventory = DEFAULT_INVENTORY.copy()
    if "background" not in st.session_state:
        st.session_state.background = DEFAULT_BACKGROUND.copy()
    if "credits" not in st.session_state:
        st.session_state.credits = DEFAULT_CREDITS.copy()
    if "selected_process" not in st.session_state:
        st.session_state.selected_process = "Transportation"
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "transport_mass_t" not in st.session_state:
        st.session_state.transport_mass_t = 1.0
    if "return_trip" not in st.session_state:
        st.session_state.return_trip = False


def reset_demo() -> None:
    st.session_state.inventory = DEFAULT_INVENTORY.copy()
    st.session_state.background = DEFAULT_BACKGROUND.copy()
    st.session_state.credits = DEFAULT_CREDITS.copy()
    st.session_state.last_result = None
    st.session_state.transport_mass_t = 1.0
    st.session_state.return_trip = False


init_state()

# Header
h1, h2 = st.columns([0.75, 0.25])
with h1:
    st.markdown('<div class="thermo-title">🌿 ThermoLCA</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="thermo-subtitle">Process-informed Life Cycle Assessment Platform</div>',
        unsafe_allow_html=True,
    )
with h2:
    st.write("")

# Sidebar project settings
with st.sidebar:
    st.markdown("### PROJECT")
    project_name = st.text_input("Project Name", "Bioethanol Production")
    product_name = st.text_input("Product", "Ethanol")

    fu1, fu2 = st.columns([0.52, 0.48])
    with fu1:
        fu_amount = st.number_input("Functional Unit", min_value=0.0001, value=1.0)
    with fu2:
        fu_unit = st.selectbox("Unit", ["kg", "t", "MJ"])

    system_boundary = st.selectbox(
        "System Boundary",
        ["Cradle-to-Gate", "Gate-to-Gate", "Cradle-to-Grave"],
    )
    allocation_method = st.selectbox(
        "Allocation Method",
        ["Substitution"],
        help="ThermoLCA v1.0 uses substitution/avoided-burden for multi-product systems.",
    )

    st.divider()
    st.markdown("### NAVIGATION")
    page = st.radio(
        "Navigation",
        [
            "Process Modeling",
            "Background Database",
            "Substitution & Credits",
            "Results & Analysis",
            "Sensitivity Analysis",
            "Report & Export",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    if st.button("＋ New Project", use_container_width=True):
        reset_demo()
        st.rerun()

functional_unit = f"{fu_amount:g} {fu_unit} {product_name}"

# Shared result quick summary
def render_quick_summary(result: dict | None) -> None:
    if not result or result.get("errors"):
        st.markdown(
            """
            <div class="summary-box">
                <div class="summary-value">—</div>
                <div class="summary-unit">kg CO₂-eq / functional unit</div>
                <div class="small-note">Run the calculation to update results.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="summary-box">
            <div class="summary-value">{result["carbon_footprint"]:.3f}</div>
            <div class="summary-unit">kg CO₂-eq / kg {product_name}</div>
            <div class="small-note">Net carbon footprint</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    a, b, c = st.columns(3)
    a.metric("Total Emissions", f'{result["total_emissions"]:.2f}')
    b.metric("Total Credits", f'{result["total_credits"]:.2f}')
    c.metric("Net Emissions", f'{result["net_emissions"]:.2f}')


# -----------------------------
# Process Modeling
# -----------------------------
if page == "Process Modeling":
    top_main, top_side = st.columns([0.76, 0.24], gap="large")

    with top_main:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        t1, t2 = st.columns([0.7, 0.3])
        with t1:
            st.subheader("Process Flow Diagram")
            st.caption("Select a unit process and enter foreground inventory data.")
        with t2:
            c1, c2 = st.columns(2)
            c1.button("＋ Add Unit Process", use_container_width=True, disabled=True)
            c2.button("✎ Edit Flow", use_container_width=True, disabled=True)

        cols = st.columns(len(PROCESS_ORDER))
        for col, name in zip(cols, PROCESS_ORDER):
            icon = PROCESS_ICONS[name]
            is_active = name == st.session_state.selected_process
            cls = "process-card active" if is_active else "process-card"
            rows = st.session_state.inventory[
                st.session_state.inventory["Unit process"] == name
            ]
            note = rows.iloc[0]["Flow"] if not rows.empty else "Not configured"
            with col:
                st.markdown(
                    f"""
                    <div class="{cls}">
                        <div class="process-icon">{icon}</div>
                        <div class="process-name">{name}</div>
                        <div class="process-note">{note}</div>
                        <div style="margin-top:.45rem">✅</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    f"Open {name}",
                    key=f"open_{name}",
                    use_container_width=True,
                ):
                    st.session_state.selected_process = name
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        selected = st.session_state.selected_process
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader(f"{PROCESS_ICONS[selected]} {selected}")

        unit_df = st.session_state.inventory[
            st.session_state.inventory["Unit process"] == selected
        ].copy()

        edited_unit = st.data_editor(
            unit_df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Unit process": st.column_config.SelectboxColumn(
                    "Unit Process", options=PROCESS_ORDER, required=True
                ),
                "Flow": st.column_config.TextColumn("Flow", required=True),
                "Amount": st.column_config.NumberColumn(
                    "Amount", min_value=0.0, format="%.6f"
                ),
                "Unit": st.column_config.TextColumn("Unit", required=True),
                "Type": st.column_config.SelectboxColumn(
                    "Type",
                    options=["Input", "Transport", "Direct emission", "Product"],
                    required=True,
                ),
                "Notes": st.column_config.TextColumn("Notes"),
            },
            key=f"editor_{selected}",
        )

        # Replace selected process rows with edited rows
        rest = st.session_state.inventory[
            st.session_state.inventory["Unit process"] != selected
        ]
        st.session_state.inventory = pd.concat(
            [rest, edited_unit], ignore_index=True
        )

        if selected == "Transportation":
            st.markdown("#### Transportation Activity")
            tc1, tc2 = st.columns(2)
            with tc1:
                st.session_state.transport_mass_t = st.number_input(
                    "Transported Amount (t)",
                    min_value=0.0,
                    value=float(st.session_state.transport_mass_t),
                    step=0.1,
                )
            with tc2:
                st.session_state.return_trip = st.toggle(
                    "Include Return Trip",
                    value=bool(st.session_state.return_trip),
                )
            st.info(
                "For transportation rows, Amount is the one-way distance in km. "
                "ThermoLCA converts distance × transported mass to t·km."
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.subheader("All Unit Processes Overview")
        overview = (
            st.session_state.inventory.groupby("Unit process", as_index=False)
            .agg(
                Items=("Flow", lambda x: ", ".join(map(str, x.head(3)))),
                Rows=("Flow", "count"),
            )
        )
        overview["Status"] = "Completed"
        st.dataframe(overview, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with top_side:
        st.subheader("Carbon Footprint Summary")
        render_quick_summary(st.session_state.last_result)

        if st.session_state.last_result and not st.session_state.last_result.get("errors"):
            st.markdown("#### Contribution Analysis")
            by_process = st.session_state.last_result["by_process"]
            if not by_process.empty:
                fig = px.pie(
                    by_process,
                    names="Unit process",
                    values="GWP",
                    hole=0.48,
                )
                fig.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    legend=dict(orientation="h"),
                    height=360,
                )
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Substitution & Credits Summary")
        credits_view = st.session_state.credits.copy()
        credits_view["Credit"] = (
            pd.to_numeric(credits_view["Amount"], errors="coerce").fillna(0)
            * pd.to_numeric(credits_view["Credit factor"], errors="coerce").fillna(0)
        )
        st.dataframe(
            credits_view[["By-product", "Reference product", "Credit"]],
            use_container_width=True,
            hide_index=True,
        )

# -----------------------------
# Background Database
# -----------------------------
elif page == "Background Database":
    st.subheader("Background Database")
    st.caption("Built-in, editable background emission factors.")

    st.warning(
        "The default factors are demonstration values. Replace them with verified "
        "CLCD, CPCD, ecoinvent or literature values before formal research use."
    )

    st.session_state.background = st.data_editor(
        st.session_state.background,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=["Fuel", "Energy", "Transport", "Material", "Utility"],
                required=True,
            ),
            "Flow": st.column_config.TextColumn("Flow", required=True),
            "Unit": st.column_config.TextColumn("Unit", required=True),
            "Emission factor": st.column_config.NumberColumn(
                "Emission Factor", min_value=0.0, format="%.8f"
            ),
            "LHV": st.column_config.NumberColumn(
                "LHV (MJ/kg)", min_value=0.0, format="%.4f"
            ),
            "Fossil energy intensity": st.column_config.NumberColumn(
                "Fossil Energy Intensity", min_value=0.0, format="%.4f"
            ),
            "Source": st.column_config.TextColumn("Source"),
        },
        key="background_editor",
    )

# -----------------------------
# Credits
# -----------------------------
elif page == "Substitution & Credits":
    st.subheader("Substitution & Credits")
    st.caption(
        "Carbon credit = by-product quantity × emission factor of the substituted product."
    )

    st.session_state.credits = st.data_editor(
        st.session_state.credits,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "By-product": st.column_config.TextColumn("By-product", required=True),
            "Amount": st.column_config.NumberColumn(
                "Amount", min_value=0.0, format="%.6f"
            ),
            "Unit": st.column_config.TextColumn("Unit", required=True),
            "Reference product": st.column_config.TextColumn(
                "Reference Product", required=True
            ),
            "Credit factor": st.column_config.NumberColumn(
                "Credit Factor", min_value=0.0, format="%.8f"
            ),
        },
        key="credits_editor",
    )

    credits = st.session_state.credits.copy()
    credits["Credit"] = (
        pd.to_numeric(credits["Amount"], errors="coerce").fillna(0)
        * pd.to_numeric(credits["Credit factor"], errors="coerce").fillna(0)
    )
    st.metric("Total Credits", f'{credits["Credit"].sum():.3f} kg CO₂-eq')

# -----------------------------
# Results
# -----------------------------
elif page == "Results & Analysis":
    st.subheader("Results & Analysis")

    if st.button("Calculate ThermoLCA", type="primary", use_container_width=True):
        result = calculate_lca(
            inventory=st.session_state.inventory,
            background=st.session_state.background,
            credits=st.session_state.credits,
            transport_mass_t=float(st.session_state.transport_mass_t),
            return_trip=bool(st.session_state.return_trip),
        )
        st.session_state.last_result = result

    result = st.session_state.last_result

    if not result:
        st.info("Run the calculation to generate results.")
    elif result["errors"]:
        st.error("Calculation stopped. Please fix the following items:")
        for err in result["errors"]:
            st.write(f"- {err}")
    else:
        a, b, c, d = st.columns(4)
        a.metric("Total Emissions", f'{result["total_emissions"]:.3f} kg CO₂-eq')
        b.metric("Total Credits", f'{result["total_credits"]:.3f} kg CO₂-eq')
        c.metric("Net Emissions", f'{result["net_emissions"]:.3f} kg CO₂-eq')
        d.metric(
            "Carbon Footprint",
            f'{result["carbon_footprint"]:.4f} kg CO₂-eq/kg',
        )

        left, right = st.columns(2)
        with left:
            st.markdown("#### GWP Contribution by Process")
            fig = px.bar(
                result["by_process"],
                x="Unit process",
                y="GWP",
                text_auto=".2f",
                labels={"GWP": "kg CO₂-eq"},
            )
            fig.update_layout(showlegend=False, height=420)
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.markdown("#### Contribution Share")
            fig = px.pie(
                result["by_process"],
                names="Unit process",
                values="GWP",
                hole=0.48,
            )
            fig.update_layout(height=420)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Detailed Contribution")
        st.dataframe(result["detail"], use_container_width=True, hide_index=True)

# -----------------------------
# Sensitivity
# -----------------------------
elif page == "Sensitivity Analysis":
    st.subheader("Sensitivity Analysis")
    st.caption("One-at-a-time sensitivity analysis for selected background factors.")

    parameter = st.selectbox(
        "Parameter",
        st.session_state.background["Flow"].dropna().astype(str).tolist(),
    )
    lower = st.slider("Lower change (%)", -80, 0, -20)
    upper = st.slider("Upper change (%)", 0, 100, 20)
    steps = st.slider("Number of points", 5, 21, 9)

    if st.button("Run Sensitivity Analysis", type="primary"):
        sens = run_sensitivity(
            inventory=st.session_state.inventory,
            background=st.session_state.background,
            credits=st.session_state.credits,
            flow_name=parameter,
            lower_pct=lower,
            upper_pct=upper,
            steps=steps,
            transport_mass_t=float(st.session_state.transport_mass_t),
            return_trip=bool(st.session_state.return_trip),
        )
        if sens.empty:
            st.warning("No valid sensitivity results were generated.")
        else:
            fig = px.line(
                sens,
                x="Change (%)",
                y="Carbon footprint",
                markers=True,
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(sens, use_container_width=True, hide_index=True)

# -----------------------------
# Report
# -----------------------------
else:
    st.subheader("Report & Export")
    result = st.session_state.last_result

    if not result or result.get("errors"):
        st.info("Calculate the LCA first in Results & Analysis.")
    else:
        report = build_excel_report(
            project_name=project_name,
            product_name=product_name,
            functional_unit=functional_unit,
            system_boundary=system_boundary,
            allocation_method=allocation_method,
            inventory=st.session_state.inventory,
            background=st.session_state.background,
            credits=st.session_state.credits,
            result=result,
        )

        st.download_button(
            "Download Excel Report",
            data=report,
            file_name="ThermoLCA_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

        st.markdown(
            f"""
            **Project:** {project_name}  
            **Product:** {product_name}  
            **Functional unit:** {functional_unit}  
            **System boundary:** {system_boundary}  
            **Method:** {allocation_method}  
            **Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
            """
        )

st.divider()
st.markdown(
    '<div class="footer">Database: editable user database &nbsp;&nbsp;|&nbsp;&nbsp; '
    'Method: GWP + substitution credits &nbsp;&nbsp;|&nbsp;&nbsp; '
    'ThermoLCA v1.0</div>',
    unsafe_allow_html=True,
)
