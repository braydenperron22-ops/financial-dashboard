# =============================================================================
# config.py
# -----------------------------------------------------------------------------
# Central configuration file. Every ticker symbol, label, refresh interval,
# and tunable constant lives here. If you ever need to swap a ticker or change
# a setting, this is the ONLY file you touch.
# =============================================================================

# ---------------------------------------------------------------------------
# 1. MAJOR INDICES
#    These map a human-readable label to the Yahoo Finance ticker symbol.
#    yfinance uses these exact strings to pull data.
# ---------------------------------------------------------------------------
INDICES = {
    "S&P 500":        "^GSPC",
    "NASDAQ":         "^IXIC",
    "Small-Cap":      "^RUT",       # Russell 2000
    "TSX":            "^GSPTSE",    # Toronto Stock Exchange
    "International":  "EFA",        # iShares MSCI EAFE ETF
    "Emerging":       "EEM",        # iShares MSCI Emerging Markets ETF
}

# ---------------------------------------------------------------------------
# 2. PORTFOLIO ASSETS
#    Your two core holdings.
# ---------------------------------------------------------------------------
PORTFOLIO = {
    "XEQT": {
        "ticker":  "XEQT.TO",   # .TO suffix = Toronto Stock Exchange
        "weight":  0.80,        # 80% of portfolio
    },
    "BTC": {
        "ticker":  "BTC-USD",
        "weight":  0.20,        # 20% of portfolio
    },
}

# Benchmark for alpha / beta / correlation calculations
BENCHMARK_TICKER = "SPY"

# ---------------------------------------------------------------------------
# 3. SECTORS
#    Standard SPDR sector ETFs — the most liquid and widely used.
# ---------------------------------------------------------------------------
SECTORS = {
    "Tech":           "XLK",
    "Financials":     "XLF",
    "Healthcare":     "XLV",
    "Communications": "XLC",
    "Energy":         "XLE",
    "Utilities":      "XLU",
    "Staples":        "XLP",
    "Real Estate":    "XLRE",
    "Materials":      "XLB",
    "Discretionary":  "XLY",
    "Industrials":    "XLI",
    "Metals":         "GDX",   # VanEck Gold Miners as a metals proxy
}

# ---------------------------------------------------------------------------
# 4. VOLATILITY & RISK METRICS
# ---------------------------------------------------------------------------
VIX_TICKER        = "^VIX"
HYG_TICKER        = "HYG"   # High-yield corporate bonds  → risk appetite
IEF_TICKER        = "IEF"   # 7-10yr Treasuries            → risk-off proxy
RSP_TICKER        = "RSP"   # Equal-weight S&P 500         → breadth proxy
SPY_TICKER        = "SPY"   # Cap-weight S&P 500

# ---------------------------------------------------------------------------
# 5. TREASURY YIELDS
#    Yahoo Finance carries these as price series.
# ---------------------------------------------------------------------------
TREASURY_YIELDS = {
    "Fed Rate (3M)":   "^IRX",
    "5Y":             "^FVX",
    "10Y":            "^TNX",
    "30Y":            "^TYX",
}

# ---------------------------------------------------------------------------
# 6. TICKER HEADER (60 SEGMENTS)
#    The rotating top ticker. Exactly 60 items; the date anchor logic is
#    handled in the fetcher, not here.
# ---------------------------------------------------------------------------
HEADER_TICKERS = [
    # Mega-cap tech
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AVGO",
    # Major ETFs
    "SPY", "QQQ", "IWM", "EFA", "EEM", "GLD", "SLV", "USO",
    # Crypto proxies
    "BTC-USD", "ETH-USD", "COIN", "MSTR",
    # Financials
    "JPM", "BAC", "GS", "MS", "BRK-B",
    # Broad economy
    "XOM", "CVX", "LLY", "UNH", "V", "MA", "WMT", "HD",
    # Rates / bonds
    "TLT", "HYG", "IEF", "SHY", "^TNX", "^VIX",
    # TSX / Canadian
    "XEQT.TO", "XIU.TO", "ENB.TO", "RY.TO", "TD.TO",
    # Global
    "EWJ", "EWZ", "FXI", "INDA",
    # Commodities
    "GC=F", "SI=F", "CL=F", "NG=F",
    # Misc growth
    "PLTR", "SHOP", "AMD", "INTC",
    # Placeholder slots (brings total to exactly 60)
    "^GSPC", "^IXIC", "^RUT", "^GSPTSE",
]

# Sanity-check: this will raise an error at startup if the count drifts.
assert len(HEADER_TICKERS) == 60, (
    f"HEADER_TICKERS must have exactly 60 items, found {len(HEADER_TICKERS)}"
)

# ---------------------------------------------------------------------------
# 7. CACHE & REFRESH SETTINGS
# ---------------------------------------------------------------------------
CACHE_DIR         = "cache_store"   # Folder created automatically by diskcache
CACHE_TTL_SECONDS = 300             # 5 minutes: how long before a re-fetch
FETCH_TIMEOUT     = 15              # Seconds before a single yfinance call gives up
MAX_RETRIES       = 3               # How many times to retry a failed API call

# ---------------------------------------------------------------------------
# 8. DISPLAY / ROTATION SCHEDULE (minutes)
#    20 min showing % change, 5 min showing 1-month return, 5 min showing YTD.
# ---------------------------------------------------------------------------
ROTATION_SCHEDULE = {
    "1D":  20,
    "1M":   5,
    "YTD":  5,
}

# ---------------------------------------------------------------------------
# 9. MARKET CONFIDENCE INDEX WEIGHTS
#    These four factors are combined into a 0–100 score.
#    You can adjust the weights; they must sum to 1.0.
# ---------------------------------------------------------------------------
MCI_WEIGHTS = {
    "vix_regime":        0.40,  # VIX vs its 30-day MA
    "risk_rotation":     0.25,  # HYG/IEF 1-month move
    "breadth":           0.20,  # RSP/SPY ratio trend
    "trend_strength":    0.15,  # SPY above/below 200DMA
}

# ---------------------------------------------------------------------------
# 10. MARKET HOURS (New York time — NYSE/NASDAQ)
# ---------------------------------------------------------------------------
MARKET_TZ       = "America/New_York"
MARKET_OPEN_HR  = 9
MARKET_OPEN_MIN = 30
MARKET_CLOSE_HR = 16
MARKET_CLOSE_MIN = 0
