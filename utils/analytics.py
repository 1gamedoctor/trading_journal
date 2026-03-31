"""
Analytics Engine - Computes all trade performance metrics
"""
import math
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def trades_to_df(trades: List[Dict]) -> pd.DataFrame:
    """Convert trade list to DataFrame with computed columns."""
    if not trades:
        return pd.DataFrame()
    
    df = pd.DataFrame(trades)
    
    # Filter only closed trades for PnL analysis
    if "status" in df.columns:
        df = df[df["status"] == "CLOSED"].copy()
    
    if df.empty:
        return df

    # Parse dates
    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"])
    
    # Ensure numeric columns
    for col in ["pnl", "entry_price", "exit_price", "lot_size", "stop_loss", "take_profit", "fees", "r_multiple"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Compute PnL if missing
    if "pnl" not in df.columns or df["pnl"].isna().all():
        df["pnl"] = df.apply(_compute_pnl, axis=1)
    
    # Net PnL after fees
    df["net_pnl"] = df["pnl"] - df.get("fees", 0).fillna(0)
    df["is_win"] = df["net_pnl"] > 0
    
    # R-multiple if stop loss is set
    if "r_multiple" not in df.columns or df["r_multiple"].isna().all():
        df["r_multiple"] = df.apply(_compute_r_multiple, axis=1)
    
    return df.sort_values("trade_date")


def _compute_pnl(row) -> float:
    """Compute PnL from entry/exit prices."""
    try:
        if pd.isna(row.get("exit_price")) or pd.isna(row.get("entry_price")):
            return 0.0
        diff = row["exit_price"] - row["entry_price"]
        direction_mult = 1 if str(row.get("direction", "BUY")).upper() == "BUY" else -1
        lot = row.get("lot_size", 1) or 1
        return diff * direction_mult * float(lot)
    except Exception:
        return 0.0


def _compute_r_multiple(row) -> float:
    """Compute R-multiple from stop loss."""
    try:
        if pd.isna(row.get("stop_loss")) or pd.isna(row.get("entry_price")):
            return 0.0
        risk = abs(row["entry_price"] - row["stop_loss"])
        if risk == 0:
            return 0.0
        pnl = row.get("net_pnl", row.get("pnl", 0)) or 0
        lot = row.get("lot_size", 1) or 1
        return pnl / (risk * float(lot))
    except Exception:
        return 0.0


def compute_overview(df: pd.DataFrame, starting_balance: float = 10000) -> Dict:
    """Compute high-level performance overview."""
    if df.empty:
        return {
            "total_trades": 0, "win_rate": 0, "total_pnl": 0,
            "profit_factor": 0, "avg_r": 0, "max_drawdown": 0,
            "sharpe": 0, "best_trade": 0, "worst_trade": 0,
            "avg_win": 0, "avg_loss": 0, "current_streak": 0,
            "streak_type": "none", "total_fees": 0, "net_pnl": 0
        }

    wins = df[df["is_win"]]
    losses = df[~df["is_win"]]
    total = len(df)
    win_rate = len(wins) / total * 100 if total > 0 else 0

    gross_profit = wins["net_pnl"].sum() if not wins.empty else 0
    gross_loss = abs(losses["net_pnl"].sum()) if not losses.empty else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    avg_r = df["r_multiple"].mean() if "r_multiple" in df.columns else 0

    # Max drawdown
    equity = starting_balance + df["net_pnl"].cumsum()
    roll_max = equity.cummax()
    drawdown = (equity - roll_max) / roll_max * 100
    max_drawdown = abs(drawdown.min()) if not drawdown.empty else 0

    # Sharpe (simplified, daily)
    daily_pnl = df.groupby("trade_date")["net_pnl"].sum()
    sharpe = (daily_pnl.mean() / daily_pnl.std() * math.sqrt(252)) if daily_pnl.std() > 0 else 0

    # Current streak
    streak, stype = _compute_streak(df)

    total_fees = df["fees"].sum() if "fees" in df.columns else 0

    return {
        "total_trades": total,
        "win_rate": round(win_rate, 1),
        "total_pnl": round(df["net_pnl"].sum(), 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else 999,
        "avg_r": round(avg_r, 2),
        "max_drawdown": round(max_drawdown, 2),
        "sharpe": round(sharpe, 2),
        "best_trade": round(df["net_pnl"].max(), 2),
        "worst_trade": round(df["net_pnl"].min(), 2),
        "avg_win": round(wins["net_pnl"].mean(), 2) if not wins.empty else 0,
        "avg_loss": round(losses["net_pnl"].mean(), 2) if not losses.empty else 0,
        "current_streak": streak,
        "streak_type": stype,
        "total_fees": round(total_fees, 2),
        "net_pnl": round(df["net_pnl"].sum(), 2),
        "total_trades_wins": len(wins),
        "total_trades_losses": len(losses),
    }


def _compute_streak(df: pd.DataFrame) -> Tuple[int, str]:
    """Compute current win/loss streak."""
    if df.empty:
        return 0, "none"
    outcomes = df.sort_values("trade_date")["is_win"].tolist()
    if not outcomes:
        return 0, "none"
    
    last = outcomes[-1]
    streak = 0
    for o in reversed(outcomes):
        if o == last:
            streak += 1
        else:
            break
    return streak, "win" if last else "loss"


def compute_equity_curve(df: pd.DataFrame, starting_balance: float = 10000) -> pd.DataFrame:
    """Compute equity curve over time."""
    if df.empty:
        return pd.DataFrame()
    
    sorted_df = df.sort_values("trade_date").copy()
    sorted_df["cumulative_pnl"] = sorted_df["net_pnl"].cumsum()
    sorted_df["equity"] = starting_balance + sorted_df["cumulative_pnl"]
    sorted_df["drawdown_pct"] = (
        (sorted_df["equity"] - sorted_df["equity"].cummax()) / sorted_df["equity"].cummax() * 100
    )
    return sorted_df[["trade_date", "equity", "cumulative_pnl", "drawdown_pct", "net_pnl"]]


def compute_daily_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate PnL by day."""
    if df.empty:
        return pd.DataFrame()
    
    daily = df.groupby("trade_date").agg(
        total_pnl=("net_pnl", "sum"),
        trades=("id", "count"),
        wins=("is_win", "sum")
    ).reset_index()
    daily["win_rate"] = daily["wins"] / daily["trades"] * 100
    return daily


def compute_by_session(df: pd.DataFrame) -> pd.DataFrame:
    """PnL breakdown by session."""
    if df.empty or "session" not in df.columns:
        return pd.DataFrame()
    return df.groupby("session").agg(
        trades=("id", "count"),
        total_pnl=("net_pnl", "sum"),
        win_rate=("is_win", lambda x: x.mean() * 100),
        avg_r=("r_multiple", "mean")
    ).reset_index().round(2)


def compute_by_asset(df: pd.DataFrame) -> pd.DataFrame:
    """PnL breakdown by asset."""
    if df.empty:
        return pd.DataFrame()
    return df.groupby("asset").agg(
        trades=("id", "count"),
        total_pnl=("net_pnl", "sum"),
        win_rate=("is_win", lambda x: x.mean() * 100),
        avg_r=("r_multiple", "mean")
    ).reset_index().round(2)


def compute_by_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """PnL breakdown by strategy."""
    if df.empty or "strategy_name" not in df.columns:
        return pd.DataFrame()
    return df.groupby("strategy_name").agg(
        trades=("id", "count"),
        total_pnl=("net_pnl", "sum"),
        win_rate=("is_win", lambda x: x.mean() * 100),
        avg_r=("r_multiple", "mean")
    ).reset_index().round(2)


def compute_hour_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """Trades PnL by hour of day."""
    if df.empty or "trade_time" not in df.columns:
        return pd.DataFrame()
    try:
        df = df.copy()
        df["hour"] = pd.to_datetime(df["trade_time"], format="%H:%M:%S", errors="coerce").dt.hour
        return df.groupby("hour").agg(
            total_pnl=("net_pnl", "sum"),
            trades=("id", "count"),
            win_rate=("is_win", lambda x: x.mean() * 100)
        ).reset_index()
    except Exception:
        return pd.DataFrame()


def compute_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """PnL by day of week."""
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    df["dow"] = df["trade_date"].dt.day_name()
    df["dow_num"] = df["trade_date"].dt.dayofweek
    return df.groupby(["dow_num", "dow"]).agg(
        total_pnl=("net_pnl", "sum"),
        trades=("id", "count"),
        win_rate=("is_win", lambda x: x.mean() * 100)
    ).reset_index().sort_values("dow_num")


def compute_monthly_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly performance breakdown."""
    if df.empty:
        return pd.DataFrame()
    df = df.copy()
    df["month"] = df["trade_date"].dt.to_period("M")
    return df.groupby("month").agg(
        trades=("id", "count"),
        total_pnl=("net_pnl", "sum"),
        win_rate=("is_win", lambda x: x.mean() * 100),
        best_trade=("net_pnl", "max"),
        worst_trade=("net_pnl", "min")
    ).reset_index().round(2)


def detect_behavioral_patterns(df: pd.DataFrame) -> List[Dict]:
    """Detect trading behavior patterns and generate insights."""
    insights = []
    if df.empty or len(df) < 5:
        return insights

    # Session performance
    if "session" in df.columns:
        session_stats = compute_by_session(df)
        if not session_stats.empty:
            best_session = session_stats.loc[session_stats["win_rate"].idxmax()]
            worst_session = session_stats.loc[session_stats["total_pnl"].idxmin()]
            insights.append({
                "type": "positive",
                "icon": "🏆",
                "title": "Best Session",
                "message": f"Your win rate is highest during {best_session['session']} session ({best_session['win_rate']:.0f}%)"
            })
            if worst_session["total_pnl"] < 0:
                insights.append({
                    "type": "warning",
                    "icon": "⚠️",
                    "title": "Losing Session",
                    "message": f"You lose most during {worst_session['session']} session. Consider reducing exposure."
                })

    # Overtrading detection
    if "trade_date" in df.columns:
        daily_counts = df.groupby("trade_date")["id"].count()
        avg_trades = daily_counts.mean()
        high_trade_days = daily_counts[daily_counts > avg_trades * 1.8]
        if not high_trade_days.empty:
            high_pnl = []
            for d in high_trade_days.index:
                day_pnl = df[df["trade_date"] == d]["net_pnl"].sum()
                high_pnl.append(day_pnl)
            if sum(1 for p in high_pnl if p < 0) > len(high_pnl) * 0.6:
                insights.append({
                    "type": "danger",
                    "icon": "🚨",
                    "title": "Overtrading Detected",
                    "message": f"On days with {avg_trades*1.8:.0f}+ trades, you tend to lose more. Average: {avg_trades:.1f} trades/day."
                })

    # Revenge trading (losses followed by more trades on same day)
    if "trade_date" in df.columns:
        df_sorted = df.sort_values(["trade_date", "created_at"] if "created_at" in df.columns else "trade_date")
        revenge_days = 0
        for d, group in df_sorted.groupby("trade_date"):
            if len(group) >= 3:
                pnl_seq = group["net_pnl"].tolist()
                for i in range(1, len(pnl_seq)-1):
                    if pnl_seq[i-1] < 0 and pnl_seq[i] < 0 and pnl_seq[i+1] < 0:
                        revenge_days += 1
                        break
        if revenge_days >= 2:
            insights.append({
                "type": "danger",
                "icon": "😤",
                "title": "Possible Revenge Trading",
                "message": f"Detected {revenge_days} days with 3+ consecutive losing trades. Consider a daily stop loss rule."
            })

    # Win rate trend
    if len(df) >= 20:
        recent = df.tail(10)["is_win"].mean() * 100
        overall = df["is_win"].mean() * 100
        if recent > overall + 10:
            insights.append({
                "type": "positive",
                "icon": "📈",
                "title": "Improving Performance",
                "message": f"Your recent win rate ({recent:.0f}%) is above your overall ({overall:.0f}%). Great momentum!"
            })
        elif recent < overall - 15:
            insights.append({
                "type": "warning",
                "icon": "📉",
                "title": "Performance Declining",
                "message": f"Your recent win rate ({recent:.0f}%) is below your overall ({overall:.0f}%). Review your recent trades."
            })

    # Best day of week
    if len(df) >= 10:
        dow = compute_day_of_week(df)
        if not dow.empty:
            best_dow = dow.loc[dow["win_rate"].idxmax()]
            worst_dow = dow.loc[dow["total_pnl"].idxmin()]
            insights.append({
                "type": "info",
                "icon": "📅",
                "title": "Best Trading Day",
                "message": f"{best_dow['dow']} is your strongest day with {best_dow['win_rate']:.0f}% win rate."
            })
            if worst_dow["total_pnl"] < 0:
                insights.append({
                    "type": "warning",
                    "icon": "📅",
                    "title": "Weakest Trading Day",
                    "message": f"{worst_dow['dow']} is your worst day. Consider skipping it or reducing size."
                })

    # High confidence trades
    if "confidence_level" in df.columns:
        df["confidence_level"] = pd.to_numeric(df["confidence_level"], errors="coerce")
        high_conf = df[df["confidence_level"] >= 8]
        low_conf = df[df["confidence_level"] <= 4]
        if len(high_conf) >= 5 and len(low_conf) >= 5:
            hc_wr = high_conf["is_win"].mean() * 100
            lc_wr = low_conf["is_win"].mean() * 100
            if hc_wr > lc_wr + 15:
                insights.append({
                    "type": "positive",
                    "icon": "💡",
                    "title": "Confidence Correlation",
                    "message": f"High-confidence trades win {hc_wr:.0f}% vs {lc_wr:.0f}% for low-confidence. Trust your gut more!"
                })

    return insights


def compute_prop_account_status(account: Dict, trades: List[Dict]) -> Dict:
    """Compute real-time prop account status."""
    df = trades_to_df(trades) if trades else pd.DataFrame()
    
    starting = float(account.get("starting_balance", 0))
    current = float(account.get("current_balance", starting))
    
    if not df.empty and "prop_account_id" in df.columns:
        account_trades = df[df["prop_account_id"] == account.get("id", "")]
        if not account_trades.empty:
            trade_pnl = account_trades["net_pnl"].sum()
            current = starting + trade_pnl
    
    profit_target_pct = float(account.get("profit_target_pct", 10))
    daily_loss_pct = float(account.get("daily_loss_limit_pct", 5))
    max_dd_pct = float(account.get("max_drawdown_pct", 10))
    
    target_balance = starting * (1 + profit_target_pct / 100)
    profit_made = current - starting
    profit_pct = (profit_made / starting) * 100
    progress_to_target = min((profit_made / (target_balance - starting)) * 100, 100) if target_balance > starting else 0
    
    # Daily loss check
    today = date.today().isoformat()
    daily_pnl = 0
    if not df.empty and "trade_date" in df.columns:
        today_trades = df[df["trade_date"].astype(str).str.startswith(today)] if not df.empty else pd.DataFrame()
        if not today_trades.empty:
            daily_pnl = today_trades["net_pnl"].sum()
    
    daily_loss_limit = starting * daily_loss_pct / 100
    daily_loss_used_pct = abs(min(daily_pnl, 0)) / daily_loss_limit * 100 if daily_loss_limit > 0 else 0
    
    # Drawdown
    drawdown_from_start = abs(min(profit_made, 0)) / starting * 100 if profit_made < 0 else 0
    
    # Status assessment
    warnings = []
    if daily_loss_used_pct >= 80:
        warnings.append({"level": "danger", "msg": f"⛔ {daily_loss_used_pct:.0f}% of daily loss limit used!"})
    elif daily_loss_used_pct >= 60:
        warnings.append({"level": "warning", "msg": f"⚠️ {daily_loss_used_pct:.0f}% of daily loss limit used"})
    
    if drawdown_from_start >= max_dd_pct * 0.8:
        warnings.append({"level": "danger", "msg": f"⛔ Approaching max drawdown limit ({drawdown_from_start:.1f}%/{max_dd_pct}%)"})
    
    remaining_to_target = max(0, target_balance - current)
    if progress_to_target >= 90:
        warnings.append({"level": "success", "msg": f"🎯 Almost there! {100-progress_to_target:.1f}% left to pass!"})
    
    return {
        "current_balance": round(current, 2),
        "profit_made": round(profit_made, 2),
        "profit_pct": round(profit_pct, 2),
        "progress_to_target": round(progress_to_target, 1),
        "target_balance": round(target_balance, 2),
        "remaining_to_target": round(remaining_to_target, 2),
        "daily_pnl": round(daily_pnl, 2),
        "daily_loss_used_pct": round(daily_loss_used_pct, 1),
        "drawdown_from_start": round(drawdown_from_start, 2),
        "warnings": warnings,
        "is_at_risk": any(w["level"] == "danger" for w in warnings),
    }
