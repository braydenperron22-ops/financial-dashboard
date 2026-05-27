# =============================================================================
# pages/2_Macro.py  —  MACRO & SENTIMENT
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
.main .block-container { padding:12px 16px !important; max-width:100% !important; }
[data-testid="stHorizontalBlock"] { gap:8px !important; }
[data-testid="stVerticalBlock"]   { gap:8px !important; }
.element-container,.stMarkdown    { margin:0 !important; padding:0 !important; }
::-webkit-scrollbar { display:none; }
* { font-family:'Roboto',sans-serif !important; box-sizing:border-box; }
.card  { background:#090909; border:1px solid #2e2e2e; border-radius:4px; padding:14px 16px; }
.card-hdr { font-size:10px; font-weight:700; letter-spacing:2px; color:#888;
  text-transform:uppercase; margin-bottom:12px; padding-bottom:8px;
  border-bottom:1px solid #222; }
.mtk-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
.mtk-cell { background:#0d0d0d; border:1px solid #222; border-radius:3px; padding:12px; text-align:center; }
.mtk-sym  { font-size:9px; color:#555; letter-spacing:2px; text-transform:uppercase; margin-bottom:6px; font-weight:700; }
.mtk-px   { font-size:20px; font-weight:700; color:#fff; line-height:1; }
.mtk-chg  { font-size:13px; font-weight:700; margin-top:5px; }
.pm-card  { background:#090909; border:1px solid #2e2e2e; border-radius:4px;
  padding:20px 16px; text-align:center; }
.pm-bank  { font-size:16px; font-weight:700; color:#fff; margin-bottom:6px; }
.pm-pct   { font-size:48px; font-weight:900; line-height:1; letter-spacing:-2px; }
.pm-lbl   { font-size:10px; color:#555; letter-spacing:1.5px; margin-top:6px; text-transform:uppercase; }
.pm-bar-bg{ background:#181818; height:8px; border-radius:4px; margin:10px 0; }
.pm-bar   { height:8px; border-radius:4px; }
.pm-sub   { font-size:10px; color:#333; margin-top:6px; }
.macro-row{ display:flex; align-items:center; gap:10px; padding:8px 0; border-bottom:1px solid #181818; }
.macro-row:last-child { border-bottom:none; }
.pos{color:#00e676!important;} .neg{color:#ff1744!important;}
.gld{color:#ffd54f!important;} .t2{color:#444!important;}
</style>
""", unsafe_allow_html=True)

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

# =============================================================================
# HEADER
# =============================================================================
tz_et  = pytz.timezone("America/New_York")
now_et = datetime.now(tz_et)
st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;'
    f'padding:8px 0 12px;border-bottom:2px solid #2e2e2e;margin-bottom:12px;">'
    f'<div style="font-size:18px;font-weight:700;color:#fff;letter-spacing:2px;">'
    f'⬡ MACRO &amp; SENTIMENT</div>'
    f'<div style="display:flex;align-items:center;gap:14px;">'
    f'<span style="font-size:11px;color:#444;">'
    f'{now_et.strftime("%A %B %-d · %-I:%M %p ET")}</span>'
    f'<a href="/" style="font-size:10px;color:#00bcd4;letter-spacing:1.5px;font-weight:700;'
    f'text-decoration:none;border:1px solid rgba(0,188,212,.3);'
    f'padding:4px 12px;border-radius:3px;">← TERMINAL</a>'
    f'</div></div>', unsafe_allow_html=True)

# =============================================================================
# MACRO TICKERS  — yfinance, reliable
# =============================================================================
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
                s = (df["Close"][sym] if isinstance(df.columns, pd.MultiIndex)
                     else df["Close"]).dropna()
                if len(s) >= 2:
                    out[lbl] = {"price": round(float(s.iloc[-1]), 2),
                                "pct":   round(float((s.iloc[-1]-s.iloc[-2])/s.iloc[-2]*100), 2)}
            except: out[lbl] = {"price": None, "pct": None}
        return out
    except: return {}

tickers = load_tickers()

st.markdown('<div class="card" style="margin-bottom:10px;">', unsafe_allow_html=True)
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

# =============================================================================
# POLYMARKET — wrapped in full try/except, never crashes page
# =============================================================================
def _get_pm_key():
    try:
        k = st.secrets.get("POLYMARKET_API_KEY", "")
        if k: return k
    except: pass
    import os; return os.environ.get("POLYMARKET_API_KEY", "")

def _fetch(slug):
    try:
        import requests
        h = {"User-Agent": "Mozilla/5.0 AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
             "Accept": "application/json"}
        k = _get_pm_key()
        if k: h["Authorization"] = f"Bearer {k}"
        r = requests.get(f"https://gamma-api.polymarket.com/markets?slug={slug}",
                         headers=h, timeout=8)
        if r.status_code != 200: return None
        data = r.json()
        if not data: return None
        m = data[0] if isinstance(data, list) else data
        if m.get("closed"): return None
        ops = m.get("outcomePrices") or []
        yes = no = None
        if len(ops) >= 2:
            try: yes=round(float(ops[0])*100,1); no=round(float(ops[1])*100,1)
            except: pass
        return {"title": m.get("question") or slug,
                "yes_pct": yes, "no_pct": no,
                "end_date": (m.get("endDate") or "")[:10]}
    except: return None

def _active(slugs):
    for s in slugs:
        r = _fetch(s)
        if r: return r
    return None

@st.cache_data(ttl=600, show_spinner=False)
def load_polymarket():
    try:
        BANKS = {
            "🇺🇸 Fed":  (["will-the-fed-cut-rates-at-the-june-2026-meeting",
                          "will-the-fed-cut-rates-at-the-july-2026-meeting"], "Cut"),
            "🇪🇺 ECB":  (["will-the-ecb-cut-rates-at-the-june-2026-meeting",
                          "will-the-ecb-cut-rates-at-the-july-2026-meeting"], "Cut"),
            "🇯🇵 BOJ":  (["will-the-boj-raise-rates-at-the-june-2026-meeting",
                          "will-the-boj-raise-rates-at-the-july-2026-meeting"], "Hike"),
            "🇬🇧 BOE":  (["will-the-boe-cut-rates-at-the-june-2026-meeting",
                          "will-the-boe-cut-rates-at-the-august-2026-meeting"], "Cut"),
            "🇨🇦 BOC":  (["will-the-boc-cut-rates-at-the-june-2026-meeting",
                          "will-the-boc-cut-rates-at-the-july-2026-meeting"], "Cut"),
            "🇦🇺 RBA":  (["will-the-rba-cut-rates-at-the-june-2026-meeting",
                          "will-the-rba-cut-rates-at-the-august-2026-meeting"], "Cut"),
        }
        MACRO = [
            ("🇺🇸 US Recession 2026",  ["will-the-us-enter-a-recession-in-2026","us-recession-in-2026"]),
            ("Fed Cuts ≥2x 2026",      ["will-the-fed-cut-rates-at-least-twice-in-2026"]),
            ("US CPI > 3% Jun 26",     ["will-us-cpi-be-above-3-percent-in-june-2026"]),
            ("Soft Landing 2026",      ["us-soft-landing-2026"]),
            ("Unemployment > 5%",      ["will-us-unemployment-exceed-5-percent-in-2026"]),
            ("US GDP > 2% 2026",       ["will-us-gdp-growth-exceed-2-percent-in-2026"]),
            ("Fed Any Cut 2026",       ["will-the-fed-cut-rates-in-2026"]),
            ("Global Recession 2026",  ["global-recession-2026"]),
        ]
        banks = {name: (_active(slugs), action) for name, (slugs, action) in BANKS.items()}
        macro = [(lbl, _active(slugs)) for lbl, slugs in MACRO]
        return {"banks": banks, "macro": macro,
                "ok": any(m is not None for m, _ in banks.values())}
    except Exception as e:
        return {"banks": {}, "macro": [], "ok": False, "error": str(e)}

pm = load_polymarket()
pm_ok = pm.get("ok", False)

# Status bar
status_col = "#00e676" if pm_ok else "#ff1744"
status_txt = "POLYMARKET CONNECTED" if pm_ok else "POLYMARKET UNAVAILABLE — SLUGS MAY NEED UPDATING"
st.markdown(
    f'<div style="text-align:right;margin-bottom:10px;">'
    f'<span style="font-size:9px;font-weight:700;letter-spacing:1.5px;color:{status_col};">'
    f'{status_txt}</span></div>', unsafe_allow_html=True)

# =============================================================================
# CENTRAL BANK CARDS
# =============================================================================
st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:2px;color:#444;'
            'text-transform:uppercase;margin-bottom:8px;">Central Bank Rate Decisions</div>',
            unsafe_allow_html=True)

bank_cols = st.columns(6, gap="small")
for col, (name, (market, action)) in zip(bank_cols, pm.get("banks", {}).items()):
    with col:
        st.markdown('<div class="pm-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="pm-bank">{name}</div>', unsafe_allow_html=True)
        if market and market.get("yes_pct") is not None:
            yes = market["yes_pct"]
            no  = market.get("no_pct", round(100-yes, 1))
            yc  = "#00e676" if yes>=70 else "#ffd54f" if yes>=50 else "#ff1744"
            st.markdown(
                f'<div class="pm-pct" style="color:{yc};">{yes:.0f}%</div>'
                f'<div class="pm-lbl">{action} odds</div>'
                f'<div class="pm-bar-bg">'
                f'<div class="pm-bar" style="background:{yc};width:{yes:.0f}%;"></div></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:11px;">'
                f'<span style="color:{yc};font-weight:700;">YES {yes:.0f}%</span>'
                f'<span style="color:#444;">NO {no:.0f}%</span></div>'
                f'<div class="pm-sub">Closes {market.get("end_date","—")}</div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="font-size:13px;color:#333;padding:20px 0;line-height:1.8;">'
                f'{action} odds<br>unavailable</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

# =============================================================================
# MACRO FORECASTS
# =============================================================================
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="card-hdr">Macroeconomic Forecasts · Polymarket</div>',
            unsafe_allow_html=True)
for lbl, m in pm.get("macro", []):
    pct = m.get("yes_pct") if m else None
    col = "#00e676" if pct and pct>=65 else "#ffd54f" if pct and pct>=40 else "#ff1744" if pct else "#333"
    bw  = f"{pct:.0f}%" if pct else "0%"
    st.markdown(
        f'<div class="macro-row">'
        f'<span style="font-size:13px;color:#ccc;flex:1;font-weight:500;">{lbl}</span>'
        f'<div style="width:80px;background:#181818;height:6px;border-radius:3px;">'
        f'<div style="background:{col};width:{bw};height:6px;border-radius:3px;"></div></div>'
        f'<span style="font-size:16px;font-weight:700;color:{col};min-width:48px;text-align:right;">'
        f'{f"{pct:.0f}%" if pct else "—"}</span></div>',
        unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="text-align:center;padding:10px 0 2px;font-size:10px;color:#1e1e1e;">'
            'POLYMARKET REFRESHES EVERY 10 MIN · ASSETS EVERY 2 MIN</div>',
            unsafe_allow_html=True)
