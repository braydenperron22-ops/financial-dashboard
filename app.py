# =============================================================================
# app.py  —  MARKET TERMINAL  v11  — TV optimised, premium redesign
# =============================================================================
from datetime import datetime
import pytz
import streamlit as st
from config import PORTFOLIO
from data.fetcher import (
    get_header_ticker_data, get_indices_data,
    get_market_confidence_index, get_market_status, get_portfolio_data,
    get_risk_breadth, get_sectors_data, get_treasury_yields,
    get_volatility_data, get_ai_market_summary, get_market_news,
    get_chart_data, prefetch_all,
    is_us_holiday, is_tsx_holiday,
    get_futures_data,
)

st.set_page_config(page_title="MARKET TERMINAL", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

/* ── RESET ── */
#MainMenu,footer,header,[data-testid="stToolbar"],
[data-testid="stHeader"],.stDeployButton { display:none !important; }
.stApp { background:#050505 !important; padding-top:0 !important; margin-top:0 !important; }
.main .block-container { padding:0 !important; max-width:100% !important; margin-top:0 !important; }
.stApp>div,[data-testid="stAppViewContainer"],[data-testid="stAppViewBlockContainer"],
[data-testid="block-container"],section.main>div,
.appview-container .main .block-container
{ padding-top:0 !important; margin-top:0 !important; }
[data-testid="stHorizontalBlock"] { gap:0 !important; padding:0 !important; }
[data-testid="column"]>div { padding:0 !important; }
[data-testid="stVerticalBlock"] { gap:0 !important; }
.element-container,.stMarkdown { margin:0 !important; padding:0 !important; }
::-webkit-scrollbar { display:none; }

/* ── FONTS ── */
* { font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important;
    box-sizing:border-box; -webkit-font-smoothing:antialiased; }
.mono,.idx-pct,.idx-px,.clock-time,.mci-num,.vix-v,
.pt-px,.pt-ch,.pt-ret,.stat-val,.big-num,.y-r,
.ti-p,.ti-c,.ti-s,.night-clock
{ font-family:'IBM Plex Mono','Courier New',monospace !important; }

/* ── TICKER ── */
.tkr-outer {
  width:100vw; position:relative; left:50%; transform:translateX(-50%);
  overflow:hidden; background:#000;
  border-bottom:1px solid #1a1a1a; padding:10px 0;
}
.tkr-track { display:inline-block; white-space:nowrap; animation:tkr 200s linear infinite; }
.tkr-track:hover { animation-play-state:paused; }
@keyframes tkr { 0%{transform:translateX(0)} 100%{transform:translateX(-50%)} }
.ti   { display:inline-flex; align-items:baseline; gap:8px; margin:0 28px; }
.ti-s { color:#fff; font-weight:700; font-size:14px; letter-spacing:.3px; }
.ti-p { color:#555; font-size:12px; }
.ti-c { font-weight:700; font-size:14px; }
.td   { display:inline-block; margin:0 20px; font-size:11px; color:#00bcd4;
        background:rgba(0,188,212,.06); padding:2px 10px;
        border:1px solid rgba(0,188,212,.2); border-radius:3px;
        font-weight:600; vertical-align:middle; letter-spacing:.5px; }

/* ── NEWS STRIP ── */
.news-breaking { display:flex; align-items:center; gap:14px;
  background:linear-gradient(90deg,#1a0000 0%,#0f0000 100%);
  border-bottom:1px solid #ff174430; padding:9px 20px; }
.news-quiet { display:flex; align-items:center; gap:14px;
  background:#080808; border-bottom:1px solid #1a1a1a; padding:9px 20px; }

/* ── INDICES ── */
.idx-row { display:flex; width:100%; background:#070707;
  border-bottom:1px solid #151515; }
.idx-cell { flex:1; padding:14px 12px; text-align:center;
  border-right:1px solid #111; position:relative; }
.idx-cell:last-of-type { border-right:none; }
.idx-lbl  { font-size:9px; color:#555; letter-spacing:2px;
  text-transform:uppercase; margin-bottom:6px; font-weight:600; }
.idx-pct  { font-size:32px; font-weight:800; line-height:1; letter-spacing:-1px; }
.idx-px   { font-size:11px; color:#555; margin-top:5px; letter-spacing:.3px; }

/* Clock / Market status */
.clock-cell { width:200px; flex-shrink:0; padding:14px;
  display:flex; flex-direction:column; justify-content:center; align-items:center;
  border-left:1px solid #111; background:#070707; }
.clock-time { font-size:36px; font-weight:700; color:#fff; line-height:1; }
.clock-sub  { font-size:9px; color:#444; letter-spacing:2.5px; margin-top:6px; font-weight:500; }
.mkt-cell { width:220px; flex-shrink:0; padding:14px;
  display:flex; align-items:center; justify-content:center;
  border-left:1px solid #111; background:#070707; }
.mkt-open   { background:rgba(0,230,118,.06); border:1px solid rgba(0,230,118,.3);
  padding:10px 18px; width:100%; text-align:center; border-radius:4px; }
.mkt-closed { background:rgba(255,23,68,.06); border:1px solid rgba(255,23,68,.3);
  padding:10px 18px; width:100%; text-align:center; border-radius:4px; }
.mkt-pre    { background:rgba(255,213,79,.06); border:1px solid rgba(255,213,79,.3);
  padding:10px 18px; width:100%; text-align:center; border-radius:4px; }
.mkt-after  { background:rgba(255,213,79,.06); border:1px solid rgba(255,213,79,.3);
  padding:10px 18px; width:100%; text-align:center; border-radius:4px; }
.mkt-s  { font-size:14px; font-weight:700; letter-spacing:.5px; }
.mkt-cd { font-size:11px; font-weight:500; margin-top:5px; color:#888; }

/* ── MODE BAR ── */
.mode-bar { background:#070707; padding:7px 18px;
  border-bottom:1px solid #111; display:flex; align-items:center; gap:14px; }
.mode-label { font-size:9px; color:#444; letter-spacing:2px; font-weight:600; text-transform:uppercase; }
.mode-pill  { font-size:13px; font-weight:800; letter-spacing:3px;
  padding:3px 12px; border-radius:3px; text-transform:uppercase; }
.mode-1d    { background:rgba(0,230,118,.1); color:#00e676; border:1px solid rgba(0,230,118,.25); }
.mode-1m    { background:rgba(0,188,212,.1); color:#00bcd4; border:1px solid rgba(0,188,212,.25); }
.mode-ytd   { background:rgba(255,213,79,.1); color:#ffd54f; border:1px solid rgba(255,213,79,.25); }
.mode-desc  { font-size:12px; color:#333; font-weight:400; }

/* ── AI SUMMARY ── */
.ai-bar { display:flex; align-items:center; gap:14px;
  background:#070707; border-bottom:1px solid #111; padding:8px 18px; }
.ai-tag { font-size:8px; font-weight:700; letter-spacing:2px; color:#00e676;
  background:rgba(0,230,118,.08); border:1px solid rgba(0,230,118,.2);
  padding:3px 8px; border-radius:3px; flex-shrink:0; }

/* ── CARD ── */
.card { background:#070707; border:1px solid #111;
  padding:14px 16px; height:100%; }
.card-hdr { font-size:9px; font-weight:700; letter-spacing:2px; color:#444;
  text-transform:uppercase; padding-bottom:8px; margin-bottom:10px;
  border-bottom:1px solid #111; display:flex;
  justify-content:space-between; align-items:center; }

/* ── MCI ── */
.mci-num { font-size:96px; font-weight:900; line-height:1;
  text-align:center; letter-spacing:-5px; }
.mci-lbl { font-size:19px; font-weight:600; text-align:center;
  letter-spacing:1.5px; margin-top:4px; }
.vix-duo { display:flex; justify-content:space-between; margin-top:12px;
  padding-top:12px; border-top:1px solid #111; }
.vix-blk { text-align:center; flex:1; }
.vix-l   { font-size:9px; color:#444; letter-spacing:1.5px; margin-bottom:6px;
  font-weight:600; text-transform:uppercase; }
.vix-v   { font-size:26px; font-weight:700; }
.fbar    { margin-top:12px; padding-top:12px; border-top:1px solid #111; }
.fb-row  { margin-bottom:6px; }
.fb-top  { display:flex; justify-content:space-between; font-size:9px;
  color:#555; margin-bottom:4px; font-weight:500; }
.fb-bg   { background:#111; height:3px; border-radius:2px; }
.fb-fill { height:3px; border-radius:2px; opacity:.7; transition:width .6s ease; }

/* ── PORTFOLIO ── */
.stats-row { display:flex; gap:6px; margin-bottom:10px; }
.stat-box  { flex:1; background:#0a0a0a; border:1px solid #111;
  border-radius:3px; padding:8px 10px; }
.stat-lbl  { font-size:8px; color:#555; letter-spacing:1.5px;
  text-transform:uppercase; margin-bottom:4px; font-weight:600; }
.stat-val  { font-size:21px; font-weight:700; letter-spacing:-.5px; }
.pt-hd     { display:grid; grid-template-columns:1fr 1.1fr 1fr 1fr;
  font-size:8px; color:#444; letter-spacing:1.5px; text-transform:uppercase;
  padding-bottom:8px; border-bottom:1px solid #111; font-weight:600; }
.pt-r      { display:grid; grid-template-columns:1fr 1.1fr 1fr 1fr;
  padding:13px 0; border-bottom:1px solid #0d0d0d; align-items:center; }
.pt-r:last-child { border-bottom:none; }
.pt-sym    { font-size:32px; font-weight:700; color:#fff; letter-spacing:-.5px; }
.pt-px     { font-size:30px; font-weight:600; transition:color .4s ease; letter-spacing:-1px; }
.pt-ch     { font-size:28px; font-weight:700; letter-spacing:-.5px; }
.pt-ret    { font-size:42px; font-weight:800; text-align:right;
  line-height:1; letter-spacing:-2px; }
.pt-wt     { font-size:10px; color:#444; text-align:right; margin-top:5px;
  font-weight:500; letter-spacing:.5px; text-transform:uppercase; }

/* ── SECTORS ── */
.sec-grid { display:grid; grid-template-columns:1fr 1fr; }
.sec-r    { display:flex; justify-content:space-between; align-items:center;
  padding:6px 4px; border-bottom:1px solid #0d0d0d; }
.sec-r:last-child { border-bottom:none; }
.sec-n    { font-size:13px; font-weight:500; letter-spacing:.1px; }
.sec-pct  { font-weight:700; font-size:13px; font-family:'IBM Plex Mono',monospace !important; }
.sec-grid>div:first-child .sec-r { padding-right:14px; border-right:1px solid #111; }
.sec-grid>div:last-child  .sec-r { padding-left:14px; }

/* ── RISK / BREADTH ── */
.big-wrap { text-align:center; padding:6px 0; }
.big-num  { font-size:56px; font-weight:900; letter-spacing:-2px; line-height:1;
  margin:6px 0 4px; }
.big-sub  { font-size:9px; color:#444; letter-spacing:1.5px; font-weight:600;
  text-transform:uppercase; }
.big-chg  { font-size:13px; font-weight:700; margin-top:8px; }
.tag      { display:inline-block; font-size:11px; font-weight:700; letter-spacing:.5px;
  padding:5px 14px; border-radius:4px; margin-top:10px; text-transform:uppercase; }
.tag-on   { background:rgba(0,230,118,.08); color:#00e676; border:1px solid rgba(0,230,118,.2); }
.tag-agg  { background:rgba(0,255,136,.08); color:#00ff88; border:1px solid rgba(0,255,136,.2); }
.tag-euph { background:rgba(57,255,20,.08); color:#39ff14; border:1px solid rgba(57,255,20,.2); }
.tag-lean { background:rgba(102,187,106,.08); color:#66bb6a; border:1px solid rgba(102,187,106,.2); }
.tag-neu  { background:rgba(144,164,174,.08); color:#90a4ae; border:1px solid rgba(144,164,174,.2); }
.tag-def  { background:rgba(255,179,0,.08); color:#ffb300; border:1px solid rgba(255,179,0,.2); }
.tag-off  { background:rgba(255,23,68,.08); color:#ff1744; border:1px solid rgba(255,23,68,.2); }
.tag-pan  { background:rgba(255,0,0,.1); color:#ff0000; border:1px solid rgba(255,0,0,.2); }
.tag-apc  { background:rgba(255,213,79,.08); color:#ffd54f; border:1px solid rgba(255,213,79,.2); }
.tag-nar  { background:rgba(255,213,79,.06); color:#ffd54f; border:1px solid rgba(255,213,79,.15); }

/* ── YIELDS ── */
.y-hd  { display:grid; grid-template-columns:1.3fr 1fr 0.9fr;
  font-size:8px; color:#444; letter-spacing:1.5px; text-transform:uppercase;
  padding-bottom:8px; border-bottom:1px solid #111; font-weight:600; }
.y-row { display:grid; grid-template-columns:1.3fr 1fr 0.9fr;
  padding:9px 0; border-bottom:1px solid #0d0d0d; align-items:center; }
.y-row:last-child { border-bottom:none; }
.y-n   { color:#ccc; font-size:13px; font-weight:500; }
.y-r   { font-size:19px; font-weight:700; color:#fff; text-align:center;
  letter-spacing:-.5px; }
.y-bp  { font-size:12px; font-weight:700; text-align:right;
  font-family:'IBM Plex Mono',monospace !important; }

/* ── COLOURS ── */
.pos { color:#00e676 !important; } .neg { color:#ff1744 !important; }
.acc { color:#00bcd4 !important; } .gld { color:#ffd54f !important; }
.org { color:#ff6d00 !important; }
.t0  { color:#ffffff !important; } .t1  { color:#888 !important; }
.t2  { color:#333 !important; }

/* ── BADGE ── */
.mb     { display:inline-block; font-size:7px; font-weight:700; letter-spacing:1.5px;
  padding:2px 7px; border-radius:3px; text-transform:uppercase; }
.mb-1d  { background:rgba(0,230,118,.1); color:#00e676; border:1px solid rgba(0,230,118,.2); }
.mb-1m  { background:rgba(0,188,212,.1); color:#00bcd4; border:1px solid rgba(0,188,212,.2); }
.mb-ytd { background:rgba(255,213,79,.1); color:#ffd54f; border:1px solid rgba(255,213,79,.2); }

/* ── DIVIDER ── */
.div-line { height:1px; background:#111; width:100%; }

/* ── FLASH ANIMATIONS ── */
@keyframes flash-pos {
  0%   { background:rgba(0,230,118,.15); text-shadow:0 0 14px #00e676; }
  100% { background:transparent; text-shadow:none; }
}
@keyframes flash-neg {
  0%   { background:rgba(255,23,68,.15); text-shadow:0 0 14px #ff1744; }
  100% { background:transparent; text-shadow:none; }
}
.flash-pos { animation:flash-pos 1.2s ease-out forwards; border-radius:3px; padding:0 3px; }
.flash-neg { animation:flash-neg 1.2s ease-out forwards; border-radius:3px; padding:0 3px; }

/* ── NIGHT MODE ── */
.night-screen { position:fixed; top:0; left:0; width:100vw; height:100vh;
  background:#000; z-index:9999; display:flex; align-items:center;
  justify-content:center; flex-direction:column; gap:6px; }
.night-clock { font-size:140px; font-weight:300; color:#d0d0d0;
  letter-spacing:-6px; line-height:1; }
.night-sub   { font-size:13px; color:#333; letter-spacing:5px; font-weight:400;
  text-transform:uppercase; }
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

def fpbp(v):
    """Format yield change as basis points. 1bp = 0.01%"""
    if v is None: return "—"
    bp = round(v * 100, 1)
    return f"{bp:+.1f} bp"

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
    if 4*60 <= t < 9*60+30:   return "pre"
    if 9*60+30 <= t < 16*60:  return "open"
    if 16*60 <= t < 20*60:    return "after"
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
    h = now.hour; dow = now.weekday()
    if dow == 6: return h >= 22 or h < 7
    return h >= 19 or h < 7

def is_futures_window():
    tz  = pytz.timezone("America/New_York")
    now = datetime.now(tz)
    if now.weekday() >= 5: return False
    t = now.hour * 60 + now.minute
    return 6*60+30 <= t < 9*60+30

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

BREAKING_KEYWORDS = [
    "breaking","urgent","fed","federal reserve","rate","cpi","gdp","inflation",
    "recession","crash","rally","surge","plunge","collapse","crisis","war",
    "oil","crude","opec","earnings","beat","miss","layoff","bankruptcy",
    "tariff","trade","sanction","default","yield","bond","treasury",
    "powell","yellen","trump","biden","election","geopolit",
    "jobs report","nonfarm","unemployment","fomc","hike","cut",
    "s&p","nasdaq","dow jones","tsx","tsx composite",
]
def is_market_headline(t): return any(kw in t.lower() for kw in BREAKING_KEYWORDS)

# =============================================================================
# SYNC MODE
# =============================================================================
sync_mode()

# =============================================================================
# NIGHT MODE
# =============================================================================
if is_night_mode():
    @st.fragment(run_every=60)
    def night_mode():
        tz      = pytz.timezone("America/New_York")
        now_et  = datetime.now(tz)
        t_str   = now_et.strftime("%-I:%M")
        ampm    = now_et.strftime("%p").lower()
        st.markdown(
            f'<div class="night-screen">'
            f'<div class="night-clock">{t_str}</div>'
            f'<div class="night-sub">{ampm} &nbsp;·&nbsp; new york</div>'
            f'</div>', unsafe_allow_html=True)
    night_mode()
    st.stop()

# =============================================================================
# ANIMATION ENGINE
# =============================================================================
st.markdown("""<script>
(function(){
  const prev={};
  function flash(el,cls){
    el.classList.remove('flash-pos','flash-neg');
    void el.offsetWidth; el.classList.add(cls);
    setTimeout(()=>el.classList.remove(cls),1300);
  }
  function countUp(el,from,to,dur){
    const start=performance.now();
    const dec=(String(to).split('.')[1]||'').length;
    const hasPct=el.textContent.includes('%');
    const hasPlus=el.textContent.startsWith('+');
    (function step(now){
      const p=Math.min((now-start)/dur,1);
      const e=p<.5?2*p*p:-1+(4-2*p)*p;
      const cur=from+(to-from)*e;
      const sign=(hasPlus&&cur>=0)?'+':'';
      el.textContent=sign+cur.toFixed(dec).replace(/\B(?=(\d{3})+(?!\d))/g,',')+(hasPct?'%':'');
      if(p<1)requestAnimationFrame(step);
    })(start);
  }
  const obs=new MutationObserver(muts=>{
    muts.forEach(m=>m.addedNodes.forEach(node=>{
      if(node.nodeType!==1)return;
      node.querySelectorAll('.idx-pct,.pt-ch,.pt-ret,.stat-val,.big-num,.y-r,.vix-v').forEach(el=>{
        const id=el.className+'|'+el.closest('[data-key]')?.dataset?.key+'|'+el.textContent;
        const num=parseFloat(el.textContent.replace(/[,%+▲▼\s]/g,''));
        if(!isNaN(num)&&id in prev&&prev[id]!==num){
          flash(el,num>prev[id]?'flash-pos':'flash-neg');
          countUp(el,prev[id],num,500);
        }
        prev[id]=num;
      });
    }));
  });
  obs.observe(document.body,{childList:true,subtree:true});
})();
</script>""", unsafe_allow_html=True)

# =============================================================================
# TICKER
# =============================================================================
@st.fragment(run_every=120)
def ticker_bar():
    header = get_header_ticker_data() or []
    items  = []
    for h in header:
        if h["type"] == "date":
            items.append(f'<span class="td">{h["label"]}</span>')
        else:
            raw  = h.get("pct_1d")
            is_b = h["label"] in ("BTC-USD","ETH-USD","COIN","MSTR")
            c,a,d = fmt_1d(raw, is_btc=is_b)
            items.append(
                f'<span class="ti">'
                f'<span class="ti-s">{h["label"]}</span>'
                f'<span class="ti-p">{fp(h.get("price"))}</span>'
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
@st.fragment(run_every=900)
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
            f'<div class="news-breaking">'
            f'<span style="background:#ff1744;color:#fff;font-size:9px;font-weight:700;'
            f'letter-spacing:1.5px;padding:3px 9px;border-radius:3px;flex-shrink:0;">⚡ BREAKING</span>'
            f'<span style="color:#fff;font-size:15px;font-weight:600;flex:1;line-height:1.3;">'
            f'{h["title"]}</span>'
            f'<span style="color:#555;font-size:10px;flex-shrink:0;white-space:nowrap;">'
            f'{h["source"]} · {age}</span>'
            f'</div>', unsafe_allow_html=True)
    elif quiet:
        h = quiet[0]
        age = f"{h['age_minutes']}m ago" if h['age_minutes']<60 else f"{h['age_minutes']//60}h ago"
        st.markdown(
            f'<div class="news-quiet">'
            f'<span style="color:#333;font-size:9px;font-weight:700;'
            f'letter-spacing:2px;flex-shrink:0;">HEADLINES</span>'
            f'<span style="color:#999;font-size:14px;font-weight:400;flex:1;">'
            f'{h["title"]}</span>'
            f'<span style="color:#333;font-size:10px;flex-shrink:0;white-space:nowrap;">'
            f'{h["source"]} · {age}</span>'
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
        f'<div class="ai-bar">'
        f'<span class="ai-tag">AI</span>'
        f'<span style="color:#ccc;font-size:13px;font-weight:400;flex:1;line-height:1.4;">'
        f'{summary}</span>'
        f'<span style="color:#333;font-size:10px;flex-shrink:0;">{t_str}</span>'
        f'</div>', unsafe_allow_html=True)

summary_bar()

# =============================================================================
# TOP ROW — indices + clock (60s)
# =============================================================================
@st.fragment(run_every=60)
def top_row():
    market  = get_market_status() or {}
    indices = get_indices_data()  or {}
    sync_mode()
    MODE = get_mode(); KEY = mk(MODE)
    now_et   = datetime.now(pytz.timezone("America/New_York"))
    time_str = now_et.strftime("%-I:%M %p").lower()
    us_hol   = get_holiday_state("us")

    futures     = get_futures_data() if is_futures_window() else {}
    FUTURES_MAP = {"S&P 500":"S&P FUT","NASDAQ":"NQ FUT","SMALL-CAP":"RUSSELL FUT"}

    idx_cells = ""
    for name, d in indices.items():
        fut_key = FUTURES_MAP.get(name) if futures else None
        fut     = futures.get(fut_key) if fut_key else None

        if fut and fut.get("price"):
            pct = fut.get("pct_1d")
            colour = cl(pct); arrow = ar(pct)
            display = fpc(pct) if pct is not None else "—"
            idx_cells += (
                f'<div class="idx-cell" style="border-top:1px solid rgba(255,213,79,.15);">'
                f'<div class="idx-lbl" style="color:#ffd54f;">{name}</div>'
                f'<div class="idx-pct {colour}">{arrow}{display}</div>'
                f'<div class="idx-px">${fp(fut["price"])} '
                f'<span style="color:#ffd54f;font-size:9px;font-weight:600;letter-spacing:1px;">FUT</span>'
                f'</div></div>')
        else:
            raw   = d.get(KEY)
            atype = "tsx" if name == "TSX" else "us"
            if KEY == "pct_1d":
                colour, arrow, display, is_hol = fmt_1d_with_holiday(raw, atype)
            else:
                colour, arrow, display, is_hol = cl(raw), ar(raw), fpc(raw,2), False
            sub       = "Holiday" if is_hol else f"${fp(d.get('price'))}"
            sub_style = "color:#333;" if is_hol else ""
            idx_cells += (
                f'<div class="idx-cell">'
                f'<div class="idx-lbl">{name}</div>'
                f'<div class="idx-pct {colour}">{arrow}{display}</div>'
                f'<div class="idx-px" style="{sub_style}">{sub}</div>'
                f'</div>')

    session = get_session()
    if us_hol:
        mkt_cls, mkt_col = "mkt-closed", "gld"
        from datetime import date as _date
        _today = datetime.now(pytz.timezone("America/New_York")).date()
        _names = {
            "Memorial Day":   lambda d: d.month==5  and d.weekday()==0 and 25<=d.day<=31,
            "Independence Day":lambda d: d.month==7 and d.day in (3,4,5),
            "Labor Day":      lambda d: d.month==9  and d.weekday()==0 and 1<=d.day<=7,
            "Thanksgiving":   lambda d: d.month==11 and d.weekday()==3 and 22<=d.day<=28,
            "Christmas":      lambda d: d.month==12 and d.day in (24,25,26),
            "New Year":       lambda d: d.month==1  and d.day in (1,2),
            "MLK Day":        lambda d: d.month==1  and d.weekday()==0 and 15<=d.day<=21,
            "Presidents Day": lambda d: d.month==2  and d.weekday()==0 and 15<=d.day<=21,
            "Good Friday":    lambda d: d.month in (3,4) and d.weekday()==4,
            "Juneteenth":     lambda d: d.month==6  and d.day in (18,19,20),
        }
        _name = next((n for n,fn in _names.items() if fn(_today)), "Market Holiday")
        mkt_stxt = f"🇺🇸 {_name.upper()}"
    elif session == "open":
        mkt_cls, mkt_stxt, mkt_col = "mkt-open",   "MARKET OPEN",    "pos"
    elif session == "pre":
        mkt_cls, mkt_stxt, mkt_col = "mkt-pre",    "PRE-MARKET",     "gld"
    elif session == "after":
        mkt_cls, mkt_stxt, mkt_col = "mkt-after",  "AFTER HOURS",    "gld"
    else:
        mkt_cls, mkt_stxt, mkt_col = "mkt-closed", "MARKET CLOSED",  "neg"

    mode_pill = {"1D":"mode-1d","1M":"mode-1m","YTD":"mode-ytd"}[MODE]
    mode_desc = {"1D":"1 Day","1M":"1 Month","YTD":"Year to Date"}[MODE]

    st.markdown(
        f'<div class="idx-row">{idx_cells}'
        f'<div class="clock-cell">'
        f'<div class="clock-time">{time_str}</div>'
        f'<div class="clock-sub">New York · ET</div></div>'
        f'<div class="mkt-cell"><div class="{mkt_cls}">'
        f'<div class="mkt-s {mkt_col}">{mkt_stxt}</div>'
        f'<div class="mkt-cd">{market.get("countdown","")}</div>'
        f'</div></div></div>'
        f'<div class="mode-bar">'
        f'<span class="mode-label">Viewing</span>'
        f'<span class="mode-pill {mode_pill}">{MODE}</span>'
        f'<span class="mode-desc">{mode_desc}</span>'
        f'</div>', unsafe_allow_html=True)

top_row()

# =============================================================================
# ROW 2 — MCI | PORTFOLIO
# =============================================================================
col_mci, col_port = st.columns([1, 3], gap="small")

with col_mci:
    @st.fragment(run_every=120)
    def mci_panel():
        vol   = get_volatility_data()         or {}
        mci   = get_market_confidence_index() or {}
        score = mci.get("score", 0)
        mlabel= mci.get("label", "—")
        vc    = vol.get("vix_current", 0)
        vma   = vol.get("vix_30dma", 0)
        facts = mci.get("factors", {})
        gc    = ("#00e676" if score>=75 else "#ffd54f" if score>=55
                 else "#ff9800" if score>=35 else "#ff1744")
        diff    = vc - vma
        vix_col = "#00e676" if diff<-1 else "#ff1744" if diff>1 else "#fff"
        fbars = "".join(
            f'<div class="fb-row"><div class="fb-top"><span>{fn}</span>'
            f'<span style="color:#888">{fv:.0f}</span></div>'
            f'<div class="fb-bg"><div class="fb-fill" style="background:{gc};width:{fv:.0f}%;"></div>'
            f'</div></div>' for fn,fv in facts.items())
        st.markdown(
            f'<div class="card" style="border-right:1px solid #111;">'
            f'<div class="card-hdr">Market Confidence</div>'
            f'<div class="mci-num" style="color:{gc};">{score:.0f}</div>'
            f'<div class="mci-lbl" style="color:{gc};">{mlabel}</div>'
            f'<div class="vix-duo">'
            f'<div class="vix-blk"><div class="vix-l">VIX</div>'
            f'<div class="vix-v" style="color:{vix_col};">{fp(vc)}</div></div>'
            f'<div style="width:1px;background:#111;"></div>'
            f'<div class="vix-blk"><div class="vix-l">30 DMA</div>'
            f'<div class="vix-v" style="color:#555;">{fp(vma)}</div></div>'
            f'</div><div class="fbar">{fbars}</div></div>',
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
        btc_pcol  = price_colour(btc_px, lv(bc2.get("sma50")),lv(bc2.get("sma200")),av(bc2.get("closes")))

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
        table = (
            f'<div class="pt-hd" style="grid-template-columns:1fr 1.1fr 1fr 1fr;">'
            f'<div>Ticker</div><div>Price</div><div>Change ({MODE})</div>'
            f'<div style="text-align:right;">Portfolio Return</div></div>'
            f'<div class="pt-r" style="grid-template-columns:1fr 1.1fr 1fr 1fr;">'
            f'<div class="pt-sym">XEQT</div>'
            f'<div class="pt-px" style="color:{xeqt_pcol};">{fp(xeqt_px)}</div>'
            f'<div class="pt-ch {xc}">{xa}{xd}</div>'
            f'<div style="text-align:right;">'
            f'<div class="pt-ret {rc}">{ra}{rd}</div>'
            f'<div class="pt-wt">{"TSX HOLIDAY" if x_hol else "Blended 80/20"}</div></div></div>'
            f'<div class="pt-r" style="grid-template-columns:1fr 1.1fr 1fr 1fr;">'
            f'<div class="pt-sym">BTC</div>'
            f'<div class="pt-px" style="color:{btc_pcol};">${fp(btc_px,0)}</div>'
            f'<div class="pt-ch {bc}">{ba}{bd}</div>'
            f'<div style="text-align:right;">'
            f'<div class="pt-wt" style="margin-top:18px;">20% Weight · 24/7</div>'
            f'</div></div></div>')
        st.markdown(
            f'<div class="card"><div class="card-hdr">'
            f'<span>Portfolio · 80% XEQT / 20% BTC</span>{badge(MODE)}</div>'
            f'{stats}{table}</div>', unsafe_allow_html=True)
    portfolio_panel()

st.markdown('<div class="div-line"></div>', unsafe_allow_html=True)

# =============================================================================
# BOTTOM ROW
# =============================================================================
@st.fragment(run_every=60)
def bottom_row():
    sync_mode()
    MODE    = get_mode(); KEY = mk(MODE)
    sectors = get_sectors_data()  or {}
    risk    = get_risk_breadth()  or {}
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
                nc = sector_name_colour(d.get("price"),d.get("sma50"),d.get("sma200"),d.get("ath"))
                rows.append(
                    f'<div class="sec-r">'
                    f'<span class="sec-n" style="color:{nc};">{name}</span>'
                    f'<span class="sec-pct {colour}">{arrow}{display}</span>'
                    f'</div>')
            return "".join(rows)
        st.markdown(
            f'<div class="card" style="border-right:1px solid #111;">'
            f'<div class="card-hdr"><span>Sectors</span>{badge(MODE)}</div>'
            f'<div class="sec-grid">'
            f'<div>{sec_col(left)}</div><div>{sec_col(right)}</div>'
            f'</div></div>', unsafe_allow_html=True)

    with c2:
        rr  = risk.get("risk_rotation_pct",0) or 0
        rrl = risk.get("risk_label","—")
        tag = {"Euphoric":"tag-euph","Aggressive":"tag-agg","Risk-On":"tag-on",
               "Risk-Leaning":"tag-lean","Neutral":"tag-neu","Defensive":"tag-def",
               "Risk-Off":"tag-off","Panic":"tag-pan"}.get(rrl,"tag-neu")
        st.markdown(
            f'<div class="card" style="border-right:1px solid #111;">'
            f'<div class="card-hdr" style="justify-content:center;">Risk Rotation</div>'
            f'<div class="big-wrap">'
            f'<div class="big-num {cl(rr)}">{abs(rr):.3f}</div>'
            f'<div class="big-sub">HYG / LQD · 1 Month</div>'
            f'<div class="big-chg {cl(rr)}">{ar(rr)}&nbsp;{fpc(rr)}</div>'
            f'<div><span class="tag {tag}">{rrl}</span></div>'
            f'</div></div>', unsafe_allow_html=True)

    with c3:
        br  = risk.get("breadth_ratio") or 0
        brl = risk.get("breadth_label","—")
        tag = {"Maximum Breadth":"tag-euph","Solid Breadth":"tag-agg",
               "Risk-On Rotation":"tag-on","Healthy Participation":"tag-lean",
               "Neutral Breadth":"tag-neu","Broadening-Out":"tag-lean",
               "Thin Participation":"tag-def","High Concentration":"tag-nar",
               "Severe Divergence":"tag-off","Apex Concentration":"tag-pan"}.get(brl,"tag-neu")
        st.markdown(
            f'<div class="card" style="border-right:1px solid #111;">'
            f'<div class="card-hdr" style="justify-content:center;">Breadth</div>'
            f'<div class="big-wrap">'
            f'<div class="big-num t0">{br:.3f}</div>'
            f'<div class="big-sub">RSP / SPY · 10-Level</div>'
            f'<div class="big-chg t2">Equal-Weight vs Cap</div>'
            f'<div><span class="tag {tag}">{brl}</span></div>'
            f'</div></div>', unsafe_allow_html=True)

    with c4:
        y_rows = ""
        for name, d in yields.items():
            yp  = d.get("yield_pct",0) or 0
            ch1 = d.get("change_1d", 0) or 0
            cc  = "neg" if ch1<0 else "pos" if ch1>0 else "t2"
            bp  = fpbp(ch1)   # basis points
            y_rows += (
                f'<div class="y-row">'
                f'<div class="y-n">{name}</div>'
                f'<div class="y-r">{yp:.3f}%</div>'
                f'<div class="y-bp {cc}">{bp}</div>'
                f'</div>')
        st.markdown(
            f'<div class="card">'
            f'<div class="card-hdr" style="justify-content:center;">Treasury Yields</div>'
            f'<div class="y-hd"><div>Tenor</div>'
            f'<div style="text-align:center;">Rate</div>'
            f'<div style="text-align:right;">Change</div></div>'
            f'{y_rows}</div>', unsafe_allow_html=True)

bottom_row()
