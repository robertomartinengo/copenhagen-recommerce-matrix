-- Copenhagen Re-Commerce Matrix — database schema (stato finale)
-- Righe addittive e ripetibili. Non modificare mai migrazioni già applicate.

-- Tabella zone di Copenhagen
CREATE TABLE IF NOT EXISTS copenhagen_zones (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    district_code TEXT UNIQUE NOT NULL,
    population_gen_z INTEGER NOT NULL,
    avg_income_dkk NUMERIC NOT NULL,
    waste_supply_score NUMERIC NOT NULL,
    market_gap_score NUMERIC NOT NULL,
    cpi_score NUMERIC DEFAULT 0,
    demographics_score NUMERIC DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabella lead acquisiti dal bot Telegram
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT,
    telegram_username TEXT,
    full_name TEXT,
    email TEXT,
    business_type TEXT,
    interested_district TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);