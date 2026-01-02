import streamlit as st
import yfinance as yf
import pandas as pd

# 1. 網頁基礎設定
st.set_page_config(page_title="Christine Lin 財運旺旺選股", layout="wide", page_icon="🧧")

st.markdown("""
    <h1 style='text-align: center; color: #FF4B4B;'>💰 Christine Lin 選股系統 (財運旺旺)</h1>
    <p style='text-align: center; font-weight: bold;'>精確 100 分制：只有完美買點才是滿分</p>
    """, unsafe_allow_html=True)

# 2. 側邊欄設定
st.sidebar.header("🧧 財運名單")
input_stocks = st.sidebar.text_area("輸入台股代碼 (逗號隔開)", value="2330, 2603, 2317, 2454, 3231")
stock_list = [s.strip() for s in input_stocks.split(",") if s.strip()]

def analyze_stock(sid):
    try:
        ticker = yf.Ticker(f"{sid}.TW")
        df = ticker.history(period="1y", auto_adjust=False)
        if df.empty or len(df) < 60: return None
        
        # 指標計算
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev_ma60 = df['MA60'].iloc[-5]
        
        # 基礎邏輯
        is_bull = last['MA20'] > last['MA60']
        is_trend_up = last['MA60'] > prev_ma60
        vol_today = last['Volume'] / 1000
        vol_yesterday = prev['Volume'] / 1000
        bias = ((last['Close'] - last['MA20']) / last['MA20']) * 100
        
        # --- 滿分 100 計分邏輯 ---
        score = 0
        if is_bull: score += 25
        if is_trend_up: score += 25
        if vol_today > 1000: score += 20
        if bias < 10: score += 10
        
        # 🟢 買點加分 (0~3% 加 20 分)
        buy_note = "整理中"
        if 0 < bias <= 3:
            score += 20
            buy_note = "🎯 絕佳買點"
        elif bias > 10:
            buy_note = "🚨 乖離過大"
            
        # 🔴 量縮扣分 (量縮扣 10 分)
        vol_note = "增量"
        if vol_today < vol_yesterday:
            score -= 10
            vol_note = "量縮"
        
        # 確保分數區間在 0~100
        score = max(0, min(100, score))

        return {
            "代碼": sid,
            "現價": round(last['Close'], 2),
            "20MA乖離": f"{round(bias, 2)}%",
            "量能態勢": f"{vol_note} ({int(vol_today)}張)",
            "財運得分": score,
            "買點判定": buy_note,
            "參考停損": round(last['MA20'] * 0.97, 2)
        }
    except: return None

# 3. 執行按鈕
if st.button("🧧 執行 100 分財運掃描"):
    results = []
    with st.spinner('正在精選滿分個股...'):
        for sid in stock_list:
            res = analyze_stock(sid)
            if res: results.append(res)
    
    if results:
        res_df = pd.DataFrame(results)
        st.subheader("📋 財運精選總覽 (滿分 100)")
        
        # 美化表格
        def highlight_100(val):
            color = 'red' if val == 100 else 'black'
            weight = 'bold' if val == 100 else 'normal'
            return f'color: {color}; font-weight: {weight}'

        st.dataframe(res_df.style.applymap(highlight_100, subset=['財運得分'])
                     .background_gradient(subset=['財運得分'], cmap='YlOrRd'))
        
        st.subheader("🔍 趨勢圖表分析")
        tabs = st.tabs(stock_list)
        for i, sid in enumerate(stock_list):
            with tabs[i]:
                data = yf.Ticker(f"{sid}.TW").history(period="100d")
                data['MA20'] = data['Close'].rolling(20).mean()
                data['MA60'] = data['Close'].rolling(60).mean()
                st.line_chart(data[['Close', 'MA20', 'MA60']])
    else:
        st.error("代碼錯誤或無資料")

st.info("💡 **滿分攻略：** 必須滿足『趨勢多頭』、『長線向上』、『爆量攻擊』且『回測紅線 3% 內』才能獲得 100 分！")