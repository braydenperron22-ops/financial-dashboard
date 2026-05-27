# =============================================================================
# pages/2_Macro.py  —  MACRO & SENTIMENT
# Completely isolated from app.py — any error here never touches the terminal
# =============================================================================
from datetime import datetime
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

.card { background:#090909; border:1px solid #2e2e2e; border-radius:4px; padding:14px 16px; height:100%; }
.card-hdr { font-size:10px; font-weight:700; letter-spacing:2px; color:#888;
  text-transform:uppercase; margin-bottom:12px; padding-bottom:8px;
  border-bottom:1px solid #222; display:flex; justify-content:space-between; align-items:center; }
.bank-name { font-size:22px; font-weight:700; color:#fff; margin-bottom:4px; }
.event-ttl { font-size:11px; color:#555; margin-bottom:14px; line-height:1.4; }
.prob-row  { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.prob-lbl  { font-size:11px; font-weight:700; width:32px; flex-shrink:0; }
.prob-bg   { flex:1; background:#181818; height:10px; border-radius:5px; }
.prob-fill { height:10px; border-radius:5px; }
.prob-num  { font-size:15px; font-weight:700; width:44px; text-align:right; flex-shrink:0; }
.no-data   { font-size:13px; color:#333; text-align:center; padding:20px 0; line-height:1.6; }
.rec-big   { font-size:80px; font-weight:900; line-height:1; text-align:center; letter-spacing:-3px; }
.rec-sub   { font-size:11px; color:#555; text-align:center; letter-spacing:2px; margin-top:6px; }
.mtk-grid  { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }
.mtk-cell  { background:#0d0d0d; border:1px solid #222; border-radius:3px; padding:10px; text-align:center; }
.mtk-sym   { font-size:9px; color:#555; letter-spacing:2px; text-transform:uppercase; margin-bottom:5px; font-weight:700; }
.mtk-px    { font-size:18px; font-weight:700; color:#fff; line-height:1; }
.mtk-chg   { font-size:13px; font-weight:700; margin-top:4px; }
.pos { color:#00e676 !important; } .neg { color:#ff1744 !important; }
.gld { color:#ffd54f !important; } .acc { color:#00bcd4 !important; }
.t2  { color:#444    !important; }
.status-ok  { font-size:10px; color:#00e676; letter-spacing:1px; }
.status-err { font-size:10px; color:#ff1744; letter-spacing:1px; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HELPERS
# =============================================================================
def fp(v, d=2):
    if v is None: return "—"
    try:
        if abs(v) >= 10000: return f"{v:,.0f}"
        if abs(v) >= 1000:  return f"{v:,.{d}f}"
        return f"{v:.{d}f}"
    except Exception: return "—"

def fpc(v, d=2):
    if v is None: return "—"
    try: return f"{v:+.{d}f}%"
    except Exception: return "—"

def cl(v):
    if v is None: return "t2"
    return "pos" if v >= 0 else "neg"

# =============================================================================
# HEADER
# =============================================================================
tz_et    = pytz.timezone("America/New_York")
now_et   = datetime.now(tz_et)
time_str = now_et.strftime("%A %B %-d · %-I:%M %p ET")

st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;'
    f'padding:10px 4px 8px;border-bottom:2px solid #2e2e2e;margin-bottom:10px;">'
    f'<div style="font-size:18px;font-weight:700;color:#fff;letter-spacing:2px;">'
    f'⬡ MACRO &amp; SENTIMENT</div>'
    f'<div style="display:flex;align-items:center;gap:16px;">'
    f'<span style="font-size:11px;color:#444;">{time_str}</span>'
    f'<a href="/" style="font-size:10px;color:#444;letter-spacing:2px;font-weight:700;'
    f'text-decoration:none;border:1px solid #2e2e2e;padding:3px 10px;border-radius:3px;">'
    f'← TERMINAL</a></div></div>',
    unsafe_allow_html=True)

# =============================================================================
# POLYMARKET FETCH  — completely wrapped in try/except, never crashes the page
# =============================================================================
def _get_api_key():
    try:
        k = st.secrets.get("POLYMARKET_API_KEY","")
        if k: return k
    except Exception: pass
    import os
    return os.environ.get("POLYMARKET_API_KEY","")

def _fetch_market(slug: str):
    """Fetch one Polymarket contract. Returns dict or None — never raises."""
    try:
        import requests
        HEADERS = {
            "User-Agent": "Mozilla/5.0 AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
        api_key = _get_api_key()
        if api_key:
            HEADERS["Authorization"] = f"Bearer {api_key}"

        r = requests.get(
            f"https://gamma-api.polymarket.com/markets?slug={slug}",
            headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if not data: return None
        m = data[0] if isinstance(data, list) else data
        outcomes = m.get("outcomePrices") or []
        yes_pct = no_pct = None
        if len(outcomes) >= 2:
            try:
                yes_pct = round(float(outcomes[0]) * 100, 1)
                no_pct  = round(float(outcomes[1]) * 100, 1)
            except Exception: pass
        return {
            "title":    m.get("question") or m.get("title") or slug,
            "yes_pct":  yes_pct,
            "no_pct":   no_pct,
            "volume":   m.get("volumeNum"),
            "end_date": (m.get("endDate") or "")[:10],
            "closed":   m.get("closed", False),
        }
    except Exception:
        return None

def _active_contract(slugs):
    for s in slugs:
        r = _fetch_market(s)
        if r and not r.get("closed"): return r
    return None

@st.cache_data(ttl=600, show_spinner=False)
def load_polymarket():
    """All Polymarket calls in one cached function. Errors return empty dicts."""
    BANKS = {
        "Fed (FOMC)": [
            "will-the-fed-cut-rates-at-the-june-2026-meeting",
            "will-the-fed-cut-rates-at-the-july-2026-meeting",
            "will-the-fed-cut-rates-at-the-september-2026-meeting",
        ],
        "ECB": [
            "will-the-ecb-cut-rates-at-the-june-2026-meeting",
            "will-the-ecb-cut-rates-at-the-july-2026-meeting",
        ],
        "BOJ": [
            "will-the-boj-raise-rates-at-the-june-2026-meeting",
            "will-the-boj-raise-rates-at-the-july-2026-meeting",
        ],
        "BOE": [
            "will-the-boe-cut-rates-at-the-june-2026-meeting",
            "will-the-boe-cut-rates-at-the-august-2026-meeting",
        ],
        "BOC": [
            "will-the-boc-cut-rates-at-the-june-2026-meeting",
            "will-the-boc-cut-rates-at-the-july-2026-meeting",
        ],
        "RBA": [
            "will-the-rba-cut-rates-at-the-june-2026-meeting",
            "will-the-rba-cut-rates-at-the-august-2026-meeting",
        ],
    }
    RECESSION = [
        "will-the-us-enter-a-recession-in-2026",
        "us-recession-in-2026",
        "recession-2026",
    ]
    OTHER = [
        ("Fed Cuts ≥2x 2026", "will-the-fed-cut-rates-at-least-twice-in-2026"),
        ("US CPI > 3% Jun",   "will-us-cpi-be-above-3-percent-in-june-2026"),
        ("Soft Landing",      "us-soft-landing-2026"),
        ("Unemployment >5%",  "will-us-unemployment-exceed-5-percent-in-2026"),
    ]
    banks = {b: _active_contract(s) for b, s in BANKS.items()}
    rec   = next((r for slug in RECESSION for r in [_fetch_market(slug)] if r), None)
    other = [(lbl, _fetch_market(sl)) for lbl, sl in OTHER]
    connected = any(v is not None for v in banks.values()) or rec is not None
    return {"banks": banks, "recession": rec, "other": other, "connected": connected}

@st.cache_data(ttl=120, show_spinner=False)
def load_macro_tickers():
    try:
        import yfinance as yf, pandas as pd
        TICKERS = {"DXY":"DX-Y.NYB","Gold":"GC=F","Oil":"CL=F","VIX":"^VIX",
                   "10Y":"^TNX","3M":"^IRX","BTC":"BTC-USD","Silver":"SI=F"}
        syms = list(TICKERS.values())
        df   = yf.download(syms, period="2d", auto_adjust=True, progress=False, threads=True)
        result = {}
        for lbl, sym in TICKERS.items():
            try:
                s = df["Close"][sym].dropna() if isinstance(df.columns, pd.MultiIndex) else df["Close"].dropna()
                if len(s) >= 2:
                    result[lbl] = {"price": round(float(s.iloc[-1]),2),
                                   "pct":   round(float((s.iloc[-1]-s.iloc[-2])/s.iloc[-2]*100),2)}
            except Exception:
                result[lbl] = {"price": None, "pct": None}
        return result
    except Exception:
        return {}

# =============================================================================
# LOAD DATA
# =============================================================================
with st.spinner("Loading…"):
    poly    = load_polymarket()
    tickers = load_macro_tickers()

pm_ok = poly.get("connected", False)
banks = poly.get("banks", {})
rec   = poly.get("recession")
other = poly.get("other", [])

# Status indicator
status_txt = "POLYMARKET CONNECTED" if pm_ok else "POLYMARKET UNAVAILABLE — UPDATE SLUGS IN pages/2_Macro.py"
status_cls = "status-ok" if pm_ok else "status-err"
st.markdown(f'<div style="text-align:right;margin-bottom:6px;">'
            f'<span class="{status_cls}">{status_txt}</span></div>',
            unsafe_allow_html=True)

# =============================================================================
# ROW 1 — Recession | Other Contracts | Macro Tickers
# =============================================================================
c1, c2, c3 = st.columns([1, 1.4, 2], gap="small")

with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-hdr">US Recession 2026</div>', unsafe_allow_html=True)
    if rec and rec.get("yes_pct") is not None:
        pct = rec["yes_pct"]
        col = "#ff1744" if pct>=50 else "#ffd54f" if pct>=30 else "#00e676"
        st.markdown(
            f'<div style="text-align:center;padding:8px 0;">'
            f'<div class="rec-big" style="color:{col};">{pct:.0f}%</div>'
            f'<div class="rec-sub">Probability</div>'
            f'<div style="margin:14px 0;background:#181818;height:12px;border-radius:6px;">'
            f'<div style="background:{col};width:{pct:.0f}%;height:12px;border-radius:6px;opacity:.8;"></div></div>'
            f'<div style="font-size:11px;color:#444;margin-top:6px;">Closes {rec.get("end_date","—")}</div>'
            f'</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="no-data">No active contract<br><span style="font-size:10px;">Check slug in 2_Macro.py</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-hdr">Other Macro Markets</div>', unsafe_allow_html=True)
    for lbl, d in other:
        pct = d.get("yes_pct") if d else None
        col = "#00e676" if pct and pct>=60 else "#ffd54f" if pct and pct>=40 else "#ff1744" if pct else "#333"
        bw  = f"{pct:.0f}%" if pct else "0%"
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;'
            f'border-bottom:1px solid #1a1a1a;">'
            f'<span style="font-size:13px;color:#ccc;flex:1;">{lbl}</span>'
            f'<div style="width:80px;background:#181818;height:6px;border-radius:3px;">'
            f'<div style="background:{col};width:{bw};height:6px;border-radius:3px;"></div></div>'
            f'<span style="font-size:16px;font-weight:700;color:{col};min-width:44px;text-align:right;">'
            f'{f"{pct:.0f}%" if pct else "—"}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-hdr">Macro Assets</div>', unsafe_allow_html=True)
    cells = ""
    for lbl, d in tickers.items():
        px = d.get("price"); pc = d.get("pct")
        cc = cl(pc)
        cells += (f'<div class="mtk-cell">'
                  f'<div class="mtk-sym">{lbl}</div>'
                  f'<div class="mtk-px">{fp(px)}</div>'
                  f'<div class="mtk-chg {cc}">{fpc(pc)}</div>'
                  f'</div>')
    st.markdown(f'<div class="mtk-grid">{cells}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# ROW 2 — Central Bank Cards
# =============================================================================
st.markdown(
    '<div style="font-size:10px;font-weight:700;letter-spacing:2px;color:#444;'
    'text-transform:uppercase;padding:10px 4px 6px;">Central Bank Rate Decisions</div>',
    unsafe_allow_html=True)

bank_cols = st.columns(6, gap="small")
for col, (bank, data) in zip(bank_cols, banks.items()):
    with col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="card-hdr">{bank}</div>', unsafe_allow_html=True)
        if data and data.get("yes_pct") is not None:
            yes = data["yes_pct"]
            no  = data.get("no_pct", round(100-yes,1))
            yc  = "#00e676" if yes>=70 else "#ffd54f" if yes>=50 else "#ff1744"
            title = data.get("title","—")
            short = title.replace("Will the ","").replace("Will ","")
            short = short[:52]+"…" if len(short)>52 else short
            st.markdown(
                f'<div class="event-ttl">{short}</div>'
                f'<div class="prob-row">'
                f'<span class="prob-lbl" style="color:{yc};">YES</span>'
                f'<div class="prob-bg"><div class="prob-fill" style="background:{yc};width:{yes:.0f}%;"></div></div>'
                f'<span class="prob-num" style="color:{yc};">{yes:.0f}%</span></div>'
                f'<div class="prob-row">'
                f'<span class="prob-lbl" style="color:#444;">NO</span>'
                f'<div class="prob-bg"><div class="prob-fill" style="background:#333;width:{no:.0f}%;"></div></div>'
                f'<span class="prob-num" style="color:#444;">{no:.0f}%</span></div>'
                f'<div style="font-size:10px;color:#333;text-align:center;margin-top:8px;">'
                f'Closes {data.get("end_date","—")}</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="no-data">No active contract<br>'
                '<span style="font-size:10px;">Update slug in<br>pages/2_Macro.py</span></div>',
                unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div style="text-align:center;padding:12px 0 4px;font-size:10px;color:#222;letter-spacing:1.5px;">'
    'POLYMARKET · REFRESHES EVERY 10 MINUTES</div>',
    unsafe_allow_html=True)
