"""
Add Trade Page - Manual trade entry form
"""
import streamlit as st
import uuid
from datetime import datetime, date
from typing import Dict, List

from utils.database import db_insert, db_select, db_update, db_delete
from utils.analytics import _compute_pnl, _compute_r_multiple
from components.ui import page_header, empty_state, badge, apply_chart_theme
import plotly.graph_objects as go


def render():
    page_header("➕", "Trade Log", "Log new trades and manage your history")
    
    tab1, tab2 = st.tabs(["📝 Add New Trade", "📋 Trade History"])
    
    with tab1:
        _render_add_trade_form()
    
    with tab2:
        _render_trade_history()


def _render_add_trade_form():
    """Main trade entry form."""
    strategies = db_select("strategies")
    prop_accounts = db_select("prop_accounts", filters={"is_active": True})
    
    with st.form("add_trade_form", clear_on_submit=True):
        # ── Core Trade Info ───────────────────────────────────────────────────
        st.markdown("#### 📌 Core Trade Details")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            trade_date = st.date_input("Trade Date", value=date.today())
        with col2:
            trade_time = st.time_input("Entry Time", value=datetime.now().time())
        with col3:
            asset = st.text_input("Asset / Symbol", placeholder="EURUSD, BTCUSD, NQ...")
        with col4:
            direction = st.selectbox("Direction", ["BUY", "SELL"])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            entry_price = st.number_input("Entry Price", min_value=0.0, value=0.0, format="%.5f")
        with col2:
            exit_price = st.number_input("Exit Price (0 if open)", min_value=0.0, value=0.0, format="%.5f")
        with col3:
            stop_loss = st.number_input("Stop Loss", min_value=0.0, value=0.0, format="%.5f")
        with col4:
            take_profit = st.number_input("Take Profit", min_value=0.0, value=0.0, format="%.5f")
        with col5:
            lot_size = st.number_input("Lot Size / Qty", min_value=0.0, value=1.0, format="%.4f")

        col1, col2, col3 = st.columns(3)
        with col1:
            fees = st.number_input("Fees / Commissions ($)", min_value=0.0, value=0.0, format="%.2f")
        with col2:
            session = st.selectbox("Session", ["", "London", "New York", "Asia", "Pre-Market", "After-Hours"])
        with col3:
            status = st.selectbox("Status", ["CLOSED", "OPEN", "CANCELLED"])

        st.markdown("<br>", unsafe_allow_html=True)
        
        # ── Strategy & Context ────────────────────────────────────────────────
        st.markdown("#### 🧠 Strategy & Context")
        col1, col2, col3 = st.columns(3)
        with col1:
            strat_options = ["None"] + [s["name"] for s in strategies]
            selected_strategy = st.selectbox("Strategy Used", strat_options)
        with col2:
            confidence = st.slider("Confidence Level (1-10)", 1, 10, 7)
        with col3:
            prop_opts = ["None"] + [f"{a['firm_name']} - {a['account_name']}" for a in prop_accounts]
            selected_prop = st.selectbox("Prop Account", prop_opts)

        pre_bias = st.text_area("Pre-Trade Bias / Setup Notes", placeholder="What was your thesis? What did you see in the market?", height=80)

        # ── Rules Checklist ───────────────────────────────────────────────────
        rules_followed = []
        rules_broken = []
        if selected_strategy != "None":
            strat = next((s for s in strategies if s["name"] == selected_strategy), None)
            if strat and strat.get("rules"):
                st.markdown("#### ✅ Rules Checklist")
                rules = strat["rules"] if isinstance(strat["rules"], list) else []
                
                if rules:
                    rule_cols = st.columns(2)
                    for i, rule in enumerate(rules):
                        rule_text = rule if isinstance(rule, str) else rule.get("text", str(rule))
                        with rule_cols[i % 2]:
                            checked = st.checkbox(rule_text, key=f"rule_{i}")
                            if checked:
                                rules_followed.append(rule_text)
                            else:
                                rules_broken.append(rule_text)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Screenshots ───────────────────────────────────────────────────────
        st.markdown("#### 📸 Screenshots")
        uploaded_files = st.file_uploader(
            "Upload chart screenshots (PNG, JPG, GIF)",
            type=["png", "jpg", "jpeg", "gif"],
            accept_multiple_files=True
        )
        
        # ── Post-Trade Reflection ─────────────────────────────────────────────
        st.markdown("#### 📝 Post-Trade Reflection")
        col1, col2 = st.columns(2)
        with col1:
            reflection = st.text_area("What happened? Execution notes", 
                                       placeholder="How did the trade play out? Any mistakes?", height=100)
        with col2:
            tags_input = st.text_input("Tags (comma-separated)", 
                                        placeholder="breakout, trend-following, FOMO...")

        submitted = st.form_submit_button("💾 Save Trade", type="primary", use_container_width=True)

        if submitted:
            if not asset:
                st.error("❌ Asset/Symbol is required!")
                return
            if entry_price == 0:
                st.error("❌ Entry price is required!")
                return

            # Compute PnL
            pnl = 0.0
            r_multiple = 0.0
            if exit_price > 0 and status == "CLOSED":
                direction_mult = 1 if direction == "BUY" else -1
                diff = exit_price - entry_price
                pnl = diff * direction_mult * lot_size
                net_pnl = pnl - fees
                if stop_loss > 0:
                    risk = abs(entry_price - stop_loss)
                    if risk > 0:
                        r_multiple = net_pnl / (risk * lot_size)

            # Resolve IDs
            strategy_id = None
            if selected_strategy != "None":
                strat = next((s for s in strategies if s["name"] == selected_strategy), None)
                if strat:
                    strategy_id = strat["id"]

            prop_account_id = None
            if selected_prop != "None":
                idx = prop_opts.index(selected_prop) - 1
                if 0 <= idx < len(prop_accounts):
                    prop_account_id = prop_accounts[idx]["id"]

            # Handle screenshots - store as base64 or local paths
            screenshot_urls = []
            for f in uploaded_files:
                import base64
                b64 = base64.b64encode(f.read()).decode()
                screenshot_urls.append(f"data:{f.type};base64,{b64}")

            tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

            trade_record = {
                "trade_date": str(trade_date),
                "trade_time": str(trade_time),
                "asset": asset.upper().strip(),
                "direction": direction,
                "entry_price": float(entry_price),
                "exit_price": float(exit_price) if exit_price > 0 else None,
                "stop_loss": float(stop_loss) if stop_loss > 0 else None,
                "take_profit": float(take_profit) if take_profit > 0 else None,
                "lot_size": float(lot_size),
                "fees": float(fees),
                "session": session or None,
                "status": status,
                "pnl": round(pnl, 4),
                "r_multiple": round(r_multiple, 3),
                "strategy_id": strategy_id,
                "prop_account_id": prop_account_id,
                "confidence_level": confidence,
                "pre_trade_bias": pre_bias,
                "post_trade_reflection": reflection,
                "rules_followed": rules_followed,
                "rules_broken": rules_broken,
                "tags": tags,
                "screenshot_urls": screenshot_urls,
            }

            result = db_insert("trades", trade_record)
            if result:
                st.success(f"✅ Trade saved! P&L: ${pnl:+.2f} | R: {r_multiple:+.2f}R")
                st.balloons()
            else:
                st.error("❌ Failed to save trade. Check your connection.")


