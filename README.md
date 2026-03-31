# ⚡ TradeForge — Professional Trade Journal

A **premium trading performance command center** built with Streamlit. TradeForge transforms raw trade data into structured feedback loops to help you evolve as a trader.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd trade_journal
pip install -r requirements.txt
```

### 2. Configure Supabase (optional but recommended)
Copy the env template:
```bash
cp .env.example .env
```

Fill in your Supabase credentials in `.env`:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

Or create `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key-here"
```

### 3. Set Up Supabase Tables
1. Go to your Supabase project → SQL Editor
2. Run the SQL from `supabase_schema.sql`
3. All tables will be created automatically

### 4. Run the App
```bash
streamlit run app.py
```

---

## 📱 Features

### 📊 Dashboard
- Real-time metrics: P&L, win rate, profit factor, R-multiple, max drawdown
- Equity curve with drawdown overlay
- Daily PnL bar chart
- Win rate donut chart
- R-multiple distribution histogram
- Session and asset performance charts
- Interactive trading calendar (green/red intensity by performance)
- Behavioral insights auto-detection

### ➕ Trade Logging
- Full trade fields: asset, direction, entry/exit, SL/TP, lot size, fees, session
- Strategy linking with rules checklist
- Confidence level tracking (1-10)
- Pre-trade bias and post-trade reflection
- Screenshot uploads (PNG/JPG/GIF)
- Tag system for trade categorization
- Automatic P&L and R-multiple calculation

### 📓 Journal & Reflection
- Daily/weekly/monthly journal entries
- Mood tracking (1-5 scale with emoji)
- Market conditions logging
- What went well / wrong analysis
- Tomorrow's game plan
- Goal setting and progress tracking
- Consistency metrics and streaks

### 🧩 Strategies & Rules
- Create strategy playbooks with rules checklists
- Track rule adherence per trade
- Strategy performance analytics
- Most broken rules analysis
- Win rate per strategy comparison

### 🏦 Prop Firm Tracker
- Support for FTMO, The Funded Trader, MyForexFunds, TopstepFX, Apex, E8, Funded Next
- Real-time progress toward profit targets
- Daily loss limit monitoring with warnings
- Max drawdown tracking
- Visual progress bars with color-coded alerts
- Multiple account management (challenge + funded)

### 🔬 Analytics Engine
- Time analysis: day of week, hour of day, monthly breakdown
- Asset segmentation analysis
- Strategy performance comparison
- Buy vs Sell analysis
- Confidence level correlation
- R-multiple and P&L distribution charts
- Streak analysis (max/avg win/loss streaks)
- Behavioral pattern detection (overtrading, revenge trading)

### ⚙️ Settings & Configuration
- Supabase connection management
- Risk limit configuration with live sidebar warnings
- Daily trade limit alerts
- CSV import/export
- Data management tools

---

## 🔄 Offline Mode & Sync

TradeForge works **100% offline** with automatic Supabase sync:

- **Primary storage**: Supabase (when connected)
- **Fallback**: Local JSON files in `/data/` directory
- **Auto-sync**: Offline changes are queued and synced when connection is restored
- **Status indicator**: Sidebar shows connection status and pending sync count

---

## 📁 Project Structure

```
trade_journal/
├── app.py                  # Main entry point & navigation
├── requirements.txt        # Python dependencies
├── supabase_schema.sql     # Database setup SQL
├── .env.example            # Environment template
├── .streamlit/
│   └── config.toml         # Streamlit theme config
├── pages/
│   ├── dashboard.py        # Main dashboard
│   ├── add_trade.py        # Trade entry & history
│   ├── journal.py          # Journaling & goals
│   ├── strategies.py       # Strategy management
│   ├── prop_firm.py        # Prop account tracker
│   ├── analytics.py        # Deep analytics
│   └── settings.py         # Configuration
├── utils/
│   ├── database.py         # DB layer (Supabase + JSON fallback)
│   └── analytics.py        # Analytics engine
├── components/
│   └── ui.py               # Reusable UI components
└── data/                   # Local JSON storage (auto-created)
    ├── trades.json
    ├── strategies.json
    ├── prop_accounts.json
    ├── journal_entries.json
    ├── goals.json
    └── settings.json
```

---

## 🎨 Design Philosophy

TradeForge uses a **premium dark terminal aesthetic**:
- Font: Space Grotesk (UI) + JetBrains Mono (numbers)
- Colors: Deep navy backgrounds with accent blues, greens, and reds
- Minimal chrome, maximum data density
- Consistent card-based layout with hover effects

---

## 📈 Supported Calculations

| Metric | Formula |
|--------|---------|
| P&L | `(exit - entry) × direction × lot_size` |
| Net P&L | `P&L - fees` |
| R-Multiple | `net_pnl / (risk_per_unit × lot_size)` |
| Profit Factor | `gross_profit / gross_loss` |
| Win Rate | `wins / total_trades × 100` |
| Sharpe Ratio | `mean_daily_pnl / std × √252` |
| Max Drawdown | `max((equity - roll_max) / roll_max)` |
