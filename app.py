import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl
import time

# 環境與時區設定
ssl._create_default_https_context = ssl._create_unverified_context
tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

st.markdown("<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# --- 核心診斷功能 ---
def diagnose_stock(sid):
    try:
        # 使用 fast_info 預先過濾，加快速度
        t = yf.Ticker(f"{sid}.TW")
        df = t.history(period="100d")
        if len(df) < 60: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        if c > ma20 and ma20 > ma60 and 0 < bias <= 5:
            return {
                "代碼": sid,
                "現價": round(c, 1),
                "汪汪指令": f"建議：{round(ma20, 1)} 守住續抱",
                "乖離": f"{round(bias, 1)}%"
            }
    except: return None
    return None

# --- 獲取清單 ---
@st.cache_data(ttl=3600)
def get_all_stock_list():
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        response = requests.get(url, verify=False)
        response.encoding = 'big5'
        df = pd.read_html(response.text)[0]
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        stocks = df['有價證券代號及名稱'].str.split('　', expand=True)
        stocks.columns = ['code', 'name']
        # 先取前 500 檔最活躍的做掃描，確保不會斷線 (或是妳可以自定義數量)
        clean_list = stocks[(stocks['code'].str.len() == 4) & (stocks['code'].str.isdigit()) & (~stocks['code'].str.startswith('28'))]
        return clean_list['code'].tolist()
    except:
        return ["2330", "2317", "2454", "2603", "3037"]

# --- 掃描區塊 (使用 Fragment 避免全頁卡死) ---
@st.fragment
def scanner_section():
    if st.button("🐕‍🦺 啟動全台股汪汪大掃描"):
        all_codes = get_all_stock_list()
        # 為了穩定，我們限制一次掃描 300 檔，避免被伺服器踢掉
        scan_pool = all_codes[:300] 
        total = len(scan_pool)
        
        progress_bar = st.progress(0)
        dog_runner = st.empty()
        found_list = []
        
        for i, code in enumerate(scan_pool):
            progress = (i + 1) / total
            num_spaces = int(progress * 40)
            dog_runner.markdown(f"**{'&nbsp;' * num_spaces}🐕💨 正在嗅探 {code}...**")
            progress_bar.progress(progress)
            
            res = diagnose_stock(code)
            if res: found_list.append(res)
            
            # 每掃描 10 檔休息一下下，防止被 Yahoo 封鎖
            if i % 10 == 0: time.sleep(0.1)
            
        dog_runner.markdown("✨ **汪！前 300 檔精選掃描完成！**")
        if found_list:
            st.table(pd.DataFrame(found_list))
        else:
            st.warning("這區沒找到好骨頭汪！")

# --- 介面呈現 ---
st.subheader("📋 我的汪汪庫存監控")
if 'my_stocks' in st.session_state and st.session_state.my_stocks:
    # 庫存顯示邏輯 (略)
    st.write("顯示庫存中...")
else:
    st.info("快去側邊欄登記庫存汪！")

st.markdown("---")
st.subheader("🐕‍🦺 發現新骨頭 (全台股雷達)")
scanner_section() # 呼叫分段掃描

st.caption(f"🕒 台灣時間：{now_str} | 汪！")