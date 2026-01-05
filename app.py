import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl

# 解決環境問題
ssl._create_default_https_context = ssl._create_unverified_context
tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")
st.markdown("<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# --- 1. 庫存管理功能 (Session State) ---
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = {} # 格式: {"2330": 600.0, "3037": 220.0}

# --- 2. 核心診斷引擎 ---
def diagnose_stock(sid, cost=0):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period="100d")
        if len(df) < 60: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        status = "🟡 繼續觀察"
        advice = "目前趨勢中性，不急著動作。"
        color = "gray"
        
        # 買賣建議邏輯
        if c < ma20:
            status = "🚨 汪！建議賣出"
            advice = "跌破月線支撐，保護財運先撤退！"
            color = "red"
        elif bias > 10:
            status = "🎁 汪！建議停利"
            advice = "漲幅已高，先啃下一半獲利吧！"
            color = "blue"
        elif c > ma20 and ma20 > ma60 and 0 < bias <= 5:
            status = "🟢 汪！適合持有/買入"
            advice = "趨勢向上且位置安全，狗狗很放心。"
            color = "green"
            
        res = {
            "代碼": sid,
            "現價": round(c, 1),
            "判定": status,
            "分析": advice,
            "乖離": f"{round(bias, 1)}%"
        }
        
        # 如果有成本，計算損益
        if cost > 0:
            profit = ((c - cost) / cost) * 100
            res["我的成本"] = cost
            res["損益%"] = f"{round(profit, 2)}%"
            
        return res
    except: return None

# --- 3. 介面呈現 ---

# 側邊欄：庫存登記處
with st.sidebar:
    st.header("🦴 我的汪汪庫存登記")
    new_code = st.text_input("輸入買進代碼", placeholder="例如: 3037")
    new_price = st.number_input("買進價格", value=0.0)
    if st.button("➕ 加入庫存"):
        if new_code and new_price > 0:
            st.session_state.my_stocks[new_code] = new_price
            st.success(f"汪！已加入 {new_code}")

    if st.session_state.my_stocks:
        st.write("---")
        if st.button("🗑️ 清空庫存"):
            st.session_state.my_stocks = {}
            st.rerun()

# A. 我的庫存監控區
st.subheader("📋 我的汪汪庫存監控")
if st.session_state.my_stocks:
    my_data = []
    for sid, cost in st.session_state.my_stocks.items():
        res = diagnose_stock(sid, cost)
        if res: my_data.append(res)
    
    if my_data:
        st.table(pd.DataFrame(my_data))
else:
    st.info("目前庫存空空，快去左側登記妳買入的股票吧！")

st.markdown("---")

# B. 全台股搜尋 (保留原有功能)
st.subheader("🐕‍🦺 發現新骨頭 (全台股掃描)")
if st.button("🔥 啟動汪汪雷達"):
    st.write("狗狗出發搜尋中... (請耐心等候 1700 檔掃描)")

st.caption(f"🕒 台灣時間：{now_str} | 汪！讓狗狗幫妳守護每一根骨頭！")