def _render_trade_history():
    """Render trade history with edit/delete."""
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_status = st.selectbox("Status", ["All", "CLOSED", "OPEN", "CANCELLED"])
    with col2:
        filter_dir = st.selectbox("Direction", ["All", "BUY", "SELL"])
    with col3:
        filter_asset = st.text_input("Filter by Asset", placeholder="EURUSD...")
    with col4:
        sort_by = st.selectbox("Sort by", ["Date ↓", "Date ↑", "P&L ↓", "P&L ↑"])

    trades = db_select("trades", order_by="trade_date", order_desc=True)
    
    # Apply filters
    if filter_status != "All":
        trades = [t for t in trades if t.get("status") == filter_status]
    if filter_dir != "All":
        trades = [t for t in trades if t.get("direction") == filter_dir]
    if filter_asset:
        trades = [t for t in trades if filter_asset.upper() in str(t.get("asset", "")).upper()]
    
    # Sort
    if sort_by == "Date ↑":
        trades.sort(key=lambda x: x.get("trade_date", ""))
    elif sort_by == "P&L ↓":
        trades.sort(key=lambda x: float(x.get("pnl", 0) or 0), reverse=True)
    elif sort_by == "P&L ↑":
        trades.sort(key=lambda x: float(x.get("pnl", 0) or 0))

    st.markdown(f"**{len(trades)} trades found**")
    st.markdown("---")

    if not trades:
        empty_state("📋", "No trades found", "Adjust filters or add your first trade")
        return

    for trade in trades:
        _render_trade_row(trade)


