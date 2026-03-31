"""
Settings Page
"""
import streamlit as st
import json
import os
from pathlib import Path
from utils.database import get_sync_status, sync_offline_changes, db_select, db_insert, db_delete
from components.ui import page_header, metric_card


SETTINGS_FILE = Path("data/settings.json")

DEFAULT_SETTINGS = {
    "trader_name": "",
    "starting_balance": 10000.0,
    "currency": "USD",
    "default_lot_size": 1.0,
    "default_risk_pct": 1.0,
    "theme": "Dark",
    "notifications_enabled": True,
    "daily_trade_limit": 5,
    "max_daily_loss_pct": 3.0,
    "max_risk_per_trade_pct": 2.0,
    "supabase_url": "",
    "supabase_key": "",
}


def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    SETTINGS_FILE.parent.mkdir(exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def render():
    page_header("⚙️", "Settings", "Configure your trading journal")
    
    settings = load_settings()
    sync_status = get_sync_status()
    
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Profile", "🔗 Database", "🔔 Risk Limits", "📦 Data Management"])
    
    with tab1:
        _render_profile_settings(settings)
    
    with tab2:
        _render_db_settings(settings, sync_status)
    
    with tab3:
        _render_risk_settings(settings)
    
    with tab4:
        _render_data_management()


def _render_profile_settings(settings):
    st.markdown("#### 👤 Trader Profile")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Trader Name", value=settings.get("trader_name", ""))
        with col2:
            currency = st.selectbox("Base Currency", ["USD", "EUR", "GBP", "JPY", "AUD"],
                                    index=["USD","EUR","GBP","JPY","AUD"].index(settings.get("currency","USD")))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            starting_bal = st.number_input("Starting Balance ($)", value=float(settings.get("starting_balance", 10000)), min_value=100.0)
        with col2:
            default_lot = st.number_input("Default Lot Size", value=float(settings.get("default_lot_size", 1.0)), min_value=0.01)
        with col3:
            default_risk = st.number_input("Default Risk per Trade (%)", value=float(settings.get("default_risk_pct", 1.0)), min_value=0.1)
        
        if st.form_submit_button("💾 Save Profile", type="primary"):
            settings.update({
                "trader_name": name, "currency": currency,
                "starting_balance": starting_bal,
                "default_lot_size": default_lot,
                "default_risk_pct": default_risk
            })
            save_settings(settings)
            st.success("✅ Profile saved!")


def _render_db_settings(settings, sync_status):
    st.markdown("#### 🔗 Supabase Connection")
    
    connected = sync_status.get("connected", False)
    pending = sync_status.get("pending_sync", 0)
    
    if connected:
        st.success("✅ Connected to Supabase")
    else:
        st.warning("⚠️ Not connected — using local JSON storage")
    
    if pending > 0:
        st.info(f"📤 {pending} changes pending sync to Supabase")
        if st.button("🔄 Sync Now", type="primary"):
            result = sync_offline_changes()
            st.success(f"✅ Synced {result['synced']} records | {result['failed']} failed | {result['pending']} total")
    
    st.markdown("---")
    st.markdown("**Configure Supabase credentials** (stored locally in `.streamlit/secrets.toml`)")
    
    with st.form("db_form"):
        url = st.text_input("Supabase URL", 
                            value=os.getenv("SUPABASE_URL", settings.get("supabase_url", "")),
                            placeholder="https://xxxxx.supabase.co",
                            type="default")
        key = st.text_input("Supabase Anon Key", 
                             value=os.getenv("SUPABASE_KEY", settings.get("supabase_key", "")),
                             placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                             type="password")
        
        if st.form_submit_button("💾 Save & Test Connection"):
            if url and key:
                # Save to secrets
                secrets_dir = Path(".streamlit")
                secrets_dir.mkdir(exist_ok=True)
                secrets_path = secrets_dir / "secrets.toml"
                
                secrets_content = f'SUPABASE_URL = "{url}"\nSUPABASE_KEY = "{key}"\n'
                with open(secrets_path, "w") as f:
                    f.write(secrets_content)
                
                settings["supabase_url"] = url
                save_settings(settings)
                
                st.success("✅ Credentials saved! Restart the app to connect.")
            else:
                st.error("❌ Both URL and key are required")
    
    st.markdown("---")
    st.markdown("**📝 Schema Setup**")
    st.info("Run the SQL in `supabase_schema.sql` in your Supabase SQL Editor to create all required tables.")
    
    schema_path = Path("supabase_schema.sql")
    if schema_path.exists():
        with open(schema_path) as f:
            schema_sql = f.read()
        st.download_button("⬇️ Download Schema SQL", data=schema_sql, 
                           file_name="supabase_schema.sql", mime="text/plain")


def _render_risk_settings(settings):
    st.markdown("#### 🔔 Risk Management Limits")
    st.info("These limits trigger visual warnings in the dashboard when exceeded.")
    
    with st.form("risk_form"):
        col1, col2 = st.columns(2)
        with col1:
            daily_limit = st.number_input("Max Trades Per Day", value=int(settings.get("daily_trade_limit", 5)), min_value=1)
            max_daily_loss = st.number_input("Max Daily Loss (%)", value=float(settings.get("max_daily_loss_pct", 3.0)), min_value=0.1)
        with col2:
            max_risk = st.number_input("Max Risk Per Trade (%)", value=float(settings.get("max_risk_per_trade_pct", 2.0)), min_value=0.1)
            notifications = st.toggle("Enable Warnings", value=settings.get("notifications_enabled", True))
        
        if st.form_submit_button("💾 Save Risk Settings", type="primary"):
            settings.update({
                "daily_trade_limit": daily_limit,
                "max_daily_loss_pct": max_daily_loss,
                "max_risk_per_trade_pct": max_risk,
                "notifications_enabled": notifications
            })
            save_settings(settings)
            st.success("✅ Risk limits saved!")


def _render_data_management():
    st.markdown("#### 📦 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📥 Import Trades from CSV**")
        st.caption("CSV should have columns: trade_date, asset, direction, entry_price, exit_price, lot_size, pnl")
        uploaded_csv = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_csv:
            import pandas as pd
            try:
                df = pd.read_csv(uploaded_csv)
                st.dataframe(df.head(), use_container_width=True)
                if st.button("📥 Import These Trades"):
                    imported = 0
                    for _, row in df.iterrows():
                        record = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
                        record["status"] = record.get("status", "CLOSED")
                        if db_insert("trades", record):
                            imported += 1
                    st.success(f"✅ Imported {imported} trades!")
            except Exception as e:
                st.error(f"❌ Import failed: {e}")
    
    with col2:
        st.markdown("**⚠️ Danger Zone**")
        st.caption("These actions are irreversible!")
        
        if st.button("🗑️ Clear All Trades", type="secondary"):
            st.session_state["confirm_clear_trades"] = True
        
        if st.session_state.get("confirm_clear_trades"):
            st.warning("Are you sure? This will delete ALL trades!")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Yes, Delete All", type="primary"):
                    trades = db_select("trades")
                    for t in trades:
                        db_delete("trades", t["id"])
                    st.session_state["confirm_clear_trades"] = False
                    st.success("✅ All trades deleted")
                    st.rerun()
            with col_no:
                if st.button("Cancel"):
                    st.session_state["confirm_clear_trades"] = False
                    st.rerun()
        
        st.markdown("---")
        st.markdown("**📊 Database Stats**")
        trades_count = len(db_select("trades"))
        strategies_count = len(db_select("strategies"))
        journals_count = len(db_select("journal_entries"))
        accounts_count = len(db_select("prop_accounts"))
        
        stats = [
            ("Trades", trades_count),
            ("Strategies", strategies_count),
            ("Journal Entries", journals_count),
            ("Prop Accounts", accounts_count),
        ]
        for label, count in stats:
            st.markdown(f"- **{label}:** {count} records")
