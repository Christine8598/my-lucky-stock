import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="Christine財運汪汪選股所", layout="wide", page_icon="🏮")

st.markdown("<h1 style='text-align: center; color: #E91E63;'>🏮 Christine財運汪汪選股所</h1>", unsafe_allow_html=True)

# --- 2. 獲取全台股清單 (排除金融) ---
@st.cache_data(ttl=3600)
def get_all_stock_list():
    try:
        # 抓取上市櫃整合清單
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        df = pd.read_html(url)[0]
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        stocks = df['有價證券代號及名稱'].str.split('　', expand=True)
        stocks.columns = ['code', 'name']
        # 篩選4碼代號且排除28開頭金融股
        clean_list = stocks[(stocks['code'].str.len() == 4) & (~stocks['code'].str.startswith('28'))]
        return clean_list['code'].tolist()
    except:
        return ["2330", "2317", "2454", "2603", "3037", "3231", "1513", "2382", "3017"]

# --- 3. 核心診斷引擎 (包含原因判定) ---
def diagnose_stock(sid):
    try:
        df = yf.Ticker(f"{sid}.TW").history(period="100d")
        if len(df) < 60: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        # 判定邏輯
        if c > ma20 and ma20 > ma60 and 0 < bias <= 3.5:
            status = "🟢 建議買進"
            reason = "趨勢向上且回檔到安全區，風險低"
        elif c > ma20 and ma20 > ma60 and 3.5 < bias <= 6:
            status = "🟡 稍微觀望"
            reason = "趨勢對但稍微漲高，建議等拉回"
        else:
            return None # 不符合條件的不顯示
            
        return {
            "代碼": sid,
            "判定": status,
            "原因說明": reason,
            "目前價格": round(c, 1),
            "破此價格跑路": round(ma20 * 0.95, 1)
        }
    except: return None

# --- 4. 介面呈現 ---

# A. 個股搜尋區
st.subheader("🔍 單一股票深度診斷")
search_id = st.text_input("輸入股票代碼：", placeholder="例如: 3037")
if search_id:
    res = diagnose_stock(search_id)
    if res:
        st.success(f"### 【{search_id}】診斷結果：{res['判定']}")
        st.write(f"💡 **原因：** {res['原因說明']}")
        st.write(f"💰 **建議操作：** 現價 {res['目前價格']}，停損設在 {res['破此價格跑路']}")
    else:
        st.error(f"❌ 【{search_id}】目前不在買點，或趨勢向下，建議先不要碰。")

st.markdown("---")

# B. 全台股掃描區
st.subheader("🚀 全台股自動掃描 (排除金融股)")
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.write(f"🕒 資料更新時間：{now}")

if st.button("啟動全台股雷達 (掃描1700+檔)"):
    all_codes = get_all_stock_list()
    progress_bar = st.progress(0)
    found_list = []
    
    # 執行掃描
    status_text = st.empty()
    for i, code in enumerate(all_codes):
        if i % 10 == 0: status_text.text(f"正在分析第 {i}/{len(all_codes)} 檔...")
        res = diagnose_stock(code)
        if res: found_list.append(res)
        progress_bar.progress((i + 1) / len(all_codes))
        
    status_text.text("✅ 掃描完成！")
    
    if found_list:
        st.write(f"共找到 {len(found_list)} 檔符合獲利條件的股票：")
        st.table(pd.DataFrame(found_list))
    else:
        st.warning("今天市場氣氛不佳，沒有符合安全買點的股票。")