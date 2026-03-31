"""
UI Components - Reusable styled components for the journal
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
import pandas as pd


# ─── THEME & CSS ────────────────────────────────────────────────────────────

def inject_css():
    """Inject global CSS styles."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Root Variables ── */
    :root {
        --bg-primary: #0d0f14;
        --bg-secondary: #131620;
        --bg-card: #181c27;
        --bg-card-hover: #1e2336;
        --border: #252a3a;
        --border-light: #2e3550;
        --text-primary: #e8ecf0;
        --text-secondary: #8b92a8;
        --text-muted: #555e7a;
        --accent-green: #00d68f;
        --accent-red: #ff4757;
        --accent-blue: #4c9eff;
        --accent-yellow: #ffcc00;
        --accent-purple: #9b59ff;
        --accent-orange: #ff7b39;
        --font-main: 'Space Grotesk', sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
        --radius: 12px;
        --shadow: 0 4px 24px rgba(0,0,0,0.4);
    }

    /* ── Global Reset ── */
    html, body, [class*="css"] {
        font-family: var(--font-main) !important;
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    .stApp { background-color: var(--bg-primary) !important; }
    .main .block-container { padding: 1.5rem 2rem; max-width: 1400px; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: var(--text-secondary) !important;
        font-size: 0.9rem !important;
        padding: 6px 0 !important;
    }

    /* ── Headers ── */
    h1, h2, h3, h4, h5 {
        font-family: var(--font-main) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }

    /* ── Cards ── */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 20px 24px;
        position: relative;
        overflow: hidden;
        transition: all 0.2s ease;
    }
    .metric-card:hover { 
        border-color: var(--border-light);
        background: var(--bg-card-hover);
        transform: translateY(-2px);
        box-shadow: var(--shadow);
    }
    .metric-card .label {
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    .metric-card .value {
        font-size: 1.8rem;
        font-weight: 700;
        font-family: var(--font-mono);
        color: var(--text-primary);
        line-height: 1;
    }
    .metric-card .delta {
        font-size: 0.8rem;
        font-family: var(--font-mono);
        margin-top: 6px;
        font-weight: 500;
    }
    .metric-card .accent-bar {
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 3px;
        border-radius: var(--radius) var(--radius) 0 0;
    }
    .value-green { color: var(--accent-green) !important; }
    .value-red { color: var(--accent-red) !important; }
    .value-blue { color: var(--accent-blue) !important; }
    .value-yellow { color: var(--accent-yellow) !important; }
    .value-purple { color: var(--accent-purple) !important; }

    /* ── Insight Cards ── */
    .insight-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 16px 20px;
        margin-bottom: 10px;
        display: flex;
        align-items: flex-start;
        gap: 14px;
    }
    .insight-card.positive { border-left: 3px solid var(--accent-green); }
    .insight-card.warning { border-left: 3px solid var(--accent-yellow); }
    .insight-card.danger { border-left: 3px solid var(--accent-red); }
    .insight-card.info { border-left: 3px solid var(--accent-blue); }
    .insight-icon { font-size: 1.5rem; margin-top: 2px; }
    .insight-title { font-weight: 600; font-size: 0.95rem; color: var(--text-primary); }
    .insight-msg { font-size: 0.85rem; color: var(--text-secondary); margin-top: 3px; }

    /* ── Badges ── */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 100px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-green { background: rgba(0,214,143,0.15); color: var(--accent-green); }
    .badge-red { background: rgba(255,71,87,0.15); color: var(--accent-red); }
    .badge-blue { background: rgba(76,158,255,0.15); color: var(--accent-blue); }
    .badge-yellow { background: rgba(255,204,0,0.15); color: var(--accent-yellow); }
    .badge-purple { background: rgba(155,89,255,0.15); color: var(--accent-purple); }
    .badge-gray { background: rgba(139,146,168,0.15); color: var(--text-secondary); }

    /* ── Progress Bars ── */
    .progress-container {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 20px;
        margin-bottom: 12px;
    }
    .progress-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 0.85rem;
    }
    .progress-bar-bg {
        background: rgba(255,255,255,0.07);
        border-radius: 100px;
        height: 8px;
        overflow: hidden;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 100px;
        transition: width 0.5s ease;
    }

    /* ── Page Header ── */
    .page-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 28px;
        padding-bottom: 20px;
        border-bottom: 1px solid var(--border);
    }
    .page-header-icon {
        width: 44px; height: 44px;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    .page-header-title {
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .page-header-sub {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin: 0;
    }

    /* ── Trade Table ── */
    .trade-row {
        display: grid;
        grid-template-columns: 80px 60px 80px 80px 80px 80px 80px 100px;
        gap: 8px;
        padding: 12px 16px;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px;
        margin-bottom: 6px;
        font-family: var(--font-mono);
        font-size: 0.82rem;
        align-items: center;
        transition: background 0.15s;
    }
    .trade-row:hover { background: var(--bg-card-hover); }

    /* ── Inputs ── */
    .stTextInput input, .stNumberInput input, .stSelectbox select,
    .stTextArea textarea, .stDateInput input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        font-family: var(--font-main) !important;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 2px rgba(76,158,255,0.15) !important;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        font-family: var(--font-main) !important;
        font-weight: 500 !important;
        transition: all 0.15s !important;
    }
    .stButton > button:hover {
        border-color: var(--accent-blue) !important;
        color: var(--accent-blue) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--accent-blue) !important;
        border-color: var(--accent-blue) !important;
        color: #fff !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid var(--border) !important;
        gap: 4px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-muted) !important;
        border: none !important;
        font-family: var(--font-main) !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
        border-radius: 8px 8px 0 0 !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--text-primary) !important;
        background: var(--bg-card) !important;
        border-bottom: 2px solid var(--accent-blue) !important;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }

    /* ── Alerts ── */
    .stAlert { border-radius: 10px !important; border: none !important; }

    /* ── Dividers ── */
    hr { border-color: var(--border) !important; margin: 20px 0 !important; }

    /* ── Status dot ── */
    .status-dot {
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .status-dot.online { background: var(--accent-green); box-shadow: 0 0 6px var(--accent-green); }
    .status-dot.offline { background: var(--text-muted); }

    /* ── Calendar cell ── */
    .cal-cell {
        padding: 8px;
        border-radius: 8px;
        text-align: center;
        font-size: 0.8rem;
        font-family: var(--font-mono);
        min-height: 50px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 1px solid transparent;
        cursor: pointer;
    }
    .cal-cell.profit { background: rgba(0,214,143,0.12); border-color: rgba(0,214,143,0.25); }
    .cal-cell.loss { background: rgba(255,71,87,0.12); border-color: rgba(255,71,87,0.25); }
    .cal-cell.neutral { background: var(--bg-card); border-color: var(--border); }
    .cal-cell.today { border-color: var(--accent-blue) !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--border-light); border-radius: 3px; }

    /* ── Sidebar nav ── */
    .nav-item {
        display: flex; align-items: center; gap: 10px;
        padding: 10px 14px; border-radius: 8px;
        cursor: pointer; margin-bottom: 3px;
        font-size: 0.9rem; font-weight: 500;
        color: var(--text-secondary);
        transition: all 0.15s;
    }
    .nav-item:hover, .nav-item.active {
        background: var(--bg-card);
        color: var(--text-primary);
    }
    .nav-item.active { border-left: 2px solid var(--accent-blue); }

    /* ── Plotly charts ── */
    .js-plotly-plot .plotly, .plot-container {
        background: transparent !important;
    }

    /* ── Empty state ── */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: var(--text-muted);
    }
    .empty-state .icon { font-size: 3rem; margin-bottom: 16px; }
    .empty-state .title { font-size: 1.1rem; font-weight: 600; color: var(--text-secondary); }
    .empty-state .desc { font-size: 0.85rem; margin-top: 8px; }

    </style>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, delta: str = "", color: str = "blue", icon: str = ""):
    """Render a styled metric card."""
    colors = {
        "green": "#00d68f", "red": "#ff4757", "blue": "#4c9eff",
        "yellow": "#ffcc00", "purple": "#9b59ff", "orange": "#ff7b39"
    }
    bar_color = colors.get(color, colors["blue"])
    delta_color = "#00d68f" if delta.startswith("+") else ("#ff4757" if delta.startswith("-") else "#8b92a8")
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="accent-bar" style="background: linear-gradient(90deg, {bar_color}, transparent);"></div>
        <div class="label">{icon} {label}</div>
        <div class="value" style="color: {bar_color};">{value}</div>
        {f'<div class="delta" style="color: {delta_color};">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)


def insight_card(insight: Dict):
    """Render an insight card."""
    st.markdown(f"""
    <div class="insight-card {insight.get('type', 'info')}">
        <div class="insight-icon">{insight.get('icon', '💡')}</div>
        <div>
            <div class="insight-title">{insight.get('title', '')}</div>
            <div class="insight-msg">{insight.get('message', '')}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = ""):
    """Render a page header."""
    st.markdown(f"""
    <div class="page-header">
        <div class="page-header-icon">{icon}</div>
        <div>
            <div class="page-header-title">{title}</div>
            {f'<div class="page-header-sub">{subtitle}</div>' if subtitle else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)


def badge(text: str, color: str = "blue") -> str:
    """Return a badge HTML string."""
    return f'<span class="badge badge-{color}">{text}</span>'


def progress_bar(label: str, value: float, max_value: float = 100, 
                 color: str = "#4c9eff", warning_at: float = 80, danger_at: float = 95):
    """Render a progress bar."""
    pct = min((value / max_value * 100) if max_value > 0 else 0, 100)
    bar_color = color
    if pct >= danger_at:
        bar_color = "#ff4757"
    elif pct >= warning_at:
        bar_color = "#ffcc00"
    
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-label">
            <span>{label}</span>
            <span style="font-family: var(--font-mono); color: {'#ff4757' if pct >= danger_at else '#ffcc00' if pct >= warning_at else '#e8ecf0'};">{pct:.1f}%</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: {pct}%; background: {bar_color};"></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 0.75rem; color: #555e7a;">
            <span>{value:,.2f}</span>
            <span>/ {max_value:,.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def empty_state(icon: str, title: str, desc: str = ""):
    """Render an empty state component."""
    st.markdown(f"""
    <div class="empty-state">
        <div class="icon">{icon}</div>
        <div class="title">{title}</div>
        {f'<div class="desc">{desc}</div>' if desc else ''}
    </div>
    """, unsafe_allow_html=True)


def sync_status_badge(status: Dict):
    """Render sync status in sidebar."""
    connected = status.get("connected", False)
    pending = status.get("pending_sync", 0)
    storage = status.get("storage", "Local")
    
    dot_class = "online" if connected else "offline"
    color = "#00d68f" if connected else "#8b92a8"
    
    pending_html = f' <span style="color:#ffcc00;font-size:0.7rem;">({pending} pending sync)</span>' if pending > 0 else ""
    
    st.markdown(f"""
    <div style="padding: 8px 14px; background: var(--bg-card); border: 1px solid var(--border); 
         border-radius: 8px; font-size: 0.8rem; color: var(--text-secondary);">
        <span class="status-dot {dot_class}"></span>
        <span style="color: {color};">{storage}</span>{pending_html}
    </div>
    """, unsafe_allow_html=True)


# ─── CHART HELPERS ──────────────────────────────────────────────────────────

CHART_THEME = {
    "bg": "rgba(0,0,0,0)",
    "paper_bg": "rgba(0,0,0,0)",
    "grid": "rgba(255,255,255,0.05)",
    "text": "#8b92a8",
    "font": "Space Grotesk",
}


def apply_chart_theme(fig: go.Figure, height: int = 350) -> go.Figure:
    """Apply dark theme to a Plotly figure."""
    fig.update_layout(
        paper_bgcolor=CHART_THEME["paper_bg"],
        plot_bgcolor=CHART_THEME["bg"],
        font=dict(color=CHART_THEME["text"], family=CHART_THEME["font"], size=12),
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(
            bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.1)",
            borderwidth=1, font=dict(size=11)
        ),
    )
    fig.update_xaxes(
        gridcolor=CHART_THEME["grid"], zeroline=False,
        showline=False, tickfont=dict(size=10)
    )
    fig.update_yaxes(
        gridcolor=CHART_THEME["grid"], zeroline=False,
        showline=False, tickfont=dict(size=10)
    )
    return fig


def equity_curve_chart(df: pd.DataFrame, starting_balance: float = 10000) -> go.Figure:
    """Create equity curve chart."""
    from utils.analytics import compute_equity_curve
    ec = compute_equity_curve(df, starting_balance)
    
    if ec.empty:
        fig = go.Figure()
        return apply_chart_theme(fig)
    
    fig = go.Figure()
    
    # Shade area
    fig.add_trace(go.Scatter(
        x=ec["trade_date"], y=ec["equity"],
        fill="tozeroy", fillcolor="rgba(76,158,255,0.06)",
        line=dict(color="#4c9eff", width=2),
        name="Equity", mode="lines",
        hovertemplate="<b>%{x}</b><br>Equity: $%{y:,.2f}<extra></extra>"
    ))
    
    # Mark drawdown periods
    fig.add_trace(go.Scatter(
        x=ec["trade_date"], y=ec["drawdown_pct"],
        line=dict(color="#ff4757", width=1, dash="dot"),
        name="Drawdown %", yaxis="y2",
        hovertemplate="DD: %{y:.1f}%<extra></extra>"
    ))
    
    fig.update_layout(
        yaxis2=dict(
            overlaying="y", side="right",
            showgrid=False, tickformat=".1f", ticksuffix="%",
            tickfont=dict(size=9, color="#ff4757")
        ),
        title=dict(text="Equity Curve", font=dict(size=14, color="#e8ecf0")),
        hovermode="x unified"
    )
    return apply_chart_theme(fig, height=320)


def pnl_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Daily PnL bar chart."""
    from utils.analytics import compute_daily_stats
    daily = compute_daily_stats(df)
    
    if daily.empty:
        return apply_chart_theme(go.Figure())
    
    colors = ["#00d68f" if v >= 0 else "#ff4757" for v in daily["total_pnl"]]
    
    fig = go.Figure(go.Bar(
        x=daily["trade_date"], y=daily["total_pnl"],
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>PnL: $%{y:,.2f}<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text="Daily PnL", font=dict(size=14, color="#e8ecf0")),
        bargap=0.3
    )
    return apply_chart_theme(fig, height=240)


def win_rate_donut(win_rate: float) -> go.Figure:
    """Win rate donut chart."""
    fig = go.Figure(go.Pie(
        values=[win_rate, 100 - win_rate],
        labels=["Win", "Loss"],
        hole=0.72,
        marker_colors=["#00d68f", "#ff4757"],
        textinfo="none",
        hoverinfo="label+percent"
    ))
    fig.add_annotation(
        text=f"{win_rate:.0f}%", x=0.5, y=0.5,
        font=dict(size=24, color="#e8ecf0", family="JetBrains Mono"),
        showarrow=False
    )
    fig.update_layout(showlegend=False)
    return apply_chart_theme(fig, height=200)


def session_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Session performance bar chart."""
    from utils.analytics import compute_by_session
    data = compute_by_session(df)
    if data.empty:
        return apply_chart_theme(go.Figure())
    
    colors = ["#00d68f" if v >= 0 else "#ff4757" for v in data["total_pnl"]]
    fig = go.Figure(go.Bar(
        x=data["session"], y=data["total_pnl"],
        marker_color=colors,
        text=[f"${v:,.0f}" for v in data["total_pnl"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>PnL: $%{y:,.2f}<br>Win Rate: " + 
                      data["win_rate"].astype(str) + "%<extra></extra>"
    ))
    fig.update_layout(title=dict(text="PnL by Session", font=dict(size=14, color="#e8ecf0")))
    return apply_chart_theme(fig, height=260)


def asset_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Asset performance chart."""
    from utils.analytics import compute_by_asset
    data = compute_by_asset(df).sort_values("total_pnl", ascending=True)
    if data.empty:
        return apply_chart_theme(go.Figure())
    
    colors = ["#00d68f" if v >= 0 else "#ff4757" for v in data["total_pnl"]]
    fig = go.Figure(go.Bar(
        x=data["total_pnl"], y=data["asset"],
        orientation="h", marker_color=colors,
        hovertemplate="<b>%{y}</b><br>PnL: $%{x:,.2f}<extra></extra>"
    ))
    fig.update_layout(title=dict(text="PnL by Asset", font=dict(size=14, color="#e8ecf0")))
    return apply_chart_theme(fig, height=260)


def r_multiple_histogram(df: pd.DataFrame) -> go.Figure:
    """R-multiple distribution histogram."""
    if df.empty or "r_multiple" not in df.columns:
        return apply_chart_theme(go.Figure())
    
    r_vals = df["r_multiple"].dropna()
    fig = go.Figure(go.Histogram(
        x=r_vals, nbinsx=20,
        marker_color="#4c9eff", opacity=0.8,
        hovertemplate="R: %{x:.1f}<br>Count: %{y}<extra></extra>"
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="#ff4757", line_width=1)
    fig.add_vline(x=r_vals.mean(), line_dash="dash", line_color="#00d68f", line_width=1,
                  annotation_text=f"Avg: {r_vals.mean():.2f}R", annotation_position="top right")
    fig.update_layout(title=dict(text="R-Multiple Distribution", font=dict(size=14, color="#e8ecf0")))
    return apply_chart_theme(fig, height=260)


def monthly_heatmap(df: pd.DataFrame) -> go.Figure:
    """Monthly PnL heatmap."""
    if df.empty:
        return apply_chart_theme(go.Figure())
    
    df = df.copy()
    df["month"] = df["trade_date"].dt.strftime("%b %Y")
    df["day"] = df["trade_date"].dt.day
    pivot = df.groupby(["month", "day"])["net_pnl"].sum().unstack(fill_value=0)
    
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(d) for d in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[[0, "#ff4757"], [0.5, "#131620"], [1, "#00d68f"]],
        zmid=0,
        hovertemplate="Day %{x}<br>%{y}<br>PnL: $%{z:,.2f}<extra></extra>"
    ))
    fig.update_layout(title=dict(text="Monthly Performance Heatmap", font=dict(size=14, color="#e8ecf0")))
    return apply_chart_theme(fig, height=300)
