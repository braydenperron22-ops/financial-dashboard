from datetime import datetime
import pytz
import streamlit as st

st.set_page_config(page_title="MACRO", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
#MainMenu,footer,header,[data-testid="stToolbar"],
[data-testid="stHeader"],.stDeployButton { display:none !important; }
.stApp { background:#050505 !important; }
* { color:#fff; font-family:'Roboto',sans-serif !important; }
</style>
""", unsafe_allow_html=True)

tz_et  = pytz.timezone("America/New_York")
now_et = datetime.now(tz_et)

st.markdown(f"## ⬡ MACRO & SENTIMENT")
st.markdown(f"*{now_et.strftime('%A %B %-d · %-I:%M %p ET')}*")
st.markdown("[← Back to Terminal](/)")
st.markdown("---")
st.markdown("### Page is loading correctly ✅")
st.markdown("Polymarket data coming soon once slugs are confirmed.")
