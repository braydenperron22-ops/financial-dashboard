# =============================================================================
# app.py  —  MARKET TERMINAL  v8
# =============================================================================
from datetime import datetime
import pytz
import streamlit as st
from config import PORTFOLIO
from data.fetcher import (
    get_header_ticker_data, get_indices_data,
    get_market_confidence_index, get_market_status, get_portfolio_data,
    get_risk_breadth, get_sectors_data, get_treasury_yields,
    get_volatility_data, get_ai_market_summary, get_market_news, prefetch_all,
)

st.set_page_config(page_title="MARKET TERMINAL", layout="wide",
                   initial_sidebar_state="collapsed")

# =============================================================================
# CSS
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

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
iframe { display:block; }
[data-testid="stHorizontalBlock"] { gap:0 !important; padding:0 !important; }
[data-testid="column"]>div        { padding:0 !important; }
[data-testid="stVerticalBlock"]   { gap:0 !important; }
.element-container { margin:0 !important; padding:0 !important; }
.stMarkdown        { margin:0 !important; padding:0 !important; }
* { font-family:'IBM Plex Mono','Courier New',monospace !important; box-sizing:border-box; }
::-webkit-scrollbar { display:none; }

/* TICKER */
.tkr-outer {
  width:100vw; position:relative; left:50%; transform:translateX(-50%);
  overflow:hidden; background:#000;
  border-top:2px solid #00e676; border-bottom:3px solid #1e1e1e; padding:7px 0;
}
.tkr-track { display:inline-block; white-space:nowrap; animation:tkr 240s linear infinite; }
.tkr-track:hover { animation-play-state:paused; }
@keyframes tkr { 0%{transform:translateX(0);} 100%{transform:translateX(-50%);} }
.ti   { display:inline-flex; align-items:baseline; gap:7px; margin:0 22px; font-size:15px; }
.ti-s { color:#fff; font-weight:700; font-size:15px; }
.ti-p { color:#b0b0b0; font-size:13px; }
.ti-c { font-weight:700; font-size:15px; }
.td   { display:inline-block; margin:0 18px; font-size:13px; color:#00bcd4;
        background:#011; padding:2px 10px; border:1px solid #0d3d4a;
        border-radius:1px; font-weight:700; vertical-align:middle; }

/* CARD */
.card     { background:#090909; border:1px solid #1e1e1e; padding:10px 12px; height:100%; }
.card-hdr { font-size:10px; font-weight:700; letter-spacing:2.5px; color:#ffffff;
            text-transform:uppercase; padding-bottom:6px; margin-bottom:7px;
            border-bottom:1px solid #1a1a1a; display:flex;
            justify-content:space-between; align-items:center; }

/* INDICES ROW */
.idx-row  { display:flex; width:100%; background:#090909; border-top:2px solid #303030; border-bottom:2px solid #1e1e1e; }
.idx-cell { flex:1; padding:10px 10px; text-align:center; border-right:1px solid #1e1e1e; }
.idx-cell:last-of-type { border-right:none; }
.idx-lbl  { font-size:9px; color:#ffffff; letter-spacing:2px; text-transform:uppercase; margin-bottom:3px; }
.idx-pct  { font-size:30px; font-weight:800; line-height:1; }
.idx-px   { font-size:12px; color:#c8c8c8; margin-top:3px; }
.clock-cell { width:190px; flex-shrink:0; padding:10px 14px; display:flex;
  flex-direction:column; justify-content:center; align-items:center;
  border-left:2px solid #1e1e1e; background:#090909; }
.clock-time { font-size:38px; font-weight:800; color:#fff; line-height:1; text-align:center; }
.clock-sub  { font-size:9px; color:#d0d0d0; letter-spacing:2px; margin-top:5px; }
.mkt-cell { width:210px; flex-shrink:0; padding:10px 14px; display:flex;
  align-items:center; justify-content:center;
  border-left:2px solid #1e1e1e; background:#090909; }
.mkt-open   { background:#011501; border:2px solid #00e676;  padding:7px 16px; width:100%; text-align:center; }
.mkt-closed { background:#150101; border:2px solid #ff1744;  padding:7px 16px; width:100%; text-align:center; }
.mkt-pre    { background:#1a1500; border:2px solid #ffd54f;  padding:7px 16px; width:100%; text-align:center; }
.mkt-after  { background:#1a1500; border:2px solid #ffd54f;  padding:7px 16px; width:100%; text-align:center; }
.mkt-s  { font-size:17px; font-weight:800; letter-spacing:1px; }
.mkt-cd { font-size:13px; font-weight:600; margin-top:5px; color:#d0d0d0; }

/* MODE BAR — big, obvious timeframe indicator */
.mode-bar {
  background:#060606; padding:5px 14px;
  border-bottom:2px solid #1e1e1e;
  display:flex; align-items:center; gap:12px;
}
.mode-label { font-size:10px; color:#707070; letter-spacing:2px; }
.mode-1d  { font-size:18px; font-weight:800; letter-spacing:3px;
            color:#00e676; border-bottom:3px solid #00e676;
            padding-bottom:1px; }
.mode-1m  { font-size:18px; font-weight:800; letter-spacing:3px;
            color:#00bcd4; border-bottom:3px solid #00bcd4;
            padding-bottom:1px; }
.mode-ytd { font-size:18px; font-weight:800; letter-spacing:3px;
            color:#ffd54f; border-bottom:3px solid #ffd54f;
            padding-bottom:1px; }

/* MCI */
.mci-num { font-size:80px; font-weight:900; line-height:1; text-align:center; letter-spacing:-4px; }
.mci-lbl { font-size:18px; font-weight:700; text-align:center; letter-spacing:2px; margin-top:2px; }
.vix-duo { display:flex; justify-content:space-between; margin-top:8px;
           padding-top:8px; border-top:1px solid #1a1a1a; }
.vix-blk { text-align:center; flex:1; }
.vix-l   { font-size:10px; color:#ffffff; letter-spacing:1.5px; margin-bottom:5px; }
.vix-v   { font-size:22px; font-weight:800; }
.fbar    { margin-top:8px; padding-top:8px; border-top:1px solid #1a1a1a; }
.fb-row  { margin-bottom:4px; }
.fb-top  { display:flex; justify-content:space-between; font-size:9px; color:#ffffff; margin-bottom:3px; }
.fb-bg   { background:#111; height:4px; border-radius:1px; }
.fb-fill { height:4px; border-radius:1px; opacity:.6; }

/* PORTFOLIO */
.stats-row { display:flex; gap:6px; margin-bottom:7px; }
.stat-box  { flex:1; background:#0d0d0d; border:1px solid #1a1a1a; border-radius:2px; padding:6px 10px; }
.stat-lbl  { font-size:9px; color:#ffffff; letter-spacing:1.5px; text-transform:uppercase; margin-bottom:2px; }
.stat-val  { font-size:20px; font-weight:700; }
.pt-hd     { display:grid; grid-template-columns:1fr 1.1fr 1fr 1fr;
             font-size:9px; color:#ffffff; letter-spacing:1.5px; text-transform:uppercase;
             padding-bottom:7px; border-bottom:1px solid #1a1a1a; }
.pt-r      { display:grid; grid-template-columns:1fr 1.1fr 1fr 1fr;
             padding:10px 0; border-bottom:1px solid #0d0d0d; align-items:center; }
.pt-r:last-child { border-bottom:none; }
.pt-sym    { font-size:30px; font-weight:700; color:#fff; }
.pt-px     { font-size:28px; font-weight:600; color:#fff; }
.pt-ch     { font-size:28px; font-weight:700; }
.pt-ret    { font-size:36px; font-weight:700; text-align:right; line-height:1; }
.pt-wt     { font-size:12px; color:#c0c0c0; text-align:right; margin-top:5px; font-weight:500; }

/* SECTORS */
.sec-grid { display:grid; grid-template-columns:1fr 1fr; }
.sec-r    { display:flex; justify-content:space-between; align-items:center;
            padding:4px 4px; border-bottom:1px solid #0d0d0d; }
.sec-r:last-child { border-bottom:none; }
.sec-n    { color:#ffffff; font-size:13px; font-weight:500; }
.sec-pct  { font-weight:700; font-size:13px; text-align:right; }
.sec-grid>div:first-child .sec-r { padding-right:12px; border-right:1px solid #1a1a1a; }
.sec-grid>div:last-child  .sec-r { padding-left:12px; }

/* RISK / BREADTH */
.big-wrap { text-align:center; padding:2px 0; }
.big-num  { font-size:48px; font-weight:900; letter-spacing:-2px; line-height:1;
            margin:8px 0 4px; color:#ffffff; }
.big-sub  { font-size:10px; color:#ffffff; letter-spacing:1.5px; }
.big-chg  { font-size:14px; font-weight:700; margin-top:6px; }
.tag      { display:inline-block; font-size:13px; font-weight:800; letter-spacing:1px;
            padding:4px 12px; border-radius:2px; margin-top:6px; }
.tag-on   { background:#011f01; color:#00e676; border:1px solid #005500; }   /* Risk-On / Broad */
.tag-agg  { background:#002200; color:#00ff88; border:1px solid #007700; }   /* Aggressive */
.tag-euph { background:#001a00; color:#39ff14; border:1px solid #005500; }   /* Euphoric */
.tag-lean { background:#071a07; color:#66bb6a; border:1px solid #2e7d32; }   /* Risk-Leaning */
.tag-neu  { background:#0a0e10; color:#90a4ae; border:1px solid #37474f; }   /* Neutral */
.tag-def  { background:#1a1200; color:#ffb300; border:1px solid #664d00; }   /* Defensive */
.tag-off  { background:#1f0101; color:#ff1744; border:1px solid #550000; }   /* Risk-Off */
.tag-pan  { background:#2a0000; color:#ff0000; border:1px solid #880000; }   /* Panic */
.tag-apc  { background:#1a0e00; color:#ffd54f; border:1px solid #553300; }   /* Apex Concentration */
.tag-nar  { background:#161000; color:#ffd54f; border:1px solid #443300; }   /* Narrow */

/* YIELDS — bigger, cleaner */
.y-hd  { display:grid; grid-template-columns:1.4fr 1fr 0.8fr;
          font-size:9px; color:#ffffff; letter-spacing:1.5px; text-transform:uppercase;
          padding-bottom:8px; border-bottom:1px solid #1a1a1a; }
.y-row { display:grid; grid-template-columns:1.4fr 1fr 0.8fr;
          padding:6px 0; border-bottom:1px solid #0d0d0d; align-items:center; }
.y-row:last-child { border-bottom:none; }
.y-n   { color:#ffffff; font-size:13px; font-weight:500; }
.y-r   { font-size:16px; font-weight:700; color:#fff; text-align:center; }
.y-chg { font-size:12px; font-weight:700; text-align:right; }

/* COLOURS */
.pos { color:#00e676 !important; } .neg { color:#ff1744 !important; }
.acc { color:#00bcd4 !important; } .gld { color:#ffd54f !important; }
.t0  { color:#ffffff !important; } .t1  { color:#c0c0c0 !important; }
.t2  { color:#707070 !important; }

/* BADGE (kept small for card headers) */
.mb     { display:inline-block; font-size:8px; font-weight:700; letter-spacing:2px;
          padding:2px 7px; border-radius:1px; text-transform:uppercase; }
.mb-1d  { background:#061a06; color:#00e676; border:1px solid #0d3d0d; }
.mb-1m  { background:#040f1a; color:#00bcd4; border:1px solid #0d2b3d; }
.mb-ytd { background:#1a1204; color:#ffd54f; border:1px solid #3d2d0d; }
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
    return f"{v:+.{d}f}%"

def cl(v):
    if v is None: return "t2"
    return "pos" if v >= 0 else "neg"

def ar(v):
    if v is None: return ""
    return "▲" if v >= 0 else "▼"

def get_mode():
    m = datetime.now().minute % 30
    if m < 20: return "1D"
    if m < 25: return "1M"
    return "YTD"

def mk(m): return {"1D":"pct_1d","1M":"pct_1m","YTD":"pct_ytd"}[m]

def badge(m):
    c = {"1D":"mb-1d","1M":"mb-1m","YTD":"mb-ytd"}[m]
    return f'<span class="mb {c}">{m}</span>'

def get_session() -> str:
    """
    Return the current US market session:
      "pre"    — weekday 4:00am–9:29am ET
      "open"   — weekday 9:30am–3:59pm ET
      "after"  — weekday 4:00pm–7:59pm ET
      "closed" — nights, weekends
    """
    tz  = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    if now.weekday() >= 5:
        return "closed"
    t = now.hour * 60 + now.minute
    if 4 * 60 <= t < 9 * 60 + 30:
        return "pre"
    if 9 * 60 + 30 <= t < 16 * 60:
        return "open"
    if 16 * 60 <= t < 20 * 60:
        return "after"
    return "closed"

def is_market_hours() -> bool:
    """True only during regular NYSE trading hours Mon-Fri 9:30am-4:00pm ET."""
    return get_session() == "open"

def in_reset_window() -> bool:
    """True outside NYSE hours — weekend or weekday 4am-9:30am ET."""
    return not is_market_hours()

def pct_1d_display(val, is_btc=False):
    """
    During reset window, return None for non-BTC so we can render
    0.00% in white with no arrow. BTC is live 24/7.
    """
    if not is_btc and in_reset_window():
        return None   # None = reset state, rendered as white 0.00% / no arrow
    return val

def fmt_1d(val, is_btc=False):
    """
    Format a 1D change for display.
    Reset window (non-BTC): white 0.00%, no arrow.
    Normal: coloured with arrow.
    Returns (colour_class, arrow_str, display_str)
    """
    if not is_btc and in_reset_window():
        return "t0", "", "+0.00%"
    if val is None:
        return "t2", "", "—"
    return cl(val), ar(val), fpc(val)

# =============================================================================
# TICKER
# =============================================================================
@st.cache_data(ttl=300)
def get_ticker_html():
    header = get_header_ticker_data() or []
    items  = []
    for h in header:
        if h["type"] == "date":
            items.append(f'<span class="td">{h["label"]}</span>')
        else:
            raw  = h.get("pct_1d")
            # BTC tickers in header — check by label
            is_b = h["label"] in ("BTC-USD", "ETH-USD", "COIN", "MSTR")
            val  = pct_1d_display(raw, is_btc=is_b)
            c    = cl(val)
            a    = ar(val)
            items.append(
                f'<span class="ti">'
                f'<span class="ti-s">{h["label"]}</span>'
                f'<span class="ti-p">{fp(h.get("price"))}</span>'
                f'<span class="ti-c {c}">{a}{fpc(val)}</span>'
                f'</span>')
    s = "".join(items)
    return f'<div class="tkr-outer"><div class="tkr-track">{s}{s}</div></div>'

st.markdown(get_ticker_html(), unsafe_allow_html=True)

# =============================================================================
# AI SUMMARY
# =============================================================================
# =============================================================================
# NEWS + AI SUMMARY BAR  — news refreshes every 15 min, summary every 60 min
# =============================================================================
@st.fragment(run_every=900)
def news_bar():
    headlines = get_market_news()
    if not headlines:
        return

    breaking = [h for h in headlines if h["breaking"]]

    if breaking:
        # Show the single most urgent breaking headline
        h       = breaking[0]
        age_str = f"{h['age_minutes']}m ago" if h['age_minutes'] < 60 else f"{h['age_minutes']//60}h ago"
        st.markdown(
            f'<div style="background:#0f0000;border-top:2px solid #ff1744;'
            f'border-bottom:2px solid #ff1744;padding:8px 20px;'
            f'display:flex;align-items:center;gap:16px;">'
            f'<span style="background:#ff1744;color:#fff;font-size:10px;'
            f'font-weight:800;letter-spacing:2px;padding:3px 10px;'
            f'border-radius:2px;flex-shrink:0;white-space:nowrap;">⚡ BREAKING</span>'
            f'<span style="color:#ffffff;font-size:16px;font-weight:600;flex:1;">'
            f'{h["title"]}</span>'
            f'<span style="color:#888;font-size:11px;white-space:nowrap;flex-shrink:0;">'
            f'{h["source"]} · {age_str}</span>'
            f'</div>',
            unsafe_allow_html=True)
    else:
        # Quiet — show most recent headline as a neutral context line
        h       = headlines[0]
        age_str = f"{h['age_minutes']}m ago" if h['age_minutes'] < 60 else f"{h['age_minutes']//60}h ago"
        st.markdown(
            f'<div style="background:#0a0a0a;border-top:2px solid #2a2a2a;'
            f'border-bottom:2px solid #2a2a2a;padding:8px 20px;'
            f'display:flex;align-items:center;gap:16px;">'
            f'<span style="color:#707070;font-size:10px;font-weight:700;'
            f'letter-spacing:2px;flex-shrink:0;white-space:nowrap;">HEADLINES</span>'
            f'<span style="color:#d0d0d0;font-size:15px;font-weight:500;flex:1;">'
            f'{h["title"]}</span>'
            f'<span style="color:#505050;font-size:11px;white-space:nowrap;flex-shrink:0;">'
            f'{h["source"]} · {age_str}</span>'
            f'</div>',
            unsafe_allow_html=True)

news_bar()

@st.fragment(run_every=3600)
def summary_bar():
    summary = get_ai_market_summary()
    if not summary:
        return
    now_et   = datetime.now(pytz.timezone("America/New_York"))
    time_str = now_et.strftime("%-I:%M %p ET")
    st.markdown(
        f'<div style="background:#080d08;border-left:4px solid #00e676;'
        f'border-bottom:1px solid #1e1e1e;padding:7px 16px;'
        f'display:flex;align-items:center;gap:14px;">'
        f'<span style="color:#00e676;font-size:9px;font-weight:700;'
        f'letter-spacing:2px;white-space:nowrap;flex-shrink:0;">AI SUMMARY</span>'
        f'<span style="color:#e8e8e8;font-size:13px;font-weight:500;flex:1;">'
        f'{summary}</span>'
        f'<span style="color:#505050;font-size:10px;white-space:nowrap;flex-shrink:0;">'
        f'Updated {time_str}</span>'
        f'</div>',
        unsafe_allow_html=True)

summary_bar()

# =============================================================================
# TOP ROW — indices + clock + market status  (every 60 s)
# =============================================================================
@st.fragment(run_every=60)
def top_row():
    market  = get_market_status() or {}
    indices = get_indices_data()  or {}
    MODE    = get_mode()
    KEY     = mk(MODE)
    now_et  = datetime.now(pytz.timezone("America/New_York"))
    time_str = now_et.strftime("%-I:%M %p").lower()

    idx_cells = ""
    for name, d in indices.items():
        raw = d.get(KEY)
        if KEY == "pct_1d":
            colour, arrow, display = fmt_1d(raw)
        else:
            colour, arrow, display = cl(raw), ar(raw), fpc(raw, 2)
        idx_cells += (
            f'<div class="idx-cell">'
            f'<div class="idx-lbl">{name}</div>'
            f'<div class="idx-pct {colour}">{arrow}{display}</div>'
            f'<div class="idx-px">${fp(d.get("price"))}</div>'
            f'</div>')

    session  = get_session()
    if session == "open":
        mkt_cls  = "mkt-open"
        mkt_stxt = "MARKET: OPEN"
        mkt_col  = "pos"
    elif session == "pre":
        mkt_cls  = "mkt-pre"
        mkt_stxt = "PRE-MARKET"
        mkt_col  = "gld"
    elif session == "after":
        mkt_cls  = "mkt-after"
        mkt_stxt = "AFTER HOURS"
        mkt_col  = "gld"
    else:
        mkt_cls  = "mkt-closed"
        mkt_stxt = "MARKET: CLOSED"
        mkt_col  = "neg"

    # Big readable mode bar
    mode_cls = {"1D":"mode-1d","1M":"mode-1m","YTD":"mode-ytd"}[MODE]
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
        # MODE BAR — large, coloured, impossible to miss
        f'<div class="mode-bar" style="padding:10px 14px;">'
        f'<span class="mode-label">DISPLAY MODE</span>'
        f'<span class="{mode_cls}">{MODE}</span>'
        f'<span style="font-size:13px;color:#505050;margin-left:4px;">'
        f'— {mode_desc}</span>'
        f'</div>',
        unsafe_allow_html=True)

top_row()

# =============================================================================
# ROW 2 — MCI (never rotates) | PORTFOLIO (rotates with mode)
# =============================================================================
col_mci, col_port = st.columns([1, 3], gap="small")

with col_mci:
    @st.fragment(run_every=300)
    def mci_panel():
        vol    = get_volatility_data()         or {}
        mci    = get_market_confidence_index() or {}
        score  = mci.get("score", 0)
        mlabel = mci.get("label", "—")
        vc     = vol.get("vix_current", 0)
        vma    = vol.get("vix_30dma", 0)
        facts  = mci.get("factors", {})
        gc     = ("#00e676" if score >= 75 else "#ffd54f" if score >= 55
                  else "#ff9800" if score >= 35 else "#ff1744")

        # VIX vs 30DMA conditional colour
        diff = vc - vma
        if diff < -1.0:
            vix_col = "#00e676"   # more than 1pt below MA = calm / green
        elif diff > 1.0:
            vix_col = "#ff1744"   # more than 1pt above MA = elevated / red
        else:
            vix_col = "#ffffff"   # within 1pt = white

        fbars = "".join(
            f'<div class="fb-row">'
            f'<div class="fb-top"><span>{fn}</span>'
            f'<span style="color:#ccc">{fv:.0f}</span></div>'
            f'<div class="fb-bg"><div class="fb-fill" '
            f'style="background:{gc};width:{fv:.0f}%;"></div></div></div>'
            for fn, fv in facts.items())

        st.markdown(
            f'<div class="card" style="border-right:2px solid #1e1e1e;">'
            f'<div class="card-hdr">Market Confidence</div>'
            f'<div class="mci-num" style="color:{gc};">{score:.0f}</div>'
            f'<div class="mci-lbl" style="color:{gc};">{mlabel}</div>'
            f'<div class="vix-duo">'
            f'<div class="vix-blk"><div class="vix-l">VIX</div>'
            f'<div class="vix-v" style="color:{vix_col};">{fp(vc)}</div></div>'
            f'<div style="width:1px;background:#1a1a1a;"></div>'
            f'<div class="vix-blk"><div class="vix-l">VIX 30DMA</div>'
            f'<div class="vix-v" style="color:#c0c0c0;">{fp(vma)}</div></div>'
            f'</div>'
            f'<div class="fbar">{fbars}</div></div>',
            unsafe_allow_html=True)
    mci_panel()

with col_port:
    @st.fragment(run_every=60)
    def portfolio_panel():
        port   = get_portfolio_data() or {}
        MODE   = get_mode()
        KEY    = mk(MODE)
        assets = port.get("assets", {})
        pf     = port.get("portfolio", {})
        xeqt   = assets.get("XEQT", {})
        btc    = assets.get("BTC", {})
        beta   = pf.get("beta")
        corr   = pf.get("correlation")
        alpha  = pf.get("alpha_bps")
        ret    = pf.get("return_ytd") if MODE == "YTD" else pf.get("return_1d")

        raw_x  = xeqt.get(KEY)
        raw_b  = btc.get(KEY)
        if KEY == "pct_1d":
            xc, xa, xd = fmt_1d(raw_x, is_btc=False)
            bc, ba, bd = fmt_1d(raw_b, is_btc=True)
            if in_reset_window():
                ret = None   # show as white 0.00% via fmt_1d
                rc, ra, rd = "t0", "", "+0.00%"
            else:
                rc, ra, rd = cl(ret), ar(ret), fpc(ret)
        else:
            xc, xa, xd = cl(raw_x), ar(raw_x), fpc(raw_x)
            bc, ba, bd = cl(raw_b), ar(raw_b), fpc(raw_b)
            rc, ra, rd = cl(ret), ar(ret), fpc(ret)
        x_pct = raw_x  # keep for legacy compat
        b_pct = raw_b

        stats = (
            f'<div class="stats-row">'
            f'<div class="stat-box"><div class="stat-lbl">Return ({MODE})</div>'
            f'<div class="stat-val {cl(ret)}">{fpc(ret)}</div></div>'
            f'<div class="stat-box"><div class="stat-lbl">Beta vs SPY</div>'
            f'<div class="stat-val t0">{f"{beta:.2f}" if beta else "—"}</div></div>'
            f'<div class="stat-box"><div class="stat-lbl">Correlation</div>'
            f'<div class="stat-val t0">{f"{corr:.3f}" if corr else "—"}</div></div>'
            f'<div class="stat-box"><div class="stat-lbl">Alpha vs SPY</div>'
            f'<div class="stat-val {cl(alpha)}">'
            f'{f"{alpha:+.0f} bps" if alpha is not None else "—"}</div></div>'
            f'</div>')

        table = (
            f'<div class="pt-hd" style="grid-template-columns:1fr 1.1fr 1fr 1fr;">'
            f'<div>Ticker</div><div>Price</div><div>Change ({MODE})</div>'
            f'<div style="text-align:right;">Portfolio Return</div></div>'
            f'<div class="pt-r" style="grid-template-columns:1fr 1.1fr 1fr 1fr;">'
            f'<div class="pt-sym">XEQT</div>'
            f'<div class="pt-px">{fp(xeqt.get("price"))}</div>'
            f'<div class="pt-ch {xc}">{xa}{xd}</div>'
            f'<div style="text-align:right;">'
            f'<div class="pt-ret {rc}">{ra}{rd}</div>'
            f'<div class="pt-wt">BLENDED 80/20</div></div></div>'
            f'<div class="pt-r" style="grid-template-columns:1fr 1.1fr 1fr 1fr;">'
            f'<div class="pt-sym">BTC</div>'
            f'<div class="pt-px">${fp(btc.get("price"),0)}</div>'
            f'<div class="pt-ch {bc}">{ba}{bd}</div>'
            f'<div style="text-align:right;">'
            f'<div class="pt-wt" style="margin-top:18px;">20% WEIGHT · 24/7</div>'
            f'</div></div></div>')

        st.markdown(
            f'<div class="card"><div class="card-hdr">'
            f'<span>Portfolio · 80% XEQT / 20% BTC</span>{badge(MODE)}</div>'
            f'{stats}{table}</div>',
            unsafe_allow_html=True)
    portfolio_panel()

# =============================================================================
# ROW 3 — SECTORS | RISK | BREADTH | YIELDS
# =============================================================================
st.markdown('<div style="height:2px;background:#1e1e1e;"></div>',
            unsafe_allow_html=True)

@st.fragment(run_every=60)
def bottom_row():
    sectors = get_sectors_data() or {}
    risk    = get_risk_breadth() or {}
    yields  = get_treasury_yields() or {}
    MODE    = get_mode()
    KEY     = mk(MODE)

    c1, c2, c3, c4 = st.columns([1.6, 1, 1, 1.2], gap="small")

    with c1:
        items = list(sectors.items())
        half  = (len(items) + 1) // 2
        left  = items[:half]; right = items[half:]

        def sec_col(lst):
            rows = []
            for name, d in lst:
                raw = d.get(KEY)
                if KEY == "pct_1d":
                    colour, arrow, display = fmt_1d(raw)
                else:
                    colour, arrow, display = cl(raw), ar(raw), fpc(raw)
                rows.append(
                    f'<div class="sec-r">'
                    f'<span class="sec-n">{name}</span>'
                    f'<span class="sec-pct {colour}">{arrow}{display}</span>'
                    f'</div>')
            return "".join(rows)

        st.markdown(
            f'<div class="card" style="border-right:2px solid #1e1e1e;">'
            f'<div class="card-hdr"><span>Sectors</span>{badge(MODE)}</div>'
            f'<div class="sec-grid">'
            f'<div>{sec_col(left)}</div><div>{sec_col(right)}</div>'
            f'</div></div>',
            unsafe_allow_html=True)

    with c2:
        rr  = risk.get("risk_rotation_pct", 0) or 0
        rrl = risk.get("risk_label", "—")
        tag = {
            "Euphoric":      "tag-euph",
            "Aggressive":    "tag-agg",
            "Risk-On":       "tag-on",
            "Risk-Leaning":  "tag-lean",
            "Neutral":       "tag-neu",
            "Defensive":     "tag-def",
            "Risk-Off":      "tag-off",
            "Panic":         "tag-pan",
        }.get(rrl, "tag-neu")
        st.markdown(
            f'<div class="card" style="border-right:2px solid #1e1e1e;">'
            f'<div class="card-hdr" style="justify-content:center;">Risk Rotation</div>'
            f'<div class="big-wrap">'
            f'<div class="big-num" style="color:#ffffff;">{abs(rr):.3f}</div>'
            f'<div class="big-sub">HYG / LQD · 1 MONTH</div>'
            f'<div class="big-chg {cl(rr)}">{ar(rr)}&nbsp;{fpc(rr)}</div>'
            f'<div><span class="tag {tag}">{rrl}</span></div>'
            f'</div></div>',
            unsafe_allow_html=True)

    with c3:
        br  = risk.get("breadth_ratio") or 0
        brl = risk.get("breadth_label", "—")
        tag = {
            "Maximum Breadth":      "tag-euph",
            "Solid Breadth":        "tag-agg",
            "Risk-On Rotation":     "tag-on",
            "Healthy Participation":"tag-lean",
            "Neutral Breadth":      "tag-neu",
            "Broadening-Out":       "tag-lean",
            "Thin Participation":   "tag-def",
            "High Concentration":   "tag-nar",
            "Severe Divergence":    "tag-off",
            "Apex Concentration":   "tag-pan",
        }.get(brl, "tag-neu")
        st.markdown(
            f'<div class="card" style="border-right:2px solid #1e1e1e;">'
            f'<div class="card-hdr" style="justify-content:center;">Breadth</div>'
            f'<div class="big-wrap">'
            f'<div class="big-num" style="color:#ffffff;">{br:.3f}</div>'
            f'<div class="big-sub">RSP / SPY · 10-LEVEL SCALE</div>'
            f'<div class="big-chg t2">EQUAL-WEIGHT vs CAP</div>'
            f'<div><span class="tag {tag}">{brl}</span></div>'
            f'</div></div>',
            unsafe_allow_html=True)

    with c4:
        y_rows = ""
        for name, d in yields.items():
            yp  = d.get("yield_pct", 0) or 0
            ch1 = d.get("change_1d",  0) or 0
            cc  = "neg" if ch1 < 0 else "pos" if ch1 > 0 else "t2"
            y_rows += (
                f'<div class="y-row">'
                f'<div class="y-n">{name}</div>'
                f'<div class="y-r">{yp:.3f}%</div>'
                f'<div class="y-chg {cc}">{fpc(ch1,3)}</div>'
                f'</div>')
        st.markdown(
            f'<div class="card">'
            f'<div class="card-hdr" style="justify-content:center;">Treasury Yields</div>'
            f'<div class="y-hd">'
            f'<div>TENOR</div>'
            f'<div style="text-align:center;">RATE</div>'
            f'<div style="text-align:right;">CHG</div></div>'
            f'{y_rows}</div>',
            unsafe_allow_html=True)

bottom_row()
