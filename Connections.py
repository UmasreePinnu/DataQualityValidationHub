import streamlit as st
from connection_manager import load_profiles, save_profile, delete_profile


_MSSQL_AUTH_OPTIONS = [
    "ActiveDirectoryDeviceCodeFlow",   # ← best for mobile / headless
    "ActiveDirectoryInteractive",      # browser pop-up (desktop only)
    "ActiveDirectoryPassword",
    "SQL",
]

# Kept as an alias for backward compatibility — Synapse and Fabric
# share the same auth mechanisms (both are SQL analytics endpoints).
_SYNAPSE_AUTH_OPTIONS = _MSSQL_AUTH_OPTIONS

_SERVER_PLACEHOLDER = {
    "Synapse": "server.sql.azuresynapse.net",
    "Fabric":  "yourlakehouse.datawarehouse.fabric.microsoft.com",
}
_DATABASE_PLACEHOLDER = {
    "Synapse": "syndw",
    "Fabric":  "YourLakehouseName",
}

_AUTH_HELP = {
    "ActiveDirectoryDeviceCodeFlow": "📱 Mobile-safe — shows a code in the app logs; open aka.ms/devicelogin on any device.",
    "ActiveDirectoryInteractive":    "🖥️ Desktop only — opens a browser pop-up for MFA. Will freeze on mobile.",
    "ActiveDirectoryPassword":       "🔑 Username + password, no MFA pop-up required.",
    "SQL":                           "🔑 SQL Server username + password.",
}


