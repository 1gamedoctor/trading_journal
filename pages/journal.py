"""
Journal & Reflection Page
"""
import streamlit as st
from datetime import date, datetime, timedelta
from utils.database import db_insert, db_select, db_update, db_delete
from components.ui import page_header, empty_state, metric_card


MOOD_LABELS = {1: "😞 Terrible", 2: "😕 Poor", 3: "😐 Neutral", 4: "😊 Good", 5: "🤩 Excellent"}
MOOD_COLORS = {1: "#ff4757", 2: "#ff7b39", 3: "#ffcc00", 4: "#4c9eff", 5: "#00d68f"}


def render():
    page_header("📓", "Journal", "Daily reflections and lessons learned")
    
    tab1, tab2, tab3, tab4 = st.tabs(["✍️ Write Entry", "📚 Past Entries", "🎯 Goals", "📈 Consistency"])
    
    with tab1:
        _render_write_entry()
    with tab2:
        _render_past_entries()
    with tab3:
        _render_goals()
    with tab4:
        _render_consistency()


def _render_write_entry():
    today = date.today()
    
    # Check if today already has an entry
    entries = db_select("journal_entries")
    today_entries = [e for e in entries if str(e.get("entry_date", ""))[:10] == str(today)]
    existing = today_entries[0] if today_entries else None
    
    if existing:
        st.info(f"📝 You already have an entry for today. Editing existing entry.")
    
    with st.form("journal_form"):
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input("Date", value=today)
        with col2:
            entry_type = st.selectbox("Entry Type", ["Daily", "Weekly", "Monthly"])
        
        st.markdown("#### 😊 How did you feel today?")
        mood = st.select_slider(
            "Mood",
            options=[1, 2, 3, 4, 5],
            value=existing.get("mood", 3) if existing else 3,
            format_func=lambda x: MOOD_LABELS[x],
            label_visibility="collapsed"
        )
        
        st.markdown("#### 🌍 Market Conditions")
        market_conditions = st.text_area(
            "What were market conditions like today?",
            value=existing.get("market_conditions", "") if existing else "",
            placeholder="Trending / ranging / high volatility / news-driven? Key levels? Overall bias?",
            height=80
        )
        
        st.markdown("#### ✅ What Went Well?")
        what_well = st.text_area(
            "Wins and positive moments",
            value=existing.get("what_went_well", "") if existing else "",
            placeholder="What did you do right? Good setups, discipline, emotional control...",
            height=100
        )
        
        st.markdown("#### ❌ What Went Wrong?")
        what_wrong = st.text_area(
            "Mistakes and negative patterns",
            value=existing.get("what_went_wrong", "") if existing else "",
            placeholder="Mistakes made, rules broken, emotional trading...",
            height=100
        )
        
        st.markdown("#### 💡 Lessons Learned")
        lessons = st.text_area(
            "Key takeaways",
            value=existing.get("lessons_learned", "") if existing else "",
            placeholder="What will you do differently next time? What insights did you gain?",
            height=100
        )
        
        st.markdown("#### 🔮 Plan for Tomorrow")
        plan = st.text_area(
            "Tomorrow's game plan",
            value=existing.get("plan_for_tomorrow", "") if existing else "",
            placeholder="Key levels to watch, setups to look for, goals for tomorrow...",
            height=80
        )
        
        st.markdown("#### 🎯 Goals Review")
        goals_review = st.text_area(
            "Did you meet today's goals?",
            value=existing.get("goals_reviewed", "") if existing else "",
            placeholder="Reflect on your daily goals and how well you followed your plan...",
            height=80
        )
        
        tags_input = st.text_input(
            "Tags",
            value=", ".join(existing.get("tags", []) or []) if existing else "",
            placeholder="disciplined, revenge-trading, FOMO, good-execution..."
        )
        
        submitted = st.form_submit_button("💾 Save Journal Entry", type="primary", use_container_width=True)
        
        if submitted:
            tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
            
            entry_data = {
                "entry_date": str(entry_date),
                "entry_type": entry_type,
                "mood": mood,
                "market_conditions": market_conditions,
                "what_went_well": what_well,
                "what_went_wrong": what_wrong,
                "lessons_learned": lessons,
                "plan_for_tomorrow": plan,
                "goals_reviewed": goals_review,
                "tags": tags
            }
            
            if existing:
                result = db_update("journal_entries", existing["id"], entry_data)
                if result:
                    st.success("✅ Journal entry updated!")
                else:
                    st.error("❌ Update failed")
            else:
                result = db_insert("journal_entries", entry_data)
                if result:
                    st.success("✅ Journal entry saved!")
                    st.balloons()
                else:
                    st.error("❌ Save failed")


