"""
Prop Firm Tracker Page
"""
import streamlit as st
from datetime import date, datetime
from utils.database import db_insert, db_select, db_update, db_delete
from utils.analytics import compute_prop_account_status
from components.ui import page_header, metric_card, progress_bar, empty_state


FIRM_PRESETS = {
    "FTMO": {"profit_target_pct": 10, "daily_loss_limit_pct": 5, "max_drawdown_pct": 10, "min_trading_days": 4},
    "The Funded Trader": {"profit_target_pct": 8, "daily_loss_limit_pct": 5, "max_drawdown_pct": 8, "min_trading_days": 0},
    "MyForexFunds": {"profit_target_pct": 8, "daily_loss_limit_pct": 5, "max_drawdown_pct": 12, "min_trading_days": 5},
    "TopstepFX": {"profit_target_pct": 6, "daily_loss_limit_pct": 2, "max_drawdown_pct": 6, "min_trading_days": 0},
    "Apex Trader": {"profit_target_pct": 6, "daily_loss_limit_pct": 3, "max_drawdown_pct": 6, "min_trading_days": 0},
    "E8 Funding": {"profit_target_pct": 8, "daily_loss_limit_pct": 5, "max_drawdown_pct": 8, "min_trading_days": 0},
    "Funded Next": {"profit_target_pct": 10, "daily_loss_limit_pct": 5, "max_drawdown_pct": 10, "min_trading_days": 5},
    "Custom": {"profit_target_pct": 10, "daily_loss_limit_pct": 5, "max_drawdown_pct": 10, "min_trading_days": 0},
}


def render():
    page_header("🏦", "Prop Firm Tracker", "Manage challenges and funded accounts")
    
    accounts = db_select("prop_accounts", order_by="created_at", order_desc=True)
    active = [a for a in accounts if a.get("is_active")]
    
    tab1, tab2, tab3 = st.tabs(["📊 Account Overview", "➕ Add Account", "📋 All Accounts"])
    
    with tab1:
        _render_account_overview(active)
    
    with tab2:
        _render_add_account_form()
    
    with tab3:
        _render_all_accounts(accounts)


def _render_account_overview(accounts):
    if not accounts:
        empty_state("🏦", "No active accounts", "Add your first prop account in the 'Add Account' tab")
        return
    
    # Summary row
    total_balance = sum(float(a.get("current_balance", a.get("starting_balance", 0))) for a in accounts)
    active_challenges = sum(1 for a in accounts if "Challenge" in str(a.get("account_type", "")))
    funded = sum(1 for a in accounts if "Funded" in str(a.get("account_type", "")) or "Live" in str(a.get("account_type", "")))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Total Managed", f"${total_balance:,.0f}", "", "blue", "💼")
    with col2:
        metric_card("Active Challenges", str(active_challenges), "", "yellow", "⚡")
    with col3:
        metric_card("Funded Accounts", str(funded), "", "green", "🏆")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Per-account cards
    for account in accounts:
        _render_account_card(account)


