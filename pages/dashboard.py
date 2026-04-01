"""
Dashboard Page - Main performance command center
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar

from utils.database import db_select
from utils.analytics import (
    trades_to_df, compute_overview, compute_equity_curve,
    compute_daily_stats, detect_behavioral_patterns
)
from components.ui import (
    metric_card, insight_card, page_header, empty_state,
    equity_curve_chart, pnl_bar_chart, win_rate_donut,
    session_bar_chart, asset_bar_chart, r_multiple_histogram,
    apply_chart_theme
)
import plotly.graph_objects as go


def render():
    page_header("📊", "Dashboard", "Your trading performance command center")

    # Load data
    all_trades = db_select("trades", order_by="trade_date", order_desc=True)
    closed_trades = [t for t in all_trades if t.get("status") == "CLOSED"]
    df = trades_to_df(closed_trades)
    
    # ── Filters ──────────────────────────────────────────────────────────────
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            date_range = st.selectbox("Period", ["All Time", "This Week", "This Month", "Last Month", "Last 3 Months", "This Year"])
        with col2:
            assets = ["All"] + sorted(list(set(t.get("asset", "") for t in closed_trades if t.get("asset"))))
            sel_asset = st.selectbox("Asset", assets)
        with col3:
            sessions = ["All", "London", "New York", "Asia", "Pre-Market", "After-Hours"]
            sel_session = st.selectbox("Session", sessions)
        with col4:
            directions = ["All", "BUY", "SELL"]
            sel_dir = st.selectbox("Direction", directions)
        with col5:
            strategies = db_select("strategies")
            strat_names = ["All"] + [s["name"] for s in strategies]
            sel_strat = st.selectbox("Strategy", strat_names)
    
    # Apply filters
    if not df.empty:
        today = date.today()
        if date_range == "This Week":
            start = today - timedelta(days=today.weekday())
            df = df[df["trade_date"].dt.date >= start]
        elif date_range == "This Month":
            df = df[df["trade_date"].dt.month == today.month]
        elif date_range == "Last Month":
            lm = (today.replace(day=1) - timedelta(days=1))
            df = df[(df["trade_date"].dt.month == lm.month) & (df["trade_date"].dt.year == lm.year)]
        elif date_range == "Last 3 Months":
            df = df[df["trade_date"].dt.date >= today - timedelta(days=90)]
        elif date_range == "This Year":
            df = df[df["trade_date"].dt.year == today.year]
        
        if sel_asset != "All":
            df = df[df["asset"] == sel_asset]
        if sel_session != "All" and "session" in df.columns:
            df = df[df["session"] == sel_session]
        if sel_dir != "All" and "direction" in df.columns:
            df = df[df["direction"] == sel_dir]

    # ── Key Metrics ──────────────────────────────────────────────────────────
    overview = compute_overview(df)
    total_pnl = overview["total_pnl"]
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        pnl_color = "green" if total_pnl >= 0 else "red"
        metric_card("Net P&L", f"${total_pnl:+,.2f}", "", pnl_color, "💰")
    with col2:
        metric_card("Win Rate", f"{overview['win_rate']:.1f}%",
                    f"{overview['total_trades_wins']}W / {overview['total_trades_losses']}L",
                    "blue", "🎯")
    with col3:
        pf = overview["profit_factor"]
        pf_str = f"{pf:.2f}" if pf < 100 else "∞"
        pf_color = "green" if pf >= 1.5 else ("yellow" if pf >= 1 else "red")
        metric_card("Profit Factor", pf_str, "", pf_color, "⚡")
    with col4:
        avg_r = overview["avg_r"]
        r_color = "green" if avg_r > 0 else "red"
        metric_card("Avg R-Multiple", f"{avg_r:+.2f}R", "", r_color, "📐")
    with col5:
        dd = overview["max_drawdown"]
        dd_color = "green" if dd < 5 else ("yellow" if dd < 10 else "red")
        metric_card("Max Drawdown", f"{dd:.1f}%", "", dd_color, "📉")
    with col6:
        streak = overview["current_streak"]
        stype = overview["streak_type"]
        s_color = "green" if stype == "win" else ("red" if stype == "loss" else "blue")
        s_icon = "🔥" if stype == "win" else ("💔" if stype == "loss" else "—")
        metric_card(f"{stype.title()} Streak", f"{streak}", f"{s_icon} current", s_color, "")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Additional Metrics Row ────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total Trades", str(overview["total_trades"]), "", "blue", "📋")
    with col2:
        metric_card("Avg Win", f"${overview['avg_win']:+,.2f}", "", "green", "✅")
    with col3:
        metric_card("Avg Loss", f"${overview['avg_loss']:+,.2f}", "", "red", "❌")
    with col4:
        metric_card("Total Fees", f"${overview['total_fees']:,.2f}", "", "yellow", "💸")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row 1 ─────────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 1])
    
    with col_left:
        st.markdown("##### Equity Curve")
        if not df.empty:
            fig = equity_curve_chart(df)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            empty_state("📈", "No trades yet", "Add your first trade to see the equity curve")

    with col_right:
        st.markdown("##### Win Rate")
        if overview["total_trades"] > 0:
            fig = win_rate_donut(overview["win_rate"])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown(f"""
            <div style="text-align:center;font-size:0.8rem;color:var(--text-muted);">
                <span style="color:#00d68f;">█</span> {overview['total_trades_wins']} Wins &nbsp;&nbsp;
                <span style="color:#ff4757;">█</span> {overview['total_trades_losses']} Losses
            </div>
            """, unsafe_allow_html=True)
        else:
            empty_state("🎯", "No data", "")

    # ── Charts Row 2 ─────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        if not df.empty:
            fig = pnl_bar_chart(df)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            empty_state("📊", "No daily P&L data", "")
    with col2:
        if not df.empty:
            fig = r_multiple_histogram(df)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            empty_state("📐", "No R-Multiple data", "")

    # ── Charts Row 3 ─────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        if not df.empty:
            fig = session_bar_chart(df)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        if not df.empty:
            fig = asset_bar_chart(df)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Calendar View ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### 📅 Trading Calendar")
    _render_calendar(df)

    # ── AI Insights ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### 💡 Behavioral Insights")
    insights = detect_behavioral_patterns(df)
    if insights:
        col1, col2 = st.columns(2)
        for i, ins in enumerate(insights):
            with col1 if i % 2 == 0 else col2:
                insight_card(ins)
    else:
        if not df.empty:
            st.info("💡 Keep trading! Insights will appear as you build more history (need 5+ trades).")
        else:
            empty_state("🔍", "No insights yet", "Add trades to get personalized insights")

    # ── Recent Trades ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### 📋 Recent Trades")
    recent = all_trades[:10]
    if recent:
        _render_trade_table(recent)
    else:
        empty_state("📋", "No trades logged", "Head to 'Add Trade' to log your first trade")


def _render_calendar(df: pd.DataFrame):
    """Render a monthly calendar view."""
    today = date.today()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        year = st.number_input("Year", min_value=2020, max_value=2030, value=today.year, label_visibility="collapsed")
    with col2:
        month_names = ["January","February","March","April","May","June",
                       "July","August","September","October","November","December"]
        month = st.selectbox("Month", range(1, 13), index=today.month - 1,
                             format_func=lambda x: month_names[x-1], label_visibility="collapsed")
    
    # Build daily PnL map
    daily_map = {}
    if not df.empty:
        daily = compute_daily_stats(df)
        for _, row in daily.iterrows():
            d = row["trade_date"]
            if hasattr(d, 'date'):
                d = d.date()
            daily_map[d] = {"pnl": row["total_pnl"], "trades": row["trades"]}
    
    cal = calendar.monthcalendar(year, month)
    days_header = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Header
    cols = st.columns(7)
    for i, d in enumerate(days_header):
        cols[i].markdown(f"<div style='text-align:center;font-size:0.75rem;font-weight:600;color:var(--text-muted);padding:8px 0;'>{d}</div>", unsafe_allow_html=True)
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown("<div style='height:50px;'></div>", unsafe_allow_html=True)
                continue
            d = date(year, month, day)
            is_today = d == today
            cell_data = daily_map.get(d)
            
            if cell_data:
                pnl = cell_data["pnl"]
                trades = cell_data["trades"]
                cls = "profit" if pnl >= 0 else "loss"
                pnl_str = f"${pnl:+,.0f}"
                color = "#00d68f" if pnl >= 0 else "#ff4757"
                today_border = "border: 2px solid #4c9eff !important;" if is_today else ""
                cols[i].markdown(f"""
                <div class="cal-cell {cls}" style="{today_border}">
                    <div style="font-weight:600;color:var(--text-secondary);">{day}</div>
                    <div style="font-size:0.7rem;color:{color};font-family:var(--font-mono);">{pnl_str}</div>
                    <div style="font-size:0.65rem;color:var(--text-muted);">{trades}t</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                today_style = "border: 2px solid #4c9eff;" if is_today else "border: 1px solid var(--border);"
                cols[i].markdown(f"""
                <div class="cal-cell neutral" style="{today_style}">
                    <div style="font-weight:500;color:var(--text-muted);">{day}</div>
                </div>
                """, unsafe_allow_html=True)


