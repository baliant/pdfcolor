import fitz  # PyMuPDF
import pandas as pd

from src.color_utils import match_color, rgb_float_to_hex


def count_annotations(
    pdf_bytes,
    configured_colors,
    tolerance,
    count_highlights=True,
):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    rows = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        annot = page.first_annot

        while annot:
            annot_type = annot.type[1]
            colors = annot.colors or {}

            if annot_type == "Square":
                row = _extract_square_annotation(
                    annot=annot,
                    page_number=page_index + 1,
                    configured_colors=configured_colors,
                    tolerance=tolerance,
                )

                if row is not None:
                    rows.append(row)

            elif annot_type == "Highlight" and count_highlights:
                row = _extract_highlight_annotation(
                    annot=annot,
                    page_number=page_index + 1,
                    configured_colors=configured_colors,
                    tolerance=tolerance,
                )

                if row is not None:
                    rows.append(row)

            annot = annot.next

    doc.close()
    return pd.DataFrame(rows)


def _extract_square_annotation(
    annot,
    page_number,
    configured_colors,
    tolerance,
):
    colors = annot.colors or {}
    fill_hex = rgb_float_to_hex(colors.get("fill"))

    if fill_hex is None:
        return None

    return _build_row(
        annot=annot,
        page_number=page_number,
        annotation_type="Square",
        color_source="Fill",
        detected_hex=fill_hex,
        configured_colors=configured_colors,
        tolerance=tolerance,
    )


def _extract_highlight_annotation(
    annot,
    page_number,
    configured_colors,
    tolerance,
):
    colors = annot.colors or {}
    stroke_hex = rgb_float_to_hex(colors.get("stroke"))

    if stroke_hex is None:
        return None

    return _build_row(
        annot=annot,
        page_number=page_number,
        annotation_type="Highlight",
        color_source="Stroke",
        detected_hex=stroke_hex,
        configured_colors=configured_colors,
        tolerance=tolerance,
    )


def _build_row(
    annot,
    page_number,
    annotation_type,
    color_source,
    detected_hex,
    configured_colors,
    tolerance,
):
    rect = annot.rect

    return {
        "Page": page_number,
        "Type": annotation_type,
        "Color source": color_source,
        "Detected HEX": detected_hex,
        "Matched color": match_color(
            detected_hex,
            configured_colors,
            tolerance,
        ),
        "X0": round(rect.x0, 2),
        "Y0": round(rect.y0, 2),
        "X1": round(rect.x1, 2),
        "Y1": round(rect.y1, 2),
    }
