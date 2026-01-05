import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl
import time

# --- 0. 基礎設定 ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = {}
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

# --- 1. 功能邏輯 ---
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
        
        status = "🟢 買入/持有" if c > ma20 and ma20 > ma60 and bias <= 5 else "🚨 警戒/觀望"
        res = {"代碼": sid, "現價": round(c, 1), "判定": status, "指令": f"防守 {round(ma20, 1)}"}
        if buy_p > 0:
            p_pct = ((c - buy_p) / buy_p) * 100
            res["損益%"] = f"{round(p_pct, 2)}%"
            res["成本"] = buy_p
        return res
    except: return None

# --- 2. 側邊欄 ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    with st.form("add_form", clear_on_submit=True):
        sc = st.text_input("股票代碼", placeholder="例如: 2330")
        sp = st.number_input("買進成本", min_value=0.0, step=0.1)
        if st.form_submit_button("➕ 確定加入庫存"):
            if sc and sp > 0:
                st.session_state.my_stocks[sc] = sp
                st.rerun()
    
    if st.session_state.my_stocks:
        st.write("---")
        del_target = st.selectbox("要移除哪檔？", list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除這筆"):
            del st.session_state.my_stocks[del_target]
            st.rerun()

# --- 3. 主畫面 (上下分層) ---
st.markdown(f"<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# 【上層：橫向庫存卡片】
st.subheader("📋 我的汪汪庫存")
if st.session_state.my_stocks:
    stock_items = list(st.session_state.my_stocks.items())
    # 建立橫向列，每排最多 4 檔股票
    cols = st.columns(4) 
    for i, (sid, cost) in enumerate(stock_items):
        res = diagnose(sid, cost)
        if res:
            with cols[i % 4]:
                # 使用 info 方框做成橫向卡片視覺
                st.info(f"**🐶 {sid}**\n\n現價：**{res['現價']}**\n\n成本：**{cost}**\n\n損益：**{res['損益%']}**\n\n📢 {res['指令']}")
else:
    st.info("💡 汪！妳的口袋空空，請在左側登記妳的骨頭！")

st.markdown("---")

# 【下層：掃描區】
st.subheader("🐕‍🦺 發現新骨頭 (全台大掃描)")
if st.button("🚀 啟動 1700+ 檔地毯大掃描"):
    codes = get_stock_list()
    with st.status("🐕 狗狗正在巡邏全台灣...", expanded=True) as status:
        p_bar = st.progress(0)
        dog_txt = st.empty()
        found = []
        for i, c in enumerate(codes):
            pct = (i + 1) / len(codes)
            dog_txt.markdown(f"**{'&nbsp;' * int(pct*20)}🐕💨 正在嗅探 {c}...**")
            p_bar.progress(pct)
            r = diagnose(c)
            if r and "🟢" in r["判定"]: found.append(r)
            if i % 100 == 0: time.sleep(0.01)
        st.session_state.scan_results = found
        status.update(label="✅ 汪！全台巡邏完畢！", state="complete")

# 顯示掃描結果
if st.session_state.scan_results:
    st.write(f"### 🏆 狗狗幫妳挖到的精華 (共 {len(st.session_state.scan_results)} 檔)")
    st.table(pd.DataFrame(st.session_state.scan_results))

st.caption(f"🕒 更新時間：{now_str} | 汪！")
