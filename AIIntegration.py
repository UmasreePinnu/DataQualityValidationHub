import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import re
import requests

from conn_picker import render_picker
from db_utils import engine_from_profile, make_safe_table_name


def call_ai_model(prompt: str) -> str:
    """
    Dispatches a prompt to the local AI model (Ollama) to perform
    intelligent query generation, key column identification, or issue analysis.
    """
    with st.spinner("🤖 Local AI is processing the metadata... Please wait."):
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": "gemma3:4b",
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(url, json=payload, timeout=300)
            if response.status_code == 200:
                return response.json().get("response", "AI failed to generate a response.")
            return "AI model connection failed. Falling back to key default heuristics."
        except requests.exceptions.Timeout:
            return "AI Generation timed out: The table metadata is too large for the local model to process within 5 minutes."
        except Exception as e:
            return f"AI Generation skipped due to connectivity constraints: {e}"


def run():
    st.title("🤖 Intelligent AI DQ Orchestrator")
    st.caption(
        "AI-driven end-to-end full table discrepancy tracking, smart key detection, and automated mismatch analysis")

    # ── Connections ────────────────────────────────────────────────────────────
    st.subheader("1. Setup Connections")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Source Environment**")
        src_profile = render_picker("Source connection", key="ai_src_conn")
    with col2:
        st.markdown("**Target Environment**")
        trg_profile = render_picker("Target connection", key="ai_trg_conn")

    st.divider()

    # ── Target Object Form Mapping ─────────────────────────────────────────────
    st.subheader("2. Define Target Scope")
    c1, c2 = st.columns(2)
    src_table = c1.text_input("Source Table (with Schema)", placeholder="ODS.SFDC_ACCOUNT").strip()
    trg_table = c2.text_input("Target Table (with Schema)", placeholder="DWH.DIM_ACCOUNT").strip()

    st.divider()

    if st.button("▶ Run AI Smart Validation", type="primary"):
        if not src_profile or not trg_profile:
            st.error("Please ensure both source and target connections are selected.")
            return
        if not src_table or not trg_table:
            st.error("Please specify both source and target table targets to validate.")
            return

        try:
            src_engine = engine_from_profile(src_profile)
            trg_engine = engine_from_profile(trg_profile)

            progress = st.progress(0, text="AI initializing workspace environment...")

            # ── STEP A: METADATA & SCHEMA VALIDATION (FIXED QUERY COLUMNS) ──
            progress.progress(10, text="AI inspecting system structural metadata...")

            def get_meta(engine, full_name):
                sch, tab = full_name.split(".", 1)
                # FIXED: Added CHAR_LENGTH, DATA_PRECISION, and DATA_SCALE to mirror SchemaValidator.py completely
                sql = (f"SELECT COLUMN_NAME, UPPER(DATA_TYPE) DATA_TYPE, "
                       f"CHARACTER_MAXIMUM_LENGTH CHAR_LENGTH, "
                       f"NUMERIC_PRECISION DATA_PRECISION, NUMERIC_SCALE DATA_SCALE "
                       f"FROM INFORMATION_SCHEMA.COLUMNS "
                       f"WHERE UPPER(TABLE_SCHEMA)='{sch.upper()}' AND UPPER(TABLE_NAME)='{tab.upper()}'")
                df = pd.read_sql(sql, engine)
                df.columns = [c.upper() for c in df.columns]
                if not df.empty:
                    df["COLUMN_NAME"] = df["COLUMN_NAME"].astype(str).str.upper().str.strip()
                return df

            df_meta_src = get_meta(src_engine, src_table)
            df_meta_trg = get_meta(trg_engine, trg_table)

            if df_meta_src.empty or df_meta_trg.empty:
                st.error("AI aborted: Unable to fetch metadata columns. Check table naming strings.")
                return

            comp_meta = pd.merge(df_meta_src, df_meta_trg, on="COLUMN_NAME", how="outer", suffixes=("_SRC", "_TGT"))

            missing_src_cols = comp_meta[pd.isna(comp_meta["DATA_TYPE_SRC"])]["COLUMN_NAME"].tolist()
            missing_trg_cols = comp_meta[pd.isna(comp_meta["DATA_TYPE_TGT"])]["COLUMN_NAME"].tolist()
            common_cols = comp_meta[pd.notna(comp_meta["DATA_TYPE_SRC"]) & pd.notna(comp_meta["DATA_TYPE_TGT"])][
                "COLUMN_NAME"].tolist()

            # Process datatype and length rules identically to SchemaValidator.py
            dtype_diffs = []
            for _, r in comp_meta.dropna(subset=["DATA_TYPE_SRC", "DATA_TYPE_TGT"]).iterrows():
                col_name = str(r["COLUMN_NAME"]).upper()

                def fmt_diff(a, b):
                    if pd.isna(a) or str(a).upper() == "NAN":
                        a_str = "NULL"
                    elif str(a).strip() == "":
                        a_str = "BLANK"
                    else:
                        a_str = str(a).strip()

                    if pd.isna(b) or str(b).upper() == "NAN":
                        b_str = "NULL"
                    elif str(b).strip() == "":
                        b_str = "BLANK"
                    else:
                        b_str = str(b).strip()

                    return f"{a_str} → {b_str}" if a_str != b_str else a_str

                type_str = fmt_diff(r["DATA_TYPE_SRC"], r["DATA_TYPE_TGT"])
                len_str = fmt_diff(r.get("CHAR_LENGTH_SRC"), r.get("CHAR_LENGTH_TGT"))
                prec_str = fmt_diff(r.get("DATA_PRECISION_SRC"), r.get("DATA_PRECISION_TGT"))
                scale_str = fmt_diff(r.get("DATA_SCALE_SRC"), r.get("DATA_SCALE_TGT"))

                # Append column formatting data points to results array safely
                diff_cols.append({
                    "TABLE NAME": src_table.split(".", 1)[-1].upper(), "COLUMN NAME": col_name,
                    "DATA TYPE": type_str, "CHAR LENGTH": len_str,
                    "PRECISION": prec_str, "SCALE": scale_str,
                })

            df_dtype_report = pd.DataFrame(diff_cols) if diff_cols else pd.DataFrame(
                columns=["TABLE NAME", "COLUMN NAME", "DATA TYPE", "CHAR LENGTH", "PRECISION", "SCALE"])
            df_missing_src_cols = pd.DataFrame(missing_src_cols, columns=["Column Name"])
            df_missing_tgt_cols = pd.DataFrame(missing_trg_cols, columns=["Column Name"])

            # ── STEP B: AI AUTOMATIC KEY COLUMN SELECTION ──
            progress.progress(25, text="AI analyzing columns to detect unique primary key identifier...")

            ai_key_prompt = f"""
            You are an expert Data Engineer. Analyze this list of table columns: {common_cols}
            Determine the best single column to act as the unique primary identifier/joining key for an inner join.
            Look for columns containing 'KEY', 'ID', 'CODE', or the first column.
            Respond with ONLY the uppercase column name, no extra text, markdown, punctuation, or spaces.
            """
            detected_key = call_ai_model(ai_key_prompt).strip().upper()
            detected_key = re.sub(r'[\W_]+', '', detected_key)
            KEY = detected_key if detected_key in common_cols else ("KEY" if "KEY" in common_cols else common_cols[0])

            st.caption(f"🧠 **AI Selected Key Column:** `[{KEY}]`")

            # ── STEP C: FULL-TABLE PROFILING & EXPLICIT DATA EXTRACTION ──
            progress.progress(40, text="AI pulling full table single-column index profiles...")
            src_safe = make_safe_table_name(src_table)
            trg_safe = make_safe_table_name(trg_table)

            df_keys_src = pd.read_sql(f"SELECT [{KEY}] FROM {src_safe}", src_engine)
            df_keys_trg = pd.read_sql(f"SELECT [{KEY}] FROM {trg_safe}", trg_engine)

            df_keys_src.columns = [c.upper() for c in df_keys_src.columns]
            df_keys_trg.columns = [c.upper() for c in df_keys_trg.columns]

            full_src_keys = set(df_keys_src[KEY].dropna().astype(str).str.strip())
            full_trg_keys = set(df_keys_trg[KEY].dropna().astype(str).str.strip())

            total_missing_in_target = len(full_src_keys - full_trg_keys)
            total_missing_in_source = len(full_trg_keys - full_src_keys)
            intersecting_keys = sorted(list(full_src_keys.intersection(full_trg_keys)))

            progress.progress(55, text="Extracting aligned matching row values for comparison sample...")
            col_select_str = ", ".join([f"[{c}]" for c in common_cols])

            if len(intersecting_keys) > 0:
                sample_keys_slice = intersecting_keys[:1500]
                key_predicates = ", ".join([f"'{k}'" for k in sample_keys_slice])

                src_query = f"SELECT {col_select_str} FROM {src_safe} WHERE [{KEY}] IN ({key_predicates})"
                trg_query = f"SELECT {col_select_str} FROM {trg_safe} WHERE [{KEY}] IN ({key_predicates})"

                df_data_src = pd.read_sql(src_query, src_engine)
                df_data_trg = pd.read_sql(trg_query, trg_engine)
            else:
                df_data_src = pd.DataFrame(columns=common_cols)
                df_data_trg = pd.DataFrame(columns=common_cols)

            for df in [df_data_src, df_data_trg]:
                df.columns = df.columns.str.upper().str.strip()
                for c in df.columns:
                    df[c] = df[c].fillna("NULL").astype(str).str.strip()
                    df.loc[df[c] == "", c] = ""

            # ── STEP D: FULL NULL COUNT EXTRACTION QUERY PASS ──
            progress.progress(70, text="Processing Null & Blank count validations across columns...")
            null_records = []
            sch_s, tab_s = src_table.split(".", 1)
            sch_t, tab_t = trg_table.split(".", 1)

            for col in common_cols:
                s_null = pd.read_sql(
                    f"SELECT COUNT(*) CNT FROM {src_safe} WHERE (CASE WHEN [{col}] IS NULL THEN 1 ELSE 0 END) = 1",
                    src_engine).iloc[0]["CNT"]
                s_blank = pd.read_sql(
                    f"SELECT COUNT(*) CNT FROM {src_safe} WHERE (CASE WHEN CAST([{col}] AS VARCHAR) = '' THEN 1 ELSE 0 END) = 1",
                    src_engine).iloc[0]["CNT"]
                s_sum = s_null + s_blank

                t_null = pd.read_sql(
                    f"SELECT COUNT(*) CNT FROM {trg_safe} WHERE (CASE WHEN [{col}] IS NULL THEN 1 ELSE 0 END) = 1",
                    trg_engine).iloc[0]["CNT"]
                t_blank = pd.read_sql(
                    f"SELECT COUNT(*) CNT FROM {trg_safe} WHERE (CASE WHEN CAST([{col}] AS VARCHAR) = '' THEN 1 ELSE 0 END) = 1",
                    trg_engine).iloc[0]["CNT"]
                t_sum = t_null + t_blank

                diff = abs(s_sum - t_sum)
                pct = (diff / max(s_sum, t_sum)) * 100 if max(s_sum, t_sum) else 0

                null_records.append([
                    tab_s.upper(), col.upper(), s_blank, s_null, s_sum,
                    tab_t.upper(), col.upper(), t_blank, t_null, t_sum,
                    diff, round(pct, 2)
                ])

            null_headers = [
                "SOURCE TABLE_NAME", "SOURCE COLUMN_NAME", "SOURCE BLANK COUNT", "SOURCE NULL COUNT",
                "SOURCE SUM OF NULL AND BLANK",
                "TARGET TABLE_NAME", "TARGET COLUMN_NAME", "TARGET BLANK COUNT", "TARGET NULL COUNT",
                "TARGET SUM OF NULL AND BLANK",
                "DIFF", "PERCENTAGE"
            ]
            df_null_metrics = pd.DataFrame(null_records, columns=null_headers)

            # Value Variance Merged Comparisons
            merged_data = pd.merge(df_data_src, df_data_trg, on=KEY, how="inner", suffixes=("_SRC", "_TRG"))
            df_all_comparison = pd.DataFrame()
            df_all_comparison[KEY] = merged_data[KEY]
            diff_col_summary = []

            for col in [c for c in common_cols if c != KEY]:
                sc, tc = col + "_SRC", col + "_TRG"
                mask = merged_data[sc] != merged_data[tc]
                df_all_comparison[col] = np.where(mask, merged_data[sc] + " → " + merged_data[tc], merged_data[sc])
                if mask.any():
                    diff_col_summary.append(
                        {"COLUMN NAME WITH ISSUES": col, "TOTAL SAMPLE RECORD MISMATCHES": mask.sum()})

            row_has_issue_mask = df_all_comparison.apply(lambda r: any("→" in str(v) for v in r), axis=1)
            df_filtered_diffs = df_all_comparison[row_has_issue_mask].copy()
            df_diff_cols_report = pd.DataFrame(diff_col_summary) if diff_col_summary else pd.DataFrame(
                columns=["COLUMN NAME WITH ISSUES", "TOTAL SAMPLE RECORD MISMATCHES"])

            # ── STEP E: AI AUTOMATED DISCREPANCY ANALYSIS ──
            progress.progress(85, text="AI analyzing data variance patterns...")

            ai_analysis_prompt = f"""
            You are a Principal Data Quality Engineer. Analyze this comprehensive schema and row metric verification:
            - Source Table Target: {src_table} (Total Rows: {len(full_src_keys)})
            - Target Table Target: {trg_table} (Total Rows: {len(full_trg_keys)})
            - COMPLETE TABLE Missing rows count in SOURCE: {total_missing_in_source} rows
            - COMPLETE TABLE Missing rows count in TARGET: {total_missing_in_target} rows
            - Structural Columns missing in Source: {len(missing_src_cols)} columns
            - Structural Columns missing in Target: {len(missing_trg_cols)} columns
            - Data Type Anomalies: {len(df_dtype_report)} variations
            - Value mismatch records observed inside sample: {len(df_filtered_diffs)} rows

            Provide an elegant, structured executive summary dashboard analysis of the findings with clear bullets.
            """
            ai_mismatch_analysis_text = call_ai_model(ai_analysis_prompt)

            st.subheader("💡 AI Executive Full-Table Analysis Report")
            st.info(ai_mismatch_analysis_text)

            # ── STEP F: UNIFIED EXCEL OUTPUT ASSEMBLY ENGINE ──
            progress.progress(95, text="AI compiling final validation workbook structure...")

            buffer = BytesIO()
            header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
            thick_blue_fill = PatternFill(start_color="002060", end_color="002060", fill_type="solid")
            yellow_diff_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                wb = writer.book

                # ── SHEET 1: MASTER STATISTICS SUMMARY ──
                df_summary_tab = pd.DataFrame([
                    {"MASTER EVALUATION METRIC": "Source Total Row Count", "VALUE": len(full_src_keys)},
                    {"MASTER EVALUATION METRIC": "Target Total Row Count", "VALUE": len(full_trg_keys)},
                    {"MASTER EVALUATION METRIC": "TOTAL MISSING RECORDS IN SOURCE (ENTIRE TABLE)",
                     "VALUE": total_missing_in_source},
                    {"MASTER EVALUATION METRIC": "TOTAL MISSING RECORDS IN TARGET (ENTIRE TABLE)",
                     "VALUE": total_missing_in_target},
                    {"MASTER EVALUATION METRIC": "Schema Column Mismatches Detected",
                     "VALUE": len(missing_src_cols) + len(missing_trg_cols)},
                    {"MASTER EVALUATION METRIC": "Sample Data Row Mismatches Found", "VALUE": len(df_filtered_diffs)}
                ])
                df_summary_tab.to_excel(writer, sheet_name="Overview_Summary", index=False)

                ws_summary = writer.sheets["Overview_Summary"]
                ws_summary.cell(row=9, column=1, value="AI DQ ANALYTICAL REASONING TRACE:").font = Font(bold=True,
                                                                                                        size=11)
                ws_summary.cell(row=10, column=1, value=ai_mismatch_analysis_text).alignment = Alignment(wrap_text=True)

                # ── SHEET 2: MISSING COLUMNS DETAILS ──
                df_miss_cols_sheet = pd.DataFrame({
                    "MISSING IN SOURCE": missing_src_cols + [""] * (
                        max(0, len(missing_trg_cols) - len(missing_src_cols))),
                    "MISSING IN TARGET": missing_trg_cols + [""] * (
                        max(0, len(missing_src_cols) - len(missing_trg_cols)))
                })
                df_miss_cols_sheet.to_excel(writer, sheet_name="Schema_Missing_Columns", index=False)

                # ── SHEET 3: FIXED DATATYPE MISMATCH ANALYSIS ──
                df_dtype_report.to_excel(writer, sheet_name="Schema_DataType_Check", index=False)

                # ── SHEET 4: UNIFIED ROW AND NULL COUNT CHECK (RULE 2 REQUIREMENT) ──
                ws_combined = wb.create_sheet(title="Row and Null Count Check")

                # Title Blocks definition for Row metrics summary
                ws_combined.cell(row=1, column=1, value="FULL TABLE ROW COUNT METRICS SUMMARY").font = Font(
                    name="Arial", size=11, bold=True)
                ws_combined.cell(row=2, column=1, value="SOURCE TOTAL ROWS")
                ws_combined.cell(row=2, column=2, value=len(full_src_keys))
                ws_combined.cell(row=3, column=1, value="TARGET TOTAL ROWS")
                ws_combined.cell(row=3, column=2, value=len(full_trg_keys))
                ws_combined.cell(row=4, column=1, value="TOTAL MISSING IN SOURCE")
                ws_combined.cell(row=4, column=2, value=total_missing_in_source)
                ws_combined.cell(row=5, column=1, value="TOTAL MISSING IN TARGET")
                ws_combined.cell(row=5, column=2, value=total_missing_in_target)

                # Append Null checks block section directly under the rows table
                ws_combined.cell(row=7, column=1,
                                 value="COLUMN-LEVEL NULL AND BLANK COUNT ANALYSIS VALIDATIONS").font = Font(
                    name="Arial", size=11, bold=True)

                for col_idx, col_name in enumerate(df_null_metrics.columns, 1):
                    cell = ws_combined.cell(row=8, column=col_idx, value=col_name)
                    cell.font = header_font
                    cell.fill = thick_blue_fill

                for row_idx, row_values in enumerate(df_null_metrics.itertuples(index=False), 9):
                    for col_idx, val in enumerate(row_values, 1):
                        ws_combined.cell(row=row_idx, column=col_idx, value=val)

                # ── SHEET 5: AFFECTED COLUMN SUMMARY ──
                df_diff_cols_report.to_excel(writer, sheet_name="Data_Differences_Columns", index=False)

                # ── SHEET 6: DATA VALUE VARIANCES SAMPLE MATRIX ──
                df_filtered_diffs.to_excel(writer, sheet_name="Data_Filtered_Differences", index=False)

                # Openpyxl styling and sizing execution path loop
                for sheet in wb.worksheets:
                    if sheet.title != "Row and Null Count Check":
                        for cell in sheet[1]:
                            cell.font = header_font
                            cell.fill = thick_blue_fill

                    if sheet.title == "Data_Filtered_Differences":
                        for r_idx in range(2, sheet.max_row + 1):
                            for c_idx in range(1, sheet.max_column + 1):
                                if "→" in str(sheet.cell(row=r_idx, column=c_idx).value or ""):
                                    sheet.cell(row=r_idx, column=c_idx).fill = yellow_diff_fill

                    for col in sheet.columns:
                        vals = [len(str(c.value or "")) for c in col]
                        max_len = max(vals) if vals else 10
                        sheet.column_dimensions[get_column_letter(col[0].column)].width = max(max_len + 3, 18)

            progress.empty()

            # Display KPIs onto screen
            m1, m2 = st.columns(2)
            m1.metric("Total Missing in Source", f"{total_missing_in_source:,}")
            m2.metric("Total Missing in Target", f"{total_missing_in_target:,}")

            st.download_button(
                label="⬇ Download Comprehensive AI Validation Report",
                data=buffer.getvalue(),
                file_name=f"AI_COMPREHENSIVE_DQ_REPORT_{src_table}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"AI Orchestration run interrupted: {e}")


if __name__ == "__main__":
    run()