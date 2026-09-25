import streamlit as st


def run():
    st.title("📊 Data Quality Validation Hub")
    st.caption("Centralised platform for schema, metrics and file validation")

    st.divider()

    st.subheader("Available Tools")

    tools = [
        {
            "name": "🔍 Schema Validator",
            "desc": "Compare Columns, Datatypes, Row Counts and Null Counts between Source and Target systems."
        },
        {
            "name": "📄 File Generator",
            "desc": "Run complex SQL queries against database and export results directly to Excel."
        },
        {
            "name": "📁 File Comparator",
            "desc": "Compare paired Source and Target Excel files to identify missing rows, columns, and data variances."
        },
        {
            "name": "🔀 MID File Validator",
            "desc": "Compare two Excel files row-by-row using highlighted cells or manually mapped columns. "
                    "Outputs a report with All Records, Mismatches, New Entries and Duplicates sheets."
        },
        {
            "name": "📊 Fact Metrics",
            "desc": "Validate aggregate functions (SUM, AVG, MIN, MAX, COUNT) for numeric metric columns across environments."
        },
        {
            "name": "🔑 Keys Validator",
            "desc": "Perform Orphan Key Validations, Duplicate Check, and Null Count Checks on primary identifiers."
        },
        {
            "name": "🎨 Colour Filter",
            "desc": "Automatically extract all colour-highlighted rows from an Excel file into a separate dedicated sheet."
        },
    ]

    col1, col2 = st.columns(2)

    for i, tool in enumerate(tools):
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            with st.container(border=True):
                st.markdown(f"### {tool['name']}")
                st.markdown(f"{tool['desc']}")
                st.write("")

    st.info("Select a tool from the sidebar to begin your validation workflow.", icon="💡")