CREATE TABLE stocks (
                    symbol VARCHAR(10) PRIMARY KEY,
                    company_name VARCHAR(255),
                    sector VARCHAR(100),
                    industry VARCHAR(100),
                    market_cap BIGINT,
                    listing_exchange VARCHAR(20),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
CREATE TABLE price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    date DATE NOT NULL,
                    open DECIMAL(10,2),
                    high DECIMAL(10,2),
                    low DECIMAL(10,2),
                    close DECIMAL(10,2),
                    volume BIGINT,
                    adjusted_close DECIMAL(10,2),
                    source VARCHAR(50),
                    quality_score DECIMAL(3,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                    UNIQUE(symbol, date, source)
                );
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE fundamental_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    reporting_date DATE NOT NULL,
                    period_type VARCHAR(10),
                    
                    -- Core financials
                    total_revenue BIGINT,
                    net_income BIGINT,
                    total_assets BIGINT,
                    total_debt BIGINT,
                    shareholders_equity BIGINT,
                    shares_outstanding BIGINT,
                    free_cash_flow BIGINT,
                    operating_cash_flow BIGINT,
                    
                    -- Key ratios (pre-calculated for efficiency)
                    eps DECIMAL(10,4),
                    book_value_per_share DECIMAL(10,4),
                    pe_ratio DECIMAL(8,2),
                    forward_pe DECIMAL(8,2),
                    peg_ratio DECIMAL(8,2),
                    price_to_book DECIMAL(8,2),
                    enterprise_value BIGINT,
                    ev_to_ebitda DECIMAL(8,2),
                    
                    -- Quality metrics
                    return_on_equity DECIMAL(6,4),
                    return_on_assets DECIMAL(6,4),
                    debt_to_equity DECIMAL(6,4),
                    current_ratio DECIMAL(6,4),
                    quick_ratio DECIMAL(6,4),
                    
                    -- Growth metrics
                    revenue_growth DECIMAL(6,4),
                    earnings_growth DECIMAL(6,4),
                    revenue_per_share DECIMAL(10,4),
                    
                    -- Market data
                    current_price DECIMAL(10,2),
                    market_cap BIGINT,
                    beta DECIMAL(6,4),
                    dividend_yield DECIMAL(6,4),
                    week_52_high DECIMAL(10,2),
                    week_52_low DECIMAL(10,2),
                    
                    -- Metadata
                    source VARCHAR(50),
                    quality_score DECIMAL(3,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                    UNIQUE(symbol, reporting_date, period_type, source)
                );
CREATE TABLE news_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    title TEXT NOT NULL,
                    summary TEXT,
                    content TEXT,
                    publisher VARCHAR(100),
                    publish_date TIMESTAMP,
                    url TEXT,
                    sentiment_score DECIMAL(4,3),
                    data_quality_score DECIMAL(4,3),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
                );
CREATE TABLE reddit_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    post_id VARCHAR(20) UNIQUE,
                    title TEXT NOT NULL,
                    content TEXT,
                    subreddit VARCHAR(50),
                    author VARCHAR(50),
                    score INTEGER,
                    upvote_ratio DECIMAL(3,2),
                    num_comments INTEGER,
                    created_utc TIMESTAMP,
                    url TEXT,
                    sentiment_score DECIMAL(4,3),
                    data_quality_score DECIMAL(4,3),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
                );
CREATE TABLE daily_sentiment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    date DATE,
                    news_sentiment DECIMAL(4,3),
                    news_count INTEGER,
                    reddit_sentiment DECIMAL(4,3),
                    reddit_count INTEGER,
                    combined_sentiment DECIMAL(4,3),
                    data_quality DECIMAL(4,3),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                    UNIQUE(symbol, date)
                );
CREATE TABLE calculated_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10),
                    calculation_date DATE NOT NULL,
                    
                    -- Component scores (0-100)
                    fundamental_score DECIMAL(5,2),
                    quality_score DECIMAL(5,2),
                    growth_score DECIMAL(5,2),
                    sentiment_score DECIMAL(5,2),
                    
                    -- Composite score
                    composite_score DECIMAL(5,2),
                    sector_percentile DECIMAL(5,2),
                    data_quality_lower DECIMAL(5,2),
                    data_quality_upper DECIMAL(5,2),
                    
                    -- Metadata
                    methodology_version VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, market_percentile REAL, outlier_category TEXT,
                    
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                    UNIQUE(symbol, calculation_date)
                );
