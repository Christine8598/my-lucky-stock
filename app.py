import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl
import time

# --- 基礎環境設定 ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

# 初始化記憶體
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = {}
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

# --- 核心邏輯 ---
@st.cache_data(ttl=3600)
def get_stock_list():
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        response = requests.get(url, verify=False, timeout=10)
        response.encoding = 'big5'
        df = pd.read_html(response.text)[0]
        df.columns = df.iloc[0]
        codes = df.iloc[1:]['有價證券代號及名稱'].str.split('　', expand=True)[0]
        return [c for c in codes.tolist() if len(str(c)) == 4 and str(c).isdigit() and not str(c).startswith('28')]
    except:
        return ["2330", "2317", "2454", "2603", "3037"]

def diagnose(sid, buy_p=0):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period="80d")
        if df.empty or len(df) < 40: return None
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        status = "🟢 適合持有" if c > ma20 and ma20 > ma60 else "🚨 警戒"
        res = {"代碼": sid, "現價": round(c, 1), "判定": status, "指令": f"防守 {round(ma20, 1)}"}
        if buy_p > 0:
            p_pct = ((c - buy_p) / buy_p) * 100
            res["損益%"] = f"{round(p_pct, 2)}%"
            res["成本"] = buy_p
        return res
    except: return None

# --- 側邊欄：輸入與登記 ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    with st.form("add_stock", clear_on_submit=True):
        sc = st.text_input("輸入股票代碼")
        sp = st.number_input("輸入買進成本", min_value=0.0)
        if st.form_submit_button("➕ 確定加入庫存"):
            if sc and sp > 0:
                st.session_state.my_stocks[sc] = sp
                st.rerun()
    
    if st.session_state.my_stocks:
        st.write("---")
        if st.button("🧨 全部清空庫存"):
            st.session_state.my_stocks = {}
            st.rerun()

# --- 主畫面布局 ---
st.markdown(f"<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# 這裡把主畫面拆成「左庫存、右掃描」，保證兩邊都看得見
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("📋 我的汪汪庫存")
    if st.session_state.my_stocks:
        for sid, cost in st.session_state.my_stocks.items():
            res = diagnose(sid, cost)
            if res:
                # 用卡片方式顯示，絕對不會被推到右邊外面
                st.info(f"🐶 **{sid}** | 現價: **{res['現價']}** | 成本: **{cost}** | 損益: **{res['損益%']}**\n\n📢 {res['指令']}")
    else:
        st.write("目前沒有登記骨頭汪！")

with right_col:
    st.subheader("🐕‍🦺 掃描新骨頭")
    if st.button("🚀 啟動全台大掃描"):
        codes = get_stock_list()
        with st.status("正在巡邏中...", expanded=True) as status:
            p_bar = st.progress(0)
            dog_txt = st.empty()
            found = []
            for i, c in enumerate(codes):
                pct = (i + 1) / len(codes)
                dog_txt.markdown(f"**{'&nbsp;' * int(pct*20)}🐕💨 {c}**")
                p_bar.progress(pct)
                r = diagnose(c)
                if r and r["判定"] == "🟢 適合持有": found.append(r)
            st.session_state.scan_results = found
            status.update(label="✅ 巡邏完成！", state="complete")

    if st.session_state.scan_results:
        st.write("### 🏆 挖到的精華：")
        st.table(pd.DataFrame(st.session_state.scan_results))

st.caption(f"🕒 系統時間：{now_str}")
