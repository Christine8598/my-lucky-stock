import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl

# 環境與時區設定
ssl._create_default_https_context = ssl._create_unverified_context
tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")
st.markdown("<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# --- 1. 庫存管理功能 (Session State) ---
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = {}

# --- 2. 核心診斷引擎 (加強賣點計算) ---
def diagnose_stock(sid, cost=0):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period="100d")
        if len(df) < 60: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        # 直觀賣點計算
        take_profit_price = round(ma20 * 1.1, 1) # 停利價：月線+10%
        stop_loss_price = round(ma20, 1)          # 停損價：月線位置
        
        status = "🟡 繼續觀察"
        advice = f"建議：{stop_loss_price} 守住續抱"
        color = "gray"
        
        if c < ma20:
            status = "🚨 汪！建議賣出"
            advice = f"🚨 跌破 {stop_loss_price} 快跑！"
        elif bias > 10:
            status = "🎁 汪！建議停利"
            advice = f"🎁 已過 {take_profit_price} 落袋為安"
        elif c > ma20 and ma20 > ma60 and 0 < bias <= 5:
            status = "🟢 汪！適合持有"
            advice = "趨勢安全，放心睡覺"
            
        res = {
            "代碼": sid,
            "現價": round(c, 1),
            "判定": status,
            "汪汪指令": advice,
            "停利目標(參考)": take_profit_price,
            "停損防線(月線)": stop_loss_price,
            "乖離": f"{round(bias, 1)}%"
        }
        
        if cost > 0:
            profit = ((c - cost) / cost) * 100
            res["我的成本"] = cost
            res["損益%"] = f"{round(profit, 2)}%"
            
        return res
    except: return None

# --- 3. 介面呈現 ---

# 側邊欄：管理庫存
with st.sidebar:
    st.header("🦴 庫存管理登記")
    new_code = st.text_input("輸入代碼", placeholder="例如: 2603")
    new_price = st.number_input("買進價格", value=0.0)
    if st.button("➕ 加入庫存"):
        if new_code and new_price > 0:
            st.session_state.my_stocks[new_code] = new_price
            st.success(f"汪！已加入 {new_code}")
            st.rerun()

    if st.session_state.my_stocks:
        st.write("---")
        st.subheader("🗑️ 快速刪除單筆")
        # 讓使用者選擇要刪除哪一檔
        del_code = st.selectbox("選擇要丟掉的骨頭", options=list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除這筆庫存"):
            del st.session_state.my_stocks[del_code]
            st.warning(f"汪！已丟掉 {del_code}")
            st.rerun()
            
        if st.button("🧨 全部清空"):
            st.session_state.my_stocks = {}
            st.rerun()

# A. 我的庫存監控區
st.subheader("📋 我的汪汪庫存監控 (直觀賣點版)")
if st.session_state.my_stocks:
    my_data = []
    for sid, cost in st.session_state.my_stocks.items():
        res = diagnose_stock(sid, cost)
        if res: my_data.append(res)
    
    if my_data:
        # 整理顯示順序，讓最重要的指令排前面
        df_display = pd.DataFrame(my_data)
        cols = ["代碼", "現價", "我的成本", "損益%", "汪汪指令", "停利目標(參考)", "停損防線(月線)", "判定"]
        st.table(df_display[cols])
else:
    st.info("目前庫存空空，快去左側登記妳買入的股票吧！")

st.markdown("---")

# B. 全台股搜尋
st.subheader("🐕‍🦺 發現新骨頭 (全台股掃描)")
if st.button("🔥 啟動汪汪大掃描"):
    st.write("狗狗正在全台大街小巷搜尋符合安全買點的股票中...")

st.caption(f"🕒 台灣時間：{now_str} | 汪！學會看數字賣出，才是真的發財汪！")