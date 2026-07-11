import streamlit as st
import pandas as pd

from lca_engine import calculate_lca


st.set_page_config(
    page_title="Bio-LCA Calculator",
    layout="wide"
)

st.title("🌱 Bio-LCA Calculator")
st.caption(
    "Process-informed Life Cycle Assessment Platform"
)

st.sidebar.header("Project Information")

project = st.sidebar.text_input(
    "Project name",
    "Bioprocess LCA"
)

product = st.sidebar.text_input(
    "Product",
    "Product"
)

functional_unit = st.sidebar.text_input(
    "Functional unit",
    "1 kg product"
)


st.header("1. Upload LCI Data")

col1, col2, col3 = st.columns(3)

with col1:
    fg_file = st.file_uploader(
        "Foreground LCI (.xlsx)",
        type="xlsx"
    )

with col2:
    bg_file = st.file_uploader(
        "Background Database (.xlsx)",
        type="xlsx"
    )

with col3:
    sub_file = st.file_uploader(
        "Substitution Database (.xlsx)",
        type="xlsx"
    )


if fg_file and bg_file:

    foreground = pd.read_excel(fg_file)
    background = pd.read_excel(bg_file)

    substitution = None

    if sub_file:
        substitution = pd.read_excel(sub_file)

    st.subheader("Foreground Data")
    st.dataframe(
        foreground,
        use_container_width=True
    )

    if st.button("Calculate LCA"):

        result, contribution = calculate_lca(
            foreground,
            background,
            substitution
        )

        st.success("Calculation completed")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Total emission",
            f"{result['Total emission']:.2f} kgCO₂e"
        )

        c2.metric(
            "Credit",
            f"-{result['Credit']:.2f} kgCO₂e"
        )

        c3.metric(
            "Carbon footprint",
            f"{result['Carbon footprint']:.3f} kgCO₂e/kg"
        )

        st.divider()

        st.subheader("Emission contribution")

        st.dataframe(
            contribution,
            use_container_width=True
        )

        if len(contribution) > 0:
            st.bar_chart(
                contribution.set_index("Flow")["Emission"]
            )

else:

    st.info(
        "Please upload foreground and background Excel files."
    )
