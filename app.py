# =============================================================================
# app.py  —  MARKET TERMINAL  v10 restored + basis points yields
# =============================================================================
from datetime import datetime
import pytz
import streamlit as st
from config import PORTFOLIO, FOREX_TICKERS
from data.fetcher import (
    get_header_ticker_data, get_indices_data,
    get_market_confidence_index, get_market_status, get_portfolio_data,
    get_risk_breadth, get_sectors_data, get_treasury_yields,
    get_volatility_data, get_ai_market_summary, get_market_news,
    get_chart_data, prefetch_all,
    is_us_holiday, is_tsx_holiday,
    get_futures_data,
    get_ibit_btc_data,
)

st.set_page_config(page_title="MARKET TERMINAL", layout="wide",
                   initial_sidebar_state="collapsed")

# Auto-recover from errors instead of white screen
st.config.set_option("runner.fastReruns", True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');

#MainMenu,footer,header,[data-testid="stToolbar"],
[data-testid="stHeader"],.stDeployButton { display:none !important; }

.stApp { background:#060606 !important; padding-top:0 !important; margin-top:0 !important; }
.main .block-container { padding:0 !important; max-width:100% !important; margin-top:0 !important; }
.stApp > div { padding-top:0 !important; margin-top:0 !important; }
section.main > div { padding-top:0 !important; }
div[data-testid="stAppViewContainer"] { padding-top:0 !important; margin-top:0 !important; }
div[data-testid="stAppViewBlockContainer"] { padding-top:0 !important; margin-top:0 !important; }
div[data-testid="block-container"] { padding-top:0 !important; margin-top:0 !important; }
div[data-testid="stAppViewContainer"] > section { padding-top:0 !important; }
.appview-container .main .block-container { padding-top:0 !important; margin-top:0 !important; }
[data-testid="stHorizontalBlock"] { gap:0 !important; padding:0 !important; }
[data-testid="column"]>div        { padding:0 !important; }
[data-testid="stVerticalBlock"]   { gap:0 !important; }
.element-container { margin:0 !important; padding:0 !important; }
.stMarkdown        { margin:0 !important; padding:0 !important; }
::-webkit-scrollbar { display:none; }

* { font-family:'Roboto',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important; box-sizing:border-box; }
/* All elements use DM Serif Display via universal rule above */

/* TICKER */
.tkr-outer {
  width:100vw; position:relative; left:50%; transform:translateX(-50%);
  overflow:hidden; background:#000;
  border-top:2px solid #00e676; border-bottom:2px solid #333333; padding:11px 0;
}
.tkr-track { display:inline-block; white-space:nowrap; animation:tkr 240s linear infinite; }
.tkr-track:hover { animation-play-state:paused; }
@keyframes tkr { 0%{transform:translateX(0);} 100%{transform:translateX(-50%);} }
.ti   { display:inline-flex; align-items:baseline; gap:8px; margin:0 26px; font-size:17px; }
.ti-s { color:#fff; font-weight:700; font-size:17px; }
.ti-p { color:#b0b0b0; font-size:14px; }
.ti-c { font-weight:700; font-size:17px; }
.td   { display:inline-block; margin:0 18px; font-size:12px; color:#00bcd4;
        background:#011; padding:2px 10px; border:1px solid #0d3d4a;
        border-radius:2px; font-weight:600; vertical-align:middle; }

/* CARD */
.card     { background:#090909; border:1px solid #2e2e2e; padding:13px 14px; height:100%; }
.card-hdr { font-size:10px; font-weight:700; letter-spacing:1.5px; color:#e8e8e8;
            text-transform:uppercase; padding-bottom:7px; margin-bottom:9px;
            border-bottom:1px solid #2a2a2a; display:flex;
            justify-content:space-between; align-items:center; }

/* INDICES ROW */
.idx-row  { display:flex; width:100%; background:#090909; border-top:2px solid #404040; border-bottom:2px solid #333333; }
.idx-cell { flex:1; padding:13px 10px; text-align:center; border-right:1px solid #2e2e2e; }
.idx-cell:last-of-type { border-right:none; }
.idx-lbl  { font-size:11px; color:#d0d0d0; letter-spacing:1.5px; text-transform:uppercase; margin-bottom:5px; font-weight:600; }
.idx-pct  { font-size:30px; font-weight:800; line-height:1; }
.idx-px   { font-size:13px; color:#c0c0c0; margin-top:5px; }
.clock-cell { width:190px; flex-shrink:0; padding:13px 14px; display:flex;
  flex-direction:column; justify-content:center; align-items:center;
  border-left:2px solid #1e1e1e; background:#090909; }
.clock-time { font-size:38px; font-weight:800; color:#fff; line-height:1; text-align:center; }
.clock-sub  { font-size:11px; color:#c0c0c0; letter-spacing:2px; margin-top:5px; font-weight:500; }
.mkt-cell { width:210px; flex-shrink:0; padding:13px 14px; display:flex;
  align-items:center; justify-content:center;
  border-left:2px solid #1e1e1e; background:#090909; }
.mkt-open   { background:#011501; border:2px solid #00e676; padding:7px 16px; width:100%; text-align:center; }
.mkt-closed { background:#150101; border:2px solid #ff1744; padding:7px 16px; width:100%; text-align:center; }
.mkt-pre    { background:#1a1500; border:2px solid #ffd54f; padding:7px 16px; width:100%; text-align:center; }
.mkt-after  { background:#1a1500; border:2px solid #ffd54f; padding:7px 16px; width:100%; text-align:center; }
.mkt-s  { font-size:16px; font-weight:800; letter-spacing:0.5px; }
.mkt-cd { font-size:13px; font-weight:500; margin-top:5px; color:#cccccc; }

/* MODE BAR */
.mode-bar { background:#060606; padding:7px 14px; border-bottom:2px solid #333333;
            display:flex; align-items:center; gap:12px; }
.mode-label { font-size:12px; color:#aaaaaa; letter-spacing:1.5px; font-weight:600; }
.mode-1d  { font-size:20px; font-weight:800; letter-spacing:2px; color:#00e676; border-bottom:3px solid #00e676; padding-bottom:1px; }
.mode-1m  { font-size:20px; font-weight:800; letter-spacing:2px; color:#00bcd4; border-bottom:3px solid #00bcd4; padding-bottom:1px; }
.mode-ytd { font-size:20px; font-weight:800; letter-spacing:2px; color:#ffd54f; border-bottom:3px solid #ffd54f; padding-bottom:1px; }

/* MCI */
.mci-num { font-size:90px; font-weight:900; line-height:1; text-align:center; letter-spacing:-4px; }
.mci-lbl { font-size:20px; font-weight:700; text-align:center; letter-spacing:1px; margin-top:2px; }
.vix-duo { display:flex; justify-content:space-between; margin-top:18px; padding-top:16px; border-top:1px solid #1a1a1a; gap:8px; }
.vix-blk { text-align:center; flex:1; background:#0d0d0d; border:1px solid #2a2a2a; border-radius:3px; padding:12px 8px; }
.vix-l   { font-size:11px; color:#888; letter-spacing:1px; margin-bottom:8px; font-weight:600; text-transform:uppercase; }
.vix-v   { font-size:36px; font-weight:800; color:#ffffff; line-height:1; }

/* PORTFOLIO */
.stats-row { display:flex; gap:7px; margin-bottom:9px; }
.stat-box  { flex:1; background:#0d0d0d; border:1px solid #2a2a2a; border-radius:3px; padding:7px 10px; }
.stat-lbl  { font-size:11px; color:#cccccc; letter-spacing:1px; text-transform:uppercase; margin-bottom:3px; font-weight:600; }
.stat-val  { font-size:22px; font-weight:700; }
.pt-hd     { display:grid; grid-template-columns:1fr 1.1fr 1fr 1fr;
             font-size:11px; color:#cccccc; letter-spacing:1px; text-transform:uppercase;
             padding-bottom:7px; border-bottom:1px solid #2a2a2a; font-weight:600; }
.pt-r      { display:grid; grid-template-columns:1fr 1.1fr 1fr 1fr;
             padding:14px 0; border-bottom:1px solid #1e1e1e; align-items:center; }
.pt-r:last-child { border-bottom:none; }
.pt-sym    { font-size:34px; font-weight:700; color:#fff; }
.pt-px     { font-size:31px; font-weight:600; transition:color .4s ease; }
.pt-ch     { font-size:31px; font-weight:700; }
.pt-ret    { font-size:40px; font-weight:700; text-align:right; line-height:1; }
.pt-wt     { font-size:12px; color:#cccccc; text-align:right; margin-top:5px; font-weight:500; letter-spacing:.5px; }

/* SECTORS */
.sec-grid { display:grid; grid-template-columns:1fr 1fr; }
.sec-r    { display:flex; justify-content:space-between; align-items:center;
            padding:7px 4px; border-bottom:1px solid #1e1e1e; }
.sec-r:last-child { border-bottom:none; }
.sec-n    { font-size:15px; font-weight:500; }
.sec-pct  { font-weight:700; font-size:15px; text-align:right; }
.sec-grid>div:first-child .sec-r { padding-right:12px; border-right:1px solid #2a2a2a; }
.sec-grid>div:last-child  .sec-r { padding-left:12px; }

/* RISK / BREADTH */
.big-wrap { text-align:center; padding:4px 0; }
.big-num  { font-size:54px; font-weight:900; letter-spacing:-2px; line-height:1; margin:8px 0 4px; color:#ffffff; }
.big-sub  { font-size:13px; color:#cccccc; letter-spacing:1px; font-weight:500; }
.big-chg  { font-size:18px; font-weight:700; margin-top:8px; }
.tag      { display:inline-block; font-size:12px; font-weight:700; letter-spacing:.5px; padding:4px 12px; border-radius:4px; margin-top:8px; }
.tag-on   { background:#011f01; color:#00e676; border:1px solid #005500; }
.tag-agg  { background:#002200; color:#00ff88; border:1px solid #007700; }
.tag-euph { background:#001a00; color:#39ff14; border:1px solid #005500; }
.tag-lean { background:#071a07; color:#66bb6a; border:1px solid #2e7d32; }
.tag-neu  { background:#0a0e10; color:#90a4ae; border:1px solid #37474f; }
.tag-def  { background:#1a1200; color:#ffb300; border:1px solid #664d00; }
.tag-off  { background:#1f0101; color:#ff1744; border:1px solid #550000; }
.tag-pan  { background:#2a0000; color:#ff0000; border:1px solid #880000; }
.tag-apc  { background:#1a0e00; color:#ffd54f; border:1px solid #553300; }
.tag-nar  { background:#161000; color:#ffd54f; border:1px solid #443300; }

/* YIELDS */
.y-hd  { display:grid; grid-template-columns:1.4fr 1fr 0.9fr;
          font-size:11px; color:#cccccc; letter-spacing:1px; text-transform:uppercase;
          padding-bottom:8px; border-bottom:1px solid #2a2a2a; font-weight:600; }
.y-row { display:grid; grid-template-columns:1.4fr 1fr 0.9fr;
          padding:8px 0; border-bottom:1px solid #1e1e1e; align-items:center; }
.y-row:last-child { border-bottom:none; }
.y-n   { color:#e8e8e8; font-size:15px; font-weight:500; }
.y-r   { font-size:19px; font-weight:700; color:#fff; text-align:center; }
.y-bp  { font-size:13px; font-weight:700; text-align:right;
}

/* COLOURS */
.pos { color:#00e676 !important; } .neg { color:#ff1744 !important; }
.acc { color:#00bcd4 !important; } .gld { color:#ffd54f !important; }
.org { color:#ff6d00 !important; }
.t0  { color:#ffffff !important; } .t1  { color:#c0c0c0 !important; }
.t2  { color:#707070 !important; }

/* BADGE */
.mb     { display:inline-block; font-size:8px; font-weight:700; letter-spacing:1px;
          padding:2px 7px; border-radius:3px; text-transform:uppercase; }
.mb-1d  { background:#061a06; color:#00e676; border:1px solid #0d3d0d; }
.mb-1m  { background:#040f1a; color:#00bcd4; border:1px solid #0d2b3d; }
.mb-ytd { background:#1a1204; color:#ffd54f; border:1px solid #3d2d0d; }

/* FLASH ANIMATIONS */
@keyframes flash-pos {
  0%   { background:rgba(0,230,118,.2); }
  100% { background:transparent; }
}
@keyframes flash-neg {
  0%   { background:rgba(255,23,68,.2); }
  100% { background:transparent; }
}
.flash-pos { animation:flash-pos 1s ease-out forwards; border-radius:3px; padding:0 3px; }
.flash-neg { animation:flash-neg 1s ease-out forwards; border-radius:3px; padding:0 3px; }

/* BREAKING PULSE */
@keyframes breaking-pulse {
  0%,100% { opacity:1; box-shadow:0 0 8px rgba(255,23,68,.8); }
  50%      { opacity:.75; box-shadow:0 0 18px rgba(255,23,68,1), 0 0 30px rgba(255,23,68,.4); }
}
.breaking-badge { animation:breaking-pulse 1.2s ease-in-out infinite; }

/* HIDE FRAGMENT REFRESH FLICKER */
[data-testid="stSpinner"] { display:none !important; }
div[data-testid="stStatusWidget"] { display:none !important; }

/* Kill the dark overlay that appears during fragment re-renders */
[data-testid="stAppViewBlockContainer"] > div > div[style*="opacity"] {
    opacity:1 !important;
    transition:none !important;
}
div[class*="overlay"],
div[class*="loading"],
div[class*="skeleton"] {
    display:none !important;
    opacity:0 !important;
}

/* 2.5 SIGMA FLASH ANIMATIONS */
@keyframes sigma-glow-pos {
  0%,100% { background:transparent; }
  50%      { background:rgba(0,230,118,.35); border-radius:4px; }
}
@keyframes sigma-glow-neg {
  0%,100% { background:transparent; }
  50%      { background:rgba(255,23,68,.35); border-radius:4px; }
}
.mci-sigma-pos { animation:sigma-glow-pos 1.2s ease-in-out infinite; padding:0 4px; border-radius:4px; }
.mci-sigma-neg { animation:sigma-glow-neg 1.2s ease-in-out infinite; padding:0 4px; border-radius:4px; }

/* NIGHT MODE */
.night-screen { position:fixed; top:0; left:0; width:100vw; height:100vh;
  background:#000; z-index:9999; display:flex; align-items:center;
  justify-content:center; flex-direction:column; gap:8px; }
.night-clock { font-family:'Roboto',sans-serif !important;
  font-size:120px; font-weight:700; color:#c0c0c0; letter-spacing:-4px; line-height:1; }
.night-sub   { font-size:16px; color:#888888; letter-spacing:4px; font-weight:500; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HELPERS
# =============================================================================
def fp(v, d=2):
    if v is None: return "—"
    if abs(v) >= 10000: return f"{v:,.0f}"
    if abs(v) >= 1000:  return f"{v:,.{d}f}"
    return f"{v:.{d}f}"

def fpc(v, d=2):
    if v is None: return "—"
    return f"{abs(v):.{d}f}%"

def fpbp(v):
    """Convert yield % change to basis points. 1bp = 0.01%"""
    if v is None: return "—"
    bp = round(v * 100, 1)
    return f"{bp:+.0f} bp"

def cl(v):
    if v is None: return "t2"
    return "pos" if v >= 0 else "neg"

def ar(v):
    if v is None: return ""
    return "▲" if v >= 0 else "▼"

def get_mode():
    if "mode" not in st.session_state:
        sync_mode()
    return st.session_state.mode

def sync_mode():
    m = datetime.now().minute % 30
    if m < 20:   st.session_state.mode = "1D"
    elif m < 25: st.session_state.mode = "1M"
    else:        st.session_state.mode = "YTD"

def mk(m): return {"1D":"pct_1d","1M":"pct_1m","YTD":"pct_ytd"}[m]

def badge(m):
    c = {"1D":"mb-1d","1M":"mb-1m","YTD":"mb-ytd"}[m]
    return f'<span class="mb {c}">{m}</span>'

def get_session() -> str:
    tz  = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    if now.weekday() >= 5: return "closed"
    t = now.hour * 60 + now.minute
    if 4*60 <= t < 9*60+30:  return "pre"
    if 9*60+30 <= t < 16*60: return "open"
    if 16*60 <= t < 20*60:   return "after"
    return "closed"

def is_market_hours(): return get_session() == "open"

def in_reset_window():
    tz  = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    if now.weekday() >= 5: return True
    t = now.hour * 60 + now.minute
    return 4*60 <= t < 9*60+30

def is_night_mode():
    tz  = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    h = now.hour
    return h >= 22 or h < 7

def is_futures_window():
    tz  = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    if now.weekday() >= 5: return False
    t = now.hour * 60 + now.minute
    return 6*60+30 <= t < 9*60+30

def is_evening_futures_window() -> bool:
    """Mon-Thu 8pm-10pm ET — evening futures session in indices bar."""
    tz  = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    dow = now.weekday()  # 0=Mon, 3=Thu
    if dow > 3: return False  # Fri/Sat/Sun handled elsewhere
    t = now.hour * 60 + now.minute
    return 20 * 60 <= t < 22 * 60

def is_sunday_futures_open() -> bool:
    """True Sunday 6pm–10pm ET — show equity futures in the indices bar."""
    tz  = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    if now.weekday() != 6: return False   # Sunday only
    t = now.hour * 60 + now.minute
    return 18 * 60 <= t < 22 * 60

# Human-readable forex labels
FOREX_LABELS = {
    "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY", "USDCAD=X": "USD/CAD",
    "AUDUSD=X": "AUD/USD", "USDCHF=X": "USD/CHF",
    "NZDUSD=X": "NZD/USD", "USDCNY=X": "USD/CNY",
    "USDBRL=X": "USD/BRL", "USDINR=X": "USD/INR",
    "DX-Y.NYB": "DXY",
}

def is_futures_active() -> bool:
    """
    Futures schedule:
    - Sunday:    active from 6pm ET
    - Mon-Thu:   active from 8pm ET (and all next day until market close)
    - Friday:    active until 5pm ET, then closed
    - Saturday:  never active
    """
    tz  = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    dow = now.weekday()   # 0=Mon … 6=Sun
    t   = now.hour * 60 + now.minute
    if dow == 5:                        return False  # All Saturday
    if dow == 6:                        return t >= 18 * 60  # Sunday: 6pm+
    if dow == 4 and t >= 17 * 60:      return False  # Friday after 5pm
    # Mon-Thu: active from 8pm OR all day (carried over from overnight session)
    if t >= 20 * 60:                    return True   # after 8pm any weekday
    return True  # during market hours Mon-Fri

def get_holiday_state(asset_type: str = "us") -> str:
    if asset_type == "btc": return ""
    if asset_type == "tsx": return "tsx_holiday" if is_tsx_holiday() else ""
    return "us_holiday" if is_us_holiday() else ""

def fmt_1d_with_holiday(val, asset_type: str = "us"):
    holiday = get_holiday_state(asset_type)
    if holiday: return "t0", "", "+0.00%", True
    if asset_type != "btc" and in_reset_window(): return "t0", "", "+0.00%", False
    if val is None: return "t2", "", "—", False
    return cl(val), ar(val), fpc(val), False

def fmt_1d(val, is_btc=False):
    if not is_btc and in_reset_window(): return "t0", "", "+0.00%"
    if val is None: return "t2", "", "—"
    return cl(val), ar(val), fpc(val)

def price_colour(price, sma50, sma200, ath):
    if price is None: return "#ffffff"
    if ath and price >= ath * 0.995:  return "#00bcd4"
    if sma200 and price < sma200:      return "#ff1744"
    if sma50  and price < sma50:       return "#ff6d00"
    return "#ffffff"

def sector_name_colour(price, sma50, sma200, ath):
    return price_colour(price, sma50, sma200, ath)

# Strict market-relevant keywords — must be clearly financial/macro
BREAKING_KEYWORDS = [
    # Central banks & monetary policy
    "federal reserve","fed rate","fomc","interest rate","rate cut","rate hike",
    "rate decision","powell","basis point","quantitative",
    "ecb","bank of england","bank of canada","bank of japan","boe","boj","boc",
    # Key economic data
    "cpi","inflation","pce","nonfarm payroll","jobs report","unemployment rate",
    "gdp","retail sales","ism manufacturing","ism services",
    # Markets
    "s&p 500","nasdaq","dow jones","tsx","russell 2000","stock market","wall street",
    "market crash","market rally","circuit breaker","trading halt",
    "earnings beat","earnings miss","quarterly earnings","revenue miss","revenue beat",
    # Assets
    "crude oil","opec","oil prices","gold prices","bitcoin","crypto",
    "treasury yield","10-year yield","bond yield","yield curve","inverted yield",
    # Macro events
    "recession","financial crisis","bank failure","default","bankruptcy","layoff",
    "mass layoff","debt ceiling","government shutdown","tariff","trade war","sanction",
    # Breaking severity
    "breaking","flash crash","black swan","emergency rate",
]

# Explicit exclusion list — topics that contain keyword fragments but aren't market news
EXCLUDE_KEYWORDS = [
    "vat cut","pub","restaurant","cooking","recipe","celebrity","sport","football",
    "cricket","rugby","weather forecast","travel","holiday","fashion","entertainment",
    "film","movie","music","album","award","health tip","diet","fitness",
]

def is_market_headline(t: str) -> bool:
    tl = t.lower()
    if any(ex in tl for ex in EXCLUDE_KEYWORDS):
        return False
    return any(kw in tl for kw in BREAKING_KEYWORDS)

def is_market_session() -> bool:
    """True during regular market hours 9:30am-4:15pm ET weekdays."""
    tz  = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    if now.weekday() >= 5: return False
    t = now.hour * 60 + now.minute
    return 9 * 60 + 30 <= t < 16 * 60 + 15

def sigma_class(sigma, base_colour: str = "", mode: str = "") -> str:
    """
    Returns a CSS class string to apply pulsing if |sigma| > 2.5.
    Only fires in 1D mode. Suppressed during reset window.
    """
    if sigma is None or in_reset_window():
        return base_colour
    if mode != "1D":
        return base_colour
    if sigma >= 2.5:
        return f"{base_colour} mci-sigma-pos".strip()
    if sigma <= -2.5:
        return f"{base_colour} mci-sigma-neg".strip()
    return base_colour

# Weather codes from Open-Meteo WMO standard
WMO_CODES = {
    0:"Clear",1:"Mostly Clear",2:"Partly Cloudy",3:"Overcast",
    45:"Fog",48:"Icy Fog",51:"Light Drizzle",53:"Drizzle",55:"Heavy Drizzle",
    61:"Light Rain",63:"Rain",65:"Heavy Rain",71:"Light Snow",73:"Snow",
    75:"Heavy Snow",77:"Snow Grains",80:"Showers",81:"Showers",82:"Heavy Showers",
    85:"Snow Showers",86:"Heavy Snow Showers",95:"Thunderstorm",
    96:"Thunderstorm + Hail",99:"Heavy Thunderstorm + Hail",
}

@st.cache_data(ttl=900, show_spinner=False)
def get_north_bay_weather():
    """
    Fetch current weather for North Bay, Ontario via Open-Meteo.
    Free, no API key. Cached 15 minutes.
    """
    try:
        import requests as _req
        r = _req.get(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=46.3135&longitude=-79.4633"
            "&current=temperature_2m,weathercode,windspeed_10m,apparent_temperature"
            "&temperature_unit=celsius&windspeed_unit=kmh&timezone=America/Toronto",
            timeout=8)
        if r.status_code != 200:
            return None
        curr = r.json()["current"]
        code = int(curr.get("weathercode", 0))
        return {
            "temp":       round(float(curr["temperature_2m"]), 1),
            "feels_like": round(float(curr["apparent_temperature"]), 1),
            "wind":       round(float(curr["windspeed_10m"]), 0),
            "condition":  WMO_CODES.get(code, "Unknown"),
            "code":       code,
        }
    except Exception:
        return None


# =============================================================================
# DATA HEALTH CHECK
# =============================================================================
def get_data_health() -> dict:
    """
    Check if yfinance is returning live data by verifying the indices.
    Returns a status dict with ok=True/False and a message.
    """
    indices = get_indices_data() or {}
    if not indices:
        return {"ok": False, "msg": "NO DATA — yfinance may be down"}

    # Check if any index has a non-zero price
    prices = [d.get("price") for d in indices.values() if d.get("price")]
    if not prices:
        return {"ok": False, "msg": "NO PRICES — yfinance may be down"}

    # Check if data is stale — all pct_1d exactly 0.00 during market hours
    session = get_session()
    if session == "open":
        all_zero = all(d.get("pct_1d", 0) == 0.0 for d in indices.values())
        if all_zero:
            return {"ok": False, "msg": "STALE DATA — all indices showing 0.00%"}

    return {"ok": True, "msg": ""}

# =============================================================================
# SYNC MODE
# =============================================================================
sync_mode()

# =============================================================================
# NIGHT MODE
# =============================================================================
@st.fragment(run_every=60)
def night_clock():
    if not is_night_mode():
        # Night mode ended — force full page rerun to load the dashboard
        st.rerun()
        return
    tz       = pytz.timezone("America/New_York")
    now_et   = datetime.now(tz)
    t_str    = now_et.strftime("%-I:%M")
    ampm     = now_et.strftime("%p").lower()
    date_str = now_et.strftime("%A, %B %-d")
    wx = get_north_bay_weather()
    if wx:
        wx_line1 = f"{wx['condition']}  {wx['temp']}°C"
        wx_line2 = f"Feels {wx['feels_like']}°C  ·  Wind {wx['wind']:.0f} km/h"
    else:
        wx_line1 = "North Bay, ON"
        wx_line2 = ""
    st.markdown(
        f'<div class="night-screen">'
        f'<div class="night-clock">{t_str}</div>'
        f'<div class="night-sub">{ampm} · new york et</div>'
        f'<div style="font-size:36px;font-weight:600;color:#c0c0c0;letter-spacing:3px;margin-top:16px;">{date_str}</div>'
        f'<div style="font-size:28px;font-weight:500;color:#c0c0c0;letter-spacing:1px;margin-top:16px;text-align:center;">{wx_line1}</div>'
        f'<div style="font-size:24px;font-weight:400;color:#c0c0c0;letter-spacing:1px;margin-top:8px;text-align:center;">{wx_line2}</div>'
        f'</div>', unsafe_allow_html=True)

if is_night_mode():
    night_clock()
    st.stop()

# =============================================================================
# ANIMATION ENGINE
# =============================================================================
# Smart refresh — fast near boundaries, slow otherwise
st.markdown("""
<script>
(function() {
    function getET() {
        var now = new Date();
        var utc = now.getTime() + (now.getTimezoneOffset() * 60000);
        return new Date(utc + (-4 * 3600000));
    }
    function scheduleReload() {
        var et = getET();
        var h = et.getHours(), m = et.getMinutes();
        var atBoundary = (h === 21 && m >= 55) || (h === 22 && m <= 5) ||
                         (h === 6  && m >= 55) || (h === 7  && m <= 5);
        setTimeout(function(){ window.location.reload(); }, atBoundary ? 10000 : 600000);
    }
    scheduleReload();
})();
</script>
""", unsafe_allow_html=True)


st.markdown("""<script>
(function(){
  const store = {};

  function domKey(el) {
    const parts = [el.className.trim().split(' ')[0]];
    let node = el;
    for (let i = 0; i < 8; i++) {
      const p = node.parentElement;
      if (!p || p === document.body) break;
      parts.push(Array.from(p.children).indexOf(node));
      node = p;
    }
    return parts.join('|');
  }

  function parseNum(text) {
    return parseFloat(text.replace(/[+,% \u25b2\u25bc]/g, ''));
  }

  function flash(el, isUp) {
    el.classList.remove('flash-pos', 'flash-neg');
    void el.offsetWidth;
    el.classList.add(isUp ? 'flash-pos' : 'flash-neg');
    setTimeout(() => el.classList.remove('flash-pos', 'flash-neg'), 1200);
  }

  function scan() {
    const sel = '.idx-pct, .pt-ch, .pt-ret, .stat-val, .big-num, .y-r, .vix-v';
    document.querySelectorAll(sel).forEach(el => {
      const key = domKey(el);
      const num = parseNum(el.textContent);
      if (isNaN(num)) return;
      if (key in store && store[key] !== num) {
        flash(el, num > store[key]);
      }
      store[key] = num;
    });
  }

  let timer;
  const obs = new MutationObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(scan, 150);
  });
  obs.observe(document.body, { childList: true, subtree: true });
  setTimeout(scan, 1500);
})();
</script>""", unsafe_allow_html=True)

# =============================================================================
# TICKER
# =============================================================================
@st.fragment(run_every=120)
def ticker_bar():
    header   = get_header_ticker_data() or []
    fut_live = is_futures_active()
    items    = []

    # yfinance status pill
    health = get_data_health()
    if health["ok"]:
        items.append(
            '<span style="display:inline-block;margin:0 18px;font-size:11px;'            'font-weight:700;letter-spacing:1.5px;color:#00e676;'            'background:rgba(0,230,118,.08);padding:2px 10px;'            'border:1px solid rgba(0,230,118,.2);border-radius:2px;'            'vertical-align:middle;">YFINANCE ACTIVE</span>')
    else:
        items.append(
            '<span style="display:inline-block;margin:0 18px;font-size:11px;'            'font-weight:700;letter-spacing:1.5px;color:#ff1744;'            'background:rgba(255,23,68,.08);padding:2px 10px;'            'border:1px solid rgba(255,23,68,.2);border-radius:2px;'            'vertical-align:middle;">YFINANCE NOT RESPONDING</span>')

    # Weather pill at the start of the tape
    wx = get_north_bay_weather()
    if wx:
        items.append(
            f'<span style="display:inline-block;margin:0 18px;font-size:13px;'
            f'color:#90a4ae;background:rgba(144,164,174,.06);'
            f'padding:2px 12px;border:1px solid rgba(144,164,174,.15);'
            f'border-radius:2px;vertical-align:middle;font-weight:500;">'
            f'North Bay {wx["temp"]}°C · {wx["condition"]} · '
            f'Wind {wx["wind"]:.0f} km/h</span>')

    for h in header:
        if h["type"] == "section":
            items.append(
                f'<span style="display:inline-block;margin:0 18px;'
                f'font-size:10px;font-weight:700;letter-spacing:2px;'
                f'color:#ffd54f;background:rgba(255,213,79,.08);'
                f'padding:2px 10px;border:1px solid rgba(255,213,79,.2);'
                f'border-radius:2px;vertical-align:middle;">'
                f'{h["label"]}</span>')
            continue

        is_fut    = h.get("is_fut", False)
        is_crypto = h.get("is_crypto", False)
        is_forex  = h["label"] in FOREX_TICKERS
        raw       = h.get("pct_1d")
        sym       = h["label"]
        disp_lbl  = FOREX_LABELS.get(sym, sym)

        if is_fut:
            if not fut_live:
                c, a, d = "t0", "", "0.00%"
            else:
                c, a, d = cl(raw), ar(raw), fpc(raw) if raw is not None else ("t2","","—")
        elif is_crypto:
            # Crypto always live 24/7
            c, a, d = cl(raw), ar(raw), fpc(raw) if raw is not None else ("t2","","—")
        elif is_forex:
            # Forex on exact same schedule as futures (is_futures_active)
            if not fut_live:
                c, a, d = "t0", "", "0.00%"
            else:
                c, a, d = cl(raw), ar(raw), fpc(raw) if raw is not None else ("t2","","—")
        else:
            c, a, d = fmt_1d(raw)

        price_disp = fp(h.get("price"), 4) if is_forex else fp(h.get("price"))

        items.append(
            f'<span class="ti">'
            f'<span class="ti-s">{disp_lbl}</span>'
            f'<span class="ti-p">{price_disp}</span>'
            f'<span class="ti-c {c}">{a}{d}</span>'
            f'</span>')

    s = "".join(items)
    st.markdown(
        f'<div class="tkr-outer"><div class="tkr-track">{s}{s}</div></div>',
        unsafe_allow_html=True)

ticker_bar()

# =============================================================================
# NEWS
# =============================================================================
@st.fragment(run_every=300)
def news_bar():
    headlines = get_market_news()
    if not headlines: return
    relevant = [h for h in headlines if is_market_headline(h["title"])] or headlines[:1]
    breaking = [h for h in relevant if h["breaking"]]
    quiet    = [h for h in relevant if not h["breaking"]]
    if breaking:
        h = breaking[0]
        age = f"{h['age_minutes']}m ago" if h['age_minutes']<60 else f"{h['age_minutes']//60}h ago"
        st.markdown(
            f'<div style="background:#0f0000;border-top:3px solid #ff1744;'
            f'border-bottom:2px solid #ff1744;padding:12px 20px;'
            f'display:flex;align-items:center;gap:16px;">'
            f'<span style="background:#ff1744;color:#fff;font-size:10px;font-weight:700;'
            f'letter-spacing:1.5px;padding:3px 10px;border-radius:3px;flex-shrink:0;">⚡ BREAKING</span>'
            f'<span style="color:#fff;font-size:17px;font-weight:600;flex:1;">{h["title"]}</span>'
            f'<span style="color:#888;font-size:11px;flex-shrink:0;">{h["source"]} · {age}</span>'
            f'</div>', unsafe_allow_html=True)
    elif quiet:
        h = quiet[0]
        age = f"{h['age_minutes']}m ago" if h['age_minutes']<60 else f"{h['age_minutes']//60}h ago"
        st.markdown(
            f'<div style="background:#0a0a0a;border-top:2px solid #383838;'
            f'border-bottom:2px solid #2a2a2a;padding:10px 20px;'
            f'display:flex;align-items:center;gap:16px;">'
            f'<span style="color:#707070;font-size:10px;font-weight:700;'
            f'letter-spacing:1.5px;flex-shrink:0;">HEADLINES</span>'
            f'<span style="color:#d8d8d8;font-size:16px;font-weight:500;flex:1;">{h["title"]}</span>'
            f'<span style="color:#505050;font-size:11px;flex-shrink:0;">{h["source"]} · {age}</span>'
            f'</div>', unsafe_allow_html=True)

news_bar()

# =============================================================================
# AI SUMMARY
# =============================================================================
@st.fragment(run_every=3600)
def summary_bar():
    summary = get_ai_market_summary()
    if not summary: return
    now_et  = datetime.now(pytz.timezone("America/New_York"))
    t_str   = now_et.strftime("%-I:%M %p ET")
    st.markdown(
        f'<div style="background:#080d08;border-left:4px solid #00e676;'
        f'border-bottom:1px solid #2e2e2e;padding:7px 16px;'
        f'display:flex;align-items:center;gap:14px;">'
        f'<span style="color:#00e676;font-size:9px;font-weight:700;'
        f'letter-spacing:1.5px;flex-shrink:0;">AI SUMMARY</span>'
        f'<span style="color:#e8e8e8;font-size:13px;font-weight:400;flex:1;">{summary}</span>'
        f'<span style="color:#505050;font-size:10px;flex-shrink:0;">Updated {t_str}</span>'
        f'</div>', unsafe_allow_html=True)

summary_bar()

# =============================================================================
# TOP ROW
# =============================================================================
@st.fragment(run_every=60)
def top_row():
    try:
        market  = get_market_status() or {}
        indices = get_indices_data()  or {}
    except Exception:
        return
    sync_mode()
    MODE = get_mode(); KEY = mk(MODE)
    now_et   = datetime.now(pytz.timezone("America/New_York"))
    time_str = now_et.strftime("%-I:%M %p").lower()
    us_hol   = get_holiday_state("us")

    # Pre-market weekday window OR Sunday 6pm-10pm evening open
    show_futures = (is_futures_window() or is_sunday_futures_open() or is_evening_futures_window()) and KEY == "pct_1d"
    futures      = get_futures_data() if show_futures else {}

    # Map each index slot to its futures replacement during futures window
    # Format: "Index Name": ("Futures key in get_futures_data()", "Display label")
    FUTURES_MAP = {
        "S&P 500":     ("S&P FUT",    "S&P 500"),
        "NASDAQ":      ("NQ FUT",     "NASDAQ"),
        "Small-Cap":   ("RUSSELL FUT","SMALL-CAP"),
        "TSX":         ("CRUDE OIL",  "CRUDE OIL"),
        "International":("GOLD",      "GOLD"),
        "Emerging":    ("SILVER",     "SILVER"),
    }

    idx_cells = ""
    for name, d in indices.items():
        mapping = FUTURES_MAP.get(name) if show_futures and futures else None
        fut_key, fut_lbl = mapping if mapping else (None, name)
        fut = futures.get(fut_key) if fut_key else None

        if fut and fut.get("price"):
            pct = fut.get("pct_1d")
            colour = cl(pct); arrow = ar(pct)
            display = fpc(pct) if pct is not None else "—"
            idx_cells += (
                f'<div class="idx-cell" style="border-top:2px solid #ffd54f20;">'
                f'<div class="idx-lbl" style="color:#ffd54f;">{fut_lbl}</div>'
                f'<div class="idx-pct {colour}">{arrow}{display}</div>'
                f'<div class="idx-px">${fp(fut["price"])} '
                f'<span style="color:#ffd54f;font-size:9px;font-weight:600;letter-spacing:1px;">FUT</span>'
                f'</div></div>')
        else:
            raw   = d.get(KEY)
            sig   = d.get("sigma_1d")
            atype = "tsx" if name == "TSX" else "us"
            if KEY == "pct_1d":
                colour, arrow, display, is_hol = fmt_1d_with_holiday(raw, atype)
                pct_cls = sigma_class(sig if not is_hol else None, colour, MODE)
            else:
                colour, arrow, display, is_hol = cl(raw), ar(raw), fpc(raw,2), False
                pct_cls = sigma_class(sig, colour, MODE)
            sub       = "Holiday" if is_hol else f"${fp(d.get('price'))}"
            sub_style = "color:#505050;" if is_hol else ""
            idx_cells += (
                f'<div class="idx-cell">'
                f'<div class="idx-lbl">{name}</div>'
                f'<div class="idx-pct {pct_cls}">{arrow}{display}</div>'
                f'<div class="idx-px" style="{sub_style}">{sub}</div>'
                f'</div>')

    session = get_session()
    if us_hol:
        mkt_cls, mkt_col = "mkt-closed", "gld"
        _today = datetime.now(pytz.timezone("America/New_York")).date()
        _names = {
            "Memorial Day":    lambda d: d.month==5  and d.weekday()==0 and 25<=d.day<=31,
            "Independence Day":lambda d: d.month==7  and d.day in (3,4,5),
            "Labor Day":       lambda d: d.month==9  and d.weekday()==0 and 1<=d.day<=7,
            "Thanksgiving":    lambda d: d.month==11 and d.weekday()==3 and 22<=d.day<=28,
            "Christmas":       lambda d: d.month==12 and d.day in (24,25,26),
            "New Year":        lambda d: d.month==1  and d.day in (1,2),
            "MLK Day":         lambda d: d.month==1  and d.weekday()==0 and 15<=d.day<=21,
            "Presidents Day":  lambda d: d.month==2  and d.weekday()==0 and 15<=d.day<=21,
            "Good Friday":     lambda d: d.month in (3,4) and d.weekday()==4,
            "Juneteenth":      lambda d: d.month==6  and d.day in (18,19,20),
        }
        _name    = next((n for n,fn in _names.items() if fn(_today)), "Market Holiday")
        mkt_stxt = f"🇺🇸 {_name.upper()}"
    elif is_sunday_futures_open():
        mkt_cls, mkt_stxt, mkt_col = "mkt-pre",    "FUTURES OPEN",   "gld"
    elif session == "open":
        mkt_cls, mkt_stxt, mkt_col = "mkt-open",   "MARKET: OPEN",   "pos"
    elif session == "pre":
        mkt_cls, mkt_stxt, mkt_col = "mkt-pre",    "PRE-MARKET",     "gld"
    elif session == "after":
        mkt_cls, mkt_stxt, mkt_col = "mkt-after",  "AFTER HOURS",    "gld"
    else:
        mkt_cls, mkt_stxt, mkt_col = "mkt-closed", "MARKET: CLOSED", "neg"

    mode_cls  = {"1D":"mode-1d","1M":"mode-1m","YTD":"mode-ytd"}[MODE]
    mode_desc = {"1D":"1 DAY","1M":"1 MONTH","YTD":"YEAR TO DATE"}[MODE]

    st.markdown(
        f'<div class="idx-row">{idx_cells}'
        f'<div class="clock-cell">'
        f'<div class="clock-time">{time_str}</div>'
        f'<div class="clock-sub">NEW YORK · ET</div></div>'
        f'<div class="mkt-cell"><div class="{mkt_cls}">'
        f'<div class="mkt-s {mkt_col}">{mkt_stxt}</div>'
        f'<div class="mkt-cd">{market.get("countdown","")}</div>'
        f'</div></div></div>'
        f'<div class="mode-bar" style="justify-content:space-between;">'
        f'<div style="display:flex;align-items:center;gap:12px;">'
        f'<span class="mode-label">DISPLAY MODE</span>'
        f'<span class="{mode_cls}">{MODE}</span>'
        f'<span style="font-size:13px;color:#505050;margin-left:4px;font-weight:400;">'
        f'— {mode_desc}</span>'
        f'</div>'
        f'<a href="/Macro" target="_self" target="_self" style="font-size:10px;color:#00bcd4;border:1px solid rgba(0,188,212,.3);padding:3px 12px;border-radius:3px;font-weight:700;letter-spacing:1.5px;text-decoration:none;">MACRO ›</a>', unsafe_allow_html=True)

top_row()

# =============================================================================
# ROW 2 — MCI | PORTFOLIO
# =============================================================================
col_mci, col_port = st.columns([1, 3], gap="small")

with col_mci:
    @st.fragment(run_every=60)
    def mci_panel():
        sync_mode()
        MODE   = get_mode()
        vol    = get_volatility_data()         or {}
        mci    = get_market_confidence_index() or {}
        score  = mci.get("score", 0)
        mlabel = mci.get("label", "—")
        vc     = vol.get("vix_current", 0)
        vma    = vol.get("vix_30dma", 0)

        # VIX vs 30DMA colour
        diff    = vc - vma
        vix_col = "#00e676" if diff < -1 else "#ff1744" if diff > 1 else "#ffffff"

        LABEL_STYLES = {
            "Euphoria":       "color:#00e676;background:rgba(0,230,118,.12);border:2px solid rgba(0,230,118,.4);padding:5px 18px;border-radius:4px;font-size:19px;font-weight:700;letter-spacing:2px;display:inline-block;",
            "Very Confident": "color:#4caf50;background:rgba(76,175,80,.12);border:2px solid rgba(76,175,80,.4);padding:5px 18px;border-radius:4px;font-size:18px;font-weight:700;letter-spacing:1px;display:inline-block;",
            "Confident":      "color:#8bc34a;background:rgba(139,195,74,.12);border:2px solid rgba(139,195,74,.4);padding:5px 18px;border-radius:4px;font-size:19px;font-weight:700;letter-spacing:2px;display:inline-block;",
            "Cautious":       "color:#ffd54f;background:rgba(255,213,79,.12);border:2px solid rgba(255,213,79,.4);padding:5px 18px;border-radius:4px;font-size:18px;font-weight:700;letter-spacing:2px;display:inline-block;",
            "Neutral":        "color:#ff9800;background:rgba(255,152,0,.12);border:2px solid rgba(255,152,0,.4);padding:5px 18px;border-radius:4px;font-size:19px;font-weight:600;letter-spacing:3px;display:inline-block;",
            "Defensive":      "color:#ff6f00;background:rgba(255,111,0,.12);border:2px solid rgba(255,111,0,.4);padding:5px 18px;border-radius:4px;font-size:18px;font-weight:700;letter-spacing:1px;display:inline-block;",
            "Concerned":      "color:#e53935;background:rgba(229,57,53,.12);border:2px solid rgba(229,57,53,.4);padding:5px 18px;border-radius:4px;font-size:18px;font-weight:800;letter-spacing:1px;display:inline-block;",
            "Fear":           "color:#b71c1c;background:rgba(183,28,28,.15);border:2px solid rgba(183,28,28,.5);padding:5px 18px;border-radius:4px;font-size:19px;font-weight:800;letter-spacing:2px;display:inline-block;",
            "Panic":          "color:#7f0000;background:rgba(127,0,0,.2);border:2px solid rgba(127,0,0,.6);padding:5px 18px;border-radius:4px;font-size:21px;font-weight:900;letter-spacing:3px;display:inline-block;",
        }
        lbl_style = LABEL_STYLES.get(mlabel, "color:#ffffff;font-size:20px;font-weight:700;")

        st.markdown(
            f'<div class="card" style="border-right:2px solid #333333;">'
            f'<div class="card-hdr">Market Confidence</div>'
            f'<div class="mci-num" style="color:#ffffff;">{score:.0f}</div>'
            f'<div style="text-align:center;margin-top:4px;"><span style="{lbl_style}">{mlabel}</span></div>'
            f'<div class="vix-duo">'
            f'<div class="vix-blk">'
            f'<div class="vix-l">VIX</div>'
            f'<div class="vix-v" style="color:{vix_col};">{fp(vc)}</div>'
            f'</div>'
            f'<div class="vix-blk">'
            f'<div class="vix-l">30 DMA</div>'
            f'<div class="vix-v" style="color:#c0c0c0;">{fp(vma)}</div>'
            f'</div>'
            f'</div></div>',
            unsafe_allow_html=True)
    mci_panel()

with col_port:
    @st.fragment(run_every=60)
    def portfolio_panel():
        sync_mode()
        MODE = get_mode(); KEY = mk(MODE)
        port  = get_portfolio_data() or {}
        assets= port.get("assets", {})
        pf    = port.get("portfolio", {})
        xeqt  = assets.get("XEQT", {})
        btc   = assets.get("BTC", {})
        beta  = pf.get("beta")
        corr  = pf.get("btc_xeqt_corr")
        alpha = pf.get("alpha_bps")
        ret   = pf.get("return_ytd") if MODE=="YTD" else pf.get("return_1d")

        raw_x = xeqt.get(KEY); raw_b = btc.get(KEY)
        if KEY == "pct_1d":
            xc,xa,xd,x_hol = fmt_1d_with_holiday(raw_x,"tsx")
            bc,ba,bd,_     = fmt_1d_with_holiday(raw_b,"btc")
            if x_hol or in_reset_window(): rc,ra,rd = "t0","","+0.00%"
            else: rc,ra,rd = cl(ret),ar(ret),fpc(ret)
        else:
            xc,xa,xd = cl(raw_x),ar(raw_x),fpc(raw_x)
            bc,ba,bd = cl(raw_b),ar(raw_b),fpc(raw_b)
            rc,ra,rd = cl(ret),ar(ret),fpc(ret)
            x_hol = False

        xc2  = get_chart_data(PORTFOLIO["XEQT"]["ticker"]) or {}
        bc2  = get_chart_data(PORTFOLIO["BTC"]["ticker"])  or {}
        def lv(lst): v=[x for x in (lst or []) if x]; return v[-1] if v else None
        def av(lst): v=[x for x in (lst or []) if x]; return max(v) if v else None
        xeqt_px   = xeqt.get("price")
        btc_px    = btc.get("price")
        xeqt_pcol = price_colour(xeqt_px,lv(xc2.get("sma50")),lv(xc2.get("sma200")),av(xc2.get("closes")))
        btc_pcol  = price_colour(btc_px,lv(bc2.get("sma50")),lv(bc2.get("sma200")),av(bc2.get("closes")))

        stats = (
            f'<div class="stats-row">'
            f'<div class="stat-box"><div class="stat-lbl">Return ({MODE})</div>'
            f'<div class="stat-val {cl(ret)}">{fpc(ret)}</div></div>'
            f'<div class="stat-box"><div class="stat-lbl">Beta vs SPY</div>'
            f'<div class="stat-val t0">{f"{beta:.2f}" if beta else "—"}</div></div>'
            f'<div class="stat-box"><div class="stat-lbl">IBIT/XEQT Corr</div>'
            f'<div class="stat-val t0">{f"{corr:.3f}" if corr is not None else "—"}</div></div>'
            f'<div class="stat-box"><div class="stat-lbl">Alpha vs SPY</div>'
            f'<div class="stat-val {cl(alpha)}">'
            f'{f"{alpha:+.0f} bps" if alpha is not None else "—"}</div></div>'
            f'</div>')
        # BTC: always show BTC's own change 24/7, sigma pulse active in 1D
        btc_ch_cls = sigma_class(btc.get("sigma_1d"), bc, KEY=="pct_1d" and "1D" or "")
        btc_ch     = f"{ba}{bd}"
        btc_lbl    = "20% WEIGHT · 24/7"

        table = (
            f'<div class="pt-hd" style="grid-template-columns:1fr 1.1fr 1fr 1fr;">'
            f'<div>Ticker</div><div>Price</div><div>Change ({MODE})</div>'
            f'<div style="text-align:right;">Portfolio Return</div></div>'
            f'<div class="pt-r" style="grid-template-columns:1fr 1.1fr 1fr 1fr;">'
            f'<div class="pt-sym">XEQT</div>'
            f'<div class="pt-px" style="color:{xeqt_pcol};">${fp(xeqt_px)}</div>'
            f'<div class="pt-ch {sigma_class(xeqt.get("sigma_1d"), xc, KEY=="pct_1d" and "1D" or "")}">{xa}{xd}</div>'
            f'<div style="text-align:right;">'
            f'<div class="pt-ret {rc}">{ra}{rd}</div>'
            f'<div class="pt-wt">{"TSX HOLIDAY" if x_hol else "BLENDED 80/20"}</div></div></div>'
            f'<div class="pt-r" style="grid-template-columns:1fr 1.1fr 1fr 1fr;">'
            f'<div class="pt-sym">BTC</div>'
            f'<div class="pt-px" style="color:{btc_pcol};">${fp(btc_px,0)}</div>'
            f'<div class="pt-ch {btc_ch_cls}">{btc_ch}</div>'
            f'<div style="text-align:right;">'
            f'<div class="pt-wt" style="margin-top:18px;">{btc_lbl}</div>'
            f'</div></div></div>')
        st.markdown(
            f'<div class="card"><div class="card-hdr">'
            f'<span>Portfolio · 80% XEQT / 20% BTC</span>{badge(MODE)}</div>'
            f'{stats}{table}</div>', unsafe_allow_html=True)
    portfolio_panel()

st.markdown('<div style="height:2px;background:#1e1e1e;"></div>', unsafe_allow_html=True)

# =============================================================================
# BOTTOM ROW
# =============================================================================
@st.fragment(run_every=60)
def bottom_row():
    sync_mode()
    MODE    = get_mode(); KEY = mk(MODE)
    sectors = get_sectors_data()    or {}
    risk    = get_risk_breadth()    or {}
    yields  = get_treasury_yields() or {}

    c1, c2, c3, c4 = st.columns([1.6, 1, 1, 1.2], gap="small")

    with c1:
        items = list(sectors.items())
        half  = (len(items)+1)//2
        left  = items[:half]; right = items[half:]
        def sec_col(lst):
            rows = []
            for name, d in lst:
                raw = d.get(KEY)
                if KEY == "pct_1d":
                    colour,arrow,display,_ = fmt_1d_with_holiday(raw,"us")
                else:
                    colour,arrow,display = cl(raw),ar(raw),fpc(raw)
                nc    = sector_name_colour(d.get("price"),d.get("sma50"),d.get("sma200"),d.get("ath"))
                sig   = d.get("sigma_1d")   # check sigma in all modes
                pcls  = sigma_class(sig, colour, MODE)
                rows.append(
                    f'<div class="sec-r">'
                    f'<span class="sec-n" style="color:{nc};">{name}</span>'
                    f'<span class="sec-pct {pcls}">{arrow}{display}</span>'
                    f'</div>')
            return "".join(rows)
        st.markdown(
            f'<div class="card" style="border-right:2px solid #333333;">'
            f'<div class="card-hdr"><span>Sectors</span>{badge(MODE)}</div>'
            f'<div class="sec-grid">'
            f'<div>{sec_col(left)}</div><div>{sec_col(right)}</div>'
            f'</div></div>', unsafe_allow_html=True)

    with c2:
        rr   = risk.get("risk_rotation_pct", 0) or 0
        rrl  = risk.get("risk_label", "—")
        # Pick the right period change to display alongside the 1M spread
        rr_chg = {
            "1D":  None if (MODE == "1D" and in_reset_window()) else (risk.get("risk_pct_1d",  0) or 0),
            "1M":  risk.get("risk_pct_1m",  0) or 0,
            "YTD": risk.get("risk_pct_ytd", 0) or 0,
        }.get(MODE, 0)
        RR_STYLES = {'Euphoric': 'color:#00e676;background:rgba(0,230,118,0.12);border:2px solid rgba(0,230,118,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Aggressive': 'color:#4caf50;background:rgba(76,175,80,0.12);border:2px solid rgba(76,175,80,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Risk-On': 'color:#8bc34a;background:rgba(139,195,74,0.12);border:2px solid rgba(139,195,74,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Risk-Leaning': 'color:#cddc39;background:rgba(205,220,57,0.12);border:2px solid rgba(205,220,57,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Neutral': 'color:#ffd54f;background:rgba(255,213,79,0.12);border:2px solid rgba(255,213,79,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Defensive': 'color:#ff9800;background:rgba(255,152,0,0.12);border:2px solid rgba(255,152,0,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Risk-Off': 'color:#e53935;background:rgba(229,57,53,0.12);border:2px solid rgba(229,57,53,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Panic': 'color:#7f0000;background:rgba(127,0,0,0.2);border:2px solid rgba(127,0,0,0.6);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;'}
        rr_style = RR_STYLES.get(rrl, RR_STYLES["Neutral"])
        period_lbl = {"1D":"TODAY","1M":"1 MONTH","YTD":"YEAR TO DATE"}[MODE]
        st.markdown(
            f'<div class="card" style="border-right:2px solid #333333;">'
            f'<div class="card-hdr" style="justify-content:center;">'
            f'Risk Rotation&nbsp;{badge(MODE)}</div>'
            f'<div class="big-wrap">'
            f'<div class="big-num t0">{rr:.3f}</div>'
            f'<div class="big-sub">HYG / LQD RATIO</div>'
            f'<div class="big-chg {cl(rr_chg) if rr_chg is not None else "t2"}" style="font-size:17px;">{ar(rr_chg) + "&nbsp;" + fpc(rr_chg) if rr_chg is not None else "—"}</div>'
            f'<div style="font-size:12px;color:#aaaaaa;letter-spacing:1px;margin-top:3px;font-weight:500;">{period_lbl} CHANGE</div>'
            f'<div style="text-align:center;margin-top:8px;"><span style="{rr_style}">{rrl}</span></div>'
            f'</div></div>', unsafe_allow_html=True)

    with c3:
        br  = risk.get("breadth_ratio") or 0
        brl = risk.get("breadth_label", "—")
        br_chg = {
            "1D":  None if (MODE == "1D" and in_reset_window()) else risk.get("breadth_chg_1d",  None),
            "1M":  risk.get("breadth_chg_1m",  None),
            "YTD": risk.get("breadth_chg_ytd", None),
        }.get(MODE)
        BR_STYLES = {'Maximum Breadth': 'color:#00e676;background:rgba(0,230,118,0.12);border:2px solid rgba(0,230,118,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Solid Breadth': 'color:#4caf50;background:rgba(76,175,80,0.12);border:2px solid rgba(76,175,80,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Healthy Participation': 'color:#8bc34a;background:rgba(139,195,74,0.12);border:2px solid rgba(139,195,74,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Fair Participation': 'color:#cddc39;background:rgba(205,220,57,0.12);border:2px solid rgba(205,220,57,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Thin Participation': 'color:#ffd54f;background:rgba(255,213,79,0.1);border:2px solid rgba(255,213,79,0.3);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Concentrated': 'color:#ff9800;background:rgba(255,152,0,0.12);border:2px solid rgba(255,152,0,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'High Concentration': 'color:#e53935;background:rgba(229,57,53,0.12);border:2px solid rgba(229,57,53,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Neutral Breadth': 'color:#ffd54f;background:rgba(255,213,79,0.12);border:2px solid rgba(255,213,79,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Apex Concentration': 'color:#b71c1c;background:rgba(183,28,28,0.15);border:2px solid rgba(183,28,28,0.5);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Severe Divergence': 'color:#7f0000;background:rgba(127,0,0,0.2);border:2px solid rgba(127,0,0,0.6);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Risk-On Rotation': 'color:#8bc34a;background:rgba(139,195,74,0.12);border:2px solid rgba(139,195,74,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;', 'Broadening-Out': 'color:#cddc39;background:rgba(205,220,57,0.12);border:2px solid rgba(205,220,57,0.4);padding:4px 14px;border-radius:4px;font-size:12px;font-weight:700;letter-spacing:.5px;display:inline-block;'}
        br_style = BR_STYLES.get(brl, BR_STYLES["Neutral Breadth"])
        period_lbl = {"1D":"TODAY","1M":"1 MONTH","YTD":"YEAR TO DATE"}[MODE]
        # Convert ratio change to percentage for readability
        br_chg_pct = round(br_chg * 100, 3) if br_chg is not None else None
        br_chg_str = (f"{br_chg_pct:+.2f}%" if br_chg_pct is not None else "—")
        br_chg_cl  = cl(br_chg) if br_chg is not None else "t2"
        br_chg_ar  = ar(br_chg) if br_chg is not None else ""
        st.markdown(
            f'<div class="card" style="border-right:2px solid #333333;">'
            f'<div class="card-hdr" style="justify-content:center;">'
            f'Breadth&nbsp;{badge(MODE)}</div>'
            f'<div class="big-wrap">'
            f'<div class="big-num t0">{br:.3f}</div>'
            f'<div class="big-sub">RSP / SPY · 10-LEVEL</div>'
            f'<div class="big-chg {br_chg_cl}" style="font-size:17px;">{br_chg_ar}&nbsp;{br_chg_str}</div>'
            f'<div style="font-size:12px;color:#aaaaaa;letter-spacing:1px;margin-top:3px;font-weight:500;">{period_lbl} CHANGE</div>'
            f'<div style="text-align:center;margin-top:8px;"><span style="{br_style}">{brl}</span></div>'
            f'</div></div>', unsafe_allow_html=True)

    with c4:
        y_rows = ""
        for name, d in yields.items():
            yp  = d.get("yield_pct", 0) or 0
            ch1 = d.get("change_1d",  0) or 0
            cc  = "pos" if ch1<0 else "neg" if ch1>0 else "t2"  # falling yield = green
            y_rows += (
                f'<div class="y-row">'
                f'<div class="y-n">{name}</div>'
                f'<div class="y-r">{yp:.3f}%</div>'
                f'<div class="y-bp {cc}">{fpbp(ch1)}</div>'
                f'</div>')
        st.markdown(
            f'<div class="card">'
            f'<div class="card-hdr" style="justify-content:center;">Treasury Yields</div>'
            f'<div class="y-hd"><div>TENOR</div>'
            f'<div style="text-align:center;">RATE</div>'
            f'<div style="text-align:right;">CHANGE</div></div>'
            f'{y_rows}</div>', unsafe_allow_html=True)

bottom_row()