def _render_past_entries():
    entries = db_select("journal_entries", order_by="entry_date", order_desc=True)
    
    if not entries:
        empty_state("📚", "No journal entries yet", "Start writing daily reflections to build your trading mind")
        return
    
    # Mood timeline
    import plotly.graph_objects as go
    from components.ui import apply_chart_theme
    
    mood_data = [(e["entry_date"], e.get("mood", 3)) for e in entries if e.get("mood")]
    if mood_data:
        dates, moods = zip(*sorted(mood_data))
        mood_colors = [MOOD_COLORS.get(m, "#8b92a8") for m in moods]
        
        fig = go.Figure(go.Scatter(
            x=dates, y=moods,
            mode="lines+markers",
            line=dict(color="#4c9eff", width=2),
            marker=dict(color=mood_colors, size=10),
            hovertemplate="<b>%{x}</b><br>Mood: %{y}/5<extra></extra>"
        ))
        fig.update_layout(
            title="Mood Over Time",
            yaxis=dict(tickvals=[1,2,3,4,5], ticktext=["😞","😕","😐","😊","🤩"]),
            height=180
        )
        apply_chart_theme(fig, height=180)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    st.markdown("---")
    
    # Filter
    col1, col2 = st.columns(2)
    with col1:
        filter_type = st.selectbox("Filter by Type", ["All", "Daily", "Weekly", "Monthly"])
    with col2:
        filter_mood = st.selectbox("Filter by Mood", ["All", "5 - Excellent", "4 - Good", "3 - Neutral", "2 - Poor", "1 - Terrible"])
    
    filtered = entries
    if filter_type != "All":
        filtered = [e for e in filtered if e.get("entry_type") == filter_type]
    if filter_mood != "All":
        mood_val = int(filter_mood[0])
        filtered = [e for e in filtered if e.get("mood") == mood_val]
    
    for entry in filtered:
        _render_journal_entry_card(entry)


def _render_journal_entry_card(entry: dict):
    mood = entry.get("mood", 3)
    mood_label = MOOD_LABELS.get(mood, "—")
    mood_color = MOOD_COLORS.get(mood, "#8b92a8")
    date_str = str(entry.get("entry_date", ""))[:10]
    entry_type = entry.get("entry_type", "Daily")
    tags = entry.get("tags", []) or []
    
    with st.expander(f"📅 {date_str}  ·  {entry_type}  ·  {mood_label}  ·  {', '.join(tags[:3]) if tags else ''}"):
        col1, col2 = st.columns(2)
        
        with col1:
            if entry.get("market_conditions"):
                st.markdown(f"**🌍 Market Conditions**\n\n{entry['market_conditions']}")
            if entry.get("what_went_well"):
                st.markdown(f"**✅ What Went Well**\n\n{entry['what_went_well']}")
            if entry.get("lessons_learned"):
                st.markdown(f"**💡 Lessons**\n\n{entry['lessons_learned']}")
        
        with col2:
            if entry.get("what_went_wrong"):
                st.markdown(f"**❌ What Went Wrong**\n\n{entry['what_went_wrong']}")
            if entry.get("plan_for_tomorrow"):
                st.markdown(f"**🔮 Tomorrow's Plan**\n\n{entry['plan_for_tomorrow']}")
            if entry.get("goals_reviewed"):
                st.markdown(f"**🎯 Goals Review**\n\n{entry['goals_reviewed']}")
        
        if tags:
            st.markdown("**Tags:** " + " ".join([f"`{t}`" for t in tags]))
        
        col_del, _ = st.columns([1, 5])
        with col_del:
            if st.button("🗑️ Delete", key=f"del_journal_{entry['id']}"):
                db_delete("journal_entries", entry["id"])
                st.rerun()


