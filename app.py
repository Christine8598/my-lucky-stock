import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl
import time

# --- 0. 基礎環境修復：解決 SSL 證書問題 ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

# 初始化記憶體，這步最重要，否則點按鈕會不見
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = {}
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

# --- 1. 功能定義 ---

@st.cache_data(ttl=3600)
def get_stock_list():
    """抓取清單，加入 verify=False 避免 SSL 報錯"""
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        response = requests.get(url, verify=False, timeout=10)
        response.encoding = 'big5'
        df = pd.read_html(response.text)[0]
        df.columns = df.iloc[0]
        codes = df.iloc[1:]['有價證券代號及名稱'].str.split('　', expand=True)[0]
        clean = [c for c in codes.tolist() if len(str(c)) == 4 and str(c).isdigit() and not str(c).startswith('28')]
        return sorted(clean)
    except:
        return ["2330", "2317", "2454", "2603", "3037", "3231", "1513", "2382"]

def diagnose(sid, buy_p=0):
    try:
        t = yf.Ticker(f"{sid}.TW")
        df = t.history(period="80d")
        if df.empty or len(df) < 40: return None
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        sl = round(ma20, 1)
        status = "🟡 觀望"
        advice = f"守住 {sl} 續抱"
        if c < ma20: status, advice = "🚨 賣出", f"跌破 {sl} 快跑"
        elif bias > 10: status, advice = "🎁 停利", "落袋為安"
        elif c > ma20 and ma20 > ma60 and 0 < bias <= 5: status, advice = "🟢 買入", "趨勢安全"
            
        res = {"代碼": sid, "現價": round(c, 1), "判定": status, "指令": advice, "乖離": f"{round(bias, 1)}%"}
        if buy_p > 0:
            p_pct = ((c - buy_p) / buy_p) * 100
            res["損益%"] = f"{round(p_pct, 2)}%"
            res["成本"] = buy_p
        return res
    except: return None

# --- 2. 側邊欄：操作區 ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    # 使用 st.form 確保點擊後整頁刷新能被正確處理
    with st.form("add_form", clear_on_submit=True):
        sc = st.text_input("股票代碼")
        sp = st.number_input("買進成本", min_value=0.0, step=0.1)
        if st.form_submit_button("➕ 加入庫存"):
            if sc and sp > 0:
                st.session_state.my_stocks[sc] = sp
                st.rerun()

    if st.session_state.my_stocks:
        st.write("---")
        dt = st.selectbox("要刪除哪筆？", options=list(st.session_state.my_stocks.keys()))
        if st.button("❌ 確定刪除"):
            del st.session_state.my_stocks[dt]
            st.rerun()

# --- 3. 主畫面：顯示區 ---
st.markdown(f"<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# A. 庫存儀表板
st.subheader("📋 我的汪汪庫存監控")
if st.session_state.my_stocks:
    stock_list = list(st.session_state.my_stocks.items())
    # 這裡用橫向卡片排列，保證「右邊」看得到
    cols = st.columns(4)
    for i, (sid, cost) in enumerate(stock_list):
        res = diagnose(sid, cost)
        if res:
            with cols[i % 4]:
                st.metric(label=f"🐶 {sid}", value=res["現價"], delta=f"{res['損益%']} (成本:{cost})")
                st.caption(f"📢 {res['指令']}")
else:
    st.info("💡 汪！請點擊側邊欄（左側）登記庫存，狗狗會立刻在這裡顯示卡片喔！")

st.markdown("---")

# B. 全台股跑酷掃描
st.subheader("🐕‍🦺 發現新骨頭 (全台股掃描)")
if st.button("🚀 啟動 1700+ 檔地毯大掃描"):
    codes = get_stock_list()
    with st.status("🐕 狗狗正在穿鞋子出門巡邏...", expanded=True) as status:
        p_bar = st.progress(0)
        dog_txt = st.empty()
        found = []
        for i, c in enumerate(codes):
            pct = (i + 1) / len(codes)
            dog_txt.markdown(f"**{'&nbsp;' * int(pct*30)}🐕💨 嗅探中 {i+1}/{len(codes)} : {c}**")
            p_bar.progress(pct)
            r = diagnose(c)
            if r and r["判定"] == "🟢 買入": found.append(r)
            if i % 100 == 0: time.sleep(0.01)
        st.session_state.scan_results = found
        status.update(label="✅ 巡邏完畢！", state="complete")

# 顯示結果
if st.session_state.scan_results:
    st.write(f"### 🏆 狗狗挖到的好骨頭 (共 {len(st.session_state.scan_results)} 檔)")
    st.table(pd.DataFrame(st.session_state.scan_results))

st.caption(f"🕒 最後更新：{now_str} | 汪！")
