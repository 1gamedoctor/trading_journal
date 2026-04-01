"""
Analytics Page - Deep performance analysis
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.database import db_select
from utils.analytics import (
    trades_to_df, compute_overview, compute_by_session,
    compute_by_asset, compute_hour_heatmap, compute_day_of_week,
    compute_monthly_stats, detect_behavioral_patterns
)
from components.ui import (
    page_header, metric_card, insight_card, empty_state,
    apply_chart_theme, equity_curve_chart, session_bar_chart
)


def render():
    page_header("🔬", "Analytics", "Deep dive into your performance data")
    
    all_trades = db_select("trades", order_by="trade_date", order_desc=False)
    closed = [t for t in all_trades if t.get("status") == "CLOSED"]
    
    if not closed:
        empty_state("🔬", "No closed trades to analyze", "Add and close some trades to see deep analytics")
        return
    
    # Merge strategy names
    strategies = db_select("strategies")
    strat_map = {s["id"]: s["name"] for s in strategies}
    for t in closed:
        sid = t.get("strategy_id")
        t["strategy_name"] = strat_map.get(sid, "Untagged") if sid else "Untagged"
    
    df = trades_to_df(closed)
    if df.empty:
        empty_state("🔬", "Error processing trades", "")
        return
    
    # Add strategy name column to df
    strat_name_map = {t["id"]: t["strategy_name"] for t in closed}
    if "id" in df.columns:
        df["strategy_name"] = df["id"].map(strat_name_map)
    
    tabs = st.tabs(["📊 Overview", "📅 Time Analysis", "🗂️ Segmentation", "🎲 Distribution", "💡 Insights", "📋 Reports"])
    
    with tabs[0]:
        _render_overview(df)
    with tabs[1]:
        _render_time_analysis(df)
    with tabs[2]:
        _render_segmentation(df)
    with tabs[3]:
        _render_distribution(df)
    with tabs[4]:
        _render_insights(df)
    with tabs[5]:
        _render_reports(df, closed)


def _render_overview(df):
    overview = compute_overview(df)
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    metrics = [
        ("Win Rate", f"{overview['win_rate']:.1f}%", "blue"),
        ("Profit Factor", f"{overview['profit_factor']:.2f}", "green" if overview['profit_factor'] >= 1.5 else "red"),
        ("Avg R", f"{overview['avg_r']:+.2f}R", "green" if overview['avg_r'] > 0 else "red"),
        ("Sharpe", f"{overview['sharpe']:.2f}", "green" if overview['sharpe'] > 1 else "yellow"),
        ("Max DD", f"{overview['max_drawdown']:.1f}%", "green" if overview['max_drawdown'] < 5 else "red"),
        ("Avg Win", f"${overview['avg_win']:.2f}", "green"),
        ("Avg Loss", f"${overview['avg_loss']:.2f}", "red"),
    ]
    for col, (label, val, color) in zip([col1,col2,col3,col4,col5,col6,col7], metrics):
        with col:
            metric_card(label, val, "", color)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Equity curve
    fig = equity_curve_chart(df)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    # Streak analysis
    st.markdown("#### 🔥 Streak Analysis")
    _render_streak_analysis(df)


def _render_streak_analysis(df):
    if df.empty:
        return
    
    sorted_df = df.sort_values("trade_date")
    outcomes = sorted_df["is_win"].tolist()
    
    # Compute all streaks
    win_streaks, loss_streaks = [], []
    current_streak = 1
    current_type = outcomes[0] if outcomes else True
    
    for i in range(1, len(outcomes)):
        if outcomes[i] == current_type:
            current_streak += 1
        else:
            if current_type:
                win_streaks.append(current_streak)
            else:
                loss_streaks.append(current_streak)
            current_streak = 1
            current_type = outcomes[i]
    
    if current_streak > 0:
        if current_type:
            win_streaks.append(current_streak)
        else:
            loss_streaks.append(current_streak)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Max Win Streak", str(max(win_streaks) if win_streaks else 0), "", "green", "🔥")
    with col2:
        metric_card("Max Loss Streak", str(max(loss_streaks) if loss_streaks else 0), "", "red", "💔")
    with col3:
        metric_card("Avg Win Streak", f"{sum(win_streaks)/len(win_streaks):.1f}" if win_streaks else "0", "", "green")
    with col4:
        metric_card("Avg Loss Streak", f"{sum(loss_streaks)/len(loss_streaks):.1f}" if loss_streaks else "0", "", "red")


def _render_time_analysis(df):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📅 Day of Week Performance")
        dow = compute_day_of_week(df)
        if not dow.empty:
            colors = ["#00d68f" if v >= 0 else "#ff4757" for v in dow["total_pnl"]]
            fig = go.Figure(go.Bar(
                x=dow["dow"], y=dow["total_pnl"],
                marker_color=colors,
                text=[f"${v:,.0f}" for v in dow["total_pnl"]],
                textposition="outside"
            ))
            fig.update_layout(title="P&L by Day of Week")
            apply_chart_theme(fig, 280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    with col2:
        st.markdown("#### 🕐 Hour of Day Performance")
        hourly = compute_hour_heatmap(df)
        if not hourly.empty:
            colors = ["#00d68f" if v >= 0 else "#ff4757" for v in hourly["total_pnl"]]
            fig = go.Figure(go.Bar(
                x=hourly["hour"], y=hourly["total_pnl"],
                marker_color=colors
            ))
            fig.update_layout(title="P&L by Hour", xaxis_title="Hour (UTC)")
            apply_chart_theme(fig, 280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            empty_state("🕐", "No time data", "Add trade times to see hourly patterns")
    
    # Monthly performance
    st.markdown("#### 📆 Monthly Performance")
    monthly = compute_monthly_stats(df)
    if not monthly.empty:
        monthly["month_str"] = monthly["month"].astype(str)
        colors = ["#00d68f" if v >= 0 else "#ff4757" for v in monthly["total_pnl"]]
        fig = go.Figure(go.Bar(
            x=monthly["month_str"], y=monthly["total_pnl"],
            marker_color=colors,
            text=[f"${v:,.0f}" for v in monthly["total_pnl"]],
            textposition="outside"
        ))
        fig.update_layout(title="Monthly P&L")
        apply_chart_theme(fig, 280)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    # Session analysis
    st.markdown("#### 🌍 Session Analysis")
    fig = session_bar_chart(df)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_segmentation(df):
    if df.empty:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Performance by Asset")
        from components.ui import asset_bar_chart
        fig = asset_bar_chart(df)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    with col2:
        st.markdown("#### 🧩 Performance by Strategy")
        if "strategy_name" in df.columns:
            strat_perf = df.groupby("strategy_name").agg(
                trades=("id", "count"),
                total_pnl=("net_pnl", "sum"),
                win_rate=("is_win", lambda x: x.mean() * 100)
            ).reset_index()
            
            colors = ["#00d68f" if v >= 0 else "#ff4757" for v in strat_perf["total_pnl"]]
            fig = go.Figure(go.Bar(
                x=strat_perf["strategy_name"], y=strat_perf["total_pnl"],
                marker_color=colors,
                text=[f"WR:{v:.0f}%" for v in strat_perf["win_rate"]],
                textposition="outside"
            ))
            apply_chart_theme(fig, 280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    # Buy vs Sell
    st.markdown("#### ⬆️⬇️ Buy vs Sell Analysis")
    if "direction" in df.columns:
        dir_perf = df.groupby("direction").agg(
            trades=("id", "count"),
            total_pnl=("net_pnl", "sum"),
            win_rate=("is_win", lambda x: x.mean() * 100),
            avg_r=("r_multiple", "mean")
        ).reset_index()
        
        col1, col2, col3, col4 = st.columns(4)
        for i, row in dir_perf.iterrows():
            color = "green" if row["total_pnl"] >= 0 else "red"
            with [col1, col2, col3, col4][i*2]:
                metric_card(f"{row['direction']} Trades", str(int(row['trades'])), "", "blue")
            with [col1, col2, col3, col4][i*2+1]:
                metric_card(f"{row['direction']} Win Rate", f"{row['win_rate']:.0f}%", f"${row['total_pnl']:+,.0f}", color)


def _render_distribution(df):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📐 R-Multiple Distribution")
        from components.ui import r_multiple_histogram
        fig = r_multiple_histogram(df)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    with col2:
        st.markdown("#### 💰 P&L Distribution")
        if "net_pnl" in df.columns:
            fig = go.Figure(go.Histogram(
                x=df["net_pnl"], nbinsx=25,
                marker_color="#4c9eff", opacity=0.8
            ))
            pnl_mean = df["net_pnl"].mean()
            fig.add_vline(x=0, line_dash="dash", line_color="#ff4757", line_width=1)
            fig.add_vline(x=pnl_mean, line_dash="dash", line_color="#00d68f", line_width=1,
                         annotation_text=f"Mean: ${pnl_mean:.2f}")
            fig.update_layout(title="P&L Distribution")
            apply_chart_theme(fig, 280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    # Confidence level analysis
    if "confidence_level" in df.columns:
        df["confidence_level"] = pd.to_numeric(df["confidence_level"], errors="coerce")
        conf_df = df.dropna(subset=["confidence_level"])
        if not conf_df.empty:
            st.markdown("#### 🎯 Win Rate by Confidence Level")
            conf_perf = conf_df.groupby("confidence_level").agg(
                trades=("id", "count"),
                win_rate=("is_win", lambda x: x.mean() * 100),
                avg_pnl=("net_pnl", "mean")
            ).reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=conf_perf["confidence_level"], y=conf_perf["win_rate"],
                marker_color="#4c9eff", name="Win Rate %",
                opacity=0.8
            ))
            fig.add_trace(go.Scatter(
                x=conf_perf["confidence_level"], y=conf_perf["avg_pnl"],
                line=dict(color="#00d68f", width=2),
                name="Avg P&L", yaxis="y2"
            ))
            fig.update_layout(
                title="Win Rate & Avg P&L by Confidence Level",
                xaxis_title="Confidence (1-10)",
                yaxis=dict(title="Win Rate %"),
                yaxis2=dict(overlaying="y", side="right", title="Avg P&L $"),
                hovermode="x unified"
            )
            apply_chart_theme(fig, 280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_insights(df):
    insights = detect_behavioral_patterns(df)
    
    if not insights:
        st.info("💡 Keep trading! Deeper insights appear with more trade history (need 5+ trades).")
        return
    
    col1, col2 = st.columns(2)
    for i, ins in enumerate(insights):
        with col1 if i % 2 == 0 else col2:
            insight_card(ins)
    
    # Behavioral tags analysis
    st.markdown("---")
    st.markdown("#### 🏷️ Common Tags")
    all_trades = db_select("trades")
    all_tags = []
    for t in all_trades:
        all_tags.extend(t.get("tags", []) or [])
    
    if all_tags:
        from collections import Counter
        tag_counts = Counter(all_tags).most_common(20)
        
        tags_html = " ".join([
            f'<span style="background:rgba(76,158,255,0.15);color:#4c9eff;padding:4px 12px;'
            f'border-radius:100px;font-size:0.8rem;margin:3px;display:inline-block;">'
            f'{tag} ({count})</span>'
            for tag, count in tag_counts
        ])
        st.markdown(f"<div style='line-height:2.2;'>{tags_html}</div>", unsafe_allow_html=True)


def _render_reports(df, raw_trades):
    st.markdown("#### 📋 Performance Summary Report")
    
    overview = compute_overview(df)
    
    report_lines = [
        f"# Trading Performance Report",
        f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## Key Metrics",
        f"- Total Trades: {overview['total_trades']}",
        f"- Win Rate: {overview['win_rate']:.1f}%",
        f"- Net P&L: ${overview['net_pnl']:+,.2f}",
        f"- Profit Factor: {overview['profit_factor']:.2f}",
        f"- Average R-Multiple: {overview['avg_r']:+.2f}R",
        f"- Max Drawdown: {overview['max_drawdown']:.1f}%",
        f"- Sharpe Ratio: {overview['sharpe']:.2f}",
        f"",
        f"## Win/Loss Analysis",
        f"- Total Wins: {overview['total_trades_wins']}",
        f"- Total Losses: {overview['total_trades_losses']}",
        f"- Average Win: ${overview['avg_win']:+.2f}",
        f"- Average Loss: ${overview['avg_loss']:+.2f}",
        f"- Best Trade: ${overview['best_trade']:+.2f}",
        f"- Worst Trade: ${overview['worst_trade']:+.2f}",
        f"- Total Fees Paid: ${overview['total_fees']:,.2f}",
    ]
    
    # Session breakdown
    session_data = compute_by_session(df)
    if not session_data.empty:
        report_lines.append(f"\n## Session Breakdown")
        for _, row in session_data.iterrows():
            report_lines.append(f"- {row['session']}: {row['trades']} trades | WR: {row['win_rate']:.0f}% | P&L: ${row['total_pnl']:+,.2f}")
    
    report_text = "\n".join(report_lines)
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_area("Report Preview", report_text, height=400)
    with col2:
        st.download_button(
            "⬇️ Download Report (TXT)",
            data=report_text,
            file_name=f"trading_report_{pd.Timestamp.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        # CSV export
        if not df.empty:
            csv = df.to_csv(index=False)
            st.download_button(
                "⬇️ Export Trades (CSV)",
                data=csv,
                file_name=f"trades_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
