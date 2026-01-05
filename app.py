import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import os
import time

# --- 1. 基礎設定與永久記憶功能 ---
st.set_page_config(page_title="Christine 財運汪汪系統", layout="wide", page_icon="🐶")

DB_FILE = "my_stock_memory.json"

def load_memory():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_memory(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# 初始化 Session State
if 'my_stocks' not in st.session_state:
    st.session_state.my_stocks = load_memory()

# --- 2. 核心邏輯函數 (結合計分、回測與骨頭風險) ---
def analyze_stock_full(sid, buy_p=0):
    try:
        ticker = yf.Ticker(f"{sid}.TW")
        df = ticker.history(period="1y", auto_adjust=False)
        if df.empty or len(df) < 60: return None
        
        # 指標計算
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        last, prev = df.iloc[-1], df.iloc[-2]
        bias = ((last['Close'] - last['MA20']) / last['MA20']) * 100
        
        # 🦴 骨頭風險評估 (基於波動率)
        returns = df['Close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100
        bone_count = min(5, max(1, int(volatility / 10)))
        bones = "🦴" * bone_count
        
        # 💯 100 分計分邏輯
        score = 0
        if last['MA20'] > last['MA60']: score += 25
        if last['MA60'] > df['MA60'].iloc[-5]: score += 25
        if last['Volume']/1000 > 1000: score += 20
        if bias < 10: score += 10
        
        buy_note = "整理中"
        if 0 < bias <= 3.5:
            score += 20
            buy_note = "🎯 絕佳買點"
        elif bias > 10: buy_note = "🚨 乖離過大"
        if last['Volume'] < prev['Volume']: score -= 10
        score = max(0, min(100, score))

        res = {
            "代碼": sid, "現價": round(last['Close'], 1), "得分": score,
            "買點": buy_note, "風險": bones, "乖離": f"{round(bias, 1)}%",
            "MA20": round(last['MA20'], 1)
        }
        if buy_p > 0:
            res["損益%"] = ((last['Close'] - buy_p) / buy_p) * 100
            res["成本"] = buy_p
        return res
    except: return None

# --- 3. 側邊欄：庫存登記與回測參數 ---
with st.sidebar:
    st.title("🐶 汪汪庫存登記")
    sc = st.text_input("股票代碼 (例: 2330)")
    sp = st.number_input("買進成本", min_value=0.0, step=0.1)
    if st.button("➕ 存入永久記憶"):
        if sc and sp > 0:
            st.session_state.my_stocks[sc] = sp
            save_memory(st.session_state.my_stocks)
            st.success(f"汪！{sc} 已記憶")
            time.sleep(1)
            st.rerun()

    if st.session_state.my_stocks:
        st.write("---")
        del_t = st.selectbox("移除庫存：", list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除紀錄"):
            del st.session_state.my_stocks[del_t]
            save_memory(st.session_state.my_stocks)
            st.rerun()

    st.write("---")
    st.header("📊 回測設定")
    hold_days = st.sidebar.slider("買入後持有天數", 5, 20, 10)
    stop_loss = st.sidebar.slider("強制停損 %", 3, 10, 5)

# --- 4. 主畫面 ---
st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>💰 Christine 財運汪汪終極系統</h1>", unsafe_allow_html=True)

# 【上層：指標卡片顯示庫存】
st.subheader("📋 我的永久記憶庫存")
if st.session_state.my_stocks:
    cols = st.columns(4)
    for i, (sid, cost) in enumerate(st.session_state.my_stocks.items()):
        res = analyze_stock_full(sid, cost)
        if res:
            with cols[i % 4]:
                st.metric(label=f"🐶 {sid}", value=f"{res['現價']}", delta=f"{round(res['損益%'],2)}%")
                with st.expander("🔍 詳細診斷"):
                    st.write(f"**得分:** {res['得分']} / 100")
                    st.write(f"**風險:** {res['風險']}")
                    st.write(f"**判定:** {res['買點']}")
                    st.write(f"**停損建議:** {round(res['MA20']*0.97, 1)}")
else: st.info("目前庫存空空，快去左側登記骨頭汪！")

# 【中層：100 分選股選單】
st.markdown("---")
st.subheader("🧧 即時財運 100 分掃描")
scan_list_str = st.text_input("輸入掃描清單 (逗號隔開)", "2330, 2603, 2317, 2454, 3231, 1513, 2303")
scan_list = [s.strip() for s in scan_list_str.split(",")]

if st.button("🚀 開始精準掃描"):
    scan_res = [analyze_stock_full(s) for s in scan_list if analyze_stock_full(s)]
    if scan_res:
        df_show = pd.DataFrame(scan_res)[["代碼", "現價", "得分", "買點", "風險", "乖離"]]
        st.dataframe(df_show.style.background_gradient(subset=['得分'], cmap='YlOrRd'))

# 【下層：歷史回測專區】
st.markdown("---")
st.subheader("📊 歷史勝率回測 (含停損邏輯)")
bt_stock = st.selectbox("選擇回測對象", scan_list)
if st.button(f"🚀 啟動 {bt_stock} 歷史回測"):
    ticker = yf.Ticker(f"{bt_stock}.TW")
    df = ticker.history(period="2y", auto_adjust=False)
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA60'] = df['Close'].rolling(60).mean()
    df['Bias'] = ((df['Close'] - df['MA20']) / df['MA20']) * 100
    df['Signal'] = (df['MA20'] > df['MA60']) & (df['Bias'] > 0) & (df['Bias'] <= 3.5)
    
    trades = []
    for i in range(len(df) - hold_days):
        if df['Signal'].iloc[i]:
            entry = df['Close'].iloc[i]
            hold_period = df.iloc[i+1 : i+hold_days+1]
            if hold_period['Low'].min() < entry * (1 - stop_loss/100):
                trades.append(-stop_loss)
            else:
                trades.append(((df['Close'].iloc[i + hold_days] - entry) / entry) * 100)
    
    if trades:
        col1, col2 = st.columns(2)
        col1.metric("策略勝率", f"{round(len([r for r in trades if r > 0])/len(trades)*100, 1)}%")
        col2.metric("平均報酬", f"{round(np.mean(trades), 2)}%")
        st.bar_chart(trades)