CREATE INDEX idx_price_data_symbol_date ON price_data(symbol, date);
CREATE INDEX idx_fundamental_data_symbol_date ON fundamental_data(symbol, reporting_date);
CREATE INDEX idx_news_articles_symbol_date ON news_articles(symbol, publish_date);
CREATE INDEX idx_reddit_posts_symbol_date ON reddit_posts(symbol, created_utc);
CREATE INDEX idx_daily_sentiment_symbol_date ON daily_sentiment(symbol, date);
CREATE INDEX idx_calculated_metrics_symbol_date ON calculated_metrics(symbol, calculation_date);
CREATE TABLE quality_gates (
                gate_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                component TEXT NOT NULL,
                status TEXT NOT NULL,
                quality_score REAL,
                approval_timestamp TEXT,
                approved_by TEXT,
                expires_at TEXT,
                blocking_rules TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (symbol) REFERENCES stocks (symbol)
            );
CREATE TABLE data_versions (
                version_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                component TEXT NOT NULL,
                data_snapshot TEXT,
                approval_gate_id TEXT,
                created_at TEXT NOT NULL,
                approved_at TEXT,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (symbol) REFERENCES stocks (symbol),
                FOREIGN KEY (approval_gate_id) REFERENCES quality_gates (gate_id)
            );
CREATE TABLE quality_gate_rules (
                rule_id TEXT PRIMARY KEY,
                component TEXT NOT NULL,
                metric TEXT NOT NULL,
                threshold REAL NOT NULL,
                operator TEXT NOT NULL,
                block_analysis INTEGER DEFAULT 1,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
CREATE TABLE temp_sentiment_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol VARCHAR(10) NOT NULL,
                    content_type VARCHAR(10) NOT NULL, -- 'news' or 'reddit'
                    content_id INTEGER NOT NULL,       -- FK to original article/post
                    text_content TEXT NOT NULL,        -- Combined title + summary/content
                    source_table VARCHAR(50) NOT NULL, -- 'news_articles' or 'reddit_posts'

                    -- Processing status
                    processing_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
                    batch_id VARCHAR(50),              -- Anthropic batch ID
                    custom_id VARCHAR(100),            -- Individual request ID within batch

                    -- Results
                    sentiment_score REAL,
                    confidence REAL,
                    processing_method VARCHAR(20),     -- 'bulk_claude', 'individual', 'fallback'

                    -- Audit trail
                    raw_response TEXT,                 -- Full Anthropic response for debugging
                    error_message TEXT,                -- Error details if failed
                    retry_count INTEGER DEFAULT 0,    -- Number of retry attempts

                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,

                    -- Constraints
                    FOREIGN KEY (symbol) REFERENCES stocks(symbol),
                    UNIQUE(symbol, content_type, content_id) -- Prevent duplicates
                );
CREATE INDEX idx_temp_sentiment_queue_status ON temp_sentiment_queue(processing_status);
CREATE INDEX idx_temp_sentiment_queue_batch ON temp_sentiment_queue(batch_id);
CREATE INDEX idx_temp_sentiment_queue_symbol ON temp_sentiment_queue(symbol);
CREATE TABLE batches (
        batch_id TEXT PRIMARY KEY,
        status TEXT NOT NULL,
        request_count INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        error_message TEXT
    );
CREATE INDEX idx_batches_status ON batches(status);
CREATE TABLE batch_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id TEXT NOT NULL,
        record_type TEXT NOT NULL,
        record_id INTEGER NOT NULL,
        custom_id TEXT NOT NULL,
        symbol TEXT,
        status TEXT DEFAULT 'submitted',
        processed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(batch_id, custom_id)
    );
CREATE INDEX idx_batch_mapping_batch_id ON batch_mapping(batch_id);
CREATE INDEX idx_batch_mapping_custom_id ON batch_mapping(custom_id);
CREATE INDEX idx_batch_mapping_record ON batch_mapping(record_type, record_id);
CREATE INDEX idx_batch_mapping_status ON batch_mapping(status);
CREATE INDEX idx_batch_mapping_batch ON batch_mapping(batch_id);
