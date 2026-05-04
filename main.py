# app.py
import io
import fitz  # PyMuPDF
import pandas as pd
import streamlit as st

st.set_page_config(page_title="PDF Rectangle Color Counter", layout="wide")

st.title("PDF Colored Rectangle Counter")

st.write(
    "Upload a PDF, define target colors, and count rectangle annotations by color."
)

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

st.sidebar.header("Target colors")

default_colors = {
    "Analog Input": "#FFFF31",
    "Helyi kijelző": "#FFBF28",
    "Vezérelt csap": "#8ACF56",
    "Digital Input": "#00AEED",
    "Motor": "#FF1318",
    "Purple": "#ff00ff",
}

color_config = {}

for name, default_hex in default_colors.items():
    enabled = st.sidebar.checkbox(f"Enable {name}", value=True)
    color = st.sidebar.color_picker(name, default_hex)
    if enabled:
        color_config[name] = color.lower()

tolerance = st.sidebar.slider(
    "RGB tolerance",
    min_value=0,
    max_value=80,
    value=25,
    help="Higher tolerance groups visually similar colors together.",
)

show_details = st.sidebar.checkbox("Show annotation details", value=False)


def rgb_float_to_hex(rgb):
    """
    PyMuPDF annotation colors are usually floats from 0 to 1.
    Converts them to #RRGGBB.
    """
    if not rgb:
        return None

    r, g, b = rgb[:3]
    return "#{:02x}{:02x}{:02x}".format(
        int(round(r * 255)),
        int(round(g * 255)),
        int(round(b * 255)),
    )


def hex_to_rgb(hex_color):
    hex_color = hex_color.replace("#", "")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def color_distance(hex1, hex2):
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)

    return max(
        abs(r1 - r2),
        abs(g1 - g2),
        abs(b1 - b2),
    )


def match_color(actual_hex, configured_colors, tolerance):
    if actual_hex is None:
        return "No color"

    best_name = "Other"
    best_distance = 999

    for name, target_hex in configured_colors.items():
        dist = color_distance(actual_hex, target_hex)
        if dist < best_distance:
            best_distance = dist
            best_name = name

    if best_distance <= tolerance:
        return best_name

    return "Other"


def count_rectangles(pdf_bytes, configured_colors, tolerance):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    rows = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        annot = page.first_annot

        while annot:
            annot_type = annot.type[1]

            # Common rectangle-like annotation types:
            # "Square" = rectangle annotation
            # "Highlight" etc. are ignored by default
            if annot_type == "Square":
                colors = annot.colors or {}

                stroke_hex = rgb_float_to_hex(colors.get("stroke"))
                fill_hex = rgb_float_to_hex(colors.get("fill"))

                # Prefer fill color if available, otherwise stroke color
                actual_hex = fill_hex or stroke_hex
                matched_color = match_color(actual_hex, configured_colors, tolerance)

                rect = annot.rect

                rows.append(
                    {
                        "Page": page_index + 1,
                        "Annotation type": annot_type,
                        "Detected HEX": actual_hex,
                        "Matched color": matched_color,
                        "X0": round(rect.x0, 2),
                        "Y0": round(rect.y0, 2),
                        "X1": round(rect.x1, 2),
                        "Y1": round(rect.y1, 2),
                    }
                )

            annot = annot.next

    doc.close()
    return pd.DataFrame(rows)


if uploaded_file is not None:
    pdf_bytes = uploaded_file.read()

    df = count_rectangles(pdf_bytes, color_config, tolerance)

    if df.empty:
        st.warning("No rectangle / square annotations were found in this PDF.")
    else:
        summary = (
            df.groupby("Matched color")
            .size()
            .reset_index(name="Rectangle count")
            .sort_values("Rectangle count", ascending=False)
        )

        st.subheader("Summary")
        st.dataframe(summary, use_container_width=True)

        csv = summary.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download summary CSV",
            csv,
            file_name="rectangle_color_count_summary.csv",
            mime="text/csv",
        )

        if show_details:
            st.subheader("Annotation details")
            st.dataframe(df, use_container_width=True)

            details_csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download detailed CSV",
                details_csv,
                file_name="rectangle_color_count_details.csv",
                mime="text/csv",
            )
else:
    st.info("Upload a PDF to start.")
