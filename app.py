import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import ssl
import time

# --- 0. 基礎設定 ---
ssl._create_default_https_context = ssl._create_unverified_context
tw_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
now_str = tw_time.strftime("%Y-%m-%d %H:%M:%S")

st.set_page_config(page_title="Christine 財運汪汪選股所", layout="wide", page_icon="🐶")

# --- 1. 核心邏輯定義 ---

@st.cache_data(ttl=3600)
def get_full_stock_list():
    """獲取完整的台股清單 (包含所有開頭代碼)"""
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, verify=False)
        response.encoding = 'big5'
        df = pd.read_html(response.text)[0]
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        stocks = df['有價證券代號及名稱'].str.split('　', expand=True)
        stocks.columns = ['code', 'name']
        # 篩選：4碼數字且排除 28 金融股
        clean = stocks[(stocks['code'].str.len() == 4) & (stocks['code'].str.isdigit()) & (~stocks['code'].str.startswith('28'))]
        return sorted(list(set(clean['code'].tolist()))) # 確保排序且不重複
    except:
        return [str(i) for i in range(1101, 9999)] # 失敗時的暴力保底

def diagnose_stock(sid):
    """偵測買賣點邏輯"""
    try:
        # 為了全量掃描，我們只抓最近 80 天的資料以加快反應
        df = yf.Ticker(f"{sid}.TW").history(period="80d")
        if len(df) < 40: return None
        
        c = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        bias = ((c - ma20) / ma20) * 100
        
        # 嚴格篩選符合買點的狗狗
        if c > ma20 and ma20 > ma60 and 0 < bias <= 5:
            return {
                "代碼": sid,
                "現價": round(c, 1),
                "判定": "🟢 適合買入",
                "汪汪指令": f"防守價: {round(ma20, 1)}",
                "乖離": f"{round(bias, 1)}%"
            }
    except:
        return None
    return None

# --- 2. 側邊欄 ---
with st.sidebar:
    st.title("🦴 汪汪庫存登記")
    if 'my_stocks' not in st.session_state:
        st.session_state.my_stocks = {}
    with st.form("add_stock", clear_on_submit=True):
        input_code = st.text_input("代碼")
        input_price = st.number_input("買進成本", min_value=0.0)
        if st.form_submit_button("➕ 加入庫存"):
            if input_code and input_price > 0:
                st.session_state.my_stocks[input_code] = input_price
                st.rerun()
    if st.session_state.my_stocks:
        st.write("---")
        del_target = st.selectbox("要刪除哪筆？", options=list(st.session_state.my_stocks.keys()))
        if st.button("❌ 刪除"):
            del st.session_state.my_stocks[del_target]
            st.rerun()

# --- 3. 主畫面 ---
st.markdown("<h1 style='text-align: center; color: #FF69B4;'>🐾 Christine 財運汪汪選股所 🐾</h1>", unsafe_allow_html=True)

# A. 庫存監控
st.subheader("📋 我的汪汪庫存監控")
if st.session_state.my_stocks:
    my_results = []
    for sid, cost in st.session_state.my_stocks.items():
        # 庫存診斷使用較完整的數據
        res = diagnose_stock(sid)
        if res:
            res["成本"] = cost
            res["損益%"] = f"{round(((res['現價'] - cost) / cost) * 100, 2)}%"
            my_results.append(res)
    if my_results:
        st.table(pd.DataFrame(my_results))
else:
    st.info("💡 汪！請點擊側邊欄登記庫存喔！")

st.markdown("---")

# B. 終極全台股地毯掃描
st.subheader("🐕‍🦺 發現新骨頭 (全台股地毯式搜索)")
st.write("點擊按鈕後，狗狗將開始巡邏全台灣 1,700+ 檔股票，請耐心等候狗狗回家！")

if st.button("🚀 啟動 1700+ 檔地毯式大掃描"):
    all_codes = get_full_stock_list()
    total = len(all_codes)
    
    with st.status("🐕 狗狗正在穿裝備，準備巡邏全台灣...", expanded=True) as status:
        progress_bar = st.progress(0)
        dog_runner = st.empty()
        found_list = []
        
        # 分批執行，每 200 檔稍微更新一次狀態
        for i, code in enumerate(all_codes):
            pct = (i + 1) / total
            # 狗狗奔跑視覺
            num_s = int(pct * 30)
            dog_runner.markdown(f"**{'&nbsp;' * num_s}🐕💨 正在嗅探第 {i+1}/{total} 檔：{code}**")
            progress_bar.progress(pct)
            
            res = diagnose_stock(code)
            if res:
                found_list.append(res)
            
            # 每掃描 100 檔主動讓網頁稍微喘息，避免卡死
            if i % 100 == 0:
                time.sleep(0.01)
                
        status.update(label=f"✅ 汪！全台股 {total} 檔掃描完成！", state="complete", expanded=False)

    if found_list:
        st.write(f"### 🏆 狗狗在全台灣挖到的精華骨頭 (共 {len(found_list)} 檔)")
        st.table(pd.DataFrame(found_list)[["代碼", "現價", "汪汪指令", "乖離"]])
    else:
        st.warning("天啊！狗狗跑遍全台灣都沒找到符合條件的骨頭，建議主人先空手觀望。")

st.caption(f"🕒 台灣時間：{now_str} | 汪！這就是最強的財運汪汪雷達！")