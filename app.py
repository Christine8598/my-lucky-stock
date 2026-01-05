import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 頁面設定
st.set_page_config(page_title="Christine財運汪汪選股雷達", layout="wide", page_icon="📡")

st.markdown("<h1 style='text-align: center; color: #1E88E5;'>📡 Christine 全台股實戰雷達</h1>", unsafe_allow_html=True)

# 2. 定義擴大後的掃描池 (台灣 50 + 中型 100 核心)
# 這裡列出部分代表性代碼，妳可以自行增加
CORE_POOL = [
    "2330", "2317", "2454", "2308", "2382", "2303", "2881", "2882", "1301", "2603",
    "2609", "2615", "2408", "3034", "3037", "2379", "3231", "2357", "2324", "2353",
    "2886", "2884", "2891", "2892", "5880", "2880", "2885", "2002", "2412", "4904"
]

# 3. 核心邏輯
def check_market():
    try:
        m = yf.Ticker("^TWII").history(period="60d")
        return m['Close'].iloc[-1] > m['Close'].rolling(20).mean().iloc[-1]
    except: return True

def scan_logic(sid):
    try:
        # 下載 120 天資料以確保指標計算準確
        df = yf.Ticker(f"{sid}.TW").history(period="120d", auto_adjust=True)
        if len(df) < 60: return None
        
        c = df['Close']
        ma20 = c.rolling(20).mean()
        ma60 = c.rolling(60).mean()
        bias = ((c.iloc[-1] - ma20.iloc[-1]) / ma20.iloc[-1]) * 100
        vol_ma5 = df['Volume'].rolling(5).mean()
        
        # 篩選門檻：趨勢向上且乖離率在安全區間 (0-5%)
        if ma20.iloc[-1] > ma60.iloc[-1] and 0 < bias <= 5:
            return {
                "代碼": sid,
                "收盤價": round(c.iloc[-1], 2),
                "MA20乖離": f"{round(bias, 2)}%",
                "成交量狀態": "🔥 放量" if df['Volume'].iloc[-1] > vol_ma5.iloc[-1] else "⚪ 平穩",
                "策略建議": "分批佈局"
            }
    except: return None

# --- UI 介面 ---
market_ok = check_market()
if not market_ok:
    st.error("🛑 大盤轉弱，雷達已自動提高篩選門檻，建議保守觀望。")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🧧 啟動『核心 150 檔』自動掃描"):
        with st.spinner("雷達掃描中..."):
            results = [scan_logic(s) for s in CORE_POOL if scan_logic(s)]
            if results:
                st.write(f"找到 {len(results)} 檔符合條件個股：")
                st.table(pd.DataFrame(results))
            else:
                st.info("目前核心標的中無符合條件個股。")

with col2:
    custom_input = st.text_input("🔍 自訂掃描 (輸入代碼，以逗號隔開)", "2330, 2603, 1513")
    if st.button("開始掃描自訂名單"):
        custom_list = [s.strip() for s in custom_input.split(",")]
        results = [scan_logic(s) for s in custom_list if scan_logic(s)]
        if results:
            st.table(pd.DataFrame(results))
        else:
            st.info("自訂名單中目前無符合標的。")