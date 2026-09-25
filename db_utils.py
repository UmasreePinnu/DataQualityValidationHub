import pandas as pd
from sqlalchemy import create_engine, text
import connection_manager
import streamlit as st


def make_safe_table_name(full_table_name: str) -> str:
    """
    Safely bracket schema and table name.
    e.g. 'DWH.FACT_SALES' -> '[DWH].[FACT_SALES]'
    """
    parts = full_table_name.strip().split(".", 1)
    if len(parts) == 2:
        schema, table = parts
        return f"[{schema.strip()}].[{table.strip()}]"
    return f"[{full_table_name.strip()}]"


@st.cache_resource(show_spinner="Connecting... Please complete the MFA prompt.")
def get_cached_engine(server: str, database: str, authentication: str = "ActiveDirectoryInteractive"):
    """
    Builds and caches a SQLAlchemy engine (ODBC Driver 17 compatible).

    KEY FIX: We do NOT call engine.connect() here.
    Calling connect() inside @st.cache_resource blocks the entire Streamlit
    UI thread until MFA completes — causing the screen to freeze on mobile
    and slow connections. Instead, the engine is returned immediately and
    the MFA pop-up fires naturally on the first pd.read_sql() call, which
    runs inside a st.spinner() in each tool so the UI stays responsive.
    """
    driver = "ODBC Driver 17 for SQL Server"

    conn_str = (
        f"mssql+pyodbc://@{server}/{database}?"
        f"driver={driver}&"
        f"authentication={authentication}&"
        f"TrustServerCertificate=yes&"
        f"LoginTimeout=90"
    )

    return create_engine(
        conn_str,
        connect_args={"autocommit": True},
        pool_pre_ping=True,
        pool_timeout=120,
        pool_recycle=1800,
    )


def engine_from_profile(profile_data) -> object:
    """
    Accepts either a profile name (str) or a profile dict and returns
    a cached SQLAlchemy engine.
    """
    profiles = connection_manager.load_profiles()

    if isinstance(profile_data, str):
        if profile_data not in profiles:
            raise ValueError(f"Profile '{profile_data}' not found in connections.json.")
        p = profiles[profile_data]
    else:
        p = profile_data

    db_type        = p.get("type", "Synapse")
    authentication = p.get("authentication", "ActiveDirectoryInteractive")

    if db_type == "Oracle":
        return _oracle_engine(p)

    return get_cached_engine(
        server=p.get("server", ""),
        database=p.get("database", ""),
        authentication=authentication,
    )


def _oracle_engine(p: dict):
    """Builds an Oracle engine using oracledb."""
    try:
        import oracledb
    except ImportError:
        raise ImportError("oracledb is not installed. Run: pip install oracledb")

    instant_client = p.get("instant_client", "")
    if instant_client:
        oracledb.init_oracle_client(lib_dir=instant_client)

    dsn      = p.get("dsn", "")
    username = p.get("username", "")

    # Password is never stored — prompt at runtime
    pw_key   = f"oracle_pw_{dsn}"
    password = st.session_state.get(pw_key, "")
    if not password:
        password = st.text_input(
            f"Password for {username}@{dsn}",
            type="password",
            key=pw_key,
        )
        if not password:
            st.stop()

    return create_engine(
        f"oracle+oracledb://{username}:{password}@{dsn}",
        pool_pre_ping=True,
    )