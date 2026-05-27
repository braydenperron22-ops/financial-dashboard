# =============================================================================
# pages/2_Macro.py  —  MACRO & SENTIMENT DASHBOARD
# Completely isolated — errors here NEVER affect the main terminal
# =============================================================================
from datetime import datetime, timedelta
import pytz
import streamlit as st

st.set_page_config(page_title="MACRO", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');
#MainMenu,footer,header,[data-testid="stToolbar"],
[data-testid="stHeader"],.stDeployButton { display:none !important; }
.stApp { background:#050505 !important; padding-top:0 !important; }
.main .block-container { padding:10px 14px !important; max-width:100% !important; }
[data-testid="stHorizontalBlock"] { gap:8px !important; }
[data-testid="stVerticalBlock"]   { gap:8px !important; }
.element-container,.stMarkdown    { margin:0 !important; padding:0 !important; }
::-webkit-scrollbar { display:none; }
* { font-family:'Roboto',sans-serif !important; box-sizing:border-box; }

.card  { background:#090909; border:1px solid #2e2e2e; border-radius:4px; padding:14px 16px; height:100%; }
.card-hdr { font-size:10px; font-weight:700; letter-spacing:2px; color:#888;
  text-transform:uppercase; margin-bottom:12px; padding-bottom:8px;
  border-bottom:1px solid #222; display:flex; justify-content:space-between; align-items:center; }
.bank-ttl { font-size:11px; color:#555; margin-bottom:12px; line-height:1.4; min-height:32px; }
.prob-row { display:flex; align-items:center; gap:8px; margin-bottom:7px; }
.prob-lbl { font-size:10px; font-weight:700; width:28px; flex-shrink:0; }
.prob-bg  { flex:1; background:#181818; height:9px; border-radius:4px; }
.prob-fill{ height:9px; border-radius:4px; }
.prob-num { font-size:14px; font-weight:700; width:40px; text-align:right; flex-shrink:0; }
.big-pct  { font-size:52px; font-weight:900; line-height:1; text-align:center; letter-spacing:-2px; }
.big-sub  { font-size:10px; color:#555; text-align:center; letter-spacing:2px; margin-top:5px; text-transform:uppercase; }
.trend-up   { color:#00e676; font-size:11px; font-weight:700; }
.trend-down { color:#ff1744; font-size:11px; font-weight:700; }
.trend-flat { color:#555;    font-size:11px; font-weight:700; }
.no-data  { font-size:12px; color:#333; text-align:center; padding:16px 0; line-height:1.8; }
.mtk-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }
.mtk-cell { background:#0d0d0d; border:1px solid #222; border-radius:3px; padding:10px; text-align:center; }
.mtk-sym  { font-size:9px; color:#555; letter-spacing:2px; text-transform:uppercase; margin-bottom:4px; font-weight:700; }
.mtk-px   { font-size:17px; font-weight:700; color:#fff; line-height:1; }
.mtk-chg  { font-size:12px; font-weight:700; margin-top:4px; }
.macro-row{ display:flex; align-items:center; gap:10px; padding:7px 0; border-bottom:1px solid #181818; }
.macro-row:last-child { border-bottom:none; }
.pos{color:#00e676!important;}.neg{color:#ff1744!important;}
.gld{color:#ffd54f!important;}.acc{color:#00bcd4!important;}.t2{color:#444!important;}
.pill { display:inline-block; font-size:8px; font-weight:700; letter-spacing:1px;
  padding:2px 6px; border-radius:3px; text-transform:uppercase; }
.pill-live { background:rgba(0,230,118,.1); color:#00e676; border:1px solid rgba(0,230,118,.2); }
.pill-err  { background:rgba(255,23,68,.1);  color:#ff1744; border:1px solid rgba(255,23,68,.2); }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HELPERS
# =============================================================================
def fp(v, d=2):
    if v is None: return "—"
    try:
        if abs(v)>=10000: return f"{v:,.0f}"
        if abs(v)>=1000:  return f"{v:,.{d}f}"
        return f"{v:.{d}f}"
    except: return "—"

def fpc(v, d=2):
    if v is None: return "—"
    try: return f"{v:+.{d}f}%"
    except: return "—"

def cl(v): return "t2" if v is None else ("pos" if v>=0 else "neg")

def _get_pm_key():
    try:
        k = st.secrets.get("POLYMARKET_API_KEY","")
        if k: return k
    except: pass
    import os; return os.environ.get("POLYMARKET_API_KEY","")

# =============================================================================
# POLYMARKET FETCHERS
# =============================================================================
def _pm_headers():
    h = {"User-Agent":"Mozilla/5.0 AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
         "Accept":"application/json","Origin":"https://polymarket.com"}
    k = _get_pm_key()
    if k: h["Authorization"] = f"Bearer {k}"
    return h

def _fetch_market(slug):
    try:
        import requests
        r = requests.get(f"https://gamma-api.polymarket.com/markets?slug={slug}",
                         headers=_pm_headers(), timeout=10)
        if r.status_code != 200: return None
        data = r.json()
        if not data: return None
        m = data[0] if isinstance(data, list) else data
        if m.get("closed"): return None
        outcomes = m.get("outcomePrices") or []
        yes = no = None
        if len(outcomes) >= 2:
            try: yes=round(float(outcomes[0])*100,1); no=round(float(outcomes[1])*100,1)
            except: pass
        return {"title": m.get("question") or slug, "yes_pct": yes, "no_pct": no,
                "end_date": (m.get("endDate") or "")[:10],
                "volume": m.get("volumeNum"), "id": m.get("id","")}
    except: return None

def _fetch_timeseries(market_id, days=30):
    """Fetch rolling odds history for a market."""
    try:
        import requests
        end   = datetime.utcnow()
        start = end - timedelta(days=days)
        r = requests.get(
            f"https://clob.polymarket.com/prices-history"
            f"?market={market_id}&startTs={int(start.timestamp())}"
            f"&endTs={int(end.timestamp())}&interval=1d&fidelity=1",
            headers=_pm_headers(), timeout=10)
        if r.status_code != 200: return []
        data = r.json()
        history = data.get("history", [])
        return [{"t": h["t"], "p": round(float(h["p"])*100,1)} for h in history]
    except: return []

def _active(slugs):
    for s in slugs:
        r = _fetch_market(s)
        if r: return r
    return None

@st.cache_data(ttl=600, show_spinner=False)
def load_all():
    # ── Central bank rate cut/hike contracts ──────────────────────────────────
    BANK_SLUGS = {
        "🇺🇸 Fed": {
            "cut": ["will-the-fed-cut-rates-at-the-june-2026-meeting",
                    "will-the-fed-cut-rates-at-the-july-2026-meeting",
                    "will-the-fed-cut-rates-at-the-september-2026-meeting"],
            "hold": ["will-the-fed-hold-rates-at-the-june-2026-meeting"],
            "action": "Cut",
        },
        "🇪🇺 ECB": {
            "cut": ["will-the-ecb-cut-rates-at-the-june-2026-meeting",
                    "will-the-ecb-cut-rates-at-the-july-2026-meeting"],
            "action": "Cut",
        },
        "🇯🇵 BOJ": {
            "cut": ["will-the-boj-raise-rates-at-the-june-2026-meeting",
                    "will-the-boj-raise-rates-at-the-july-2026-meeting"],
            "action": "Hike",
        },
        "🇬🇧 BOE": {
            "cut": ["will-the-boe-cut-rates-at-the-june-2026-meeting",
                    "will-the-boe-cut-rates-at-the-august-2026-meeting"],
            "action": "Cut",
        },
        "🇨🇦 BOC": {
            "cut": ["will-the-boc-cut-rates-at-the-june-2026-meeting",
                    "will-the-boc-cut-rates-at-the-july-2026-meeting"],
            "action": "Cut",
        },
        "🇦🇺 RBA": {
            "cut": ["will-the-rba-cut-rates-at-the-june-2026-meeting",
                    "will-the-rba-cut-rates-at-the-august-2026-meeting"],
            "action": "Cut",
        },
    }

    banks = {}
    for name, cfg in BANK_SLUGS.items():
        market = _active(cfg["cut"])
        ts = _fetch_timeseries(market["id"]) if market and market.get("id") else []
        trend = None
        if len(ts) >= 2:
            trend = ts[-1]["p"] - ts[0]["p"]
        banks[name] = {"market": market, "timeseries": ts,
                       "trend": trend, "action": cfg["action"]}

    # ── Recession & macro forecasts ───────────────────────────────────────────
    MACRO_MARKETS = [
        ("🇺🇸 US Recession 2026",     ["will-the-us-enter-a-recession-in-2026","us-recession-in-2026"]),
        ("Fed Cuts ≥2x 2026",         ["will-the-fed-cut-rates-at-least-twice-in-2026"]),
        ("US CPI > 3% (Jun 26)",      ["will-us-cpi-be-above-3-percent-in-june-2026"]),
        ("Soft Landing 2026",         ["us-soft-landing-2026"]),
        ("Unemployment > 5% 2026",    ["will-us-unemployment-exceed-5-percent-in-2026"]),
        ("US GDP > 2% 2026",          ["will-us-gdp-growth-exceed-2-percent-in-2026"]),
        ("Fed Pivot (any cut 2026)",  ["will-the-fed-cut-rates-in-2026"]),
        ("Global Recession 2026",     ["global-recession-2026"]),
    ]
    macro = [(lbl, _active(slugs)) for lbl, slugs in MACRO_MARKETS]
    connected = any(b["market"] is not None for b in banks.values())
    return {"banks": banks, "macro": macro, "connected": connected}

@st.cache_data(ttl=120, show_spinner=False)
def load_tickers():
    try:
        import yfinance as yf, pandas as pd
        T = {"DXY":"DX-Y.NYB","Gold":"GC=F","Oil":"CL=F","VIX":"^VIX",
             "10Y":"^TNX","3M":"^IRX","BTC":"BTC-USD","Silver":"SI=F"}
        df = yf.download(list(T.values()), period="2d",
                         auto_adjust=True, progress=False, threads=True)
        out = {}
        for lbl, sym in T.items():
            try:
                s = df["Close"][sym].dropna() if isinstance(df.columns,pd.MultiIndex) else df["Close"].dropna()
                if len(s)>=2:
                    out[lbl]={"price":round(float(s.iloc[-1]),2),
                              "pct":round(float((s.iloc[-1]-s.iloc[-2])/s.iloc[-2]*100),2)}
            except: out[lbl]={"price":None,"pct":None}
        return out
    except: return {}

# =============================================================================
# HEADER
# =============================================================================
tz_et    = pytz.timezone("America/New_York")
now_et   = datetime.now(tz_et)
time_str = now_et.strftime("%A %B %-d · %-I:%M %p ET")

st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;'
    f'padding:8px 4px 8px;border-bottom:2px solid #2e2e2e;margin-bottom:10px;">'
    f'<div style="font-size:18px;font-weight:700;color:#fff;letter-spacing:2px;">'
    f'⬡ MACRO &amp; SENTIMENT</div>'
    f'<div style="display:flex;align-items:center;gap:14px;">'
    f'<span style="font-size:11px;color:#444;">{time_str}</span>'
    f'<a href="/" style="font-size:10px;color:#00bcd4;letter-spacing:1.5px;font-weight:700;'
    f'text-decoration:none;border:1px solid rgba(0,188,212,.3);'
    f'padding:4px 12px;border-radius:3px;">← TERMINAL</a>'
    f'</div></div>',
    unsafe_allow_html=True)

# =============================================================================
# LOAD
# =============================================================================
with st.spinner("Loading prediction markets…"):
    data    = load_all()
    tickers = load_tickers()

banks     = data.get("banks", {})
macro     = data.get("macro", [])
connected = data.get("connected", False)
pill      = '<span class="pill pill-live">LIVE</span>' if connected else '<span class="pill pill-err">OFFLINE</span>'

# =============================================================================
# ROW 1 — CENTRAL BANK RATE CARDS
# =============================================================================
st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;'
    f'padding:4px 0 8px;">'
    f'<span style="font-size:10px;font-weight:700;letter-spacing:2px;color:#444;'
    f'text-transform:uppercase;">Central Bank Rate Decisions</span>'
    f'{pill}</div>',
    unsafe_allow_html=True)

bank_cols = st.columns(6, gap="small")
for col, (name, bd) in zip(bank_cols, banks.items()):
    with col:
        market = bd.get("market")
        ts     = bd.get("timeseries", [])
        trend  = bd.get("trend")
        action = bd.get("action","Cut")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-hdr">{name}</div>', unsafe_allow_html=True)

        if market and market.get("yes_pct") is not None:
            yes = market["yes_pct"]
            no  = market.get("no_pct", round(100-yes,1))
            yc  = "#00e676" if yes>=70 else "#ffd54f" if yes>=50 else "#ff1744"

            # Trend arrow vs 30 days ago
            if trend is not None:
                if trend > 2:   tr_html = f'<span class="trend-up">▲ +{trend:.1f}pp (30d)</span>'
                elif trend < -2:tr_html = f'<span class="trend-down">▼ {trend:.1f}pp (30d)</span>'
                else:            tr_html = f'<span class="trend-flat">→ {trend:+.1f}pp (30d)</span>'
            else: tr_html = ""

            title = market.get("title","—")
            short = title.replace("Will the ","").replace("Will ","")
            short = short[:50]+"…" if len(short)>50 else short

            st.markdown(
                f'<div class="bank-ttl">{short}</div>'
                f'<div style="text-align:center;margin:8px 0;">'
                f'<div class="big-pct" style="color:{yc};">{yes:.0f}%</div>'
                f'<div class="big-sub">{action} probability</div>'
                f'<div style="margin-top:6px;">{tr_html}</div>'
                f'</div>'
                f'<div class="prob-row">'
                f'<span class="prob-lbl" style="color:{yc};">YES</span>'
                f'<div class="prob-bg"><div class="prob-fill" style="background:{yc};width:{yes:.0f}%;"></div></div>'
                f'<span class="prob-num" style="color:{yc};">{yes:.0f}%</span></div>'
                f'<div class="prob-row">'
                f'<span class="prob-lbl" style="color:#444;">NO</span>'
                f'<div class="prob-bg"><div class="prob-fill" style="background:#2a2a2a;width:{no:.0f}%;"></div></div>'
                f'<span class="prob-num" style="color:#444;">{no:.0f}%</span></div>'
                f'<div style="font-size:9px;color:#333;text-align:right;margin-top:6px;">'
                f'Closes {market.get("end_date","—")}</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="no-data">{action} odds<br>unavailable<br>'
                f'<span style="font-size:9px;color:#222;">Update slug in<br>pages/2_Macro.py</span></div>',
                unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# =============================================================================
# ROW 2 — MACRO FORECASTS | MACRO TICKERS
# =============================================================================
c1, c2 = st.columns([1.4, 2], gap="small")

with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-hdr">Macroeconomic Forecasts</div>', unsafe_allow_html=True)
    for lbl, m in macro:
        pct = m.get("yes_pct") if m else None
        col = "#00e676" if pct and pct>=65 else "#ffd54f" if pct and pct>=40 else "#ff1744" if pct else "#333"
        bw  = f"{pct:.0f}%" if pct else "0%"
        val = f"{pct:.0f}%" if pct else "—"
        st.markdown(
            f'<div class="macro-row">'
            f'<span style="font-size:13px;color:#ccc;flex:1;font-weight:500;">{lbl}</span>'
            f'<div style="width:70px;background:#181818;height:6px;border-radius:3px;flex-shrink:0;">'
            f'<div style="background:{col};width:{bw};height:6px;border-radius:3px;"></div></div>'
            f'<span style="font-size:16px;font-weight:700;color:{col};min-width:48px;text-align:right;">'
            f'{val}</span></div>',
            unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-hdr">Macro Assets · Live</div>', unsafe_allow_html=True)
    cells = ""
    for lbl, d in tickers.items():
        px = d.get("price"); pc = d.get("pct")
        cells += (f'<div class="mtk-cell">'
                  f'<div class="mtk-sym">{lbl}</div>'
                  f'<div class="mtk-px">{fp(px)}</div>'
                  f'<div class="mtk-chg {cl(pc)}">{fpc(pc)}</div>'
                  f'</div>')
    st.markdown(f'<div class="mtk-grid">{cells}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div style="text-align:center;padding:10px 0 2px;font-size:10px;color:#1e1e1e;letter-spacing:1.5px;">'
    'POLYMARKET · REFRESHES EVERY 10 MINUTES · MACRO ASSETS EVERY 2 MINUTES</div>',
    unsafe_allow_html=True)