def _render_goals():
    goals = db_select("goals", order_by="created_at", order_desc=False)
    
    col_left, col_right = st.columns([2, 1])
    
    with col_right:
        st.markdown("#### ➕ New Goal")
        with st.form("new_goal_form", clear_on_submit=True):
            title = st.text_input("Goal Title*", placeholder="Max 3 trades per day")
            description = st.text_area("Description", height=60)
            goal_type = st.selectbox("Type", ["Daily", "Weekly", "Monthly", "Yearly"])
            col1, col2 = st.columns(2)
            with col1:
                target = st.number_input("Target Value", min_value=0.0, value=0.0)
            with col2:
                unit = st.text_input("Unit", placeholder="trades, %, $...")
            
            col1, col2 = st.columns(2)
            with col1:
                start = st.date_input("Start", value=date.today())
            with col2:
                end = st.date_input("End", value=date.today() + timedelta(days=30))
            
            if st.form_submit_button("Add Goal", type="primary", use_container_width=True):
                if title:
                    db_insert("goals", {
                        "title": title, "description": description,
                        "goal_type": goal_type, "target_value": target,
                        "current_value": 0, "unit": unit,
                        "start_date": str(start), "end_date": str(end),
                        "is_active": True, "is_completed": False
                    })
                    st.success("✅ Goal added!")
                    st.rerun()
    
    with col_left:
        st.markdown("#### 🎯 Active Goals")
        active_goals = [g for g in goals if g.get("is_active") and not g.get("is_completed")]
        completed_goals = [g for g in goals if g.get("is_completed")]
        
        if not active_goals and not completed_goals:
            empty_state("🎯", "No goals set", "Set goals to track your progress")
        
        for goal in active_goals:
            _render_goal_card(goal, False)
        
        if completed_goals:
            st.markdown("#### ✅ Completed Goals")
            for goal in completed_goals:
                _render_goal_card(goal, True)


