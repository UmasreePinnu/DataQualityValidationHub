import streamlit as st
import pandas as pd
from metrics_tracker import get_stats, clear_stats

FEATURE_LIST = [
    "📄 File Generator",
    "📁 File Comparator",
    "🔀 MID File Validator",
    "📊 Fact Metrics Validator",
    "🔑 Keys Validator",
    "🔍 Schema Validator",
]

# Mapping internal feature names to selector labels
FEATURE_NAME_MAP = {
    "File Generator": "📄 File Generator",
    "File Comparator": "📁 File Comparator",
    "MID File Validator": "🔀 MID File Validator",
    "Fact Metrics Validator": "📊 Fact Metrics Validator",
    "Keys Validator": "🔑 Keys Validator",
    "Schema Validator": "🔍 Schema Validator",
}


def run():
    st.title("📈 Application Statistics")
    st.caption("Telemetry, execution durations, and feature metrics across DQ Validation Hub")

    stats = get_stats()

    top_col1, top_col2 = st.columns([6, 1])
    with top_col2:
        if st.button("🗑️ Clear Logs", help="Reset all saved execution logs"):
            clear_stats()
            st.rerun()

    if not stats:
        st.info("No statistics captured yet. Run validations in any tool to view metrics here.", icon="📊")
        return

    df_all = pd.DataFrame(stats)

    total_runs = len(df_all)
    total_time_spent = df_all["duration_sec"].sum()
    features_used = df_all["feature"].nunique()

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Executions", total_runs)
    k2.metric("Total Execution Time", f"{total_time_spent:,.2f} s")
    k3.metric("Features Utilized", features_used)

    st.divider()

    # ── Time Spent By Feature ──────────────────────────────────────────────────
    st.subheader("⏱️ Time Spent by Feature")
    feature_time = (
        df_all.groupby("feature")
        .agg(
            Total_Duration_Sec=("duration_sec", "sum"),
            Avg_Duration_Sec=("duration_sec", "mean"),
            Run_Count=("feature", "count"),
        )
        .reset_index()
    )
    feature_time["Avg_Duration_Sec"] = feature_time["Avg_Duration_Sec"].round(2)
    feature_time["Total_Duration_Sec"] = feature_time["Total_Duration_Sec"].round(2)

    c_chart, c_tbl = st.columns([4, 4])
    with c_chart:
        chart_df = feature_time.set_index("feature")["Total_Duration_Sec"]
        st.bar_chart(chart_df)

    with c_tbl:
        # Table Header
        th1, th2, th3, th4 = st.columns([3, 2, 2, 1.5])
        th1.markdown("**Feature**")
        th2.markdown("**Total Duration (s)**")
        th3.markdown("**Avg Duration (s)**")
        th4.markdown("**Runs**")

        # Interactive Table Rows: clicking feature name navigates to its section
        for _, row in feature_time.iterrows():
            feat_raw = row["feature"]
            tr1, tr2, tr3, tr4 = st.columns([3, 2, 2, 1.5])
            with tr1:
                target_label = FEATURE_NAME_MAP.get(feat_raw, feat_raw)
                if st.button(feat_raw, key=f"tbl_btn_{feat_raw}", help=f"View {feat_raw} metrics"):
                    st.session_state["active_stat_feature"] = target_label
                    st.rerun()
            with tr2:
                st.write(f"{row['Total_Duration_Sec']:.2f}")
            with tr3:
                st.write(f"{row['Avg_Duration_Sec']:.2f}")
            with tr4:
                st.write(int(row["Run_Count"]))

    st.divider()

    # ── Feature Breakdowns ─────────────────────────────────────────────────────
    st.subheader("🔍 Feature-Specific Metrics")

    if "active_stat_feature" not in st.session_state:
        st.session_state["active_stat_feature"] = FEATURE_LIST[0]

    selected_feature = st.radio(
        "Select Feature to View",
        FEATURE_LIST,
        index=FEATURE_LIST.index(st.session_state["active_stat_feature"])
        if st.session_state["active_stat_feature"] in FEATURE_LIST
        else 0,
        horizontal=True,
        key="active_stat_feature",
        label_visibility="collapsed",
    )

    # 1. File Generator
    if selected_feature == "📄 File Generator":
        fg_records = [s for s in stats if s["feature"] == "File Generator"]
        if fg_records:
            total_fg_files = sum(r["details"].get("files_count", 0) for r in fg_records)
            total_fg_rows = sum(r["details"].get("total_records", 0) for r in fg_records)
            total_fg_time = sum(r["duration_sec"] for r in fg_records)

            c1, c2, c3 = st.columns(3)
            c1.metric("Files Generated", total_fg_files)
            c2.metric("Total Records Generated", f"{total_fg_rows:,}")
            c3.metric("Total Duration", f"{total_fg_time:,.2f} s")

            flat_fg = []
            for r in fg_records:
                for item in r["details"].get("items", []):
                    flat_fg.append({
                        "Run Time": r["timestamp"],
                        "File / Sheet Name": item.get("name"),
                        "Records (Rows)": item.get("rows"),
                        "Columns": item.get("columns"),
                        "Table Query Time (s)": item.get("duration_sec", r["duration_sec"]),
                        "Total Batch Run Time (s)": r["duration_sec"],
                    })
            if flat_fg:
                st.dataframe(pd.DataFrame(flat_fg), use_container_width=True, hide_index=True)
        else:
            st.info("No File Generator executions logged.")

    # 2. File Comparator
    elif selected_feature == "📁 File Comparator":
        fc_records = [s for s in stats if s["feature"] == "File Comparator"]
        if fc_records:
            total_fc_files = sum(r["details"].get("output_files_count", 0) for r in fc_records)
            total_fc_time = sum(r["duration_sec"] for r in fc_records)

            c1, c2 = st.columns(2)
            c1.metric("Output Files Generated", total_fc_files)
            c2.metric("Total Duration", f"{total_fc_time:,.2f} s")

            flat_fc = []
            for r in fc_records:
                for t in r["details"].get("per_table_timings", []):
                    flat_fc.append({
                        "Run Time": r["timestamp"],
                        "Table / Base Name": t.get("table"),
                        "Table Processing Time (s)": t.get("duration_sec"),
                    })
            if flat_fc:
                st.dataframe(pd.DataFrame(flat_fc), use_container_width=True, hide_index=True)
        else:
            st.info("No File Comparator executions logged.")

    # 3. MID File Validator
    elif selected_feature == "🔀 MID File Validator":
        mid_records = [s for s in stats if s["feature"] == "MID File Validator"]
        if mid_records:
            total_mid_runs = len(mid_records)
            total_mid_time = sum(r["duration_sec"] for r in mid_records)

            c1, c2 = st.columns(2)
            c1.metric("Comparisons Completed", total_mid_runs)
            c2.metric("Total Duration", f"{total_mid_time:,.2f} s")

            flat_mid = []
            for r in mid_records:
                flat_mid.append({
                    "Run Time": r["timestamp"],
                    "Source File": r["details"].get("source_file"),
                    "Target File": r["details"].get("target_file"),
                    "Source Rows": r["details"].get("source_rows"),
                    "Target Rows": r["details"].get("target_rows"),
                    "Mismatches": r["details"].get("mismatches"),
                    "Duration (s)": r["duration_sec"],
                })
            st.dataframe(pd.DataFrame(flat_mid), use_container_width=True, hide_index=True)
        else:
            st.info("No MID File Validator executions logged.")

    # 4. Fact Metrics Validator
    elif selected_feature == "📊 Fact Metrics Validator":
        fm_records = [s for s in stats if s["feature"] == "Fact Metrics Validator"]
        if fm_records:
            total_tables = sum(r["details"].get("fact_tables_count", 0) for r in fm_records)
            total_fm_time = sum(r["duration_sec"] for r in fm_records)

            c1, c2 = st.columns(2)
            c1.metric("Fact Tables Validated", total_tables)
            c2.metric("Total Duration", f"{total_fm_time:,.2f} s")

            flat_fm = [
                {
                    "Timestamp": r["timestamp"],
                    "Tables Count": r["details"].get("fact_tables_count"),
                    "Aggregates Used": ", ".join(r["details"].get("aggs", [])),
                    "Duration (s)": r["duration_sec"],
                    "Mappings Validated": ", ".join(r["details"].get("table_pairs", [])),
                }
                for r in fm_records
            ]
            st.dataframe(pd.DataFrame(flat_fm), use_container_width=True, hide_index=True)
        else:
            st.info("No Fact Metrics Validator executions logged.")

    # 5. Keys Validator
    elif selected_feature == "🔑 Keys Validator":
        kv_records = [s for s in stats if s["feature"] == "Keys Validator"]
        if kv_records:
            total_kv_time = sum(r["duration_sec"] for r in kv_records)
            st.metric("Total Time Spent on Keys Validation", f"{total_kv_time:,.2f} s")

            flat_kv = [
                {
                    "Timestamp": r["timestamp"],
                    "Scenario": r["details"].get("scenario"),
                    "Items/Validations Count": r["details"].get("validations_count"),
                    "Duration (s)": r["duration_sec"],
                }
                for r in kv_records
            ]
            st.dataframe(pd.DataFrame(flat_kv), use_container_width=True, hide_index=True)
        else:
            st.info("No Keys Validator executions logged.")

    # 6. Schema Validator
    elif selected_feature == "🔍 Schema Validator":
        sv_records = [s for s in stats if s["feature"] == "Schema Validator"]
        if sv_records:
            total_sv_tables = sum(r["details"].get("tables_count", 0) for r in sv_records)
            total_sv_time = sum(r["duration_sec"] for r in sv_records)

            c1, c2 = st.columns(2)
            c1.metric("Tables Validated", total_sv_tables)
            c2.metric("Total Duration", f"{total_sv_time:,.2f} s")

            flat_sv = [
                {
                    "Timestamp": r["timestamp"],
                    "Tables Evaluated": r["details"].get("tables_count"),
                    "Columns & Data Types Checked": r["details"].get("column_check"),
                    "Row Counts Checked": r["details"].get("row_count_check"),
                    "Null Counts Checked": r["details"].get("null_check"),
                    "Duration (s)": r["duration_sec"],
                }
                for r in sv_records
            ]
            st.dataframe(pd.DataFrame(flat_sv), use_container_width=True, hide_index=True)
        else:
            st.info("No Schema Validator executions logged.")


if __name__ == "__main__":
    run()







