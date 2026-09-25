# DQ Validation Hub

A Streamlit application for data quality validation across Azure Synapse and Oracle databases.

## Tools included
| Tool | Description |
|---|---|
| 🔍 Schema Validator | Compare columns, datatypes and row counts between source and target |
| 📄 File Generator | Run SQL queries and export results to Excel |
| 📁 File Comparator | Diff paired Source / Target Excel files |
| 📊 Fact Metrics | Compare numeric metric sums across Synapse / Oracle |
| 🔑 Keys Validator | Orphan keys, duplicate check, null count (4 scenarios) |
| 🎨 Colour Filter | Extract colour-highlighted rows from Excel |
| 🔌 Connections | Save and manage database profiles reused across all tools |

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

For Oracle support also install:
```bash
pip install oracledb
```

### 2. ODBC Driver (for Synapse)
Install **ODBC Driver 17 for SQL Server** from Microsoft:
https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

### 3. Run the app
```bash
streamlit run Application.py
```

## Project structure
```
dq_hub/
├── Application.py          # Main entry point and routing
├── requirements.txt
├── connections.json        # Auto-created when you save first profile
├── pages/
│   ├── Home.py
│   ├── Connections.py
│   ├── SchemaValidator.py
│   ├── FileGenerator.py
│   ├── FileComparator.py
│   ├── FactMetrics.py
│   ├── KeysValidator.py
│   └── ColourFilter.py
└── utils/
    ├── connection_manager.py   # JSON read/write for profiles
    ├── conn_picker.py          # Reusable connection dropdown widget
    └── db_utils.py             # SQLAlchemy engine builder
```

## Connection profiles
Go to **Connections** in the sidebar to save a profile once.
Every tool then shows a dropdown to pick that profile — no re-entering server/database details.

Profiles are stored in `connections.json` next to `Application.py`.
**Do not commit this file if it contains sensitive credentials.**

## File Comparator naming convention
Files must be named: `TableName_Source.xlsx` and `TableName_Target.xlsx`
Upload both files together and the tool auto-pairs them.

## Notes
- Passwords for Oracle are not stored in profiles — enter them at runtime in the tool.
- The `connections.json` file is created automatically on first save.
- All validation results can be downloaded as Excel reports.
