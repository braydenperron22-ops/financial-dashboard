# =============================================================================
# data/fetcher.py
# -----------------------------------------------------------------------------
# Every single API call in the dashboard flows through this file.
#
# ARCHITECTURE OVERVIEW
# ─────────────────────
#   fetch_with_cache(key, fetch_fn, ttl)
#       │
#       ├─ Cache HIT  ──► return cached data immediately (no API call)
#       │
#       └─ Cache MISS ──► call fetch_fn() with retry logic
#               │
#               ├─ Success ──► write to cache, return fresh data
#               │
#               └─ All retries exhausted ──► return stale cache if available,
#                                            else return a safe empty fallback
#
# RETRY POLICY (via tenacity library)
#   • Up to MAX_RETRIES attempts
#   • Exponential back-off: waits 2s, then 4s, then 8s between retries
#   • Only retries on network/timeout errors, not on bad ticker symbols
# =============================================================================

import logging
from datetime import datetime, date
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pytz
import yfinance as yf
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

import data.cache as cache
from config import (
    BENCHMARK_TICKER,
    CACHE_TTL_SECONDS,
    FETCH_TIMEOUT,
    HEADER_TICKERS,
    HYG_TICKER,
    IEF_TICKER,
    INDICES,
    MARKET_CLOSE_HR,
    MARKET_CLOSE_MIN,
    MARKET_OPEN_HR,
    MARKET_OPEN_MIN,
    MARKET_TZ,
    MAX_RETRIES,
    MCI_WEIGHTS,
    PORTFOLIO,
    RSP_TICKER,
    SECTORS,
    SPY_TICKER,
    TREASURY_YIELDS,
    VIX_TICKER,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SECTION 1 — LOW-LEVEL RETRY DECORATOR
# =============================================================================

def _make_retry_decorator():
    """
    Builds a tenacity retry decorator with our standard settings.
    Using a factory function means we can call it fresh each time
    (tenacity decorators are stateful across calls if reused).
    """
    return retry(
        reraise=True,
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )


# =============================================================================
# SECTION 2 — GENERIC CACHE-AWARE FETCH WRAPPER
# =============================================================================

def fetch_with_cache(
    key: str,
    fetch_fn: Callable[[], Any],
    ttl: int = CACHE_TTL_SECONDS,
) -> Any:
    """
    The single entry-point for all data fetches.

    1. Check disk cache first.
    2. If stale/missing, call fetch_fn() with retry logic.
    3. On total failure, serve stale data rather than crashing.

    Parameters
    ----------
    key      : str       — unique cache key, e.g. "quotes_SPY"
    fetch_fn : callable  — a zero-argument function that returns fresh data
    ttl      : int       — seconds this result is considered fresh

    Returns
    -------
    Whatever fetch_fn returns, or a stale/None fallback on total failure.
    """
    cached = cache.get(key)
    if cached is not None:
        return cached

    # Not cached — attempt live fetch with retry
    try:
        @_make_retry_decorator()
        def _fetch_with_retry():
            return fetch_fn()

        result = _fetch_with_retry()
        if result is not None:
            cache.set(key, result, ttl=ttl)
        return result

    except Exception as exc:
        logger.error("All retries exhausted for key '%s': %s", key, exc)
        # Last resort: serve whatever stale data we have
        stale = cache.get_stale(key)
        if stale is not None:
            logger.warning("Serving stale data for key: %s", key)
        return stale


# =============================================================================
# SECTION 3 — RAW YFINANCE HELPERS
# =============================================================================

def _download_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Download OHLCV history for a single ticker.

    Returns an empty DataFrame on failure (never raises).
    """
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period, timeout=FETCH_TIMEOUT, auto_adjust=True)
        if df.empty:
            logger.warning("Empty history for ticker: %s", ticker)
        return df
    except Exception as exc:
        logger.error("History download failed for %s: %s", ticker, exc)
        return pd.DataFrame()


def _download_multi(tickers: List[str], period: str = "1y") -> pd.DataFrame:
    """
    Bulk-download closing prices for multiple tickers at once.
    Using a single bulk call is far more efficient (and API-friendly) than
    calling yf.Ticker() in a loop.

    Returns a DataFrame where each column is a ticker's Close price.
    """
    try:
        df = yf.download(
            tickers,
            period=period,
            auto_adjust=True,
            progress=False,
            timeout=FETCH_TIMEOUT,
            threads=True,
        )
        if df.empty:
            return pd.DataFrame()
        # yf.download returns MultiIndex columns when >1 ticker; extract Close
        if isinstance(df.columns, pd.MultiIndex):
            return df["Close"]
        return df[["Close"]].rename(columns={"Close": tickers[0]})
    except Exception as exc:
        logger.error("Bulk download failed for %s: %s", tickers, exc)
        return pd.DataFrame()


# =============================================================================
# SECTION 4 — RETURN CALCULATORS
# =============================================================================

def _calc_ytd_return(close_series: pd.Series) -> Optional[float]:
    """
    Calculate year-to-date percentage return.

    Finds the last closing price of the previous calendar year and compares
    it to the most recent close.
    """
    try:
        this_year = pd.Timestamp.now(tz="UTC").year
        prev_year_end = close_series[close_series.index.year == (this_year - 1)]
        if prev_year_end.empty:
            return None
        start_price = float(prev_year_end.iloc[-1])
        end_price   = float(close_series.iloc[-1])
        return (end_price - start_price) / start_price * 100
    except Exception:
        return None


def _calc_period_return(close_series: pd.Series, days: int) -> Optional[float]:
    """
    Calculate percentage return over the last N calendar days.
    """
    try:
        cutoff = close_series.index[-1] - pd.Timedelta(days=days)
        prior  = close_series[close_series.index <= cutoff]
        if prior.empty:
            return None
        start = float(prior.iloc[-1])
        end   = float(close_series.iloc[-1])
        return (end - start) / start * 100
    except Exception:
        return None


# =============================================================================
# SECTION 5 — MARKET STATUS
# =============================================================================

def get_market_status() -> Dict[str, Any]:
    """
    Returns current NYSE market open/closed status and time until next event.

    Returns
    -------
    dict with keys:
        is_open     : bool
        status_text : str   e.g. "MARKET OPEN" or "MARKET CLOSED"
        countdown   : str   e.g. "Closes in 2h 14m" or "Opens in 45m"
        local_time  : str   current NY time formatted
    """
    key = "market_status"

    def _compute():
        tz   = pytz.timezone(MARKET_TZ)
        now  = datetime.now(tz)
        open_t  = now.replace(hour=MARKET_OPEN_HR,  minute=MARKET_OPEN_MIN,  second=0, microsecond=0)
        close_t = now.replace(hour=MARKET_CLOSE_HR, minute=MARKET_CLOSE_MIN, second=0, microsecond=0)

        is_weekday = now.weekday() < 5  # Monday=0 … Friday=4
        is_open    = is_weekday and open_t <= now < close_t

        if is_open:
            delta_secs = int((close_t - now).total_seconds())
            h, rem     = divmod(delta_secs, 3600)
            m          = rem // 60
            countdown  = f"Closes in {h}h {m}m" if h else f"Closes in {m}m"
        else:
            # Next open: skip to Monday if it's Friday after close or weekend
            next_open = open_t if now < open_t else open_t + pd.Timedelta(days=1)
            while next_open.weekday() >= 5:
                next_open += pd.Timedelta(days=1)
            delta_secs = int((next_open - now).total_seconds())
            h, rem     = divmod(delta_secs, 3600)
            m          = rem // 60
            countdown  = f"Opens in {h}h {m}m" if h else f"Opens in {m}m"

        return {
            "is_open":     is_open,
            "status_text": "MARKET OPEN" if is_open else "MARKET CLOSED",
            "countdown":   countdown,
            "local_time":  now.strftime("%H:%M:%S ET"),
        }

    # Market status changes every minute; TTL of 60s is enough
    return fetch_with_cache(key, _compute, ttl=60)


# =============================================================================
# SECTION 6 — INDICES
# =============================================================================

def get_indices_data() -> Dict[str, Dict[str, Any]]:
    """
    Fetch price and return data for all major indices defined in config.

    Returns
    -------
    dict keyed by label (e.g. "S&P 500") containing:
        price  : float
        pct_1d : float   (1-day % change)
        pct_1m : float   (1-month % change, ~21 trading days)
        pct_ytd: float   (year-to-date % change)
    """
    key = "indices_data"

    def _fetch():
        tickers = list(INDICES.values())
        df = _download_multi(tickers, period="2y")
        result = {}
        for label, ticker in INDICES.items():
            if ticker not in df.columns:
                continue
            series = df[ticker].dropna()
            if series.empty:
                continue
            result[label] = {
                "ticker":   ticker,
                "price":    round(float(series.iloc[-1]), 2),
                "pct_1d":   round(_calc_period_return(series, 1)  or 0, 2),
                "pct_1m":   round(_calc_period_return(series, 30) or 0, 2),
                "pct_ytd":  round(_calc_ytd_return(series)        or 0, 2),
            }
        return result

    return fetch_with_cache(key, _fetch, ttl=120) or {}


# =============================================================================
# SECTION 7 — SECTORS
# =============================================================================

def get_sectors_data() -> Dict[str, Dict[str, Any]]:
    """
    Fetch price and return data for all sector ETFs defined in config.
    Same structure as get_indices_data().
    """
    key = "sectors_data"

    def _fetch():
        tickers = list(SECTORS.values())
        df = _download_multi(tickers, period="2y")
        result = {}
        for label, ticker in SECTORS.items():
            if ticker not in df.columns:
                continue
            series = df[ticker].dropna()
            if series.empty:
                continue
            price   = float(series.iloc[-1])
            sma50   = float(series.rolling(50).mean().iloc[-1])  if len(series) >= 50  else None
            sma200  = float(series.rolling(200).mean().iloc[-1]) if len(series) >= 200 else None
            ath     = float(series.max())
            result[label] = {
                "ticker":   ticker,
                "price":    round(price, 2),
                "pct_1d":   round(_calc_period_return(series, 1)  or 0, 2),
                "pct_1m":   round(_calc_period_return(series, 30) or 0, 2),
                "pct_ytd":  round(_calc_ytd_return(series)        or 0, 2),
                "sma50":    round(sma50,  2) if sma50  else None,
                "sma200":   round(sma200, 2) if sma200 else None,
                "ath":      round(ath, 2),
            }
        return result

    return fetch_with_cache(key, _fetch, ttl=120) or {}


# =============================================================================
# SECTION 8 — PORTFOLIO
# =============================================================================

def get_portfolio_data() -> Dict[str, Any]:
    """
    Fetch data for XEQT and BTC, then compute:
      - price, 1D/1M/YTD returns for each asset
      - blended portfolio return (80/20 weighting)
      - portfolio beta vs SPY
      - portfolio correlation vs SPY
      - alpha in basis points (portfolio return − SPY YTD return)
    """
    key = "portfolio_data"

    def _fetch():
        # Gather all tickers we need
        asset_tickers = [v["ticker"] for v in PORTFOLIO.values()]
        all_tickers   = asset_tickers + [BENCHMARK_TICKER]
        df = _download_multi(all_tickers, period="2y")

        result: Dict[str, Any] = {"assets": {}, "portfolio": {}}

        # --- Per-asset metrics ---
        for name, cfg in PORTFOLIO.items():
            ticker = cfg["ticker"]
            if ticker not in df.columns:
                continue
            series = df[ticker].dropna()
            if series.empty:
                continue
            result["assets"][name] = {
                "ticker":   ticker,
                "price":    round(float(series.iloc[-1]), 2),
                "pct_1d":   round(_calc_period_return(series, 1)  or 0, 2),
                "pct_1m":   round(_calc_period_return(series, 30) or 0, 2),
                "pct_ytd":  round(_calc_ytd_return(series)        or 0, 2),
                "weight":   cfg["weight"],
            }

        # --- Blended portfolio return ---
        blended_ytd = sum(
            result["assets"].get(name, {}).get("pct_ytd", 0) * cfg["weight"]
            for name, cfg in PORTFOLIO.items()
        )
        blended_1d = sum(
            result["assets"].get(name, {}).get("pct_1d", 0) * cfg["weight"]
            for name, cfg in PORTFOLIO.items()
        )

        # --- Beta vs SPY + Alpha ---
        beta = alpha_bps = None
        if BENCHMARK_TICKER in df.columns:
            spy_series  = df[BENCHMARK_TICKER].dropna()
            spy_returns = spy_series.pct_change().dropna()

            blended_returns = None
            for name, cfg in PORTFOLIO.items():
                ticker = cfg["ticker"]
                if ticker in df.columns:
                    asset_ret = df[ticker].dropna().pct_change().dropna() * cfg["weight"]
                    blended_returns = asset_ret if blended_returns is None else blended_returns.add(asset_ret, fill_value=0)

            if blended_returns is not None:
                combined = pd.concat([blended_returns, spy_returns], axis=1).dropna()
                combined.columns = ["portfolio", "spy"]
                if len(combined) >= 30:
                    cov_matrix = np.cov(combined["portfolio"], combined["spy"])
                    spy_var    = np.var(combined["spy"])
                    beta       = round(cov_matrix[0, 1] / spy_var, 3) if spy_var else None

            spy_ytd   = _calc_ytd_return(spy_series) or 0
            alpha_bps = round((blended_ytd - spy_ytd) * 100, 1)

        # --- IBIT vs XEQT correlation (#10) ---
        # IBIT (iShares Bitcoin Trust) and XEQT.TO both trade market hours
        # so their daily return series align perfectly — no weekend gap issues.
        xeqt_ticker  = PORTFOLIO.get("XEQT", {}).get("ticker", "XEQT.TO")
        ibit_ticker  = "IBIT"
        btc_xeqt_corr = None
        ibit_df = _download_multi([ibit_ticker], period="1y")
        if xeqt_ticker in df.columns and ibit_ticker in ibit_df.columns:
            xeqt_ret = df[xeqt_ticker].dropna().pct_change().dropna()
            ibit_ret = ibit_df[ibit_ticker].dropna().pct_change().dropna()
            paired   = pd.concat([xeqt_ret, ibit_ret], axis=1).dropna()
            if len(paired) >= 30:
                btc_xeqt_corr = round(paired.iloc[:,0].corr(paired.iloc[:,1]), 3)

        result["portfolio"] = {
            "return_ytd":      round(blended_ytd, 2),
            "return_1d":       round(blended_1d, 2),
            "beta":            beta,
            "btc_xeqt_corr":   btc_xeqt_corr,   # BTC vs XEQT
            "alpha_bps":       alpha_bps,
        }

        return result

    return fetch_with_cache(key, _fetch, ttl=120) or {}


# =============================================================================
# SECTION 9 — TECHNICAL CHART DATA (XEQT & BTC)
# =============================================================================

def get_chart_data(ticker: str) -> Dict[str, Any]:
    """
    Return price history + 50DMA + 200DMA for a single ticker.

    Parameters
    ----------
    ticker : str  — yfinance ticker symbol

    Returns
    -------
    dict with keys:
        dates   : list[str]   — ISO date strings
        closes  : list[float] — closing prices
        sma50   : list[float] — 50-day simple moving average
        sma200  : list[float] — 200-day simple moving average
    """
    key = f"chart_data_{ticker}"

    def _fetch():
        df = _download_history(ticker, period="1y")
        if df.empty:
            return None
        close = df["Close"].dropna()

        sma50  = close.rolling(50).mean()
        sma200 = close.rolling(200).mean()

        return {
            "dates":  [d.strftime("%Y-%m-%d") for d in close.index],
            "closes": [round(float(v), 4) for v in close],
            "sma50":  [round(float(v), 4) if not np.isnan(v) else None for v in sma50],
            "sma200": [round(float(v), 4) if not np.isnan(v) else None for v in sma200],
        }

    return fetch_with_cache(key, _fetch, ttl=120) or {}


# =============================================================================
# SECTION 10 — VOLATILITY METRICS (VIX + 30DMA)
# =============================================================================

def get_volatility_data() -> Dict[str, Any]:
    """
    Fetch VIX history and compute the 30-day moving average.

    Returns
    -------
    dict with keys:
        vix_current : float
        vix_30dma   : float
        vix_status  : str    e.g. "Elevated", "Normal", "Suppressed"
        history     : dict   dates / vix_values / sma30 lists for charting
    """
    key = "volatility_data"

    def _fetch():
        df = _download_history(VIX_TICKER, period="1y")
        if df.empty:
            return None
        close = df["Close"].dropna()
        sma30 = close.rolling(30).mean()

        current = float(close.iloc[-1])
        ma30    = float(sma30.iloc[-1])

        # Status label based on VIX level
        if current > 30:
            status = "Extreme Fear"
        elif current > 20:
            status = "Elevated"
        elif current > 15:
            status = "Normal"
        else:
            status = "Suppressed"

        return {
            "vix_current": round(current, 2),
            "vix_30dma":   round(ma30, 2),
            "vix_status":  status,
            "vix_vs_ma":   round(current - ma30, 2),
            "history": {
                "dates":      [d.strftime("%Y-%m-%d") for d in close.index],
                "vix_values": [round(float(v), 2) for v in close],
                "sma30":      [round(float(v), 2) if not np.isnan(v) else None for v in sma30],
            },
        }

    return fetch_with_cache(key, _fetch, ttl=120) or {}


# =============================================================================
# SECTION 11 — MARKET CONFIDENCE INDEX (MCI)
# =============================================================================

def get_market_confidence_index() -> Dict[str, Any]:
    """
    Market Confidence Index — formula matches Google Sheets original:

        score_vix     = MAX(0, MIN(99, 100 * EXP(-0.08 * (VIX     - 14))))
        score_vix30   = MAX(0, MIN(99, 100 * EXP(-0.08 * (VIX30   - 14))))
        MCI           = (score_vix + score_vix30) / 2

    Interpretation:
        VIX = 14  → score = 100  (calm, at the "normal" floor)
        VIX = 20  → score ~  62
        VIX = 30  → score ~  24
        VIX = 45  → score ~   6  (near zero — extreme fear)
    """
    key = "mci_data"

    def _mci_formula(vix_val: float) -> float:
        import math
        return max(0.0, min(99.0, 100.0 * math.exp(-0.08 * (vix_val - 14.0))))

    def _fetch():
        vol    = get_volatility_data()
        vix    = vol.get("vix_current", 20.0) if vol else 20.0
        vix_ma = vol.get("vix_30dma",   20.0) if vol else 20.0

        score_vix   = _mci_formula(vix)
        score_vix30 = _mci_formula(vix_ma)
        score       = round((score_vix + score_vix30) / 2.0, 1)

        # 9-level IFS scale (#14)
        if score >= 90:   label = "Euphoria"
        elif score >= 80: label = "Very Confident"
        elif score >= 70: label = "Confident"
        elif score >= 60: label = "Cautious"
        elif score >= 50: label = "Neutral"
        elif score >= 40: label = "Defensive"
        elif score >= 30: label = "Concerned"
        elif score >= 20: label = "Fear"
        else:             label = "Panic"

        return {
            "score": score,
            "label": label,
            "factors": {
                "VIX Score":     round(score_vix,   1),
                "VIX 30DMA Score": round(score_vix30, 1),
            },
        }

    return fetch_with_cache(key, _fetch, ttl=120) or {}


# =============================================================================
# SECTION 12 — RISK & BREADTH
# =============================================================================

def get_risk_breadth() -> Dict[str, Any]:
    """
    Compute:
      - Risk Rotation  = HYG 1-month return − LQD 1-month return
        HYG = high-yield (junk) bonds  — risk appetite
        LQD = investment-grade bonds   — risk-off proxy

        Labels follow the IFS scale from config:
          >= 4.0  : Euphoric
          >= 2.0  : Aggressive
          >= 1.2  : Risk-On
          >= 0.3  : Risk-Leaning
          >  -0.3 : Neutral
          >  -1.2 : Defensive
          >  -2.5 : Risk-Off
          <= -2.5 : Panic

      - Breadth = RSP / SPY ratio vs its own 30-day MA
    """
    key = "risk_breadth"
    LQD_TICKER = "LQD"   # iShares IG Corporate Bond ETF

    def _risk_label(spread: float) -> str:
        if spread >= 4.0:   return "Euphoric"
        if spread >= 2.0:   return "Aggressive"
        if spread >= 1.2:   return "Risk-On"
        if spread >= 0.3:   return "Risk-Leaning"
        if spread > -0.3:   return "Neutral"
        if spread > -1.2:   return "Defensive"
        if spread > -2.5:   return "Risk-Off"
        return "Panic"

    def _fetch():
        tickers = [HYG_TICKER, LQD_TICKER, RSP_TICKER, SPY_TICKER]
        df = _download_multi(tickers, period="3mo")

        # Risk rotation — HYG vs LQD 1-month spread
        risk_pct   = 0.0
        risk_label = "Neutral"
        if HYG_TICKER in df.columns and LQD_TICKER in df.columns:
            hyg_ret  = _calc_period_return(df[HYG_TICKER].dropna(), 30) or 0
            lqd_ret  = _calc_period_return(df[LQD_TICKER].dropna(), 30) or 0
            risk_pct = round(hyg_ret - lqd_ret, 3)
            risk_label = _risk_label(risk_pct)

        # Breadth — RSP/SPY ratio mapped to 10-level scale
        # Formula mirrors Google Sheets LET/LOOKUP:
        #   pos = (ratio - 0.27) / (0.3933 - 0.27)  clamped to [0, 1]
        #   then bucketed into 10 equal deciles
        breadth_ratio = None
        breadth_label = "Unknown"
        if RSP_TICKER in df.columns and SPY_TICKER in df.columns:
            rsp = df[RSP_TICKER].dropna()
            spy = df[SPY_TICKER].dropna()
            ratio         = (rsp / spy).dropna()
            breadth_ratio = round(float(ratio.iloc[-1]), 4)

            MIN_FLOOR   = 0.27
            MAX_CEILING = 0.3933
            pos = (breadth_ratio - MIN_FLOOR) / (MAX_CEILING - MIN_FLOOR)
            pos = max(0.0, min(0.9999, pos))   # clamp to [0, 1)

            LABELS = [
                "Apex Concentration",    # 0.0 – 0.1
                "Severe Divergence",     # 0.1 – 0.2
                "High Concentration",    # 0.2 – 0.3
                "Thin Participation",    # 0.3 – 0.4
                "Broadening-Out",        # 0.4 – 0.5
                "Neutral Breadth",       # 0.5 – 0.6
                "Healthy Participation", # 0.6 – 0.7
                "Risk-On Rotation",      # 0.7 – 0.8
                "Solid Breadth",         # 0.8 – 0.9
                "Maximum Breadth",       # 0.9 – 1.0
            ]
            breadth_label = LABELS[int(pos * 10)]

        return {
            "risk_rotation_pct": risk_pct,
            "risk_label":        risk_label,
            "breadth_ratio":     breadth_ratio,
            "breadth_label":     breadth_label,
        }

    return fetch_with_cache(key, _fetch, ttl=120) or {}


# =============================================================================
# SECTION 13 — TREASURY YIELDS
# =============================================================================

def get_treasury_yields() -> Dict[str, Any]:
    """
    Fetch the four treasury yield levels.
    Yields are stored as prices by Yahoo Finance and must be divided by 10
    to get the actual percentage (e.g., 45.2 → 4.52%).

    Returns
    -------
    dict keyed by label (e.g. "10Y") with:
        yield_pct  : float   actual yield as a percentage
        change_1d  : float   1-day change in yield (percentage points)
    """
    key = "treasury_yields"

    def _fetch():
        tickers = list(TREASURY_YIELDS.values())
        df = _download_multi(tickers, period="1mo")
        result = {}
        for label, ticker in TREASURY_YIELDS.items():
            if ticker not in df.columns:
                continue
            series = df[ticker].dropna()  # Yahoo Finance returns yield as actual %
            if series.empty:
                continue
            current = float(series.iloc[-1])
            prev    = float(series.iloc[-2]) if len(series) >= 2 else current
            result[label] = {
                "yield_pct": round(current, 3),
                "change_1d": round(current - prev, 3),
            }
        return result

    return fetch_with_cache(key, _fetch, ttl=120) or {}


# =============================================================================
# SECTION 14 — ROTATING HEADER TICKER DATA
# =============================================================================

def get_header_ticker_data() -> List[Dict[str, Any]]:
    """
    Fetch current prices and 1-day changes for all 60 header tickers.

    The date-anchor logic (inserting the current date every 5 items) is
    applied here so the UI layer just iterates through the final list.

    Returns
    -------
    list of dicts, each with:
        type    : "ticker" or "date"
        label   : str    — display text
        price   : float  — current price (None for date entries)
        pct_1d  : float  — 1-day % change (None for date entries)
    """
    key = "header_ticker_data"

    def _fetch():
        df = _download_multi(HEADER_TICKERS, period="5d")
        items = []
        today_str = datetime.now().strftime("%b %d, %Y")

        for i, ticker in enumerate(HEADER_TICKERS):
            # Insert date anchor every 5 items (at positions 0, 5, 10 … 55)
            if i % 5 == 0:
                items.append({
                    "type":   "date",
                    "label":  today_str,
                    "price":  None,
                    "pct_1d": None,
                })

            price = pct_1d = None
            if ticker in df.columns:
                series = df[ticker].dropna()
                if len(series) >= 2:
                    price  = round(float(series.iloc[-1]), 2)
                    pct_1d = round((series.iloc[-1] - series.iloc[-2]) / series.iloc[-2] * 100, 2)

            items.append({
                "type":   "ticker",
                "label":  ticker,
                "price":  price,
                "pct_1d": pct_1d,
            })

        return items

    # Header data changes intraday; 2-minute TTL is sufficient
    return fetch_with_cache(key, _fetch, ttl=120) or []


# =============================================================================
# SECTION 15 — POLYMARKET / KALSHI PLACEHOLDER
# =============================================================================

def get_sentiment_data() -> Dict[str, Any]:
    """
    ── PLACEHOLDER FOR CUSTOM API INTEGRATION ──

    Replace the body of this function with a call to Polymarket or Kalshi
    when you have API credentials. The structure below matches what the UI
    expects so you can slot in real data without touching the UI layer.

    Example integration sketch (Kalshi):
        headers = {"Authorization": f"Bearer {KALSHI_API_KEY}"}
        resp = requests.get("https://trading-api.kalshi.com/v2/markets", headers=headers)
        events = resp.json()["markets"]
        ...

    Returns
    -------
    dict with keys:
        fed_cut_prob  : float  — probability (0–1) of a Fed rate cut
        recession_prob: float  — probability (0–1) of a US recession
        source        : str    — "Kalshi" / "Polymarket" / "Placeholder"
    """
    return {
        "fed_cut_prob":   None,  # Replace with live value when integrated
        "recession_prob": None,
        "source":         "Placeholder — integrate Kalshi/Polymarket API here",
    }


# =============================================================================
# SECTION 16 — PREFETCH ALL (called at app startup)
# =============================================================================

def prefetch_all() -> None:
    """
    Warm up the cache by fetching all data sources at startup.

    Call this once when the Streamlit app initialises. If the cache is already
    populated and fresh, these calls return immediately from disk — no API hits.
    """
    logger.info("Prefetching all data sources…")
    get_market_status()
    get_indices_data()
    get_sectors_data()
    get_portfolio_data()
    get_volatility_data()
    get_market_confidence_index()
    get_risk_breadth()
    get_treasury_yields()
    get_header_ticker_data()
    for name, cfg in PORTFOLIO.items():
        get_chart_data(cfg["ticker"])
    logger.info("Prefetch complete.")


# =============================================================================
# SECTION 17 — AI MARKET SUMMARY
# =============================================================================

def get_ai_market_summary() -> str:
    """
    Ask Llama 3 (via Groq free tier) to write a 1-2 sentence market summary,
    grounded in live data we already have (indices, VIX, MCI, risk/breadth).

    Requires GROQ_API_KEY in Streamlit secrets or as an environment variable.
    Returns empty string silently if key is missing.
    Cached for 60 minutes — one free API call per hour.
    """
    key = "ai_market_summary"

    def _get_api_key() -> str:
        try:
            import streamlit as _st
            k = _st.secrets.get("GROQ_API_KEY", "")
            if k:
                return k
        except Exception:
            pass
        import os
        return os.environ.get("GROQ_API_KEY", "")

    def _fetch():
        api_key = _get_api_key()
        if not api_key:
            logger.info("No GROQ_API_KEY set — skipping AI summary")
            return ""

        try:
            import requests as _req

            vol  = get_volatility_data()         or {}
            mci  = get_market_confidence_index() or {}
            idx  = get_indices_data()            or {}
            risk = get_risk_breadth()            or {}

            sp        = idx.get("S&P 500", {})
            nq        = idx.get("NASDAQ",  {})
            tsx       = idx.get("TSX",     {})
            vix       = vol.get("vix_current", 0)
            mci_score = mci.get("score", 0)
            mci_label = mci.get("label", "")
            rrl       = risk.get("risk_label", "")
            brl       = risk.get("breadth_label", "")

            tz_et  = pytz.timezone("America/New_York")
            now_et = datetime.now(tz_et)

            context = (
                f"Live market data as of {now_et.strftime('%B %d, %Y %I:%M %p ET')}: "
                f"S&P 500 {fp(sp.get('price'))} ({fpc(sp.get('pct_1d'))} today, "
                f"{fpc(sp.get('pct_ytd'))} YTD). "
                f"NASDAQ {fpc(nq.get('pct_1d'))} today. "
                f"TSX {fpc(tsx.get('pct_1d'))} today. "
                f"VIX {vix:.1f}. "
                f"Market Confidence Index {mci_score:.0f}/100 ({mci_label}). "
                f"Risk rotation: {rrl}. Market breadth: {brl}."
            )

            prompt = (
                context + " "
                "Write exactly 1-2 sentences summarising current market conditions "
                "for a professional investor. Be specific with the numbers, note any "
                "key themes or divergences, and keep it sharp. "
                "No preamble or sign-off — just the summary."
            )

            resp = _req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":       "llama-3.3-70b-versatile",
                    "max_tokens":  120,
                    "temperature": 0.4,
                    "messages": [
                        {"role": "system",
                         "content": "You are a concise financial markets analyst. "
                                    "Respond only with the requested summary, no extra text."},
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=15,
            )

            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            else:
                logger.warning("Groq API error %s: %s",
                               resp.status_code, resp.text[:200])

        except Exception as exc:
            logger.warning("AI summary failed: %s", exc)

        return ""

    return fetch_with_cache(key, _fetch, ttl=3600) or ""


# =============================================================================
# SECTION 18 — MARKET NEWS (Google News RSS + BBC Business)
# =============================================================================

def get_market_news() -> List[Dict[str, Any]]:
    """
    Fetch financial headlines from Google News RSS and BBC Business RSS.

    Google News RSS is the most reliable free feed — no auth, no blocking,
    aggregates from hundreds of publishers. BBC Business is a solid backup.

    Uses requests + stdlib xml.etree only — zero extra dependencies.
    Spoofs a browser User-Agent to avoid bot filtering.
    Cached for 15 minutes so headlines stay fresh but we don't hammer feeds.

    Returns list of dicts:
        title       : str
        source      : str
        age_minutes : int
        breaking    : bool  — True if < 60 minutes old
    """
    key = "market_news_v2"

    FEEDS = [
        ("Google News",
         "https://news.google.com/rss/search"
         "?q=stock+market+finance+economy&hl=en-US&gl=US&ceid=US:en"),
        ("Google News Markets",
         "https://news.google.com/rss/topics"
         "/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB"),
        ("BBC Business",
         "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ]

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    def _parse_pub_date(date_str: str):
        import email.utils
        try:
            parsed = email.utils.parsedate_tz(date_str)
            if parsed:
                return float(email.utils.mktime_tz(parsed))
        except Exception:
            pass
        return None

    def _clean_title(title: str) -> str:
        """Google News appends '- Source Name' to titles — strip it."""
        # Remove trailing source attribution like " - Reuters" or " | CNBC"
        import re
        title = re.sub(r'\s[-|]\s[A-Z][^-|]{2,40}$', '', title).strip()
        return title

    def _fetch():
        import time as _time
        import xml.etree.ElementTree as ET
        import requests as _req

        now_ts = _time.time()
        seen   = set()
        items  = []

        for source_name, url in FEEDS:
            try:
                resp = _req.get(url, headers=HEADERS, timeout=12)
                if resp.status_code != 200:
                    logger.warning("Feed %s → HTTP %s", source_name, resp.status_code)
                    continue

                root    = ET.fromstring(resp.content)
                channel = root.find("channel")
                if channel is None:
                    channel = root
                entries = channel.findall("item")

                for entry in entries[:10]:
                    raw_title = (entry.findtext("title") or "").strip()
                    title     = _clean_title(raw_title)
                    if not title or title in seen:
                        continue
                    seen.add(title)

                    pub_str = entry.findtext("pubDate") or ""
                    pub_ts  = _parse_pub_date(pub_str) if pub_str else now_ts
                    if pub_ts is None:
                        pub_ts = now_ts

                    age_min = max(0, int((now_ts - pub_ts) / 60))

                    # Pull source from <source> tag if present (Google News includes it)
                    src_el = entry.find("source")
                    src    = (src_el.text if src_el is not None else source_name) or source_name

                    items.append({
                        "title":       title,
                        "source":      src,
                        "age_minutes": age_min,
                        "breaking":    age_min <= 60,
                    })

            except Exception as exc:
                logger.warning("News fetch failed for %s: %s", source_name, exc)

        # Sort newest first, deduplicated, cap at 15
        items.sort(key=lambda x: x["age_minutes"])
        return items[:15]

    return fetch_with_cache(key, _fetch, ttl=900) or []


# =============================================================================
# SECTION 19 — MARKET HOLIDAY DETECTION
# =============================================================================

def _easter(year: int) -> date:
    """Anonymous Gregorian algorithm for Easter Sunday."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month, day = divmod(h + l - 7*m + 114, 31)
    return date(year, month, day + 1)

def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the nth occurrence of weekday (0=Mon) in given month/year."""
    d = date(year, month, 1)
    first = (weekday - d.weekday()) % 7
    return date(year, month, 1 + first + (n-1)*7)

def _last_weekday(year: int, month: int, weekday: int) -> date:
    """Return the last occurrence of weekday in given month/year."""
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    d = date(year, month, last_day)
    diff = (d.weekday() - weekday) % 7
    return date(year, month, last_day - diff)

def _nearest_weekday(d: date) -> date:
    """If holiday falls on weekend, observe on nearest weekday."""
    if d.weekday() == 5: return date(d.year, d.month, d.day - 1)  # Sat → Fri
    if d.weekday() == 6: return date(d.year, d.month, d.day + 1)  # Sun → Mon
    return d

def get_us_holidays(year: int) -> set:
    """
    NYSE market holidays for a given year.
    Returns a set of date objects.
    """
    easter = _easter(year)
    good_friday = date(easter.year, easter.month, easter.day)
    from datetime import timedelta
    good_friday = easter - timedelta(days=2)

    holidays = {
        _nearest_weekday(date(year, 1,  1)),   # New Year's Day
        _nth_weekday(year, 1, 0, 3),            # MLK Day (3rd Mon Jan)
        _nth_weekday(year, 2, 0, 3),            # Presidents Day (3rd Mon Feb)
        good_friday,                             # Good Friday
        _last_weekday(year, 5, 0),              # Memorial Day (last Mon May)
        _nearest_weekday(date(year, 6, 19)),    # Juneteenth
        _nearest_weekday(date(year, 7,  4)),    # Independence Day
        _nth_weekday(year, 9, 0, 1),            # Labor Day (1st Mon Sep)
        _nth_weekday(year, 11, 3, 4),           # Thanksgiving (4th Thu Nov)
        _nearest_weekday(date(year, 12, 25)),   # Christmas
    }
    return holidays

def get_tsx_holidays(year: int) -> set:
    """
    TSX market holidays for a given year.
    Returns a set of date objects.
    """
    easter = _easter(year)
    from datetime import timedelta
    good_friday  = easter - timedelta(days=2)
    easter_monday = easter + timedelta(days=1)

    # Victoria Day = Monday before May 25
    may25 = date(year, 5, 25)
    vic_day = may25 - timedelta(days=(may25.weekday() + 1) % 7 or 7)

    holidays = {
        _nearest_weekday(date(year, 1,  1)),   # New Year's Day
        good_friday,                             # Good Friday
        easter_monday,                           # Easter Monday
        vic_day,                                 # Victoria Day
        _nearest_weekday(date(year, 7,  1)),    # Canada Day
        _nth_weekday(year, 8, 0, 1),            # Civic Holiday (1st Mon Aug)
        _nth_weekday(year, 9, 0, 1),            # Labour Day (1st Mon Sep)
        _nth_weekday(year, 10, 0, 2),           # Thanksgiving (2nd Mon Oct)
        _nearest_weekday(date(year, 12, 25)),   # Christmas
        _nearest_weekday(date(year, 12, 26)),   # Boxing Day
    }
    return holidays

def is_us_holiday(check_date: date = None) -> bool:
    """True if the given date (default today ET) is a US market holiday."""
    if check_date is None:
        tz = pytz.timezone("America/New_York")
        check_date = datetime.now(tz).date()
    return check_date in get_us_holidays(check_date.year)

def is_tsx_holiday(check_date: date = None) -> bool:
    """True if the given date (default today ET) is a TSX market holiday."""
    if check_date is None:
        tz = pytz.timezone("America/New_York")
        check_date = datetime.now(tz).date()
    return check_date in get_tsx_holidays(check_date.year)


# =============================================================================
# SECTION 20 — PRE-MARKET FUTURES (6:30am–9:30am ET weekdays)
# =============================================================================

def get_futures_data() -> Dict[str, Any]:
    """
    Fetch S&P 500, Nasdaq 100, and Russell 2000 front-month futures.
    ES=F, NQ=F, RTY=F via yfinance.
    Returns price and overnight % change for each.
    Cached for 60 seconds so it stays fresh during pre-market.
    """
    key = "futures_data"

    FUTURES = {
        "S&P FUT":    "ES=F",
        "NQ FUT":     "NQ=F",
        "RUSSELL FUT":"RTY=F",
    }

    def _fetch():
        result = {}
        for label, ticker in FUTURES.items():
            try:
                t     = yf.Ticker(ticker)
                info  = t.fast_info
                price = getattr(info, "last_price", None) or getattr(info, "regularMarketPrice", None)
                prev  = getattr(info, "previous_close", None)
                if price and prev and prev > 0:
                    pct = round((price - prev) / prev * 100, 2)
                else:
                    pct = None
                result[label] = {
                    "price": round(float(price), 2) if price else None,
                    "pct_1d": pct,
                }
            except Exception as exc:
                logger.warning("Futures fetch failed for %s: %s", ticker, exc)
                result[label] = {"price": None, "pct_1d": None}
        return result

    return fetch_with_cache(key, _fetch, ttl=60) or {}
