import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import requests
import ssl

# --- 0. 解決 SSL 憑證報錯 (通關密碼) ---
ssl._create_default_https_context = ssl._create_unverified_context

# --- 1. 網頁基礎設定 ---
st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

st.markdown("<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6A5ACD;'>讓可愛的狗狗們為妳嗅出股市裡的黃金骨頭！(排除金融股版)</p>", unsafe_allow_html=True)

# --- 2. 自動獲取全台股清單功能 ---
@st.cache_data(ttl=3600)
def get_all_stock_list():
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        # 偽裝成瀏覽器並忽略 SSL 檢查
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, verify=False)
        response.encoding = 'big5' # 處理台股網頁亂碼
        
        df = pd.read_html(response.text)[0]
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        
        # 拆分代號與名稱
        stocks = df['有價證券代號及名稱'].str.split('　', expand=True)
        stocks.columns = ['code', 'name']
        
        # 過濾：只要4碼數字 (普通股) 且排除 28 開頭 (金融股)
        clean_list = stocks[
            (stocks['code'].str.len() == 4) & 
            (stocks['code'].str.isdigit()) & 
            (~stocks['code'].str.startswith('28'))
        ]
        return clean_list['code'].tolist()
    except Exception as e:
        # 如果網路真的被擋，提供核心熱門股作為保底
        return ["2330", "2317", "2454", "2603", "3037", "3231", "1513", "2382", "3017", "2609"]

# --- 3. 核心診斷引擎 ---
def diagnose_stock(sid):
    try:
        # 抓取 100 天資料確保計算 MA60 準確
        df = yf.Ticker(f"{sid}.TW").history(period="120d")
        if len(df) < 60: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        # 買點判定邏輯：趨勢向上且乖離率低
        if c > ma20 and ma20 > ma60 and 0 < bias <= 5:
            return {
                "代碼": sid,
                "判定結果": "🟢 汪！適合買入！",
                "汪汪理由": f"股價 {round(c, 1)} 元，非常貼近月線支撐，安全感十足！",
                "乖離率": f"{round(bias, 1)}%",
                "停損價": round(ma20 * 0.95, 1)
            }
        return None
    except:
        return None

# --- 4. 介面呈現 ---

# A. 個股搜尋區
st.subheader("🦴 汪！這檔骨頭能啃嗎？ (個股診斷)")
search_id = st.text_input("輸入股票代碼：", placeholder="例如: 3037")
if search_id:
    with st.spinner("狗狗正在嗅探中..."):
        res = diagnose_stock(search_id)
        if res:
            st.success(f"🐶 【{search_id}】診斷報告：{res['判定結果']}")
            st.info(f"💡 **理由：** {res['汪汪理由']}")
            st.write(f"🚩 **保險：** 如果跌破 {res['停損價']} 元，汪！要乖乖跑掉喔！")
        else:
            st.error(f"❌ 【{search_id}】汪！這檔現在不是好買點。可能漲太高了，或趨勢還在跌。")

st.markdown("---")

# B. 全台股雷達區
st.subheader("🐕‍🦺 全台股尋寶雷達 (排除金融股)")
if st.button("🔥 啟動全台股汪汪大掃描"):
    all_codes = get_all_stock_list()
    total = len(all_codes)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    found_list = []
    
    for i, code in enumerate(all_codes):
        # 更新進度文字
        status_text.text(f"🐾 狗狗們正在大街小巷搜尋中：第 {i+1} / {total} 檔 (已找到 {len(found_list)} 檔)")
        progress_bar.progress((i + 1) / total)
        
        result = diagnose_stock(code)
        if result:
            found_list.append(result)
            
    status_text.success(f"🎉 汪！掃描完成！狗狗們幫主人檢查了 {total} 檔股票。")
    
    if found_list:
        st.write("### 🏆 今日精選黃金骨頭名單")
        st.table(pd.DataFrame(found_list))
    else:
        st.warning("嗚...今天市場裡沒有狗狗想啃的骨頭，建議主人先休息。")
import datetime

# 設定台灣時區偏移量 (UTC+8)
tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.markdown("---")
st.caption(f"🕒 最後更新時間 (台灣)：{now_str} | 汪汪選股所，祝主人發大財！")