def _render_trade_table(trades: list):
    """Render compact trade table."""
    headers = ["Date", "Asset", "Dir", "Entry", "Exit", "P&L", "R", "Session"]
    
    header_cols = st.columns([1.2, 1, 0.8, 1, 1, 1, 0.8, 1])
    for col, h in zip(header_cols, headers):
        col.markdown(f"<div style='font-size:0.72rem;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;padding-bottom:8px;'>{h}</div>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin:0 0 8px 0;'>", unsafe_allow_html=True)
    
    for trade in trades:
        pnl = trade.get("pnl", 0) or 0
        pnl_color = "#00d68f" if pnl >= 0 else "#ff4757"
        dir_color = "#00d68f" if trade.get("direction") == "BUY" else "#ff4757"
        
        cols = st.columns([1.2, 1, 0.8, 1, 1, 1, 0.8, 1])
        cols[0].markdown(f"<span style='font-size:0.82rem;font-family:var(--font-mono);'>{str(trade.get('trade_date',''))[:10]}</span>", unsafe_allow_html=True)
        cols[1].markdown(f"<span style='font-size:0.82rem;font-weight:600;'>{trade.get('asset','')}</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<span style='font-size:0.75rem;font-weight:600;color:{dir_color};'>{trade.get('direction','')}</span>", unsafe_allow_html=True)
        cols[3].markdown(f"<span style='font-size:0.82rem;font-family:var(--font-mono);'>{trade.get('entry_price','')}</span>", unsafe_allow_html=True)
        cols[4].markdown(f"<span style='font-size:0.82rem;font-family:var(--font-mono);'>{trade.get('exit_price','') or '—'}</span>", unsafe_allow_html=True)
        cols[5].markdown(f"<span style='font-size:0.82rem;font-family:var(--font-mono);color:{pnl_color};'>${pnl:+.2f}</span>", unsafe_allow_html=True)
        r = trade.get("r_multiple", 0) or 0
        r_color = "#00d68f" if r >= 0 else "#ff4757"
        cols[6].markdown(f"<span style='font-size:0.82rem;font-family:var(--font-mono);color:{r_color};'>{r:+.1f}R</span>", unsafe_allow_html=True)
        cols[7].markdown(f"<span style='font-size:0.75rem;color:var(--text-muted);'>{trade.get('session','') or '—'}</span>", unsafe_allow_html=True)
