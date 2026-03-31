"""
TradeForge - Professional Trade Journal
Main Application Entry Point
"""
import streamlit as st
import os
from pathlib import Path

# ── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TradeForge | Trade Journal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load environment ─────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# Ensure data dirs exist
Path("data").mkdir(exist_ok=True)
Path("data/screenshots").mkdir(exist_ok=True)

# ── Inject CSS ───────────────────────────────────────────────────────────────
from components.ui import inject_css
inject_css()

# ── Session State Init ───────────────────────────────────────────────────────
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

# ── Sidebar Navigation ───────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="padding: 20px 0 24px 0; border-bottom: 1px solid var(--border); margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 38px; height: 38px; background: linear-gradient(135deg, #4c9eff, #9b59ff);
                 border-radius: 10px; display: flex; align-items: center; justify-content: center;
                 font-size: 1.2rem;">⚡</div>
            <div>
                <div style="font-size: 1.1rem; font-weight: 700; letter-spacing: -0.02em; color: #e8ecf0;">TradeForge</div>
                <div style="font-size: 0.72rem; color: #555e7a;">Performance Journal</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation items
    nav_items = [
        ("📊", "Dashboard", "Overview & metrics"),
        ("➕", "Add Trade", "Log new trades"),
        ("📓", "Journal", "Reflections & goals"),
        ("🧩", "Strategies", "Rules & playbooks"),
        ("🏦", "Prop Firm", "Account tracker"),
        ("🔬", "Analytics", "Deep analysis"),
        ("⚙️", "Settings", "Configuration"),
    ]
    
    for icon, label, desc in nav_items:
        is_active = st.session_state.current_page == label
        active_style = "background: var(--bg-card); color: var(--text-primary); border-left: 2px solid #4c9eff;" if is_active else ""
        
        if st.button(
            f"{icon}  {label}",
            key=f"nav_{label}",
            use_container_width=True,
            type="secondary"
        ):
            st.session_state.current_page = label
            st.rerun()
    
    # Sync Status at bottom
    st.markdown("<br>" * 3, unsafe_allow_html=True)
    st.markdown("---")
    
    from utils.database import get_sync_status, sync_offline_changes
    sync = get_sync_status()
    
    from components.ui import sync_status_badge
    sync_status_badge(sync)
    
    # Auto-sync if there are pending changes and we're connected
    if sync.get("connected") and sync.get("pending_sync", 0) > 0:
        result = sync_offline_changes()
        if result["synced"] > 0:
            st.toast(f"✅ Synced {result['synced']} offline changes to Supabase!")
    
    # Quick stats
    st.markdown("<br>", unsafe_allow_html=True)
    
    from utils.database import db_select
    from utils.analytics import trades_to_df, compute_overview
    
    trades = db_select("trades")
    closed = [t for t in trades if t.get("status") == "CLOSED"]
    df = trades_to_df(closed)
    overview = compute_overview(df)
    
    pnl = overview.get("net_pnl", 0)
    pnl_color = "#00d68f" if pnl >= 0 else "#ff4757"
    wr = overview.get("win_rate", 0)
    total = overview.get("total_trades", 0)
    
    # Today's P&L
    import pandas as pd
    from datetime import date
    today_pnl = 0
    if not df.empty and "trade_date" in df.columns:
        today = str(date.today())
        today_trades = df[df["trade_date"].dt.date.astype(str) == today]
        today_pnl = today_trades["net_pnl"].sum() if not today_trades.empty else 0
    
    st.markdown(f"""
    <div style="background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; padding: 14px;">
        <div style="font-size: 0.7rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; 
             letter-spacing: 0.08em; margin-bottom: 10px;">Quick Stats</div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span style="font-size: 0.78rem; color: var(--text-secondary);">Today</span>
            <span style="font-family: var(--font-mono); font-size: 0.78rem; color: {'#00d68f' if today_pnl >= 0 else '#ff4757'};">${today_pnl:+.2f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span style="font-size: 0.78rem; color: var(--text-secondary);">All-time P&L</span>
            <span style="font-family: var(--font-mono); font-size: 0.78rem; color: {pnl_color};">${pnl:+.2f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span style="font-size: 0.78rem; color: var(--text-secondary);">Win Rate</span>
            <span style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--accent-blue);">{wr:.1f}%</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="font-size: 0.78rem; color: var(--text-secondary);">Total Trades</span>
            <span style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-primary);">{total}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Risk alerts
    settings_path = Path("data/settings.json")
    if settings_path.exists():
        import json
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            
            daily_limit = settings.get("daily_trade_limit", 5)
            max_daily_loss = settings.get("max_daily_loss_pct", 3.0)
            starting_balance = settings.get("starting_balance", 10000)
            
            # Count today's trades
            today_str = str(date.today())
            today_count = len([t for t in trades if str(t.get("trade_date",""))[:10] == today_str])
            
            if today_count >= daily_limit:
                st.markdown(f"""
                <div style="background:rgba(255,71,87,0.1);border:1px solid rgba(255,71,87,0.3);
                     border-radius:8px;padding:10px 12px;margin-top:10px;">
                    <div style="font-size:0.78rem;color:#ff4757;">⛔ Daily trade limit reached ({today_count}/{daily_limit})</div>
                </div>
                """, unsafe_allow_html=True)
            
            daily_loss_limit = starting_balance * max_daily_loss / 100
            if today_pnl < 0 and abs(today_pnl) >= daily_loss_limit * 0.8:
                pct_used = abs(today_pnl) / daily_loss_limit * 100
                st.markdown(f"""
                <div style="background:rgba(255,204,0,0.1);border:1px solid rgba(255,204,0,0.3);
                     border-radius:8px;padding:10px 12px;margin-top:10px;">
                    <div style="font-size:0.78rem;color:#ffcc00;">⚠️ {pct_used:.0f}% of daily loss limit used</div>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass


# ── Page Router ──────────────────────────────────────────────────────────────
page = st.session_state.current_page

if page == "Dashboard":
    from pages.dashboard import render
    render()

elif page == "Add Trade":
    from pages.add_trade import render
    render()

elif page == "Journal":
    from pages.journal import render
    render()

elif page == "Strategies":
    from pages.strategies import render
    render()

elif page == "Prop Firm":
    from pages.prop_firm import render
    render()

elif page == "Analytics":
    from pages.analytics import render
    render()

elif page == "Settings":
    from pages.settings import render
    render()
