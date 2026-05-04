import pandas as pd
import streamlit as st

from src.config import DEFAULT_COLORS
from src.pdf_counter import count_annotations

st.set_page_config(page_title="PDF Rectangle Color Counter", layout="wide")

st.title("PDF Colored Rectangle Counter")

st.write(
    "Upload a PDF, define colors, and count rectangle fill annotations "
    "and optionally highlight stroke annotations."
)

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

st.sidebar.header("Target colors")

color_config = {}

for name, default_hex in DEFAULT_COLORS.items():
    enabled = st.sidebar.checkbox(f"Enable {name}", value=True)
    color = st.sidebar.color_picker(name, default_hex)
    if enabled:
        color_config[name] = color.lower()

tolerance = st.sidebar.slider(
    "RGB tolerance",
    min_value=0,
    max_value=80,
    value=2,
)

count_highlights = st.sidebar.checkbox(
    "Also count highlight annotations by stroke color",
    value=True,
)

show_details = st.sidebar.checkbox("Show annotation details", value=False)

if uploaded_file is not None:
    pdf_bytes = uploaded_file.read()

    df = count_annotations(
        pdf_bytes=pdf_bytes,
        configured_colors=color_config,
        tolerance=tolerance,
        count_highlights=count_highlights,
    )

    if df.empty:
        st.warning("No matching annotations found.")
    else:
        summary = (
            df.groupby("Matched color")
            .size()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
        )

        st.subheader("Summary")
        st.dataframe(summary, use_container_width=True)

        type_summary = (
            df.groupby(["Type", "Matched color"])
            .size()
            .reset_index(name="Count")
            .sort_values(["Type", "Count"], ascending=[True, False])
        )

        st.subheader("By annotation type")
        st.dataframe(type_summary, use_container_width=True)

        st.download_button(
            "Download summary CSV",
            summary.to_csv(index=False).encode("utf-8"),
            file_name="summary.csv",
            mime="text/csv",
        )

        if show_details:
            st.subheader("Annotation details")
            st.dataframe(df, use_container_width=True)
else:
    st.info("Upload a PDF to start.")
