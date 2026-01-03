import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 網頁基礎設定
st.set_page_config(page_title="Christine Lin 財運汪汪系統", layout="wide", page_icon="🧧")

st.markdown("""
    <h1 style='text-align: center; color: #FF4B4B;'>💰 Christine Lin 選股與回測系統</h1>
    <p style='text-align: center; font-weight: bold;'>—— 永久免費雲端版 ——</p>
    """, unsafe_allow_html=True)

# 2. 側邊欄：名單輸入與回測設定
st.sidebar.header("🧧 財運清單設定")
input_stocks = st.sidebar.text_area("輸入台股代碼 (逗號隔開)", value="2330, 2603, 2317, 2454, 3231")
stock_list = [s.strip() for s in input_stocks.split(",") if s.strip()]

st.sidebar.markdown("---")
st.sidebar.header("📊 回測參數設定")
hold_days = st.sidebar.slider("買入後持有天數", 5, 20, 10)

# --- 核心邏輯函數 ---
def analyze_stock(sid):
    try:
        ticker = yf.Ticker(f"{sid}.TW")
        df = ticker.history(period="1y", auto_adjust=False)
        if df.empty or len(df) < 60: return None
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        last, prev = df.iloc[-1], df.iloc[-2]
        prev_ma60 = df['MA60'].iloc[-5]
        bias = ((last['Close'] - last['MA20']) / last['MA20']) * 100
        
        score = 0
        if last['MA20'] > last['MA60']: score += 25
        if last['MA60'] > prev_ma60: score += 25
        if last['Volume']/1000 > 1000: score += 20
        if bias < 10: score += 10
        
        buy_note = "整理中"
        if 0 < bias <= 3:
            score += 20
            buy_note = "🎯 絕佳買點"
        elif bias > 10: buy_note = "🚨 乖離過大"
        
        if last['Volume'] < prev['Volume']: score -= 10
        score = max(0, min(100, score))

        return {
            "代碼": sid, "現價": round(last['Close'], 2), "20MA乖離": f"{round(bias, 2)}%",
            "財運得分": score, "買點判定": buy_note, "參考停損": round(last['MA20'] * 0.97, 2)
        }
    except: return None

# --- 第一部分：選股總覽 ---
if st.button("🧧 執行 100 分財運掃描"):
    results = [analyze_stock(sid) for sid in stock_list if analyze_stock(sid)]
    if results:
        st.subheader("📋 財運精選總覽 (滿分 100)")
        res_df = pd.DataFrame(results)
        st.dataframe(res_df.style.background_gradient(subset=['財運得分'], cmap='YlOrRd'))
        
        st.subheader("🔍 趨勢圖表分析")
        tabs = st.tabs(stock_list)
        for i, sid in enumerate(stock_list):
            with tabs[i]:
                data = yf.Ticker(f"{sid}.TW").history(period="100d")
                data['MA20'] = data['Close'].rolling(20).mean()
                data['MA60'] = data['Close'].rolling(60).mean()
                st.line_chart(data[['Close', 'MA20', 'MA60']])

# --- 第二部分：歷史回測專區 ---
st.markdown("---")
st.subheader("📊 歷史勝率回測 (根據『絕佳買點』訊號)")
bt_stock = st.selectbox("選擇要回測的代碼", stock_list)

if st.button(f"🚀 開始回測 {bt_stock} 過去兩年勝率"):
    with st.spinner('正在分析歷史數據...'):
        ticker = yf.Ticker(f"{bt_stock}.TW")
        df = ticker.history(period="2y", auto_adjust=False)
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        df['Bias'] = ((df['Close'] - df['MA20']) / df['MA20']) * 100
        # 訊號：多頭排列 + 買點區(0-3%)
        df['Signal'] = (df['MA20'] > df['MA60']) & (df['Bias'] > 0) & (df['Bias'] <= 3)
        
        trades = []
        for i in range(len(df) - hold_days):
            if df['Signal'].iloc[i]:
                entry = df['Close'].iloc[i]
                exit = df['Close'].iloc[i + hold_days]
                trades.append(((exit - entry) / entry) * 100)
        
        if trades:
            win_rate = len([r for r in trades if r > 0]) / len(trades) * 100
            col1, col2 = st.columns(2)
            col1.metric("策略勝率", f"{round(win_rate, 1)}%")
            col2.metric("平均報酬", f"{round(np.mean(trades), 2)}%")
            st.bar_chart(trades)
        else:
            st.info("過去兩年該股未出現符合『絕佳買點』的訊號。")