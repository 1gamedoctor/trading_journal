"""
Strategies & Rules Page
"""
import streamlit as st
import json
from utils.database import db_insert, db_select, db_update, db_delete
from utils.analytics import trades_to_df, compute_by_strategy
from components.ui import page_header, metric_card, empty_state, badge


def render():
    page_header("🧩", "Strategies & Rules", "Define playbooks and track rule adherence")
    
    strategies = db_select("strategies")
    
    tab1, tab2, tab3 = st.tabs(["📚 My Strategies", "➕ New Strategy", "📊 Strategy Analytics"])
    
    with tab1:
        _render_strategy_list(strategies)
    
    with tab2:
        _render_new_strategy_form()
    
    with tab3:
        _render_strategy_analytics(strategies)


def _render_strategy_list(strategies):
    if not strategies:
        empty_state("🧩", "No strategies yet", "Create your first trading strategy in the 'New Strategy' tab")
        return
    
    for strat in strategies:
        _render_strategy_card(strat)


def _render_strategy_card(strat: dict):
    trades = db_select("trades", filters={"strategy_id": strat["id"]})
    closed = [t for t in trades if t.get("status") == "CLOSED"]
    df = trades_to_df(closed)
    
    win_rate = 0
    total_pnl = 0
    if not df.empty and "is_win" in df.columns:
        win_rate = df["is_win"].mean() * 100
        total_pnl = df["net_pnl"].sum()
    
    active_badge = "🟢 Active" if strat.get("is_active") else "🔴 Inactive"
    
    with st.expander(f"**{strat['name']}** — {len(trades)} trades | WR: {win_rate:.0f}% | P&L: ${total_pnl:+.2f}"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Description:** {strat.get('description', '—')}")
            st.markdown(f"**Ideal Conditions:** {strat.get('ideal_conditions', '—')}")
            tf = strat.get("timeframes", []) or []
            mkts = strat.get("markets", []) or []
            if tf:
                st.markdown(f"**Timeframes:** {', '.join(tf)}")
            if mkts:
                st.markdown(f"**Markets:** {', '.join(mkts)}")
            st.markdown(f"**R:R Target:** {strat.get('risk_reward_target', 2.0):.1f}")
            st.markdown(f"**Status:** {active_badge}")
        
        with col2:
            col_a, col_b = st.columns(2)
            with col_a:
                metric_card("Win Rate", f"{win_rate:.0f}%", "", "green" if win_rate >= 50 else "red")
            with col_b:
                metric_card("Net P&L", f"${total_pnl:+,.0f}", "", "green" if total_pnl >= 0 else "red")
        
        # Rules
        rules = strat.get("rules", []) or []
        if rules:
            st.markdown("**📋 Rules:**")
            
            # Compute rule adherence
            all_rule_data = {}
            for trade in [t for t in db_select("trades", filters={"strategy_id": strat["id"]}) if t.get("status") == "CLOSED"]:
                for r in (trade.get("rules_followed", []) or []):
                    if r not in all_rule_data:
                        all_rule_data[r] = {"followed": 0, "broken": 0}
                    all_rule_data[r]["followed"] += 1
                for r in (trade.get("rules_broken", []) or []):
                    if r not in all_rule_data:
                        all_rule_data[r] = {"followed": 0, "broken": 0}
                    all_rule_data[r]["broken"] += 1
            
            for rule in rules:
                rule_text = rule if isinstance(rule, str) else rule.get("text", str(rule))
                rd = all_rule_data.get(rule_text, {"followed": 0, "broken": 0})
                total_r = rd["followed"] + rd["broken"]
                adherence = (rd["followed"] / total_r * 100) if total_r > 0 else None
                
                adh_str = f" — {adherence:.0f}% adherence" if adherence is not None else ""
                color = "#00d68f" if adherence is not None and adherence >= 75 else ("#ffcc00" if adherence is not None and adherence >= 50 else "#ff4757" if adherence is not None else "#555e7a")
                
                st.markdown(f"<div style='padding:6px 12px;background:var(--bg-card);border-radius:6px;border:1px solid var(--border);margin-bottom:4px;font-size:0.85rem;'>"
                           f"{'✅' if adherence is None or adherence >= 50 else '⚠️'} {rule_text}"
                           f"<span style='float:right;color:{color};font-family:var(--font-mono);font-size:0.75rem;'>{adh_str}</span>"
                           f"</div>", unsafe_allow_html=True)
        
        col_del, col_tog, _ = st.columns([1, 1, 4])
        with col_del:
            if st.button("🗑️ Delete", key=f"del_s_{strat['id']}"):
                db_delete("strategies", strat["id"])
                st.rerun()
        with col_tog:
            label = "Deactivate" if strat.get("is_active") else "Activate"
            if st.button(label, key=f"tog_s_{strat['id']}"):
                db_update("strategies", strat["id"], {"is_active": not strat.get("is_active", True)})
                st.rerun()


def _render_new_strategy_form():
    with st.form("new_strategy_form", clear_on_submit=True):
        st.markdown("#### Strategy Information")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Strategy Name*", placeholder="ICT Smart Money Concepts")
        with col2:
            rr_target = st.number_input("R:R Target", min_value=0.5, value=2.0, step=0.5)
        
        description = st.text_area("Description", placeholder="Describe your strategy, its core concepts and edge...")
        ideal_conditions = st.text_area("Ideal Market Conditions", placeholder="When does this strategy work best?")
        
        col1, col2 = st.columns(2)
        with col1:
            tf_input = st.text_input("Timeframes (comma-separated)", placeholder="1H, 4H, Daily")
        with col2:
            mkts_input = st.text_input("Markets (comma-separated)", placeholder="Forex, Gold, Indices")
        
        st.markdown("#### Rules Checklist")
        st.markdown("*Add one rule per line. These will appear as checkboxes when logging trades.*")
        rules_text = st.text_area(
            "Rules (one per line)",
            placeholder="Wait for London open\nTrade with higher timeframe bias\nMinimum 1:2 R:R\nOnly trade A+ setups\nNo trading on news events",
            height=150
        )
        
        submitted = st.form_submit_button("💾 Save Strategy", type="primary", use_container_width=True)
        
        if submitted:
            if not name:
                st.error("❌ Strategy name is required!")
                return
            
            rules = [r.strip() for r in rules_text.split("\n") if r.strip()] if rules_text else []
            timeframes = [t.strip() for t in tf_input.split(",") if t.strip()] if tf_input else []
            markets = [m.strip() for m in mkts_input.split(",") if m.strip()] if mkts_input else []
            
            result = db_insert("strategies", {
                "name": name,
                "description": description,
                "ideal_conditions": ideal_conditions,
                "timeframes": timeframes,
                "markets": markets,
                "rules": rules,
                "risk_reward_target": rr_target,
                "is_active": True
            })
            
            if result:
                st.success(f"✅ Strategy '{name}' saved with {len(rules)} rules!")
            else:
                st.error("❌ Failed to save strategy")


def _render_strategy_analytics(strategies):
    if not strategies:
        empty_state("📊", "No strategies to analyze", "Create strategies first to see analytics here")
        return
    
    all_trades = db_select("trades")
    closed = [t for t in all_trades if t.get("status") == "CLOSED"]
    
    if not closed:
        empty_state("📊", "No closed trades yet", "Close some trades to see strategy performance")
        return
    
    # Merge strategy names into trades
    strat_map = {s["id"]: s["name"] for s in strategies}
    for t in closed:
        sid = t.get("strategy_id")
        t["strategy_name"] = strat_map.get(sid, "Untagged") if sid else "Untagged"
    
    df = trades_to_df(closed)
    if df.empty:
        return
    
    # Add strategy name to df
    import pandas as pd
    strat_name_map = {t["id"]: t["strategy_name"] for t in closed}
    df["strategy_name"] = df["id"].map(strat_name_map)
    
    strat_perf = compute_by_strategy(df)
    
    if strat_perf.empty:
        empty_state("📊", "Not enough data", "")
        return
    
    import plotly.graph_objects as go
    
    # Strategy comparison chart
    colors = ["#00d68f" if v >= 0 else "#ff4757" for v in strat_perf["total_pnl"]]
    fig = go.Figure(go.Bar(
        x=strat_perf["strategy_name"],
        y=strat_perf["total_pnl"],
        marker_color=colors,
        text=[f"${v:,.0f}" for v in strat_perf["total_pnl"]],
        textposition="outside"
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8b92a8"), height=280,
        title=dict(text="P&L by Strategy", font=dict(size=14, color="#e8ecf0"))
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    # Table
    st.markdown("#### Strategy Comparison")
    for _, row in strat_perf.iterrows():
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.markdown(f"**{row['strategy_name']}**")
        col2.markdown(f"Trades: **{int(row['trades'])}**")
        col3.markdown(f"WR: **{row['win_rate']:.0f}%**")
        pnl_color = "#00d68f" if row['total_pnl'] >= 0 else "#ff4757"
        col4.markdown(f"P&L: <span style='color:{pnl_color}'>**${row['total_pnl']:+,.2f}**</span>", unsafe_allow_html=True)
        col5.markdown(f"Avg R: **{row['avg_r']:+.2f}R**")
    
    # Rule adherence across all strategies
    st.markdown("---")
    st.markdown("#### ⚠️ Most Broken Rules")
    
    rule_broken_count = {}
    for t in closed:
        for r in (t.get("rules_broken", []) or []):
            rule_broken_count[r] = rule_broken_count.get(r, 0) + 1
    
    if rule_broken_count:
        sorted_broken = sorted(rule_broken_count.items(), key=lambda x: x[1], reverse=True)
        for rule, count in sorted_broken[:10]:
            st.markdown(f"""
            <div style='padding:10px 14px;background:rgba(255,71,87,0.08);border:1px solid rgba(255,71,87,0.2);
                 border-radius:8px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;'>
                <span style='font-size:0.85rem;'>❌ {rule}</span>
                <span style='font-family:var(--font-mono);font-size:0.8rem;color:#ff4757;font-weight:600;'>{count}x broken</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("✅ No broken rules recorded yet. Perfect discipline!")