def run():
    st.title("🔌 Connection Profiles")
    st.caption("Save and manage database connections. Select them inside any tool — no re-typing credentials.")

    # Mobile auth tip
    with st.container(border=True):
        st.markdown("**📱 Mobile / server tip**")
        st.info(
            "Use **ActiveDirectoryDeviceCodeFlow** when running on mobile or a remote server. "
            "It avoids the browser pop-up that causes the screen to freeze. "
            "A short code will appear in the Streamlit server logs — visit `aka.ms/devicelogin` on any device to authenticate.",
            icon="💡",
        )

    profiles = load_profiles()

    # ── Empty state ────────────────────────────────────────────────────────────
    if not profiles:
        st.info(
            "No connection profiles saved yet. Use the form below to add your first one.",
            icon="🔌",
        )

    # ── Existing profiles table ────────────────────────────────────────────────
    else:
        st.subheader("Saved profiles")

        for name, p in list(profiles.items()):
            db_type   = p.get("type", "Synapse")
            auth      = p.get("authentication", "")
            if db_type == "Synapse":
                type_badge = "🔵 Synapse"
            elif db_type == "Fabric":
                type_badge = "🟣 Fabric"
            else:
                type_badge = "🟠 Oracle"
            # Warn if a desktop-only auth is saved
            auth_warn = " ⚠️ Desktop only" if auth == "ActiveDirectoryInteractive" else ""

            with st.container(border=True):
                col_name, col_type, col_detail, col_edit, col_del = st.columns(
                    [2.5, 1.2, 3, 0.8, 0.8]
                )
                col_name.markdown(f"**{name}**")
                col_type.caption(f"{type_badge}{auth_warn}")

                if db_type in ("Synapse", "Fabric"):
                    col_detail.caption(
                        f"{p.get('server', '')}  ·  `{p.get('database', '')}`  ·  {auth}"
                    )
                else:
                    col_detail.caption(
                        f"{p.get('dsn', '')}  ·  `{p.get('username', '')}`"
                    )

                if col_edit.button("Edit", key=f"edit_{name}"):
                    st.session_state["editing_profile"] = name
                    st.session_state["edit_data"] = p
                    st.rerun()

                if col_del.button("Delete", key=f"del_{name}"):
                    st.session_state["confirm_delete"] = name

        # Delete confirmation
        if "confirm_delete" in st.session_state:
            target = st.session_state["confirm_delete"]
            st.warning(f"Delete **{target}**? This action cannot be undone.", icon="⚠️")
            yes, no, _ = st.columns([1, 1, 5])
            if yes.button("Yes, delete", type="primary"):
                delete_profile(target)
                st.session_state.pop("confirm_delete", None)
                st.session_state.pop("editing_profile", None)
                st.session_state.pop("edit_data", None)
                st.success(f"'{target}' deleted.")
                st.rerun()
            if no.button("Cancel"):
                st.session_state.pop("confirm_delete", None)
                st.rerun()

    st.divider()

    # ── Add / Edit form ────────────────────────────────────────────────────────
    editing   = st.session_state.get("editing_profile")
    edit_data = st.session_state.get("edit_data", {})

    st.subheader("Edit profile" if editing else "Add new profile")

    with st.container(border=True):
        col_a, col_b = st.columns(2)
        name = col_a.text_input(
            "Connection Name",
            value=editing or "",
            placeholder="e.g. Prod Synapse",
        )
        _ENV_OPTIONS = ["Synapse", "Fabric", "Oracle"]
        _saved_type = edit_data.get("type", "Synapse")
        db_type = col_b.selectbox(
            "Environment",
            _ENV_OPTIONS,
            index=_ENV_OPTIONS.index(_saved_type) if _saved_type in _ENV_OPTIONS else 0,
        )

        st.markdown("---")

        profile_data: dict = {"type": db_type}

        if db_type in ("Synapse", "Fabric"):
            st.markdown(f"**{db_type} details**")
            c1, c2 = st.columns(2)
            profile_data["server"]   = c1.text_input(
                "Server",
                value=edit_data.get("server", ""),
                placeholder=_SERVER_PLACEHOLDER[db_type],
            )
            profile_data["database"] = c2.text_input(
                "Database" if db_type == "Synapse" else "Lakehouse (Database) name",
                value=edit_data.get("database", ""),
                placeholder=_DATABASE_PLACEHOLDER[db_type],
            )

            saved_auth = edit_data.get("authentication", "ActiveDirectoryDeviceCodeFlow")
            auth_idx   = _MSSQL_AUTH_OPTIONS.index(saved_auth) if saved_auth in _MSSQL_AUTH_OPTIONS else 0
            chosen_auth = st.selectbox(
                "Authentication",
                _MSSQL_AUTH_OPTIONS,
                index=auth_idx,
                help="Choose the login method. **DeviceCodeFlow** is recommended for mobile or server use.",
            )
            profile_data["authentication"] = chosen_auth

            # Show inline help text for selected auth
            st.caption(_AUTH_HELP.get(chosen_auth, ""))

            if db_type == "Fabric":
                st.caption(
                    "💡 Find the Server and Database (Lakehouse) values in the Fabric portal → "
                    "your Lakehouse → **Settings** → **SQL analytics endpoint**."
                )

        else:  # Oracle
            st.markdown("**Oracle details**")
            c1, c2 = st.columns(2)
            profile_data["dsn"]      = c1.text_input("DSN",      value=edit_data.get("dsn", ""),      placeholder="bidwprd_low")
            profile_data["username"] = c2.text_input("Username", value=edit_data.get("username", ""), placeholder="SVC_BI_USER")

            st.markdown("**Wallet & client paths**")
            profile_data["wallet_path"]    = st.text_input("Wallet path",           value=edit_data.get("wallet_path", ""),    placeholder="C:/Wallets/Prod")
            profile_data["instant_client"] = st.text_input("Instant client directory", value=edit_data.get("instant_client", ""), placeholder="C:/instantclient_21_13")

        st.markdown("")
        col_save, col_cancel, _ = st.columns([1, 1, 5])

        if col_save.button("Save profile", type="primary"):
            if not name.strip():
                st.error("Connection Name is required.")
            else:
                save_profile(name.strip(), profile_data)
                st.session_state.pop("editing_profile", None)
                st.session_state.pop("edit_data", None)
                st.success(f"✅ '{name}' saved successfully.")
                st.rerun()

        if editing and col_cancel.button("Cancel"):
            st.session_state.pop("editing_profile", None)
            st.session_state.pop("edit_data", None)
            st.rerun()