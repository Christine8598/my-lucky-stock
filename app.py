import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 系統設定
st.set_page_config(page_title="Christine財運汪汪實戰決策系統", layout="wide", page_icon="⚖️")

st.markdown("""
    <h1 style='text-align: center; color: #1E88E5;'>⚖️ Christine 實戰決策輔助系統</h1>
    <p style='text-align: center;'><b>拒絕主觀偏好：基於統計數據與大盤濾網的紀律工具</b></p>
    """, unsafe_allow_html=True)

# 2. 自動掃描池 (台灣權值股)
DEFAULT_POOL = ["2330", "2317", "2454", "2308", "2382", "2603", "2609", "3231", "1513", "1504", "2357"]

# 3. 大盤絕對濾網 (強迫風控)
def check_market_gate():
    try:
        m = yf.Ticker("^TWII").history(period="60d")
        is_safe = m['Close'].iloc[-1] > m['Close'].rolling(20).mean().iloc[-1]
        return is_safe, m['Close'].iloc[-1]
    except: return False, 0

market_safe, mkt_price = check_market_gate()

# 4. 核心邏輯：多維度評估 (非主觀加分)
def advanced_rank(sid):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period="150d", auto_adjust=True)
        if len(df) < 60: return None
        
        # 指標計算
        c = df['Close']
        ma20 = c.rolling(20).mean()
        ma60 = c.rolling(60).mean()
        
        # A. 趨勢維度 (昨收盤資料)
        is_bull = (ma20.iloc[-1] > ma60.iloc[-1]) and (ma60.iloc[-1] > ma60.iloc[-5])
        # B. 買點維度 (乖離率)
        bias = ((c.iloc[-1] - ma20.iloc[-1]) / ma20.iloc[-1]) * 100
        # C. 動能維度 (成交量變化)
        vol_up = df['Volume'].iloc[-1] > df['Volume'].rolling(5).mean().iloc[-1]
        
        # 篩選條件 (不再給分，改為門檻制)
        if is_bull and (0 < bias <= 4):
            return {
                "代碼": sid,
                "收盤價": round(c.iloc[-1], 2),
                "MA20乖離": f"{round(bias, 2)}%",
                "動能狀態": "🔥 放量" if vol_up else "⚪ 平淡",
                "執行策略": "明日開盤分批進場",
                "嚴格停損價": round(ma20.iloc[-1] * 0.95, 2)
            }
    except: return None

# --- UI 介面 ---
if not market_safe:
    st.error(f"🛑 大盤收盤價 ({round(mkt_price,0)}) 跌破月線：系統已鎖定，空頭環境不建議任何買入操作。")
else:
    st.success("✅ 大盤趨勢向上：雷達掃描權限已開啟。")
    if st.button("🚀 執行昨日收盤數據雷達"):
        results = [advanced_rank(sid) for sid in DEFAULT_POOL if advanced_rank(sid)]
        if results:
            st.subheader("📋 符合『縮量回測支撐』個股")
            st.table(pd.DataFrame(results))
            st.warning("⚠️ 警告：以上結果基於昨日收盤，今日開盤若跳空開高 > 2% 則不建議追價。")
        else:
            st.info("目前無符合『低風險回測區』之標的。")

st.markdown("---")
st.markdown("""
### 📢 投資風險揭露與免責聲明
* **時間落後性**：本系統所有資料均為「盤後資料」，不代表今日盤中走勢。
* **非投資建議**：系統得分與判定僅為技術指標之統計結果，不保證獲利。
* **風險控管**：投資人應自行設定停損點，並嚴格執行。
""")