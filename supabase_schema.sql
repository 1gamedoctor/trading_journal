-- ============================================================
-- TRADE JOURNAL - SUPABASE SCHEMA
-- Run this in your Supabase SQL editor to set up all tables
-- ============================================================

-- TRADES table
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    trade_date DATE NOT NULL,
    trade_time TIME,
    asset TEXT NOT NULL,
    direction TEXT CHECK (direction IN ('BUY', 'SELL')) NOT NULL,
    entry_price NUMERIC NOT NULL,
    exit_price NUMERIC,
    stop_loss NUMERIC,
    take_profit NUMERIC,
    lot_size NUMERIC NOT NULL DEFAULT 1,
    fees NUMERIC DEFAULT 0,
    session TEXT CHECK (session IN ('London', 'New York', 'Asia', 'Pre-Market', 'After-Hours')),
    status TEXT CHECK (status IN ('OPEN', 'CLOSED', 'CANCELLED')) DEFAULT 'OPEN',
    pnl NUMERIC,
    pnl_percent NUMERIC,
    r_multiple NUMERIC,
    strategy_id UUID REFERENCES strategies(id) ON DELETE SET NULL,
    prop_account_id UUID REFERENCES prop_accounts(id) ON DELETE SET NULL,
    confidence_level INTEGER CHECK (confidence_level BETWEEN 1 AND 10),
    pre_trade_bias TEXT,
    post_trade_reflection TEXT,
    rules_followed JSONB DEFAULT '[]',
    rules_broken JSONB DEFAULT '[]',
    tags TEXT[],
    screenshot_urls TEXT[],
    is_synced BOOLEAN DEFAULT TRUE
);

-- STRATEGIES table
CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    timeframes TEXT[],
    markets TEXT[],
    rules JSONB DEFAULT '[]',
    ideal_conditions TEXT,
    risk_reward_target NUMERIC DEFAULT 2.0,
    is_active BOOLEAN DEFAULT TRUE
);

-- PROP ACCOUNTS table
CREATE TABLE IF NOT EXISTS prop_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    firm_name TEXT NOT NULL,
    account_name TEXT NOT NULL,
    account_type TEXT CHECK (account_type IN ('Challenge Phase 1', 'Challenge Phase 2', 'Funded', 'Live')) NOT NULL,
    starting_balance NUMERIC NOT NULL,
    current_balance NUMERIC NOT NULL,
    profit_target_pct NUMERIC,
    daily_loss_limit_pct NUMERIC,
    max_drawdown_pct NUMERIC,
    max_trailing_drawdown_pct NUMERIC,
    min_trading_days INTEGER,
    max_trading_days INTEGER,
    days_traded INTEGER DEFAULT 0,
    status TEXT CHECK (status IN ('Active', 'Passed', 'Breached', 'Withdrawn')) DEFAULT 'Active',
    start_date DATE,
    end_date DATE,
    rules_notes TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- JOURNAL ENTRIES table
CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    entry_date DATE NOT NULL UNIQUE,
    entry_type TEXT CHECK (entry_type IN ('Daily', 'Weekly', 'Monthly')) DEFAULT 'Daily',
    mood INTEGER CHECK (mood BETWEEN 1 AND 5),
    market_conditions TEXT,
    what_went_well TEXT,
    what_went_wrong TEXT,
    lessons_learned TEXT,
    plan_for_tomorrow TEXT,
    goals_reviewed TEXT,
    tags TEXT[]
);

-- GOALS table
CREATE TABLE IF NOT EXISTS goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    title TEXT NOT NULL,
    description TEXT,
    goal_type TEXT CHECK (goal_type IN ('Daily', 'Weekly', 'Monthly', 'Yearly')),
    target_value NUMERIC,
    current_value NUMERIC DEFAULT 0,
    unit TEXT,
    start_date DATE,
    end_date DATE,
    is_completed BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

-- OFFLINE SYNC QUEUE (for local fallback)
CREATE TABLE IF NOT EXISTS sync_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    operation TEXT CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    payload JSONB NOT NULL,
    synced BOOLEAN DEFAULT FALSE
);

-- Enable RLS
ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategies ENABLE ROW LEVEL SECURITY;
ALTER TABLE prop_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;

-- Public policies (adjust for auth later)
CREATE POLICY "Allow all" ON trades FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON strategies FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON prop_accounts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON journal_entries FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all" ON goals FOR ALL USING (true) WITH CHECK (true);
