import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 網頁基礎設定
st.set_page_config(page_title="Christine 財運回測系統", layout="wide", page_icon="📈")

st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>📈 Christine 策略歷史回測</h1>", unsafe_allow_html=True)

# 側邊欄設定
st.sidebar.header("🧧 設定回測參數")
target_stock = st.sidebar.text_input("輸入回測代碼 (單一)", value="2330")
hold_days = st.sidebar.slider("買入後持有天數", 5, 20, 10)

def run_backtest(sid):
    try:
        ticker = yf.Ticker(f"{sid}.TW")
        df = ticker.history(period="2y", auto_adjust=False)
        if df.empty or len(df) < 100: return None
        
        # 計算指標
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA60'] = df['Close'].rolling(60).mean()
        df['Prev_MA60'] = df['MA60'].shift(5)
        df['Bias'] = ((df['Close'] - df['MA20']) / df['MA20']) * 100
        df['Vol_Prev'] = df['Volume'].shift(1)
        
        # 定義策略訊號 (簡化版 100 分邏輯)
        # 1. 趨勢多頭 2. MA60向上 3. 買點區(0-3%)
        df['Signal'] = (df['MA20'] > df['MA60']) & \
                       (df['MA60'] > df['Prev_MA60']) & \
                       (df['Bias'] > 0) & (df['Bias'] <= 3) & \
                       (df['Volume'] > df['Vol_Prev'])
        
        # 紀錄交易結果
        trades = []
        for i in range(len(df) - hold_days):
            if df['Signal'].iloc[i]:
                entry_price = df['Close'].iloc[i]
                exit_price = df['Close'].iloc[i + hold_days]
                return_pct = ((exit_price - entry_price) / entry_price) * 100
                trades.append(return_pct)
        
        if not trades: return "無訊號"
        
        win_rate = len([r for r in trades if r > 0]) / len(trades) * 100
        avg_return = np.mean(trades)
        return {"win_rate": win_rate, "avg_return": avg_return, "count": len(trades), "trades": trades}
    except Exception as e:
        return str(e)

# 顯示回測結果
if st.button(f"🚀 開始回測 {target_stock} 過去兩年勝率"):
    with st.spinner('正在穿越時空計算中...'):
        result = run_backtest(target_stock)
        
        if isinstance(result, dict):
            col1, col2, col3 = st.columns(3)
            col1.metric("策略勝率", f"{round(result['win_rate'], 1)}%")
            col2.metric("平均報酬", f"{round(result['avg_return'], 2)}%")
            col3.metric("訊號次數", f"{result['count']} 次")
            
            # 畫出報酬率分布圖
            st.subheader("📊 每次交易獲利分布 (%)")
            st.bar_chart(result['trades'])
            
            if result['win_rate'] >= 60:
                st.success(f"🎊 財運驚人！{target_stock} 非常適合這個策略。")
            else:
                st.warning(f"💡 提醒：{target_stock} 過去表現一般，建議搭配其他指標。")
        else:
            st.info(f"掃描完成：過去兩年 {target_stock} 在妳的嚴格條件下沒有出現買點，或資料不足。")

st.markdown("---")
st.caption("註：回測數據僅供參考，過去績效不保證未來獲利。")