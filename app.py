import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl
import time
import numpy as np
import json
import os

# --- 0. 基礎設定與 SSL 修復 ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

# --- 1. 永久記憶功能：檔案存取 ---
DB_FILE = "my_stock_memory.json"

def load_memory():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_memory(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# 初始化記憶
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = load_memory()
if 'scan_results' not in st.session_state:
    st.session_state.scan_results = None

# --- 2. 核心診斷邏輯 ---
def diagnose_with_soul(sid, buy_p=0):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period="100d")
        if df.empty or len(df) < 60: return None
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        returns = df['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100
        score = min(5, max(1, int(volatility / 10)))
        
        analysis = ""
        if c > ma20 and ma20 > ma60:
            if bias <= 3: analysis = f"🐾 **黃金起跑點**：剛從月線爬起來，安全埋伏區汪！"
            else: analysis = f"🏃 **穩定慢跑中**：趨勢順暢，適合續抱看表演！"
        elif c < ma20: analysis = f"🚨 **掉進坑裡了**：已跌破月線 ({round(ma20,1)})，要小心停損！"
        else: analysis = "🌫️ **霧中散步**：方向不明，建議先觀望汪！"

        res = {
            "代碼": sid, "現價": round(c, 1), "判定": "🟢 強勢" if c > ma20 else "🔴 轉弱",
            "深度分析": analysis, "風險等級": "🦴" * score, "防守價": round(ma20, 1), "乖離": f"{round(bias, 1)}%"
        }
        if buy_p > 0:
            res["損益%"] = ((c - buy_p) / buy_p) * 100
            res["成本"] = buy_p
        return res
    except: return None

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
    except: return ["2330", "2317", "2454", "2603", "3037"]

# --- 3. 側邊欄 ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    # 這裡直接用文字輸入，不放在 Form 裡可以減少干擾
    sc = st.text_input("股票代碼")
    sp = st.number_input("買進成本", min_value=0.0, step=0.1)
    if st.button("➕ 寫入記憶存檔"):
        if sc and sp > 0:
            st.session_state.my_stocks[sc] = sp
            save_memory(st.session_state.my_stocks) # 存入檔案
            st.success(f"汪！{sc} 已存入永久記憶！")
            time.sleep(1)
            st.rerun()

    if st.session_state.my_stocks:
        st.write("---")
        del_t = st.selectbox("移除：", list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除並更新檔案"):
            del st.session_state.my_stocks[del_t]
            save_memory(st.session_state.my_stocks) # 更新檔案
            st.rerun()

# --- 4. 主畫面 ---
st.markdown(f"<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# 【上層：永久庫存卡片】
st.subheader("📋 我的永久記憶庫存")
if st.session_state.my_stocks:
    items = list(st.session_state.my_stocks.items())
    cols = st.columns(4)
    for i, (sid, cost) in enumerate(items):
        res = diagnose_with_soul(sid, cost)
        if res:
            with cols[i % 4]:
                p_color = "inverse" if res["損益%"] > 0 else "normal"
                st.metric(label=f"🐶 {sid}", value=f"{res['現價']}", delta=f"{round(res['損益%'],2)}%", delta_color=p_color)
                with st.expander("🔍 深度分析"):
                    st.write(f"**風險:** {res['風險等級']}")
                    st.write(res["深度分析"])
else: st.info("💡 汪！目前沒有存檔的骨頭。")

st.markdown("---")

# 【下層：不中斷掃描雷達】
st.subheader("🐕‍🦺 全台股地毯雷達")
if st.button("🚀 啟動掃描 (掃描中可同時登記庫存)"):
    codes = get_stock_list()
    # 這裡用這招：掃描結果會直接在頁面刷新時被 session_state 保護
    status_area = st.empty()
    progress_bar = st.progress(0)
    found = []
    
    # 為了讓掃描不被「感覺」中斷，我們把進度顯示做得很明顯
    for i, c in enumerate(codes):
        progress = (i + 1) / len(codes)
        progress_bar.progress(progress)
        if i % 10 == 0:
            status_area.markdown(f"🐕 狗狗巡邏中... 當前進度: **{int(progress*100)}%** ({c})")
        
        r = diagnose_with_soul(c)
        if r and "🟢" in r["判定"]:
            found.append(r)
            # 每掃到一個就即時更新給主人看，減少等待感
            st.session_state.scan_results = found 
            
    status_area.success("✅ 全台巡邏完畢！")

if st.session_state.scan_results:
    st.write(f"### 🏆 推薦清單 (共 {len(st.session_state.scan_results)} 檔)")
    st.table(pd.DataFrame(st.session_state.scan_results)[["代碼", "現價", "風險等級", "深度分析", "防守價"]])

st.caption(f"🕒 更新時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 汪！")
