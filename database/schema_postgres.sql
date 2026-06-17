CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT,
    firebase_uid TEXT UNIQUE,
    email_notifications INTEGER DEFAULT 1,
    google_id TEXT UNIQUE,
    auth_provider TEXT DEFAULT 'local',
    profile_picture TEXT,
    email_verified BOOLEAN DEFAULT 0,
    plan TEXT DEFAULT 'free',
    plan_expiry DATE,
    currency TEXT DEFAULT 'INR',
    currency_symbol TEXT DEFAULT '₹',
    occupation TEXT DEFAULT '',
    monthly_income REAL DEFAULT 0.0,
    savings_goal REAL DEFAULT 0.0,
    budget_style TEXT DEFAULT '50/30/20',
    risk_appetite TEXT DEFAULT 'Moderate',
    advice_level TEXT DEFAULT 'Balanced',
    theme TEXT DEFAULT 'dark',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('income', 'expense')),
    transaction_date TEXT NOT NULL,
    is_recurring INTEGER DEFAULT 0,
    recurrence_type TEXT CHECK(recurrence_type IN ('daily', 'weekly', 'monthly', 'yearly', NULL)),
    next_due_date TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    budget_amount REAL NOT NULL,
    month TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS savings_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL NOT NULL DEFAULT 0,
    deadline TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    title TEXT,
    target_amount REAL,
    current_amount REAL DEFAULT 0,
    deadline DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sent_alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    category TEXT,
    month TEXT,
    alert_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS auth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    token TEXT UNIQUE NOT NULL,
    token_type TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    plan TEXT NOT NULL,
    billing_cycle TEXT,
    razorpay_subscription_id TEXT,
    razorpay_payment_id TEXT,
    status TEXT DEFAULT 'active',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS ai_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    usage_date DATE,
    message_count INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id),
    UNIQUE(user_id, usage_date)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid);
