import streamlit as st
import openpyxl
from copy import copy
from io import BytesIO


def _process_excel(uploaded_file) -> openpyxl.Workbook:
    wb = openpyxl.load_workbook(uploaded_file)
    original_ws       = wb.active
    original_ws.title = "ALL DATA"
    colour_ws         = wb.create_sheet(title="COLOUR RECORDS")

    def copy_style(src, tgt):
        if src.has_style:
            tgt.font         = copy(src.font)
            tgt.border       = copy(src.border)
            tgt.fill         = copy(src.fill)
            tgt.number_format = copy(src.number_format)
            tgt.protection   = copy(src.protection)
            tgt.alignment    = copy(src.alignment)

    # Header row
    for ci, cell in enumerate(original_ws[1], 1):
        new_cell = colour_ws.cell(row=1, column=ci, value=cell.value)
        copy_style(cell, new_cell)

    # Coloured rows
    colour_row = 2
    detected_colours = set()

    for row in original_ws.iter_rows(min_row=2):
        has_colour = False
        for cell in row:
            if cell.fill and cell.fill.start_color:
                idx = str(cell.fill.start_color.index)
                if idx not in ("00000000", "64") and cell.fill.fill_type is not None:
                    has_colour = True
                    detected_colours.add(idx)
                    break

        if has_colour:
            for ci, cell in enumerate(row, 1):
                new_cell = colour_ws.cell(row=colour_row, column=ci, value=cell.value)
                copy_style(cell, new_cell)
            h = original_ws.row_dimensions[row[0].row].height
            if h:
                colour_ws.row_dimensions[colour_row].height = h
            colour_row += 1

    for col_letter, dim in original_ws.column_dimensions.items():
        colour_ws.column_dimensions[col_letter].width = dim.width

    return wb, colour_row - 2, len(list(original_ws.iter_rows(min_row=2))), detected_colours


def run():
    st.title("🎨 Colour Record Filter")
    st.caption("Extract all colour-highlighted rows from an Excel file into a separate sheet")

    with st.container(border=True):
        st.markdown("**What this tool does**")
        col1, col2 = st.columns(2)
        col1.markdown("- ✅ Renames original sheet to **ALL DATA**")
        col1.markdown("- ✅ Detects all background-coloured rows")
        col2.markdown("- ✅ Preserves all cell formatting exactly")
        col2.markdown("- ✅ Creates **COLOUR RECORDS** sheet with extracted rows")

    st.divider()
    st.subheader("Upload file")

    uploaded = st.file_uploader(
        "Drop your Excel file here",
        type=["xlsx"],
        label_visibility="collapsed",
    )

    if uploaded is None:
        st.info("Upload an `.xlsx` file to begin.", icon="📂")
        return

    # File info
    st.success(f"**{uploaded.name}** uploaded successfully.", icon="📊")

    if st.button("▶ Process File", type="primary"):
        with st.spinner("Extracting coloured rows and preserving formatting…"):
            try:
                wb, colour_count, total_rows, detected = _process_excel(uploaded)

                st.divider()
                st.subheader("Results")

                c1, c2, c3 = st.columns(3)
                c1.metric("Total data rows",   total_rows)
                c2.metric("Colour rows found", colour_count)
                c3.metric("Colours detected",  len(detected))

                with st.container(border=True):
                    st.markdown("**Output file sheets**")
                    st.markdown(f"- **ALL DATA** — {total_rows} rows (original data, renamed sheet)")
                    st.markdown(f"- **COLOUR RECORDS** — {colour_count} rows (extracted coloured rows)")

                output = BytesIO()
                wb.save(output)

                base_name = uploaded.name.replace(".xlsx", "")
                st.download_button(
                    "⬇ Download Filtered Excel",
                    data=output.getvalue(),
                    file_name=f"{base_name}_Colour_Filter.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            except Exception as e:
                st.error(f"Error processing file: {e}")