def _render_trade_row(trade: Dict):
    """Render a single trade row with expand/collapse."""
    pnl = float(trade.get("pnl", 0) or 0)
    pnl_color = "#00d68f" if pnl >= 0 else "#ff4757"
    dir_color = "#00d68f" if trade.get("direction") == "BUY" else "#ff4757"
    r = float(trade.get("r_multiple", 0) or 0)
    r_color = "#00d68f" if r >= 0 else "#ff4757"
    status = trade.get("status", "OPEN")
    status_badge = {"CLOSED": "green", "OPEN": "blue", "CANCELLED": "gray"}.get(status, "gray")
    
    header = (
        f"{str(trade.get('trade_date',''))[:10]}  |  "
        f"**{trade.get('asset','')}**  |  "
        f"<span style='color:{dir_color}'>{trade.get('direction','')}</span>  |  "
        f"Entry: {trade.get('entry_price','')}  |  "
        f"<span style='color:{pnl_color}'>P&L: ${pnl:+.2f}</span>  |  "
        f"<span style='color:{r_color}'>{r:+.1f}R</span>  |  "
        f"{trade.get('session','') or ''}"
    )
    
    with st.expander(f"{str(trade.get('trade_date',''))[:10]} | {trade.get('asset','')} {trade.get('direction','')} | ${pnl:+.2f}"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Asset:** {trade.get('asset','')}")
            st.markdown(f"**Direction:** {trade.get('direction','')}")
            st.markdown(f"**Entry:** {trade.get('entry_price','')}")
            st.markdown(f"**Exit:** {trade.get('exit_price','') or 'Open'}")
            st.markdown(f"**Stop Loss:** {trade.get('stop_loss','') or '—'}")
            st.markdown(f"**Take Profit:** {trade.get('take_profit','') or '—'}")
        
        with col2:
            st.markdown(f"**Lot Size:** {trade.get('lot_size','')}")
            st.markdown(f"**Fees:** ${float(trade.get('fees',0) or 0):.2f}")
            st.markdown(f"**Session:** {trade.get('session','') or '—'}")
            st.markdown(f"**Confidence:** {trade.get('confidence_level','') or '—'}/10")
            st.markdown(f"**R-Multiple:** {r:+.2f}R")
            st.markdown(f"**Status:** {status}")
        
        with col3:
            tags = trade.get("tags", []) or []
            if tags:
                st.markdown("**Tags:** " + " ".join([f"`{t}`" for t in tags]))
            
            rules_followed = trade.get("rules_followed", []) or []
            rules_broken = trade.get("rules_broken", []) or []
            if rules_followed:
                st.markdown("**✅ Rules Followed:**")
                for r_item in rules_followed:
                    st.markdown(f"  - {r_item}")
            if rules_broken:
                st.markdown("**❌ Rules Broken:**")
                for r_item in rules_broken:
                    st.markdown(f"  - {r_item}")
        
        if trade.get("pre_trade_bias"):
            st.markdown(f"**Pre-Trade Bias:** {trade['pre_trade_bias']}")
        if trade.get("post_trade_reflection"):
            st.markdown(f"**Reflection:** {trade['post_trade_reflection']}")
        
        # Screenshots
        screenshots = trade.get("screenshot_urls", []) or []
        if screenshots:
            st.markdown("**Screenshots:**")
            img_cols = st.columns(min(len(screenshots), 4))
            for i, url in enumerate(screenshots[:4]):
                with img_cols[i]:
                    st.image(url, use_column_width=True)
        
        # Actions
        col_edit, col_delete, _ = st.columns([1, 1, 4])
        with col_edit:
            if st.button("✏️ Edit", key=f"edit_{trade['id']}"):
                st.session_state[f"editing_{trade['id']}"] = True
        with col_delete:
            if st.button("🗑️ Delete", key=f"del_{trade['id']}"):
                if db_delete("trades", trade["id"]):
                    st.success("Trade deleted!")
                    st.rerun()