def _render_goal_card(goal: dict, completed: bool):
    target = float(goal.get("target_value", 0) or 0)
    current = float(goal.get("current_value", 0) or 0)
    pct = (current / target * 100) if target > 0 else 0
    unit = goal.get("unit", "")
    
    bar_color = "#00d68f" if completed or pct >= 100 else ("#4c9eff" if pct >= 50 else "#ffcc00")
    
    st.markdown(f"""
    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:16px;margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:10px;">
            <div>
                <span style="font-weight:600;">{'✅ ' if completed else ''}{goal['title']}</span>
                <span style="background:rgba(255,255,255,0.05);padding:2px 8px;border-radius:100px;
                      font-size:0.7rem;color:var(--text-muted);margin-left:8px;">{goal.get('goal_type','')}</span>
            </div>
            <span style="font-family:var(--font-mono);font-size:0.85rem;color:{bar_color};">{current}/{target} {unit}</span>
        </div>
        {'<p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:10px;">' + goal['description'] + '</p>' if goal.get('description') else ''}
        <div style="background:rgba(255,255,255,0.07);border-radius:100px;height:6px;">
            <div style="width:{min(pct,100):.0f}%;height:100%;background:{bar_color};border-radius:100px;"></div>
        </div>
        <div style="font-size:0.72rem;color:var(--text-muted);margin-top:6px;">{pct:.0f}% complete · {str(goal.get('end_date',''))[:10]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, _ = st.columns([1, 1, 1, 4])
    with col1:
        new_val = st.number_input("Progress", value=float(current), label_visibility="collapsed", key=f"gval_{goal['id']}")
        if st.button("Update", key=f"gupd_{goal['id']}"):
            is_done = target > 0 and new_val >= target
            db_update("goals", goal["id"], {"current_value": new_val, "is_completed": is_done})
            st.rerun()
    with col2:
        if st.button("✅ Complete", key=f"gcomp_{goal['id']}"):
            db_update("goals", goal["id"], {"is_completed": True, "current_value": target})
            st.rerun()
    with col3:
        if st.button("🗑️", key=f"gdel_{goal['id']}"):
            db_delete("goals", goal["id"])
            st.rerun()


def _render_consistency():
    entries = db_select("journal_entries", order_by="entry_date", order_desc=False)
    trades = db_select("trades", order_by="trade_date", order_desc=False)
    
    if not entries and not trades:
        empty_state("📈", "No data yet", "Start journaling and trading to see your consistency metrics")
        return
    
    # Journal streak
    if entries:
        dates = sorted(set(str(e.get("entry_date",""))[:10] for e in entries))
        streak = 0
        today = str(date.today())
        check = today
        for _ in range(365):
            if check in dates:
                streak += 1
                from datetime import timedelta
                check = str((date.fromisoformat(check) - timedelta(days=1)))
            else:
                break
        
        st.markdown("#### 📊 Journal Consistency")
        col1, col2, col3 = st.columns(3)
        with col1:
            metric_card("Total Entries", str(len(entries)), "", "blue", "📓")
        with col2:
            metric_card("Current Streak", f"{streak} days", "", "green" if streak >= 5 else "yellow", "🔥")
        with col3:
            # Avg mood
            moods = [e.get("mood", 3) for e in entries if e.get("mood")]
            avg_mood = sum(moods) / len(moods) if moods else 0
            metric_card("Avg Mood", f"{avg_mood:.1f}/5", MOOD_LABELS.get(round(avg_mood), ""), "blue", "😊")
        
        # Mood trend
        import plotly.graph_objects as go
        from components.ui import apply_chart_theme
        
        mood_by_date = {str(e["entry_date"])[:10]: e.get("mood", 3) for e in entries}
        if len(mood_by_date) > 1:
            sorted_dates = sorted(mood_by_date.keys())
            moods_sorted = [mood_by_date[d] for d in sorted_dates]
            colors = [MOOD_COLORS.get(m, "#4c9eff") for m in moods_sorted]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=sorted_dates, y=moods_sorted,
                marker_color=colors,
                hovertemplate="%{x}<br>Mood: %{y}/5<extra></extra>"
            ))
            fig.update_layout(
                title="Journal Mood History",
                yaxis=dict(range=[0, 6], tickvals=[1,2,3,4,5], ticktext=["Terrible","Poor","Neutral","Good","Excellent"]),
                height=220
            )
            apply_chart_theme(fig, 220)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    # Trading days consistency
    if trades:
        st.markdown("---")
        st.markdown("#### 📅 Trading Day Activity")
        closed_trades = [t for t in trades if t.get("status") == "CLOSED"]
        
        from utils.analytics import trades_to_df
        df = trades_to_df(closed_trades)
        if not df.empty:
            import pandas as pd
            trade_dates = set(df["trade_date"].dt.date.astype(str))
            journal_dates = set(str(e.get("entry_date",""))[:10] for e in entries)
            
            both = len(trade_dates & journal_dates)
            only_trade = len(trade_dates - journal_dates)
            only_journal = len(journal_dates - trade_dates)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                metric_card("Days Traded + Journaled", str(both), "Complete days", "green", "✅")
            with col2:
                metric_card("Traded, Not Journaled", str(only_trade), "Missed reflections", "yellow", "⚠️")
            with col3:
                metric_card("Journaled, Not Traded", str(only_journal), "Rest days", "blue", "😴")