def _render_account_card(account: dict):
    all_trades = db_select("trades", filters={"prop_account_id": account["id"]})
    status_data = compute_prop_account_status(account, all_trades)
    
    account_type = account.get("account_type", "")
    type_color = {
        "Challenge Phase 1": "#ffcc00",
        "Challenge Phase 2": "#ff7b39",
        "Funded": "#00d68f",
        "Live": "#4c9eff"
    }.get(account_type, "#8b92a8")
    
    status = account.get("status", "Active")
    status_icon = {"Active": "🟢", "Passed": "🏆", "Breached": "🔴", "Withdrawn": "⚪"}.get(status, "⚪")
    
    # Warning alerts
    for warning in status_data.get("warnings", []):
        level = warning["level"]
        if level == "danger":
            st.error(f"**{account['firm_name']} - {account['account_name']}:** {warning['msg']}")
        elif level == "warning":
            st.warning(f"**{account['firm_name']} - {account['account_name']}:** {warning['msg']}")
        elif level == "success":
            st.success(f"**{account['firm_name']} - {account['account_name']}:** {warning['msg']}")
    
    with st.container():
        st.markdown(f"""
        <div style="background:var(--bg-card);border:1px solid var(--border);border-left:3px solid {type_color};
             border-radius:var(--radius);padding:20px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <div>
                    <span style="font-size:1.1rem;font-weight:700;">{account['firm_name']}</span>
                    <span style="color:var(--text-muted);margin:0 10px;">·</span>
                    <span style="color:var(--text-secondary);">{account['account_name']}</span>
                </div>
                <div>
                    <span style="background:rgba(255,255,255,0.05);padding:4px 12px;border-radius:100px;
                          font-size:0.75rem;color:{type_color};">{account_type}</span>
                    <span style="margin-left:8px;font-size:0.85rem;">{status_icon} {status}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            metric_card("Starting", f"${float(account.get('starting_balance',0)):,.0f}", "", "blue")
        with col2:
            curr_bal = status_data["current_balance"]
            bal_color = "green" if curr_bal >= float(account.get("starting_balance", 0)) else "red"
            metric_card("Current Balance", f"${curr_bal:,.2f}", "", bal_color)
        with col3:
            profit = status_data["profit_made"]
            p_color = "green" if profit >= 0 else "red"
            metric_card("Profit Made", f"${profit:+,.2f}", f"{status_data['profit_pct']:+.2f}%", p_color)
        with col4:
            metric_card("Today's P&L", f"${status_data['daily_pnl']:+,.2f}", "", 
                       "green" if status_data['daily_pnl'] >= 0 else "red")
        with col5:
            metric_card("Drawdown", f"{status_data['drawdown_from_start']:.1f}%", "", 
                       "green" if status_data['drawdown_from_start'] < 3 else "yellow" if status_data['drawdown_from_start'] < 7 else "red")
        
        st.markdown("")
        
        # Progress bars
        col1, col2 = st.columns(2)
        with col1:
            target = float(account.get("profit_target_pct", 10))
            if target > 0:
                progress_bar(
                    f"📈 Profit Target ({target}%)",
                    abs(status_data["profit_pct"]) if status_data["profit_pct"] > 0 else 0,
                    target,
                    color="#00d68f"
                )
        
        with col2:
            dl = float(account.get("daily_loss_limit_pct", 5))
            if dl > 0:
                dl_used = status_data["daily_loss_used_pct"]
                starting = float(account.get("starting_balance", 0))
                daily_limit_abs = starting * dl / 100
                daily_used_abs = abs(min(status_data["daily_pnl"], 0))
                progress_bar(
                    f"⚠️ Daily Loss Limit (${daily_limit_abs:,.0f})",
                    daily_used_abs,
                    daily_limit_abs,
                    color="#ff4757",
                    warning_at=60,
                    danger_at=80
                )
        
        col1, col2 = st.columns(2)
        with col1:
            max_dd = float(account.get("max_drawdown_pct", 10))
            if max_dd > 0:
                progress_bar(
                    f"📉 Max Drawdown ({max_dd}%)",
                    status_data["drawdown_from_start"],
                    max_dd,
                    color="#ff4757",
                    warning_at=70,
                    danger_at=85
                )
        with col2:
            min_days = account.get("min_trading_days", 0) or 0
            if min_days > 0:
                days_traded = account.get("days_traded", 0) or 0
                progress_bar(
                    f"📅 Min Trading Days ({min_days})",
                    days_traded,
                    min_days,
                    color="#4c9eff"
                )
        
        # Rules notes
        if account.get("rules_notes"):
            with st.expander("📋 Account Rules"):
                st.markdown(account["rules_notes"])
        
        # Action buttons
        col_edit, col_pass, col_breach, col_del, _ = st.columns([1, 1, 1, 1, 3])
        with col_edit:
            if st.button("✏️ Edit", key=f"edit_prop_{account['id']}"):
                st.session_state[f"editing_prop_{account['id']}"] = True
        with col_pass:
            if st.button("🏆 Mark Passed", key=f"pass_{account['id']}"):
                db_update("prop_accounts", account["id"], {"status": "Passed"})
                st.rerun()
        with col_breach:
            if st.button("💥 Breached", key=f"breach_{account['id']}"):
                db_update("prop_accounts", account["id"], {"status": "Breached", "is_active": False})
                st.rerun()
        with col_del:
            if st.button("🗑️ Delete", key=f"del_prop_{account['id']}"):
                db_delete("prop_accounts", account["id"])
                st.rerun()


def _render_add_account_form():
    with st.form("add_prop_form", clear_on_submit=True):
        st.markdown("#### Firm & Account Details")
        col1, col2 = st.columns(2)
        with col1:
            firm_preset = st.selectbox("Firm Preset", list(FIRM_PRESETS.keys()))
        with col2:
            firm_name = st.text_input("Firm Name", value=firm_preset if firm_preset != "Custom" else "")
        
        preset = FIRM_PRESETS.get(firm_preset, FIRM_PRESETS["Custom"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            account_name = st.text_input("Account Name / ID", placeholder="Account #12345")
        with col2:
            account_type = st.selectbox("Account Type", ["Challenge Phase 1", "Challenge Phase 2", "Funded", "Live"])
        with col3:
            start_date = st.date_input("Start Date", value=date.today())
        
        st.markdown("#### Balance & Targets")
        col1, col2 = st.columns(2)
        with col1:
            starting_balance = st.number_input("Starting Balance ($)", min_value=100.0, value=10000.0, step=1000.0)
        with col2:
            current_balance = st.number_input("Current Balance ($)", min_value=0.0, value=10000.0, step=100.0)
        
        st.markdown("#### Risk Parameters")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            profit_target = st.number_input("Profit Target (%)", min_value=0.0, value=float(preset["profit_target_pct"]), step=0.5)
        with col2:
            daily_loss = st.number_input("Daily Loss Limit (%)", min_value=0.0, value=float(preset["daily_loss_limit_pct"]), step=0.5)
        with col3:
            max_dd = st.number_input("Max Drawdown (%)", min_value=0.0, value=float(preset["max_drawdown_pct"]), step=0.5)
        with col4:
            min_days = st.number_input("Min Trading Days", min_value=0, value=int(preset["min_trading_days"]))
        
        col1, col2 = st.columns(2)
        with col1:
            max_days = st.number_input("Max Trading Days (0=unlimited)", min_value=0, value=30)
        with col2:
            trailing_dd = st.number_input("Max Trailing Drawdown (%)", min_value=0.0, value=0.0, step=0.5)
        
        rules_notes = st.text_area("Additional Rules / Notes", 
                                    placeholder="No news trading, max 5 lots, weekend holding allowed...",
                                    height=80)
        
        submitted = st.form_submit_button("💾 Save Account", type="primary", use_container_width=True)
        
        if submitted:
            if not firm_name or not account_name:
                st.error("❌ Firm name and account name are required!")
                return
            
            result = db_insert("prop_accounts", {
                "firm_name": firm_name,
                "account_name": account_name,
                "account_type": account_type,
                "starting_balance": starting_balance,
                "current_balance": current_balance,
                "profit_target_pct": profit_target,
                "daily_loss_limit_pct": daily_loss,
                "max_drawdown_pct": max_dd,
                "max_trailing_drawdown_pct": trailing_dd,
                "min_trading_days": min_days,
                "max_trading_days": max_days if max_days > 0 else None,
                "start_date": str(start_date),
                "rules_notes": rules_notes,
                "status": "Active",
                "is_active": True,
                "days_traded": 0
            })
            
            if result:
                st.success(f"✅ Account '{firm_name} - {account_name}' added!")
            else:
                st.error("❌ Failed to save account")


def _render_all_accounts(accounts):
    if not accounts:
        empty_state("🏦", "No accounts yet", "")
        return
    
    for acc in accounts:
        status = acc.get("status", "Active")
        status_color = {"Active": "#00d68f", "Passed": "#4c9eff", "Breached": "#ff4757", "Withdrawn": "#8b92a8"}.get(status, "#8b92a8")
        
        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1, 1])
        col1.markdown(f"**{acc['firm_name']}** · {acc['account_name']}")
        col2.markdown(f"{acc.get('account_type','')}")
        col3.markdown(f"${float(acc.get('starting_balance',0)):,.0f}")
        col4.markdown(f"<span style='color:{status_color};'>● {status}</span>", unsafe_allow_html=True)
        col5.markdown(f"{str(acc.get('start_date',''))[:10]}")
